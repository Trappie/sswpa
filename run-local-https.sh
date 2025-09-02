#!/bin/bash

# Local HTTPS Docker development script for SSWPA
set -e

IMAGE_NAME="sswpa-local"
CONTAINER_NAME="sswpa-local"
CADDY_CONTAINER_NAME="caddy-local"
PORT=8000

echo "🔐 Starting SSWPA with local HTTPS support..."

# Check if certificates exist
if [ ! -f "localhost+2.pem" ] || [ ! -f "localhost+2-key.pem" ]; then
    echo "❌ mkcert certificates not found!"
    echo "Please run: mkcert localhost 127.0.0.1 ::1"
    exit 1
fi

# Create local data directory if it doesn't exist
echo "📁 Creating local data directory..."
mkdir -p ./local-data
chmod 755 ./local-data

# Stop and remove existing containers if running
echo "🛑 Stopping existing containers..."
docker stop ${CONTAINER_NAME} 2>/dev/null || true
docker rm ${CONTAINER_NAME} 2>/dev/null || true
docker stop ${CADDY_CONTAINER_NAME} 2>/dev/null || true
docker rm ${CADDY_CONTAINER_NAME} 2>/dev/null || true

# Create a network for the containers to communicate
echo "🌐 Creating Docker network..."
docker network create sswpa-local-net 2>/dev/null || true

# Build the image
echo "🔨 Building Docker image..."
docker build -t ${IMAGE_NAME} .

# Load environment variables from .env file if it exists
if [ -f .env ]; then
    echo "📄 Loading environment variables from .env..."
    export $(grep -v '^#' .env | xargs)
fi

# Run the app container
echo "🚀 Starting app container..."
docker run -d \
  --name ${CONTAINER_NAME} \
  --network sswpa-local-net \
  -v $(pwd)/local-data:/data \
  -e ENVIRONMENT=local \
  -e SQUARE_SANDBOX_ACCESS_TOKEN="${SQUARE_SANDBOX_ACCESS_TOKEN}" \
  -e SQUARE_SANDBOX_APP_ID="${SQUARE_SANDBOX_APP_ID}" \
  -e SQUARE_SANDBOX_LOCATION_ID="${SQUARE_SANDBOX_LOCATION_ID}" \
  -e GMAIL_PASSWORD="${GMAIL_APP_PASSWORD}" \
  -e ADMIN_PASSWORD="${ADMIN_PASSWORD}" \
  --restart unless-stopped \
  ${IMAGE_NAME}

# Run Caddy with HTTPS
echo "🔐 Starting Caddy with HTTPS..."
docker run -d \
  --name ${CADDY_CONTAINER_NAME} \
  --network sswpa-local-net \
  -p 443:443 \
  -p 80:80 \
  -v $(pwd)/Caddyfile.local:/etc/caddy/Caddyfile \
  -v $(pwd)/localhost+2.pem:/etc/caddy/certs/localhost+2.pem \
  -v $(pwd)/localhost+2-key.pem:/etc/caddy/certs/localhost+2-key.pem \
  --restart unless-stopped \
  caddy:2

# Wait a moment for containers to start
sleep 5

# Check container status
echo "📊 Container status:"
docker ps | grep -E "(${CONTAINER_NAME}|${CADDY_CONTAINER_NAME})"

# Show useful info
echo ""
echo "✅ SSWPA is running with HTTPS!"
echo "🌐 Application: https://localhost"
echo "🔧 Admin Panel: https://localhost/admin/wm"
echo "🗄️  Database: ./local-data/sswpa.db"
echo ""
echo "📋 Useful commands:"
echo "  View app logs:    docker logs -f ${CONTAINER_NAME}"
echo "  View caddy logs:  docker logs -f ${CADDY_CONTAINER_NAME}"
echo "  Stop:             docker stop ${CONTAINER_NAME} ${CADDY_CONTAINER_NAME}"
echo "  Restart:          docker restart ${CONTAINER_NAME} ${CADDY_CONTAINER_NAME}"
echo "  Shell:            docker exec -it ${CONTAINER_NAME} /bin/bash"