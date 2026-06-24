#!/bin/bash
set -euo pipefail

KONG_YAML="${1:-validation/kong.yaml}"

echo "Reloading Kong config from $KONG_YAML..."
cp "$KONG_YAML" "$(dirname "$0")/../validation/kong.yaml"
docker exec layer7-migration-kong kong reload
echo "Kong reloaded."
