#!/bin/bash

# Stop local Docker development container
set -e

CONTAINER_NAME="sswpa-local"

echo "🛑 Stopping local SSWPA development container..."

# Stop and remove the container
docker stop ${CONTAINER_NAME} 2>/dev/null || true
docker rm ${CONTAINER_NAME} 2>/dev/null || true

echo "✅ Local development container stopped"
echo "📁 Database preserved in ./local-data/"