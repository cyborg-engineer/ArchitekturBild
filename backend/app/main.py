from __future__ import annotations

import base64
import hashlib
import os
from pathlib import Path
from typing import Union

import httpx
from dotenv import load_dotenv
from fastapi import FastAPI, File, Form, HTTPException, UploadFile
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy.exc import SQLAlchemyError

from .db import LLMCallPayload, init_db, list_calls, save_call
from .storage import MinioStorage, MinioStorageError


ROOT_ENV_PATH = Path(__file__).resolve().parents[2] / ".env"
load_dotenv(ROOT_ENV_PATH)

OPENROUTER_API_URL = "https://openrouter.ai/api/v1/chat/completions"

app = FastAPI(title="ArchitekturBild Backend", version="0.1.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=False,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.on_event("startup")
def on_startup() -> None:
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


@app.get("/health")
async def health() -> dict[str, str]:
    return {"status": "ok"}


@app.get("/api/history")
async def read_history(limit: int = 50) -> dict[str, list[dict[str, Union[str, int, None]]]]:
    normalized_limit = max(1, min(limit, 200))
    try:
        items = list_calls(limit=normalized_limit)
    except SQLAlchemyError as exc:
        raise HTTPException(
            status_code=500,
            detail="Failed to load history from PostgreSQL",
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
