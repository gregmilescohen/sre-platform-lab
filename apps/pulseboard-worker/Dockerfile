FROM python:3.13-slim
COPY --from=ghcr.io/astral-sh/uv:0.7.8 /uv /usr/local/bin/uv
WORKDIR /app
COPY pyproject.toml uv.lock* ./
RUN uv sync --no-group dev --frozen
COPY app/ ./app/
CMD ["uv", "run", "python", "-m", "app.main"]
