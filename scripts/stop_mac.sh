#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$ROOT_DIR"

if ! command -v docker >/dev/null 2>&1; then
  echo "Docker is required but not installed."
  exit 1
fi

if [[ ! -f "$ROOT_DIR/docker-compose.yml" ]]; then
  echo "docker-compose.yml not found in project root."
  exit 1
fi

STOP_RETRIES="${STOP_RETRIES:-5}"
STOP_BACKOFF_SECONDS="${STOP_BACKOFF_SECONDS:-2}"

compose_down_with_retry() {
  local attempt
  local max_attempts="$STOP_RETRIES"
  local backoff="$STOP_BACKOFF_SECONDS"

  for ((attempt = 1; attempt <= max_attempts; attempt++)); do
    if docker compose down; then
      return 0
    fi

    if (( attempt == max_attempts )); then
      break
    fi

    echo "docker compose down failed (attempt ${attempt}/${max_attempts}). Retrying in ${backoff}s..."
    sleep "$backoff"
    backoff=$((backoff * 2))
  done

  return 1
}

echo "Stopping container stack (volumes are kept)..."
if ! compose_down_with_retry; then
  echo "Failed to stop stack after ${STOP_RETRIES} attempts."
  echo "Likely Docker daemon/API instability. Please restart Docker Desktop and retry."
  exit 1
fi
