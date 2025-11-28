#!/bin/bash
set -e

cd /var/www/lootmore-backend

echo "Pulling latest code..."
git pull

echo "Applying database migrations..."
alembic upgrade head

echo "Restarting Docker services..."
docker-compose down
docker-compose up -d --build

echo "Deployment complete."
