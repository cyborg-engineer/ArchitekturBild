# Scripts (Mac)

## Zweck
Diese Skripte starten und stoppen den lokalen MVP-Stack:
- Backend (FastAPI) auf Port `8000`
- Frontend (NextJS dev server) auf Port `3000`

## Voraussetzungen
- Root-`.env` enthaelt `OPENROUTER_API_KEY`
- Root-`.env` enthaelt `DATABASE_URL` (PostgreSQL), z. B. `postgresql+pg8000://architekturbild:architekturbild@localhost:5432/architekturbild`
- Root-`.env` enthaelt MinIO-Werte: `MINIO_ENDPOINT`, `MINIO_ACCESS_KEY`, `MINIO_SECRET_KEY`, `MINIO_BUCKET`
- Optional fuer lokale Docker-Orchestrierung: `MINIO_DOCKER_CONTAINER_NAME`, `MINIO_DOCKER_IMAGE`, `MINIO_DOCKER_VOLUME_NAME`
- Backend-Venv vorhanden: `backend/.venv`
- Frontend-Abhaengigkeiten installiert: `frontend/node_modules`

## Start
Vom Projektroot:

```bash
./scripts/start_mac.sh
```

Ausgabe nach Start:
- PID von Backend und Frontend
- Log-Pfade
- Falls `MINIO_ENDPOINT` lokal ist, wird MinIO per Docker automatisch gestartet/neu erstellt.
- MinIO-Daten werden im benannten Volume (`MINIO_DOCKER_VOLUME_NAME`) persistent gehalten.

## Stop
Vom Projektroot:

```bash
./scripts/stop_mac.sh
```

## Logs und Runtime-Dateien
Werden unter `.run/` abgelegt:
- `.run/backend.log`
- `.run/frontend.log`
- `.run/backend.pid`
- `.run/frontend.pid`

## Kurzer Check
- Frontend: [http://localhost:3000](http://localhost:3000)
- Backend Health: [http://localhost:8000/health](http://localhost:8000/health)
