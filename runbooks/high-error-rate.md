# Runbook: High Error Rate

## Alerts
- `PulseBoardHighErrorRateFast` (critical) — fast burn at 14x SLO budget consumption
- `PulseBoardHighErrorRateSlow` (warning) — slow burn at 2x

## Diagnosis

1. **Check chaos status first:**
   ```bash
   curl http://localhost:8080/chaos/status
   ```
   If `error_rate > 0` — chaos injection is the cause. The sre-agent handles this automatically.

2. **Prometheus:** error breakdown by status code:
   ```promql
   sum by (status_code) (rate(pulseboard_api_requests_total{status_code=~"5.."}[5m]))
   ```

3. **Loki:** recent error logs:
   ```logql
   {service="pulseboard-api"} |= "error" | json
   ```

4. **Tempo:** search for error traces:
   ```traceql
   {resource.service.name="pulseboard-api" && status=error}
   ```

5. **Health check:**
   ```bash
   curl http://localhost:8080/health
   ```

## Remediation

- **Chaos active:** `make chaos-reset` (or wait for sre-agent)
- **API down:** `docker compose restart pulseboard-api`
- **DB issue:** `docker compose logs postgres | tail -50`
