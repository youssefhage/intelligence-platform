FROM python:3.12-slim

WORKDIR /app

RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential libpq-dev curl && \
    rm -rf /var/lib/apt/lists/*

COPY pyproject.toml ./
ARG CACHE_BUST=3
RUN pip install --no-cache-dir . 2>&1 | tail -5 && echo "=== Core deps installed ==="
RUN pip install --no-cache-dir prophet 2>&1 | tail -5 || echo "Prophet not available, forecasting will use fallback"

COPY backend/ ./backend/
COPY alembic/ ./alembic/
COPY alembic.ini ./

EXPOSE 8000

CMD ["uvicorn", "backend.main:app", "--host", "0.0.0.0", "--port", "8000"]
