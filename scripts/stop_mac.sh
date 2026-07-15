#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
RUNTIME_DIR="$ROOT_DIR/.run"
BACKEND_PID_FILE="$RUNTIME_DIR/backend.pid"
FRONTEND_PID_FILE="$RUNTIME_DIR/frontend.pid"
MANAGED_MINIO_FILE="$RUNTIME_DIR/minio.managed"
DEBUG_LOG_PATH="$ROOT_DIR/.cursor/debug-9f67bc.log"
DEBUG_SESSION_ID="9f67bc"
DEBUG_RUN_ID="${DEBUG_RUN_ID:-run_$(date +%s)}"

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

stop_from_pid_file() {
  local name="$1"
  local pid_file="$2"

  if [[ ! -f "$pid_file" ]]; then
    echo "$name is not running (no pid file)."
    return 0
  fi

  local pid
  pid="$(cat "$pid_file")"

  if kill -0 "$pid" >/dev/null 2>&1; then
    kill "$pid" >/dev/null 2>&1 || true
    sleep 1
    if kill -0 "$pid" >/dev/null 2>&1; then
      kill -9 "$pid" >/dev/null 2>&1 || true
    fi
    echo "Stopped $name (PID $pid)"
  else
    echo "$name already stopped (stale pid file)."
    #region agent log
    debug_log "H1" "scripts/stop_mac.sh:66" "Stale pid file detected" "service=$name pid=$pid"
    #endregion
  fi

  rm -f "$pid_file"
}

stop_from_pid_file "backend" "$BACKEND_PID_FILE"
stop_from_pid_file "frontend" "$FRONTEND_PID_FILE"

if [[ -f "$MANAGED_MINIO_FILE" ]]; then
  minio_container_name="$(cat "$MANAGED_MINIO_FILE")"
  if command -v docker >/dev/null 2>&1; then
    running_container="$(docker ps --filter "name=^${minio_container_name}$" --format '{{.Names}}')"
    if [[ -n "$running_container" ]]; then
      docker stop "$minio_container_name" >/dev/null 2>&1 || true
      echo "Stopped minio ($minio_container_name)"
      #region agent log
      debug_log "H3" "scripts/stop_mac.sh:82" "Stopped managed MinIO container" "container=$minio_container_name"
      #endregion
    else
      echo "minio already stopped ($minio_container_name)."
    fi
  else
    echo "docker not found; cannot stop managed minio container."
  fi
  rm -f "$MANAGED_MINIO_FILE"
fi
