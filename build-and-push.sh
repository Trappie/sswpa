#!/bin/bash

# Build and push script for SSWPA FastAPI app to Artifact Registry
set -e

PROJECT_ID="tech-bridge-initiative"
LOCATION="us-central1"
REPOSITORY="tech-bridge-initiative-repo"
IMAGE_NAME="sswpa"
TAG="latest"
FULL_IMAGE_NAME="${LOCATION}-docker.pkg.dev/${PROJECT_ID}/${REPOSITORY}/${IMAGE_NAME}:${TAG}"

echo "🔨 Building Docker image for AMD64 platform..."
docker build --platform linux/amd64 -t ${IMAGE_NAME}:${TAG} .

echo "🏷️  Tagging image for Artifact Registry..."
docker tag ${IMAGE_NAME}:${TAG} ${FULL_IMAGE_NAME}

echo "📤 Pushing to Artifact Registry..."
docker push ${FULL_IMAGE_NAME}

echo "✅ Successfully pushed ${FULL_IMAGE_NAME}"