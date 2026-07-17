from __future__ import annotations

import asyncio
import base64
import hashlib
import logging
import os
from collections.abc import Sequence
from pathlib import Path
from typing import Any, Optional, Union
from uuid import uuid4

import httpx
from dotenv import load_dotenv
from fastapi import FastAPI, File, Form, HTTPException, UploadFile
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy.exc import SQLAlchemyError

from .db import (
    LLMCallPayload,
    init_db,
    list_calls,
    list_calls_by_vector_query,
    list_calls_missing_embeddings,
    save_call,
    update_call_embedding,
)
from .storage import MinioStorage, MinioStorageError


ROOT_ENV_PATH = Path(__file__).resolve().parents[2] / ".env"
load_dotenv(ROOT_ENV_PATH)

OPENROUTER_API_URL = "https://openrouter.ai/api/v1/chat/completions"
OPENROUTER_EMBEDDING_API_URL = "https://openrouter.ai/api/v1/embeddings"
OPENROUTER_EMBEDDING_MODEL = os.getenv("OPENROUTER_EMBEDDING_MODEL", "openai/text-embedding-3-small")
VECTOR_MIN_RELEVANCE = float(os.getenv("VECTOR_MIN_RELEVANCE", "0.18"))
OPENROUTER_RETRY_ATTEMPTS = max(1, int(os.getenv("OPENROUTER_RETRY_ATTEMPTS", "3")))
OPENROUTER_RETRY_BACKOFF_SECONDS = max(0.0, float(os.getenv("OPENROUTER_RETRY_BACKOFF_SECONDS", "1")))
OPENROUTER_RETRYABLE_STATUSES = {502, 503, 504}
OPENROUTER_FALLBACK_MODELS = [
    value.strip() for value in os.getenv("OPENROUTER_FALLBACK_MODELS", "").split(",") if value.strip()
]

app = FastAPI(title="ArchitekturBild Backend", version="0.1.0")
logger = logging.getLogger(__name__)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=False,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.on_event("startup")
async def on_startup() -> None:
    try:
        init_db()
    except SQLAlchemyError as exc:
        raise RuntimeError(
            "PostgreSQL connection failed. Check DATABASE_URL and database availability."
        ) from exc
    try:
        app.state.storage = MinioStorage.from_env()
    except MinioStorageError as exc:
        raise RuntimeError(f"MinIO configuration/startup failed: {exc}") from exc
    await backfill_missing_embeddings()


def compose_embedding_text(
    model: Optional[str], filename: Optional[str], prompt: Optional[str], description: Optional[str]
) -> str:
    return " \n ".join([str(value).strip() for value in [model, filename, prompt, description] if value and str(value).strip()])


def parse_openrouter_message_content(response_json: dict[str, Any]) -> str:
    content = response_json["choices"][0]["message"]["content"]
    if isinstance(content, str):
        text_content = content.strip()
        if text_content:
            return text_content
        raise ValueError("Message content is empty")
    if isinstance(content, Sequence):
        parts: list[str] = []
        for entry in content:
            if isinstance(entry, dict) and entry.get("type") == "text":
                text_value = str(entry.get("text") or "").strip()
                if text_value:
                    parts.append(text_value)
        if parts:
            return "\n".join(parts)
        raise ValueError("No text parts in message content sequence")
    raise ValueError("Unsupported message content type")


def extract_error_body_text(response: httpx.Response) -> str:
    try:
        return response.text or ""
    except Exception:
        return ""


def is_html_error_response(content_type: str, body_text: str) -> bool:
    normalized_content_type = content_type.lower()
    stripped = body_text.lstrip()
    return "text/html" in normalized_content_type or stripped.startswith("<!DOCTYPE html") or stripped.startswith("<html")


def build_openrouter_error_detail(
    *,
    request_id: str,
    model: str,
    status_code: int,
    content_type: str,
    body_text: str,
) -> dict[str, Union[str, int]]:
    if is_html_error_response(content_type=content_type, body_text=body_text):
        return {
            "kind": "openrouter_html_error",
            "message": f"OpenRouter upstream error ({status_code})",
            "status_code": status_code,
            "request_id": request_id,
            "model": model,
            "html": body_text,
        }
    return {
        "kind": "openrouter_error",
        "message": f"OpenRouter upstream error ({status_code}): {body_text}",
        "status_code": status_code,
        "request_id": request_id,
        "model": model,
    }


