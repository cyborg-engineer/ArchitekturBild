# Lokaler Start (Mac, containerisiert)

## Voraussetzungen
- Docker Desktop oder Docker Engine inkl. Compose-Plugin ist installiert.
- Root-`.env` enthaelt:
  - `OPENROUTER_API_KEY`
  - `MINIO_ACCESS_KEY`
  - `MINIO_SECRET_KEY`
  - `MINIO_BUCKET`

Beispiel:

```env
OPENROUTER_API_KEY=<dein_key>
MINIO_ACCESS_KEY=minioadmin
MINIO_SECRET_KEY=minioadmin
MINIO_BUCKET=architekturbild-images
MINIO_SECURE=false
MINIO_PRESIGNED_EXPIRES_SECONDS=900
OPENROUTER_EMBEDDING_MODEL=openai/text-embedding-3-small
VECTOR_MIN_RELEVANCE=0.18
RAG_EMBEDDING_DIMENSIONS=1536
NEXT_PUBLIC_API_BASE_URL=http://localhost:8000
```

Hinweis:
- `DATABASE_URL` und `MINIO_ENDPOINT` werden im Containerbetrieb ueber `docker-compose.yml` auf interne Service-Namen gesetzt.
- Persistenz liegt in Docker Volumes (`postgres_data`, `minio_data`).

## Start
Im Projektroot ausfuehren:

```bash
./scripts/start_mac.sh
```

Das Skript baut und startet alle Container mit:
`docker compose up -d --build`

Danach:
- Frontend: `http://localhost:3000`
- Backend Health: `http://localhost:8000/health`
- MinIO Console: `http://localhost:9001`

## Stop
Im Projektroot ausfuehren:

```bash
./scripts/stop_mac.sh
```

Das Skript nutzt:
`docker compose down`

Volumes bleiben erhalten.
