# SSWPA FastAPI Deployment Guide

This guide covers the complete deployment process for the SSWPA FastAPI application on Google Cloud Platform.

## Project Overview

- **Framework**: FastAPI with Jinja2 templates
- **Deployment**: Containerized with Docker on GCP Container-Optimized OS
- **Registry**: Google Artifact Registry
- **Infrastructure**: Single GCP VM with static IP

## Project Structure

```
sswpa/
├── app/
│   ├── __init__.py
│   └── main.py              # FastAPI application
├── static/
│   ├── css/
│   │   └── styles.css
│   ├── images/
│   │   ├── steinway_logo_centered.svg
│   │   └── steinway_society_logo_centered.svg
│   └── js/                  # Future JS files
├── templates/
│   └── index.html           # Jinja2 template
├── main.py                  # Entry point
├── Dockerfile               # Container definition
├── requirements.txt         # Python dependencies
├── build-and-push.sh        # Build and push script
├── update-vm.sh             # Update deployment script
├── gcp-startup.sh           # VM startup script
└── docker-compose.yml       # Local development
```

## Prerequisites

1. **GCP Account**: Active Google Cloud Platform account
2. **Docker Desktop**: Installed and running locally
3. **gcloud CLI**: Installed and authenticated
4. **Project Setup**: GCP project with billing enabled

## Initial Setup

### 1. GCP Authentication
```bash
# Login to GCP
gcloud auth login

# Set project
gcloud config set project tech-bridge-initiative

# Set region and zone
gcloud config set compute/region us-central1
gcloud config set compute/zone us-central1-c

# Fix quota project
gcloud auth application-default set-quota-project tech-bridge-initiative
```

### 2. Enable Required APIs
```bash
# Enable Compute Engine API
gcloud services enable compute.googleapis.com

# Enable Artifact Registry API
gcloud services enable artifactregistry.googleapis.com
```

### 3. Create Artifact Registry Repository
```bash
gcloud artifacts repositories create tech-bridge-initiative-repo \
  --repository-format=docker \
  --location=us-central1 \
  --description="Tech Bridge Initiative applications repository"
```

### 4. Configure Docker Authentication
```bash
# Configure Docker for Artifact Registry
gcloud auth configure-docker us-central1-docker.pkg.dev
```

### 5. VM Setup (if creating new VM)
```bash
# Create VM with Container-Optimized OS
gcloud compute instances create ngo-backend \
  --zone=us-central1-c \
  --machine-type=e2-micro \
  --image-family=cos-stable \
  --image-project=cos-cloud \
  --tags=http-server,https-server \
  --scopes=https://www.googleapis.com/auth/cloud-platform

# Reserve static IP
gcloud compute addresses create ngo-backend-static-ip \
  --addresses=34.70.2.1 \
  --region=us-central1

# Assign static IP to VM
gcloud compute instances delete-access-config ngo-backend \
  --access-config-name="External NAT" \
  --zone=us-central1-c

gcloud compute instances add-access-config ngo-backend \
  --access-config-name="External NAT" \
  --address=34.70.2.1 \
  --zone=us-central1-c
```

## Deployment Scripts

### 1. Build and Push Script (`build-and-push.sh`)
```bash
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
```

### 2. VM Update Script (`update-vm.sh`)
```bash
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
gcloud compute ssh ${VM_NAME} --zone=${VM_ZONE} --command="
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
sudo docker run -d --name ${CONTAINER_NAME} --restart unless-stopped -p 80:8000 ${FULL_IMAGE_NAME} &&
echo '✅ Container updated successfully!' &&
echo '📊 Container status:' &&
sudo docker ps | grep ${CONTAINER_NAME}
"

echo "🎉 Update complete! Application should be running at http://34.70.2.1"
```

### 3. VM Startup Script (`gcp-startup.sh`)
```bash
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
```

## Development Workflow

### 1. Initial Deployment
```bash
# 1. Build and push Docker image
./build-and-push.sh

# 2. Set startup script on VM (one-time setup)
gcloud compute instances add-metadata ngo-backend \
  --zone=us-central1-c \
  --metadata-from-file startup-script=gcp-startup.sh

# 3. Restart VM to deploy (one-time setup)
gcloud compute instances reset ngo-backend --zone=us-central1-c
```