async def create_embedding(text_value: str) -> list[float]:
    api_key = os.getenv("OPENROUTER_API_KEY")
    if not api_key:
        raise RuntimeError("OPENROUTER_API_KEY is missing in root .env")
    if not text_value.strip():
        raise RuntimeError("Embedding input text is empty")

    headers = {
        "Authorization": f"Bearer {api_key}",
        "Content-Type": "application/json",
        "HTTP-Referer": "http://localhost",
        "X-Title": "ArchitekturBild",
    }
    payload = {
        "model": OPENROUTER_EMBEDDING_MODEL,
        "input": text_value,
    }
    try:
        async with httpx.AsyncClient(timeout=60.0) as client:
            response = await client.post(OPENROUTER_EMBEDDING_API_URL, headers=headers, json=payload)
    except httpx.RequestError as exc:
        raise RuntimeError(f"OpenRouter embedding request failed: {exc}") from exc

    if response.status_code >= 400:
        raise RuntimeError(f"OpenRouter embedding error: {response.text}")

    try:
        response_json = response.json()
        vector = response_json["data"][0]["embedding"]
        if not isinstance(vector, list) or not vector:
            raise ValueError("Missing embedding vector")
        return [float(value) for value in vector]
    except (KeyError, IndexError, TypeError, ValueError) as exc:
        raise RuntimeError("Unexpected OpenRouter embedding response format") from exc


async def backfill_missing_embeddings(max_items: int = 200) -> None:
    try:
        candidates = list_calls_missing_embeddings(limit=max_items)
    except SQLAlchemyError:
        return

    for candidate in candidates:
        text_value = compose_embedding_text(
            candidate.get("model"),
            candidate.get("image_filename"),
            candidate.get("system_prompt"),
            candidate.get("description"),
        )
        if not text_value:
            continue
        try:
            embedding = await create_embedding(text_value)
            call_id = candidate.get("id")
            if isinstance(call_id, int):
                update_call_embedding(call_id=call_id, embedding=embedding)
        except Exception:
            continue


@app.get("/health")
async def health() -> dict[str, str]:
    return {"status": "ok"}


@app.get("/api/history")
async def read_history(
    limit: int = 50,
    vector_query: Optional[str] = None,
) -> dict[str, list[dict[str, Union[str, int, float, None]]]]:
    normalized_limit = max(1, min(limit, 200))
    try:
        normalized_vector_query = (vector_query or "").strip()
        if normalized_vector_query:
            query_embedding = await create_embedding(normalized_vector_query)
            items = list_calls_by_vector_query(
                query_embedding=query_embedding,
                limit=normalized_limit,
                min_relevance=VECTOR_MIN_RELEVANCE,
            )
        else:
            items = list_calls(limit=normalized_limit)
    except SQLAlchemyError as exc:
        raise HTTPException(
            status_code=500,
            detail="Failed to load history from PostgreSQL",
        ) from exc
    except RuntimeError as exc:
        raise HTTPException(
            status_code=502,
            detail=str(exc),
        ) from exc
    storage = app.state.storage
    for item in items:
        bucket = item.get("storage_bucket")
        object_key = item.get("storage_object_key")
        if isinstance(bucket, str) and bucket and isinstance(object_key, str) and object_key:
            try:
                item["image_url"] = storage.presigned_url(bucket=bucket, object_key=object_key)
            except MinioStorageError:
                item["image_url"] = None
        else:
            item["image_url"] = None
    return {"items": items}


