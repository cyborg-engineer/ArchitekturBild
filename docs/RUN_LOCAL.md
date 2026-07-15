# Lokaler Start (Mac)

## Voraussetzungen
- `OPENROUTER_API_KEY` ist in der Root-Datei `.env` gesetzt.
- `DATABASE_URL` ist in der Root-Datei `.env` gesetzt und zeigt auf eine laufende PostgreSQL-Instanz.
- MinIO-Konfiguration ist in der Root-Datei `.env` gesetzt (`MINIO_ENDPOINT`, `MINIO_ACCESS_KEY`, `MINIO_SECRET_KEY`, `MINIO_BUCKET`).
- Backend-Abhaengigkeiten sind in `backend/.venv` installiert.
- Frontend-Abhaengigkeiten sind in `frontend/node_modules` installiert.

Beispiel:

```env
DATABASE_URL=postgresql+pg8000://architekturbild:architekturbild@localhost:5432/architekturbild
MINIO_ENDPOINT=localhost:9000
MINIO_ACCESS_KEY=minioadmin
MINIO_SECRET_KEY=minioadmin
MINIO_BUCKET=architekturbild-images
MINIO_SECURE=false
MINIO_PRESIGNED_EXPIRES_SECONDS=900
```

## Start
Im Projektroot ausfuehren:

```bash
./scripts/start_mac.sh
```

Danach:
- Frontend: `http://localhost:3000`
- Backend Health: `http://localhost:8000/health`

Logs liegen in:
- `.run/backend.log`
- `.run/frontend.log`

## Stop
Im Projektroot ausfuehren:

```bash
./scripts/stop_mac.sh
```
