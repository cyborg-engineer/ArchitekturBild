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

echo "Building and starting container stack..."
docker compose up -d --build

echo "Container status:"
docker compose ps

echo "Frontend: http://localhost:3000"
echo "Backend health: http://localhost:8000/health"
echo "MinIO console: http://localhost:9001"
