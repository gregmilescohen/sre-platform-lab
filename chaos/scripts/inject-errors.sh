#!/usr/bin/env bash
set -euo pipefail

RATE="${1:-0.5}"
API_URL="${PULSEBOARD_API_URL:-http://localhost:8080}"

curl -sf -X POST "${API_URL}/chaos/errors" \
  -H "Content-Type: application/json" \
  -d "{\"rate\": ${RATE}}"
echo ""
echo "Injected ${RATE} error rate. PulseBoardHighErrorRateFast fires in ~2 minutes."
echo "The sre-agent will receive the Alertmanager webhook and auto-remediate."
echo "Watch: open http://localhost:8090"
