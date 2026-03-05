#!/bin/bash
echo "=== Starting FMCG Intelligence Platform ==="
echo "Python: $(python --version)"
echo "DATABASE_URL: ${DATABASE_URL:0:50}..."

# Start uvicorn, capture exit code
uvicorn backend.main:app --host 0.0.0.0 --port 8000 2>&1 | tee /tmp/uvicorn.log &
UVICORN_PID=$!

# Wait a bit to see if it crashes
sleep 10

# Check if uvicorn is still running
if kill -0 $UVICORN_PID 2>/dev/null; then
    echo "Uvicorn started successfully, waiting..."
    wait $UVICORN_PID
else
    echo "=== Uvicorn crashed! Starting debug server ==="
    echo "Last log output:"
    tail -30 /tmp/uvicorn.log

    # Start a minimal server that exposes the error
    python -c "
from fastapi import FastAPI
from fastapi.responses import PlainTextResponse
import uvicorn

app = FastAPI()

@app.get('/api/health')
@app.get('/')
def health():
    try:
        with open('/tmp/uvicorn.log') as f:
            return PlainTextResponse(f.read(), status_code=500)
    except:
        return PlainTextResponse('No log file found', status_code=500)

uvicorn.run(app, host='0.0.0.0', port=8000)
"
fi
