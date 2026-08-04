#!/bin/sh
set -e

if [ "$APP_DEBUG" = "true" ]; then
    exec uvicorn app.main:app --host 0.0.0.0 --port 8001 --reload
else
    exec uvicorn app.main:app --host 0.0.0.0 --port 8001
fi
