#!/bin/bash

# GCP Container-Optimized OS startup script
# This script pulls and runs the containerized FastAPI application

set -e

# Configuration
CONTAINER_NAME="sswpa-web"
IMAGE_NAME="us-central1-docker.pkg.dev/tech-bridge-initiative/tech-bridge-initiative-repo/sswpa:latest"
PORT=8000

# Configure Docker authentication for Artifact Registry
echo "Configuring Docker authentication..."
mkdir -p /tmp/.docker
export DOCKER_CONFIG=/tmp/.docker
ACCESS_TOKEN=$(curl -s "http://metadata.google.internal/computeMetadata/v1/instance/service-accounts/default/token" -H "Metadata-Flavor: Google" | cut -d'"' -f4)
echo "$ACCESS_TOKEN" | docker login -u oauth2accesstoken --password-stdin https://us-central1-docker.pkg.dev

# Pull the latest image
echo "Pulling latest image..."
docker pull $IMAGE_NAME

# Stop and remove existing container if it exists
echo "Stopping existing container..."
docker stop $CONTAINER_NAME 2>/dev/null || true
docker rm $CONTAINER_NAME 2>/dev/null || true

# Run the new container
echo "Starting new container..."
docker run -d \
  --name $CONTAINER_NAME \
  --restart unless-stopped \
  -p 80:$PORT \
  -p 443:$PORT \
  $IMAGE_NAME

# Show container status
echo "Container status:"
docker ps | grep $CONTAINER_NAME

echo "Application should be running on port 80"