@app.post("/api/analyze")
async def analyze_image(
    file: UploadFile = File(...),
    system_prompt: str = Form(...),
    model: str = Form(...),
) -> dict[str, str]:
    storage = app.state.storage
    api_key = os.getenv("OPENROUTER_API_KEY")
    if not api_key:
        raise HTTPException(
            status_code=500,
            detail="OPENROUTER_API_KEY is missing in root .env",
        )

    if not file.content_type or not file.content_type.startswith("image/"):
        raise HTTPException(status_code=400, detail="Uploaded file must be an image")

    image_bytes = await file.read()
    if not image_bytes:
        raise HTTPException(status_code=400, detail="Uploaded image is empty")

    encoded_image = base64.b64encode(image_bytes).decode("utf-8")
    image_data_url = f"data:{file.content_type};base64,{encoded_image}"
    image_sha256 = hashlib.sha256(image_bytes).hexdigest()

    headers = {
        "Authorization": f"Bearer {api_key}",
        "Content-Type": "application/json",
        "HTTP-Referer": "http://localhost",
        "X-Title": "ArchitekturBild",
    }
    request_id = uuid4().hex[:12]
    candidate_models = [model, *OPENROUTER_FALLBACK_MODELS]
    deduplicated_models: list[str] = []
    for candidate in candidate_models:
        if candidate not in deduplicated_models:
            deduplicated_models.append(candidate)

    response: Optional[httpx.Response] = None
    response_json: dict[str, Any] = {}
    final_model = model
    final_body_text = ""
    final_content_type = ""
    final_status_code: Optional[int] = None
    last_request_error: Optional[httpx.RequestError] = None
    completed = False

    for model_index, candidate_model in enumerate(deduplicated_models):
        final_model = candidate_model
        fallback_used = model_index > 0
        for attempt in range(1, OPENROUTER_RETRY_ATTEMPTS + 1):
            payload = {
                "model": candidate_model,
                "messages": [
                    {"role": "system", "content": system_prompt},
                    {
                        "role": "user",
                        "content": [
                            {
                                "type": "text",
                                "text": "Describe the image in clear, useful detail.",
                            },
                            {"type": "image_url", "image_url": {"url": image_data_url}},
                        ],
                    },
                ],
            }
            try:
                async with httpx.AsyncClient(timeout=60.0) as client:
                    response = await client.post(
                        OPENROUTER_API_URL,
                        headers=headers,
                        json=payload,
                    )
                final_status_code = response.status_code
                final_content_type = response.headers.get("content-type") or ""
                final_body_text = extract_error_body_text(response)
            except httpx.RequestError as exc:
                last_request_error = exc
                logger.warning(
                    "openrouter_request_error request_id=%s model=%s attempt=%s/%s fallback_used=%s error=%s",
                    request_id,
                    candidate_model,
                    attempt,
                    OPENROUTER_RETRY_ATTEMPTS,
                    fallback_used,
                    exc,
                )
                if attempt < OPENROUTER_RETRY_ATTEMPTS:
                    await asyncio.sleep(OPENROUTER_RETRY_BACKOFF_SECONDS * (2 ** (attempt - 1)))
                continue

            if response.status_code < 400:
                try:
                    response_json = response.json()
                    description = parse_openrouter_message_content(response_json)
                except (KeyError, IndexError, TypeError, ValueError) as exc:
                    logger.warning(
                        "openrouter_response_parse_error request_id=%s model=%s fallback_used=%s",
                        request_id,
                        candidate_model,
                        fallback_used,
                    )
                    raise HTTPException(
                        status_code=502,
                        detail={
                            "kind": "openrouter_parse_error",
                            "message": "Unexpected OpenRouter response format",
                            "request_id": request_id,
                            "model": candidate_model,
                        },
                    ) from exc
                completed = True
                final_model = candidate_model
                if fallback_used:
                    logger.info(
                        "openrouter_fallback_success request_id=%s initial_model=%s final_model=%s",
                        request_id,
                        model,
                        candidate_model,
                    )
                break

            retryable = response.status_code in OPENROUTER_RETRYABLE_STATUSES
            logger.warning(
                "openrouter_upstream_error request_id=%s model=%s attempt=%s/%s fallback_used=%s status=%s",
                request_id,
                candidate_model,
                attempt,
                OPENROUTER_RETRY_ATTEMPTS,
                fallback_used,
                response.status_code,
            )
            if retryable and attempt < OPENROUTER_RETRY_ATTEMPTS:
                await asyncio.sleep(OPENROUTER_RETRY_BACKOFF_SECONDS * (2 ** (attempt - 1)))
                continue
            break

        if completed:
            break

        should_try_next_model = (
            model_index + 1 < len(deduplicated_models)
            and (
                last_request_error is not None
                or (final_status_code is not None and final_status_code in OPENROUTER_RETRYABLE_STATUSES)
            )
        )
        if should_try_next_model:
            logger.info(
                "openrouter_fallback_switch request_id=%s from_model=%s to_model=%s",
                request_id,
                candidate_model,
                deduplicated_models[model_index + 1],
            )
            continue
        break

    if not completed:
        if last_request_error and final_status_code is None:
            raise HTTPException(
                status_code=502,
                detail={
                    "kind": "openrouter_request_error",
                    "message": f"OpenRouter request failed: {last_request_error}",
                    "request_id": request_id,
                    "model": final_model,
                },
            ) from last_request_error
        raise HTTPException(
            status_code=502,
            detail=build_openrouter_error_detail(
                request_id=request_id,
                model=final_model,
                status_code=final_status_code or 502,
                content_type=final_content_type,
                body_text=final_body_text,
            ),
        )

    try:
        stored = storage.store_image(
            image_bytes=image_bytes,
            content_type=file.content_type,
            image_sha256=image_sha256,
            filename=file.filename,
        )
    except MinioStorageError as exc:
        raise HTTPException(
            status_code=500,
            detail=f"Saving image to MinIO failed: {exc}",
        ) from exc

    embedding: Optional[list[float]] = None
    embedding_source = compose_embedding_text(final_model, file.filename, system_prompt, description)
    if embedding_source:
        try:
            embedding = await create_embedding(embedding_source)
        except RuntimeError:
            embedding = None

    try:
        save_call(
            LLMCallPayload(
                image_filename=file.filename,
                image_content_type=file.content_type,
                image_size_bytes=len(image_bytes),
                image_sha256=image_sha256,
                storage_bucket=stored.bucket,
                storage_object_key=stored.object_key,
                system_prompt=system_prompt,
                model=final_model,
                description=description,
                embedding=embedding,
            )
        )
    except SQLAlchemyError as exc:
        raise HTTPException(
            status_code=500,
            detail="Analyze succeeded but saving call to PostgreSQL failed",
        ) from exc

    return {
        "description": description,
        "model": final_model,
        "system_prompt": system_prompt,
    }
