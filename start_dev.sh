#!/bin/bash

# Activate virtual environment (adjust path if needed)
source venv/bin/activate

# Ensure logs directory exists
mkdir -p logs

# 1. Start Redis server if not running
if ! redis-cli ping | grep -q PONG; then
    echo "🚀 Starting Redis server..."
    nohup redis-server > logs/redis.log 2>&1 &
    sleep 2  # give Redis some time to start
else
    echo "✅ Redis is already running."
fi

# 2. Start Celery if not already running
if ! pgrep -f 'celery -A photon_cure'; then
    echo "🚀 Starting Celery worker..."
    nohup celery -A photon_cure worker --loglevel=info > logs/celery.log 2>&1 &
else
    echo "✅ Celery worker is already running."
fi

# 3. Start Django server in foreground
echo "🚀 Starting Django development server..."
exec python manage.py runserver
