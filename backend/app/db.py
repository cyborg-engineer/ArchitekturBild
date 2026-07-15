from __future__ import annotations

import os
from dataclasses import dataclass
from datetime import datetime
from typing import Optional, Union

from sqlalchemy import DateTime, Integer, String, Text, create_engine, desc, func, text
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column, sessionmaker


DEFAULT_DATABASE_URL = "postgresql+pg8000://architekturbild:architekturbild@localhost:5432/architekturbild"
DATABASE_URL = os.getenv("DATABASE_URL", DEFAULT_DATABASE_URL)

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


def init_db() -> None:
    Base.metadata.create_all(bind=engine)
    with engine.begin() as conn:
        conn.execute(text("ALTER TABLE llm_calls ADD COLUMN IF NOT EXISTS storage_bucket VARCHAR(255)"))
        conn.execute(text("ALTER TABLE llm_calls ADD COLUMN IF NOT EXISTS storage_object_key VARCHAR(1024)"))


def save_call(payload: LLMCallPayload) -> None:
    with SessionLocal() as session:
        session.add(
            LLMCall(
                image_filename=payload.image_filename,
                image_content_type=payload.image_content_type,
                image_size_bytes=payload.image_size_bytes,
                image_sha256=payload.image_sha256,
                storage_bucket=payload.storage_bucket,
                storage_object_key=payload.storage_object_key,
                system_prompt=payload.system_prompt,
                model=payload.model,
                description=payload.description,
            )
        )
        session.commit()


def list_calls(limit: int = 50) -> list[dict[str, Union[str, int, None]]]:
    with SessionLocal() as session:
        rows = (
            session.query(LLMCall)
            .order_by(desc(LLMCall.created_at), desc(LLMCall.id))
            .limit(limit)
            .all()
        )

    return [serialize_call(row) for row in rows]


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
