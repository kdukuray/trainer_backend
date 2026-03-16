#!/bin/sh
set -e

MAX_RETRIES=30
RETRY_COUNT=0

echo "Waiting for database (max ${MAX_RETRIES} seconds)..."

# Show actual errors instead of silencing them
while ! uv run python manage.py check --database default 2>&1; do
    RETRY_COUNT=$((RETRY_COUNT + 1))
    if [ $RETRY_COUNT -ge $MAX_RETRIES ]; then
        echo "ERROR: Database not available after ${MAX_RETRIES} seconds. Starting server anyway..."
        break
    fi
    echo "Database unavailable - attempt ${RETRY_COUNT}/${MAX_RETRIES} - sleeping"
    sleep 1
done

if [ $RETRY_COUNT -lt $MAX_RETRIES ]; then
    echo "Database available!"
fi

echo "Running migrations..."
uv run python manage.py migrate --noinput || echo "Migration failed, continuing..."

echo "Collecting static files..."
uv run python manage.py collectstatic --noinput || echo "Collectstatic failed, continuing..."

echo "Starting server..."
exec "$@"