FROM python:3.13-slim
COPY --from=ghcr.io/astral-sh/uv:0.7.8 /uv /usr/local/bin/uv
WORKDIR /app
# Copy shared lib first so ../lib resolves to /app/lib (not the system /lib)
COPY lib/ ./lib/
WORKDIR /app/pulseboard-consumer
COPY pulseboard-consumer/pyproject.toml pulseboard-consumer/uv.lock* ./
RUN uv sync --no-group dev --frozen
COPY pulseboard-consumer/app/ ./app/
CMD ["uv", "run", "python", "-m", "app.main"]
HEALTHCHECK --interval=15s --timeout=5s --start-period=10s --retries=3 \
    CMD test -f /tmp/consumer.heartbeat && \
        [ $(( $(date +%s) - $(date +%s -r /tmp/consumer.heartbeat) )) -lt 30 ]
