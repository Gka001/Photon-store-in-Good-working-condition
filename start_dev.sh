#!/bin/bash

# Activate virtual environment (adjust path if needed)
source venv/bin/activate

# 1. Start Redis if not already running
if ! redis-cli ping | grep -q PONG; then
    echo "🚀 Starting Redis server..."
    redis-server > logs/redis.log 2>&1 &
else
    echo "✅ Redis is already running."
fi

# 2. Start Celery in background
echo "🚀 Starting Celery worker..."
celery -A photon_cure worker --loglevel=info > logs/celery.log 2>&1 &

# 3. Start Django in foreground
echo "🚀 Starting Django development server..."
python manage.py runserver
