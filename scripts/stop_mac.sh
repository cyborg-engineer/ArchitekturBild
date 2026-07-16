#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
RUNTIME_DIR="$ROOT_DIR/.run"
BACKEND_PID_FILE="$RUNTIME_DIR/backend.pid"
FRONTEND_PID_FILE="$RUNTIME_DIR/frontend.pid"
MANAGED_MINIO_FILE="$RUNTIME_DIR/minio.managed"

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
    else
      echo "minio already stopped ($minio_container_name)."
    fi
  else
    echo "docker not found; cannot stop managed minio container."
  fi
  rm -f "$MANAGED_MINIO_FILE"
fi
