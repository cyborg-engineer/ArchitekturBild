from __future__ import annotations

import base64
import hashlib
import os
from pathlib import Path
from typing import Optional, Union

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

app = FastAPI(title="ArchitekturBild Backend", version="0.1.0")

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

    payload = {
        "model": model,
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

    headers = {
        "Authorization": f"Bearer {api_key}",
        "Content-Type": "application/json",
        "HTTP-Referer": "http://localhost",
        "X-Title": "ArchitekturBild",
    }

    try:
        async with httpx.AsyncClient(timeout=60.0) as client:
            response = await client.post(
                OPENROUTER_API_URL,
                headers=headers,
                json=payload,
            )
    except httpx.RequestError as exc:
        raise HTTPException(
            status_code=502,
            detail=f"OpenRouter request failed: {exc}",
        ) from exc

    if response.status_code >= 400:
        raise HTTPException(
            status_code=502,
            detail=f"OpenRouter error: {response.text}",
        )

    try:
        response_json = response.json()
        description = response_json["choices"][0]["message"]["content"]
    except (KeyError, IndexError, TypeError, ValueError) as exc:
        raise HTTPException(
            status_code=502,
            detail="Unexpected OpenRouter response format",
        ) from exc

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
    embedding_source = compose_embedding_text(model, file.filename, system_prompt, description)
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
                model=model,
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
        "model": model,
        "system_prompt": system_prompt,
    }
