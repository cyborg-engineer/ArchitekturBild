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

echo "Stopping container stack (volumes are kept)..."
docker compose down
