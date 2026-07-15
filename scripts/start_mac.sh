#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
RUNTIME_DIR="$ROOT_DIR/.run"
BACKEND_PID_FILE="$RUNTIME_DIR/backend.pid"
FRONTEND_PID_FILE="$RUNTIME_DIR/frontend.pid"
BACKEND_LOG_FILE="$RUNTIME_DIR/backend.log"
FRONTEND_LOG_FILE="$RUNTIME_DIR/frontend.log"
MANAGED_MINIO_FILE="$RUNTIME_DIR/minio.managed"
DEBUG_LOG_PATH="$ROOT_DIR/.cursor/debug-9f67bc.log"
DEBUG_SESSION_ID="9f67bc"
DEBUG_RUN_ID="${DEBUG_RUN_ID:-run_$(date +%s)}"

mkdir -p "$RUNTIME_DIR"

debug_log() {
  local hypothesis_id="$1"
  local location="$2"
  local message="$3"
  local data="$4"
  python3 - "$DEBUG_LOG_PATH" "$DEBUG_SESSION_ID" "$DEBUG_RUN_ID" "$hypothesis_id" "$location" "$message" "$data" <<'PY'
import json
import time
import uuid
import sys

path, session_id, run_id, hypothesis_id, location, message, data = sys.argv[1:]
payload = {
    "sessionId": session_id,
    "id": f"log_{int(time.time()*1000)}_{uuid.uuid4().hex[:8]}",
    "timestamp": int(time.time() * 1000),
    "location": location,
    "message": message,
    "data": {"raw": data},
    "runId": run_id,
    "hypothesisId": hypothesis_id,
}
with open(path, "a", encoding="utf-8") as f:
    f.write(json.dumps(payload, ensure_ascii=False) + "\n")
PY
}

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

get_env_value() {
  local key="$1"
  python3 - "$ROOT_DIR/.env" "$key" <<'PY'
import re
import sys
from pathlib import Path

env_path = Path(sys.argv[1])
target_key = sys.argv[2]

if not env_path.exists():
    print("")
    raise SystemExit(0)

for raw_line in env_path.read_text().splitlines():
    line = raw_line.strip()
    if not line or line.startswith("#"):
        continue
    match = re.match(r"^([A-Za-z_][A-Za-z0-9_]*)=(.*)$", line)
    if not match:
        continue
    key = match.group(1)
    value = match.group(2).strip()
    if key != target_key:
        continue
    if (value.startswith('"') and value.endswith('"')) or (value.startswith("'") and value.endswith("'")):
        value = value[1:-1]
    print(value)
    break
PY
}

ensure_database_reachable() {
  local database_url="$1"
  if [[ -z "$database_url" ]]; then
    echo "DATABASE_URL is empty in .env"
    return 1
  fi

  if ! "$ROOT_DIR/backend/.venv/bin/python" - "$database_url" <<'PY'
import sys
from urllib.parse import urlparse
import pg8000.dbapi as pg

database_url = sys.argv[1]
parsed = urlparse(database_url)
host = parsed.hostname or "localhost"
port = parsed.port or 5432
user = parsed.username
password = parsed.password
database = (parsed.path or "").lstrip("/") or "postgres"

try:
    conn = pg.connect(
        host=host,
        port=port,
        user=user,
        password=password,
        database=database,
        timeout=3,
    )
    conn.close()
except Exception:
    print(f"db_reachable=false host={host} port={port} db={database}")
    raise SystemExit(1)
print(f"db_reachable=true host={host} port={port} db={database}")
PY
  then
    echo "PostgreSQL is not reachable/authenticated with DATABASE_URL. Check DB service and credentials."
    return 1
  fi

  return 0
}

