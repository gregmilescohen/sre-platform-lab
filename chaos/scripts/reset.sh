#!/usr/bin/env bash
set -euo pipefail

API_URL="${PULSEBOARD_API_URL:-http://localhost:8080}"
curl -sf -X POST "${API_URL}/chaos/reset"
echo ""
echo "All chaos modes cleared."
