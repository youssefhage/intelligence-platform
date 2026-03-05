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

# Verify imports work at build time - each step separate for debugging
RUN python -c "from backend.core.config import settings; print('config OK')"
RUN python -c "from backend.models import *; print('models OK')"
RUN python -c "import importlib; \
mods = ['backend.api.routes.dashboard','backend.api.routes.commodities','backend.api.routes.suppliers', \
'backend.api.routes.intelligence','backend.api.routes.analytics','backend.api.routes.notifications', \
'backend.api.routes.sync','backend.api.routes.webhooks']; \
[print(f'{m}: OK') if importlib.import_module(m) else None for m in mods]"
RUN python -c "from backend.main import app; print('app import OK')"

EXPOSE 8000

CMD ["uvicorn", "backend.main:app", "--host", "0.0.0.0", "--port", "8000"]