container_uses_volume() {
  local container_name="$1"
  local expected_volume="$2"
  local destination="$3"
  local mount_name
  mount_name="$(docker inspect -f "{{range .Mounts}}{{if eq .Destination \"${destination}\"}}{{.Name}}{{end}}{{end}}" "$container_name" 2>/dev/null || true)"
  [[ "$mount_name" == "$expected_volume" ]]
}

ensure_minio_for_local_endpoint() {
  local endpoint="$1"
  local access_key="$2"
  local secret_key="$3"
  local container_name="$4"
  local image_name="$5"
  local volume_name="$6"

  if [[ "$endpoint" != "localhost:9000" && "$endpoint" != "127.0.0.1:9000" ]]; then
    rm -f "$MANAGED_MINIO_FILE"
    return 0
  fi

  if ! command -v docker >/dev/null 2>&1; then
    echo "Docker is required to auto-manage local MinIO but was not found."
    return 1
  fi

  local existing_container=""
  existing_container="$(docker ps -a --filter "name=^${container_name}$" --format '{{.Names}}')"

  if [[ -n "$existing_container" ]]; then
    if ! container_uses_volume "$container_name" "$volume_name" "/data"; then
      echo "Existing MinIO container '$container_name' is not mounted to expected volume '$volume_name'."
      echo "Refusing to start to avoid non-persistent image storage."
      echo "Please recreate container with: docker rm -f \"$container_name\""
      return 1
    fi

    local running_container=""
    running_container="$(docker ps --filter "name=^${container_name}$" --format '{{.Names}}')"
    if [[ -z "$running_container" ]]; then
      docker start "$container_name" >/dev/null
      echo "$container_name" > "$MANAGED_MINIO_FILE"
      echo "Started local MinIO container: $container_name"
    else
      rm -f "$MANAGED_MINIO_FILE"
    fi
    return 0
  fi

  docker run -d \
    --name "$container_name" \
    -p 9000:9000 \
    -p 9001:9001 \
    -v "${volume_name}:/data" \
    -e "MINIO_ROOT_USER=$access_key" \
    -e "MINIO_ROOT_PASSWORD=$secret_key" \
    "$image_name" server /data --console-address ":9001" >/dev/null

  echo "$container_name" > "$MANAGED_MINIO_FILE"
  echo "Created and started local MinIO container: $container_name (volume: $volume_name)"
  return 0
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

database_url="$(get_env_value "DATABASE_URL")"
minio_endpoint="$(get_env_value "MINIO_ENDPOINT")"
minio_access_key="$(get_env_value "MINIO_ACCESS_KEY")"
minio_secret_key="$(get_env_value "MINIO_SECRET_KEY")"
minio_container_name="$(get_env_value "MINIO_DOCKER_CONTAINER_NAME")"
minio_image_name="$(get_env_value "MINIO_DOCKER_IMAGE")"
minio_volume_name="$(get_env_value "MINIO_DOCKER_VOLUME_NAME")"

if [[ -z "$minio_container_name" ]]; then
  minio_container_name="architekturbild-minio"
fi
if [[ -z "$minio_image_name" ]]; then
  minio_image_name="minio/minio"
fi
if [[ -z "$minio_volume_name" ]]; then
  minio_volume_name="architekturbild-minio-data"
fi

if ! ensure_database_reachable "$database_url"; then
  #region agent log
  debug_log "H2" "scripts/start_mac.sh:286" "Database precheck failed" "database_url_set=$([[ -n "$database_url" ]] && echo true || echo false)"
  #endregion
  exit 1
fi
 #region agent log
debug_log "H2" "scripts/start_mac.sh:290" "Database precheck passed" "database_url_set=$([[ -n "$database_url" ]] && echo true || echo false)"
#endregion

if ! ensure_minio_for_local_endpoint "$minio_endpoint" "$minio_access_key" "$minio_secret_key" "$minio_container_name" "$minio_image_name" "$minio_volume_name"; then
  #region agent log
  debug_log "H3" "scripts/start_mac.sh:294" "MinIO orchestration failed" "endpoint=$minio_endpoint container=$minio_container_name volume=$minio_volume_name"
  #endregion
  exit 1
fi
 #region agent log
debug_log "H3" "scripts/start_mac.sh:298" "MinIO orchestration passed" "endpoint=$minio_endpoint container=$minio_container_name volume=$minio_volume_name"
#endregion

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
#region agent log
debug_log "H4" "scripts/start_mac.sh:319" "Spawned backend and frontend processes" "backend_pid=$backend_pid frontend_pid=$frontend_pid"
#endregion

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
  #region agent log
  debug_log "H4" "scripts/start_mac.sh:337" "Backend health readiness failed" "backend_pid=$backend_pid"
  #endregion
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

#region agent log
debug_log "H4" "scripts/start_mac.sh:356" "Start script completed successfully" "backend_pid=$backend_pid frontend_pid=$frontend_pid"
#endregion

echo "Started backend PID $(cat "$BACKEND_PID_FILE")"
echo "Started frontend PID $(cat "$FRONTEND_PID_FILE")"
echo "Backend log: $BACKEND_LOG_FILE"
echo "Frontend log: $FRONTEND_LOG_FILE"
