#!/bin/bash
set -e
set -o pipefail

echo "Initializing container setup..."
export PYTHONUNBUFFERED=1  

wait_for_main_api() {
    echo "Waiting for main_api to finish loading..."
    for i in {1..15}; do  # up to ~5 minutes (15*20s)
        sleep 20
        STATUS=$(curl -sf http://127.0.0.1:8000/health | grep -o '"status": *"ok"' || echo "")
        TIMESTAMP=$(date +'%Y-%m-%d %H:%M:%S')
        if [[ "$STATUS" == '"ok"' ]]; then
            echo "$TIMESTAMP - Main API loaded successfully!"
            return 0
        else
            echo "$TIMESTAMP - Attempt $i: main_api still loading..." >&2
        fi
    done
    TIMESTAMP=$(date +'%Y-%m-%d %H:%M:%S')
    echo "$TIMESTAMP - main_api failed to load in time. Exiting..." >&2
    return 1
}

# --- Start Main Process ---

echo "Starting Uvicorn..."
exec uvicorn rag.main_api:app --host 0.0.0.0 --port 8000 &
UVICORN_PID=$!

# Wait until main API responds and model is fully loaded

if ! wait_for_main_api; then
    echo "Exiting container due to failed main API load." >&2
    kill $UVICORN_PID
    exit 1
fi

# --- Check Service Running ----

echo "Entering periodic health check loop (every 60 seconds)..."
FAIL_COUNT=0
while true; do
    sleep 60
    TIMESTAMP=$(date +'%Y-%m-%d %H:%M:%S')
    if curl -sf http://127.0.0.1:8000/health >/dev/null; then
        echo "$TIMESTAMP - API is healthy."
        FAIL_COUNT=0
    else
        FAIL_COUNT=$((FAIL_COUNT+1))
        echo "$TIMESTAMP - API health check failed (consecutive failures: $FAIL_COUNT)." >&2
        if [ "$FAIL_COUNT" -ge 3 ]; then
            echo "$TIMESTAMP - 3 consecutive health check failures. Exiting..." >&2
            kill $UVICORN_PID
            exit 1
        fi
    fi
done