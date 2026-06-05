FROM python:3.13-slim

COPY --from=ghcr.io/astral-sh/uv:0.7.8 /uv /usr/local/bin/uv

WORKDIR /app

# Copy shared lib first so ../lib resolves to /app/lib (not the system /lib)
COPY lib/ ./lib/

WORKDIR /app/pulseboard-api

COPY pulseboard-api/pyproject.toml pulseboard-api/uv.lock* ./

RUN uv sync --frozen --no-dev --no-editable

COPY pulseboard-api/app/ ./app/

EXPOSE 8080

CMD ["uv", "run", "uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8080"]
