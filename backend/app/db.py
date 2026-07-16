from __future__ import annotations

import os
from dataclasses import dataclass
from datetime import datetime
from typing import Optional, Sequence, Union

from sqlalchemy import DateTime, Integer, String, Text, create_engine, desc, func, text
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column, sessionmaker
from pgvector.sqlalchemy import Vector


DEFAULT_DATABASE_URL = "postgresql+pg8000://architekturbild:architekturbild@localhost:5432/architekturbild"
DATABASE_URL = os.getenv("DATABASE_URL", DEFAULT_DATABASE_URL)
EMBEDDING_DIMENSIONS = int(os.getenv("RAG_EMBEDDING_DIMENSIONS", "1536"))

engine = create_engine(DATABASE_URL, pool_pre_ping=True)
SessionLocal = sessionmaker(bind=engine, autoflush=False, autocommit=False)


class Base(DeclarativeBase):
    pass


class LLMCall(Base):
    __tablename__ = "llm_calls"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    image_filename: Mapped[str] = mapped_column(String(512), nullable=True)
    image_content_type: Mapped[str] = mapped_column(String(128))
    image_size_bytes: Mapped[int] = mapped_column(Integer)
    image_sha256: Mapped[str] = mapped_column(String(64))
    storage_bucket: Mapped[str] = mapped_column(String(255), nullable=True)
    storage_object_key: Mapped[str] = mapped_column(String(1024), nullable=True)
    system_prompt: Mapped[str] = mapped_column(Text)
    model: Mapped[str] = mapped_column(String(255))
    description: Mapped[str] = mapped_column(Text)
    embedding: Mapped[Optional[list[float]]] = mapped_column(Vector(EMBEDDING_DIMENSIONS), nullable=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        nullable=False,
    )


@dataclass
class LLMCallPayload:
    image_filename: Optional[str]
    image_content_type: str
    image_size_bytes: int
    image_sha256: str
    storage_bucket: Optional[str]
    storage_object_key: Optional[str]
    system_prompt: str
    model: str
    description: str
    embedding: Optional[list[float]] = None


def init_db() -> None:
    with engine.begin() as conn:
        conn.execute(text("CREATE EXTENSION IF NOT EXISTS vector"))
    Base.metadata.create_all(bind=engine)
    with engine.begin() as conn:
        conn.execute(text("ALTER TABLE llm_calls ADD COLUMN IF NOT EXISTS storage_bucket VARCHAR(255)"))
        conn.execute(text("ALTER TABLE llm_calls ADD COLUMN IF NOT EXISTS storage_object_key VARCHAR(1024)"))
        conn.execute(
            text(
                f"ALTER TABLE llm_calls ADD COLUMN IF NOT EXISTS embedding VECTOR({EMBEDDING_DIMENSIONS})"
            )
        )


def save_call(payload: LLMCallPayload) -> int:
    with SessionLocal() as session:
        call = LLMCall(
            image_filename=payload.image_filename,
            image_content_type=payload.image_content_type,
            image_size_bytes=payload.image_size_bytes,
            image_sha256=payload.image_sha256,
            storage_bucket=payload.storage_bucket,
            storage_object_key=payload.storage_object_key,
            system_prompt=payload.system_prompt,
            model=payload.model,
            description=payload.description,
            embedding=payload.embedding,
        )
        session.add(call)
        session.commit()
        session.refresh(call)
        return call.id


def update_call_embedding(call_id: int, embedding: Sequence[float]) -> None:
    with SessionLocal() as session:
        row = session.get(LLMCall, call_id)
        if row is None:
            return
        row.embedding = list(embedding)
        session.commit()


def list_calls_missing_embeddings(limit: int = 200) -> list[dict[str, Union[str, int, None]]]:
    with SessionLocal() as session:
        rows = (
            session.query(LLMCall)
            .filter(LLMCall.embedding.is_(None))
            .order_by(desc(LLMCall.created_at), desc(LLMCall.id))
            .limit(limit)
            .all()
        )

    return [serialize_call(row) for row in rows]


def list_calls(limit: int = 50) -> list[dict[str, Union[str, int, None]]]:
    with SessionLocal() as session:
        rows = (
            session.query(LLMCall)
            .order_by(desc(LLMCall.created_at), desc(LLMCall.id))
            .limit(limit)
            .all()
        )

    return [serialize_call(row) for row in rows]


def list_calls_by_vector_query(
    query_embedding: Sequence[float],
    limit: int = 50,
    min_relevance: float = 0.18,
) -> list[dict[str, Union[str, int, None, float]]]:
    vector_literal = "[" + ",".join(f"{value:.12f}" for value in query_embedding) + "]"
    sql = text(
        """
        SELECT
          id,
          image_filename,
          image_content_type,
          image_size_bytes,
          image_sha256,
          storage_bucket,
          storage_object_key,
          system_prompt,
          model,
          description,
          created_at,
          (1 - (embedding <=> CAST(:query_vector AS vector))) AS relevance
        FROM llm_calls
        WHERE embedding IS NOT NULL
        ORDER BY embedding <=> CAST(:query_vector AS vector), created_at DESC, id DESC
        LIMIT :limit
        """
    )

    with engine.begin() as conn:
        rows = conn.execute(sql, {"query_vector": vector_literal, "limit": limit}).mappings().all()

    result: list[dict[str, Union[str, int, None, float]]] = []
    for row in rows:
        relevance = float(row.get("relevance") or 0.0)
        if relevance < min_relevance:
            continue
        result.append(
            {
                "id": row.get("id"),
                "image_filename": row.get("image_filename"),
                "image_content_type": row.get("image_content_type"),
                "image_size_bytes": row.get("image_size_bytes"),
                "image_sha256": row.get("image_sha256"),
                "storage_bucket": row.get("storage_bucket"),
                "storage_object_key": row.get("storage_object_key"),
                "system_prompt": row.get("system_prompt"),
                "model": row.get("model"),
                "description": row.get("description"),
                "created_at": row.get("created_at").isoformat() if row.get("created_at") else None,
                "relevance": relevance,
            }
        )
    return result


def serialize_call(row: LLMCall) -> dict[str, Union[str, int, None]]:
    return {
        "id": row.id,
        "image_filename": row.image_filename,
        "image_content_type": row.image_content_type,
        "image_size_bytes": row.image_size_bytes,
        "image_sha256": row.image_sha256,
        "storage_bucket": row.storage_bucket,
        "storage_object_key": row.storage_object_key,
        "system_prompt": row.system_prompt,
        "model": row.model,
        "description": row.description,
        "created_at": row.created_at.isoformat() if row.created_at else None,
    }
