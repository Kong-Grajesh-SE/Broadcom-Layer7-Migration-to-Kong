#!/bin/bash
set -euo pipefail
cd "$(dirname "$0")/../validation"
echo "Stopping validation environment..."
docker compose down
echo "Done."
