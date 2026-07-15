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

stop_pid_if_running() {
  local pid="$1"
  if is_running "$pid"; then
    kill "$pid" >/dev/null 2>&1 || true
  fi
}

wait_for_http() {
  local url="$1"
  local attempts="$2"
  local delay_seconds="$3"

  local i
  for ((i = 1; i <= attempts; i++)); do
    if curl -sS "$url" >/dev/null 2>&1; then
      return 0
    fi
    sleep "$delay_seconds"
  done

  return 1
}

has_env_key() {
  local key="$1"
  grep -Eq "^[[:space:]]*${key}=" "$ROOT_DIR/.env"
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

if ! has_env_key "DATABASE_URL"; then
  echo "Warning: DATABASE_URL is not set in .env"
  echo "Backend will fall back to default local PostgreSQL URL."
fi

required_minio_keys=(
  "MINIO_ENDPOINT"
  "MINIO_ACCESS_KEY"
  "MINIO_SECRET_KEY"
  "MINIO_BUCKET"
)

for key in "${required_minio_keys[@]}"; do
  if ! has_env_key "$key"; then
    echo "Missing required MinIO setting in .env: $key"
    exit 1
  fi
done

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

sleep 1

backend_pid="$(cat "$BACKEND_PID_FILE")"
frontend_pid="$(cat "$FRONTEND_PID_FILE")"

if ! is_running "$backend_pid"; then
  echo "Backend failed to start. Check log: $BACKEND_LOG_FILE"
  stop_pid_if_running "$frontend_pid"
  rm -f "$BACKEND_PID_FILE" "$FRONTEND_PID_FILE"
  exit 1
fi

if ! is_running "$frontend_pid"; then
  echo "Frontend failed to start. Check log: $FRONTEND_LOG_FILE"
  stop_pid_if_running "$backend_pid"
  rm -f "$BACKEND_PID_FILE" "$FRONTEND_PID_FILE"
  exit 1
fi

if ! wait_for_http "http://localhost:8000/health" 10 1; then
  echo "Backend health endpoint did not become ready. Check log: $BACKEND_LOG_FILE"
  stop_pid_if_running "$backend_pid"
  stop_pid_if_running "$frontend_pid"
  rm -f "$BACKEND_PID_FILE" "$FRONTEND_PID_FILE"
  exit 1
fi

if ! wait_for_http "http://localhost:3000" 20 1; then
  echo "Frontend endpoint did not become ready. Check log: $FRONTEND_LOG_FILE"
  stop_pid_if_running "$backend_pid"
  stop_pid_if_running "$frontend_pid"
  rm -f "$BACKEND_PID_FILE" "$FRONTEND_PID_FILE"
  exit 1
fi

echo "Started backend PID $(cat "$BACKEND_PID_FILE")"
echo "Started frontend PID $(cat "$FRONTEND_PID_FILE")"
echo "Backend log: $BACKEND_LOG_FILE"
echo "Frontend log: $FRONTEND_LOG_FILE"
