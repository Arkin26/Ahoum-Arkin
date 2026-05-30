#!/usr/bin/env bash
set -euo pipefail

ROOT="$(cd "$(dirname "$0")/.." && pwd)"
cd "$ROOT"

if [ ! -f .env ]; then
  cp .env.example .env
  echo "Created .env from .env.example"
fi

if ! command -v docker >/dev/null 2>&1; then
  echo "Docker is not installed. Install Docker Desktop: https://www.docker.com/products/docker-desktop/"
  exit 1
fi

if ! docker info >/dev/null 2>&1; then
  echo "Docker is not running. Start Docker Desktop, then run: npm run dev"
  exit 1
fi

echo ""
echo "Starting Ahoum Events Platform..."
echo "  API:     http://localhost:8000/api/"
echo "  Swagger: http://localhost:8000/api/docs/"
echo "  Login:   seeker@ahoum.com / Test1234!"
echo ""
echo "Press Ctrl+C to stop."
echo ""

docker compose -f docker-compose.yml -f docker-compose.dev.yml up --build
