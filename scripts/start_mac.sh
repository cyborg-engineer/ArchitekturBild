#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
RUNTIME_DIR="$ROOT_DIR/.run"
BACKEND_PID_FILE="$RUNTIME_DIR/backend.pid"
FRONTEND_PID_FILE="$RUNTIME_DIR/frontend.pid"
BACKEND_LOG_FILE="$RUNTIME_DIR/backend.log"
FRONTEND_LOG_FILE="$RUNTIME_DIR/frontend.log"

mkdir -p "$RUNTIME_DIR"

is_running() {
  local pid="$1"
  if [[ -z "$pid" ]]; then
    return 1
  fi
  kill -0 "$pid" >/dev/null 2>&1
}

if [[ -f "$BACKEND_PID_FILE" ]]; then
  existing_backend_pid="$(cat "$BACKEND_PID_FILE")"
  if is_running "$existing_backend_pid"; then
    echo "Backend already running (PID $existing_backend_pid)"
    exit 1
  fi
  rm -f "$BACKEND_PID_FILE"
fi

if [[ -f "$FRONTEND_PID_FILE" ]]; then
  existing_frontend_pid="$(cat "$FRONTEND_PID_FILE")"
  if is_running "$existing_frontend_pid"; then
    echo "Frontend already running (PID $existing_frontend_pid)"
    exit 1
  fi
  rm -f "$FRONTEND_PID_FILE"
fi

if [[ ! -d "$ROOT_DIR/backend/.venv" ]]; then
  echo "Missing backend virtual environment at backend/.venv"
  echo "Create it first, for example:"
  echo "python3 -m venv backend/.venv"
  echo "backend/.venv/bin/pip install fastapi httpx python-dotenv python-multipart uvicorn"
  exit 1
fi

if [[ ! -d "$ROOT_DIR/frontend/node_modules" ]]; then
  echo "Missing frontend dependencies in frontend/node_modules"
  echo "Run: (cd frontend && npm install)"
  exit 1
fi

(
  cd "$ROOT_DIR/backend"
  nohup .venv/bin/python -m uvicorn app.main:app --host 0.0.0.0 --port 8000 >"$BACKEND_LOG_FILE" 2>&1 &
  echo $! >"$BACKEND_PID_FILE"
)

(
  cd "$ROOT_DIR/frontend"
  nohup npm run dev -- --hostname 0.0.0.0 --port 3000 >"$FRONTEND_LOG_FILE" 2>&1 &
  echo $! >"$FRONTEND_PID_FILE"
)

echo "Started backend PID $(cat "$BACKEND_PID_FILE")"
echo "Started frontend PID $(cat "$FRONTEND_PID_FILE")"
echo "Backend log: $BACKEND_LOG_FILE"
echo "Frontend log: $FRONTEND_LOG_FILE"
