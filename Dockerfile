FROM python:3.12-slim

WORKDIR /app

RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential libpq-dev curl && \
    rm -rf /var/lib/apt/lists/*

COPY pyproject.toml ./
ARG CACHE_BUST=4
SHELL ["/bin/bash", "-o", "pipefail", "-c"]
RUN pip install --no-cache-dir . && echo "=== Core deps installed ==="
RUN pip install --no-cache-dir prophet || echo "Prophet not available, forecasting will use fallback"
RUN pip list

COPY backend/ ./backend/
COPY alembic/ ./alembic/
COPY alembic.ini ./

# Verify imports work at build time
RUN python -c "from backend.core.config import settings; print('config OK')" && \
    python -c "from backend.models import *; print('models OK')" && \
    python -c "from backend.main import app; print('app import OK')"

EXPOSE 8000

CMD ["uvicorn", "backend.main:app", "--host", "0.0.0.0", "--port", "8000"]
