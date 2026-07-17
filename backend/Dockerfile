FROM python:3.12-slim

ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1

WORKDIR /app/backend

RUN pip install --no-cache-dir --upgrade pip
RUN pip install --no-cache-dir \
    fastapi \
    httpx \
    minio \
    pg8000 \
    pgvector \
    python-dotenv \
    python-multipart \
    sqlalchemy \
    "uvicorn[standard]"

COPY backend/app ./app

EXPOSE 8000

CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
