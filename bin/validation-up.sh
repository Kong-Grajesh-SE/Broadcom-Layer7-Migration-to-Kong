#!/bin/bash
set -euo pipefail
cd "$(dirname "$0")/../validation"
echo "Starting validation environment..."
docker compose up -d
echo "Waiting for Kong to be healthy..."
until curl -sf http://localhost:8001/status > /dev/null 2>&1; do
    sleep 2
done
echo "Kong is ready at http://localhost:8000"
echo "Admin API at http://localhost:8001"
echo "Mock API at http://localhost:8080"
