#!/bin/bash

# Local Docker development script for SSWPA
set -e

IMAGE_NAME="sswpa-local"
CONTAINER_NAME="sswpa-local"
PORT=8000

echo "🏠 Starting SSWPA in local development mode..."

# Create local data directory if it doesn't exist
echo "📁 Creating local data directory..."
mkdir -p ./local-data
chmod 755 ./local-data

# Stop and remove existing container if running
echo "🛑 Stopping existing container..."
docker stop ${CONTAINER_NAME} 2>/dev/null || true
docker rm ${CONTAINER_NAME} 2>/dev/null || true

# Build the image
echo "🔨 Building Docker image..."
docker build -t ${IMAGE_NAME} .

# Run the container with local volume mount
echo "🚀 Starting container..."
docker run -d \
  --name ${CONTAINER_NAME} \
  -p ${PORT}:8000 \
  -v $(pwd)/local-data:/data \
  -e ENVIRONMENT=local \
  --restart unless-stopped \
  ${IMAGE_NAME}

# Wait a moment for container to start
sleep 3

# Check container status
echo "📊 Container status:"
docker ps | grep ${CONTAINER_NAME}

# Show useful info
echo ""
echo "✅ SSWPA is running locally!"
echo "🌐 Application: http://localhost:${PORT}"
echo "🔧 Admin Panel: http://localhost:${PORT}/admin/wm"
echo "🗄️  Database: ./local-data/sswpa.db"
echo ""
echo "📋 Useful commands:"
echo "  View logs:    docker logs -f ${CONTAINER_NAME}"
echo "  Stop:         docker stop ${CONTAINER_NAME}"
echo "  Restart:      docker restart ${CONTAINER_NAME}"
echo "  Shell:        docker exec -it ${CONTAINER_NAME} /bin/bash"