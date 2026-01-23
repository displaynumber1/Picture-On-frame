#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$ROOT_DIR"

echo "Pull latest code..."
git pull

echo "Build & restart backend..."
docker compose -f docker-compose.prod.yml up -d --build

echo "Done."
