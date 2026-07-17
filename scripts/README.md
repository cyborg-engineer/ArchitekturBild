# Scripts (Mac)

## Zweck
Diese Skripte steuern den kompletten Container-Stack per Docker Compose:
- `postgres` (mit `pgvector`)
- `minio`
- `backend` (FastAPI)
- `frontend` (NextJS)

## Voraussetzungen
- Docker Desktop oder Docker Engine mit Compose-Plugin ist installiert.
- Root-`.env` enthaelt mindestens:
  - `OPENROUTER_API_KEY`
  - `MINIO_ACCESS_KEY`
  - `MINIO_SECRET_KEY`
  - `MINIO_BUCKET`

## Start
Vom Projektroot:

```bash
./scripts/start_mac.sh
```

Das Skript fuehrt `docker compose up -d --build` aus.

## Stop
Vom Projektroot:

```bash
./scripts/stop_mac.sh
```

Das Skript fuehrt `docker compose down` aus.
Volumes bleiben dabei erhalten.

## Persistente Daten
- PostgreSQL: Volume `postgres_data`
- MinIO: Volume `minio_data`

## Kurzer Check
- Frontend: [http://localhost:3000](http://localhost:3000)
- Backend Health: [http://localhost:8000/health](http://localhost:8000/health)
- MinIO Console: [http://localhost:9001](http://localhost:9001)
