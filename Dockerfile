FROM python:3.12-slim

WORKDIR /app

RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential libpq-dev curl && \
    rm -rf /var/lib/apt/lists/*

COPY pyproject.toml ./
ARG CACHE_BUST=5
SHELL ["/bin/bash", "-o", "pipefail", "-c"]
RUN pip install --no-cache-dir . && echo "=== Core deps installed ==="
RUN pip install --no-cache-dir prophet || echo "Prophet not available, forecasting will use fallback"

COPY backend/ ./backend/
COPY alembic/ ./alembic/
COPY alembic.ini ./

# Verify imports work at build time
RUN python -c "from backend.main import app; print('All imports OK')"

EXPOSE 8000

COPY entrypoint.sh ./
RUN chmod +x entrypoint.sh
CMD ["./entrypoint.sh"]