### 2. Code Updates (Regular Workflow)
```bash
# 1. Make code changes locally

# 2. Build and push new image
./build-and-push.sh

# 3. Update deployment (fast, no VM restart)
./update-vm.sh
```

### 3. Local Development
```bash
# Run locally for testing
docker-compose up

# Or run directly
source venv/bin/activate
python main.py
```

## Monitoring and Troubleshooting

### Check Container Status
```bash
# SSH into VM
gcloud compute ssh ngo-backend --zone=us-central1-c

# Check running containers
sudo docker ps

# Check container logs
sudo docker logs sswpa-web

# Check container health
sudo docker inspect sswpa-web
```

### Check VM Startup Logs
```bash
# View startup script logs
gcloud compute ssh ngo-backend --zone=us-central1-c \
  --command="sudo journalctl -u google-startup-scripts.service --no-pager -n 50"
```

### Test Application
```bash
# Test health endpoint
curl http://34.70.2.1/health

# Test main page
curl -I http://34.70.2.1
```

### Common Issues and Solutions

#### 1. Architecture Mismatch
**Error**: `exec format error`
**Solution**: Ensure Docker builds for AMD64 platform:
```bash
docker build --platform linux/amd64 -t image-name .
```

#### 2. Authentication Errors
**Error**: `denied: Unauthenticated request`
**Solution**: VM service account needs cloud-platform scope:
```bash
gcloud compute instances set-service-account ngo-backend \
  --zone=us-central1-c \
  --service-account=PROJECT_NUMBER-compute@developer.gserviceaccount.com \
  --scopes=https://www.googleapis.com/auth/cloud-platform
```

#### 3. Container Won't Start
**Check**: 
- Container logs: `sudo docker logs sswpa-web`
- Image architecture: `sudo docker inspect image-name`
- Port conflicts: `sudo netstat -tlnp | grep :80`

## Infrastructure Details

### VM Configuration
- **Name**: ngo-backend
- **Zone**: us-central1-c
- **Machine Type**: e2-micro (1 vCPU, 1GB RAM)
- **OS**: Container-Optimized OS
- **External IP**: 34.70.2.1 (static)
- **Firewall Tags**: http-server, https-server

### Network Configuration
- **Port 80**: HTTP traffic (mapped to container port 8000)
- **Port 443**: HTTPS traffic (mapped to container port 8000)
- **Firewall Rules**: Allow HTTP/HTTPS from anywhere (0.0.0.0/0)

### Container Configuration
- **Registry**: us-central1-docker.pkg.dev/tech-bridge-initiative/tech-bridge-initiative-repo/sswpa:latest
- **Container Name**: sswpa-web
- **Restart Policy**: unless-stopped
- **Port Mapping**: 80:8000, 443:8000

## Cost Optimization

- **VM**: e2-micro is free tier eligible
- **Static IP**: ~$1.46/month when VM is running
- **Artifact Registry**: 0.5GB free storage, minimal usage charges
- **Egress**: Minimal for typical web traffic

## Security Considerations

- VM uses service account with minimal required permissions
- Container runs as non-root user
- Static files served through FastAPI (no direct file system access)
- HTTPS can be configured with load balancer or reverse proxy

## Next Steps

1. **Domain Setup**: Configure custom domain with Cloud DNS
2. **SSL/HTTPS**: Set up SSL certificate with Let's Encrypt
3. **Load Balancer**: Add Google Cloud Load Balancer for HTTPS termination
4. **Monitoring**: Set up Cloud Monitoring and logging
5. **Backup**: Implement automated backups of VM and data
6. **CI/CD**: Integrate with GitHub Actions for automated deployments

## Quick Reference

### Key URLs
- **Application**: http://34.70.2.1
- **Health Check**: http://34.70.2.1/health

### Key Commands
```bash
# Build and deploy
./build-and-push.sh && ./update-vm.sh

# Check status
gcloud compute ssh ngo-backend --zone=us-central1-c --command="sudo docker ps"

# View logs
gcloud compute ssh ngo-backend --zone=us-central1-c --command="sudo docker logs sswpa-web"
```

### File Permissions
```bash
# Make scripts executable
chmod +x build-and-push.sh update-vm.sh gcp-startup.sh
```