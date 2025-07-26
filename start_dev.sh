#!/bin/bash

# Activate virtual environment
source venv/bin/activate
echo "[✓] Virtual environment activated."

# Start Redis if not already running
if ! pgrep -x "redis-server" > /dev/null; then
    echo "[✓] Starting Redis server in background..."
    redis-server --daemonize yes
else
    echo "[✓] Redis is already running."
fi

# Start Celery worker in background using nohup (keeps running even after Ctrl+C)
if ! pgrep -f "celery -A photon_cure worker" > /dev/null; then
    echo "[✓] Starting Celery worker in background..."
    nohup celery -A photon_cure worker --loglevel=info > logs/celery.log 2>&1 &
else
    echo "[✓] Celery worker is already running."
fi

# Create logs folder if it doesn't exist
mkdir -p logs

# Start Django development server (runs in foreground)
echo "[✓] Starting Django development server..."
python manage.py runserver

# After Django stops
echo "[!] Django server stopped. Celery and Redis are still running."
echo "[✓] Virtual environment is still active. You can keep working."
