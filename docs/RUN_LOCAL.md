# Lokaler Start (Mac)

## Voraussetzungen
- `OPENROUTER_API_KEY` ist in der Root-Datei `.env` gesetzt.
- Backend-Abhaengigkeiten sind in `backend/.venv` installiert.
- Frontend-Abhaengigkeiten sind in `frontend/node_modules` installiert.

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
