#!/usr/bin/env bash
set -euo pipefail

DELAY_MS="${1:-2000}"
API_URL="${PULSEBOARD_API_URL:-http://localhost:8080}"

curl -sf -X POST "${API_URL}/chaos/slow" \
  -H "Content-Type: application/json" \
  -d "{\"delay_ms\": ${DELAY_MS}}"
echo ""
echo "Injected ${DELAY_MS}ms latency. PulseBoardHighLatency fires in ~5 minutes."
