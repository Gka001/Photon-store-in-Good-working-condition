#!/bin/bash

echo "🛑 Stopping Celery worker..."
pkill -f "celery -A photon_cure" && echo "✅ Celery stopped." || echo "⚠️ Celery not running."

echo "🛑 Stopping Redis server..."
pkill -f redis-server && echo "✅ Redis stopped." || echo "⚠️ Redis not running."

echo "🛑 Stopping Django development server..."
pkill -f "manage.py runserver" && echo "✅ Django server stopped." || echo "⚠️ Django server not running."

echo "✅ All development services stopped."
