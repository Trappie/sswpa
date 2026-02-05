#!/bin/bash

# Update SSWPA container on GCP VM without restarting VM
set -e

PROJECT_ID="tech-bridge-initiative"
LOCATION="us-central1"
REPOSITORY="tech-bridge-initiative-repo"
IMAGE_NAME="sswpa"
TAG="latest"
FULL_IMAGE_NAME="${LOCATION}-docker.pkg.dev/${PROJECT_ID}/${REPOSITORY}/${IMAGE_NAME}:${TAG}"

VM_NAME="ngo-backend"
VM_ZONE="us-central1-c"
CONTAINER_NAME="sswpa-web"

echo "🔄 Updating SSWPA container on VM: ${VM_NAME}"

# Execute update commands on the VM
gcloud compute ssh wu_di_network@${VM_NAME} --zone=${VM_ZONE} --command="
echo '🔐 Configuring Docker authentication...' &&
sudo mkdir -p /tmp/.docker &&
ACCESS_TOKEN=\$(curl -s 'http://metadata.google.internal/computeMetadata/v1/instance/service-accounts/default/token' -H 'Metadata-Flavor: Google' | cut -d'\"' -f4) &&
echo \"\$ACCESS_TOKEN\" | sudo DOCKER_CONFIG=/tmp/.docker docker login -u oauth2accesstoken --password-stdin https://us-central1-docker.pkg.dev &&
echo '📥 Pulling latest image...' &&
sudo DOCKER_CONFIG=/tmp/.docker docker pull ${FULL_IMAGE_NAME} &&
echo '🛑 Stopping existing container...' &&
sudo docker stop ${CONTAINER_NAME} 2>/dev/null || true &&
echo '🗑️  Removing old container...' &&
sudo docker rm ${CONTAINER_NAME} 2>/dev/null || true &&
echo '🚀 Starting new container...' &&
sudo docker network create sswpa-net 2>/dev/null || true &&
sudo docker run -d --name ${CONTAINER_NAME} --restart unless-stopped --network sswpa-net -v /mnt/stateful_partition/sswpa-data:/data ${FULL_IMAGE_NAME} &&
echo '✅ Container updated successfully!' &&
echo '📊 Container status:' &&
sudo docker ps | grep ${CONTAINER_NAME}
"

echo "🎉 Update complete! Application should be running behind Caddy proxy"