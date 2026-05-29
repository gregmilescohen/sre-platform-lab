FROM python:3.13-slim
COPY --from=ghcr.io/astral-sh/uv:0.7.8 /uv /usr/local/bin/uv
WORKDIR /app
COPY pyproject.toml uv.lock* ./
RUN uv sync --no-group dev --frozen
COPY app/ ./app/
CMD ["uv", "run", "python", "-m", "app.main"]
HEALTHCHECK --interval=15s --timeout=5s --start-period=10s --retries=3 \
    CMD test -f /tmp/worker.heartbeat && \
        [ $(( $(date +%s) - $(date +%s -r /tmp/worker.heartbeat) )) -lt 30 ]
