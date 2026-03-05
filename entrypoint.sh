#!/bin/bash
echo "=== Starting FMCG Intelligence Platform ==="
echo "Python: $(python --version)"
echo "Working directory: $(pwd)"
echo "DATABASE_URL set: $([ -n "$DATABASE_URL" ] && echo 'yes' || echo 'no')"

# Test import first
python -c "
import sys
try:
    from backend.main import app
    print('Import OK')
except Exception as e:
    print(f'Import FAILED: {e}', file=sys.stderr)
    import traceback
    traceback.print_exc()
    sys.exit(1)
"

if [ $? -ne 0 ]; then
    echo "Import failed, sleeping 30s for log visibility"
    sleep 30
    exit 1
fi

echo "Starting uvicorn..."
exec uvicorn backend.main:app --host 0.0.0.0 --port 8000
