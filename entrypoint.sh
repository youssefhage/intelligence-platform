#!/bin/bash
echo "=== Starting FMCG Intelligence Platform ==="
echo "Python: $(python --version)"
echo "Env vars: $(env | grep -c .)"
echo "DATABASE_URL: ${DATABASE_URL:0:40}..."

# Write startup error to file accessible by health endpoint
python -c "
import sys, os, traceback

# Write errors to a file so we can read them via health endpoint
error_file = '/tmp/startup_error.txt'
try:
    from backend.main import app
    print('Import OK')
    # Remove any old error file
    if os.path.exists(error_file):
        os.remove(error_file)
except Exception as e:
    error_msg = traceback.format_exc()
    print(f'Import FAILED: {e}', file=sys.stderr)
    print(error_msg, file=sys.stderr)
    with open(error_file, 'w') as f:
        f.write(error_msg)
    sys.exit(1)
"

if [ $? -ne 0 ]; then
    echo "=== Import failed! Starting minimal debug server ==="
    python -c "
from fastapi import FastAPI
from fastapi.responses import PlainTextResponse
import uvicorn

app = FastAPI()

@app.get('/api/health')
@app.get('/')
def health():
    try:
        with open('/tmp/startup_error.txt') as f:
            return PlainTextResponse(f.read(), status_code=500)
    except:
        return PlainTextResponse('Unknown startup error', status_code=500)

uvicorn.run(app, host='0.0.0.0', port=8000)
"
    exit 0
fi

echo "Starting uvicorn..."
exec uvicorn backend.main:app --host 0.0.0.0 --port 8000
