# Scripts (Mac)

## Zweck
Diese Skripte starten und stoppen den lokalen MVP-Stack:
- Backend (FastAPI) auf Port `8000`
- Frontend (NextJS dev server) auf Port `3000`

## Voraussetzungen
- Root-`.env` enthaelt `OPENROUTER_API_KEY`
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
