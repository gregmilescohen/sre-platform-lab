# Runbook: High Latency

## Alert
- `PulseBoardHighLatency` (warning) — p95 > 500ms

## Diagnosis

1. **Check chaos:** `curl http://localhost:8080/chaos/status` — if `slow_ms > 0`: `make chaos-reset`

2. **Endpoint breakdown:**
   ```promql
   histogram_quantile(0.95,
     sum by (le, endpoint) (rate(pulseboard_api_request_duration_seconds_bucket[5m]))
   )
   ```

3. **Grafana Tempo:** search for slow traces:
   ```traceql
   {resource.service.name="pulseboard-api" && duration>500ms}
   ```
   Click any span to see the flame graph — DB spans will stand out if Postgres is the bottleneck.

4. **DB stats:**
   ```bash
   docker compose stats postgres
   ```

## Remediation

- **Chaos active:** `make chaos-reset`
- **DB slow:** `docker compose restart postgres` (data is persisted on the volume)
