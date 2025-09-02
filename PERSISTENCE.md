# Data Persistence Architecture

## Overview
This document explains how data persistence works across VM reboots for the SSWPA application.

## Persistent Storage Locations

### 1. Database Storage
- **Location**: `/mnt/stateful_partition/sswpa-data/`
- **Contains**: SQLite database file (`sswpa.db`)
- **Mounted to**: Container's `/data/` directory
- **Purpose**: Store application data (orders, payments, events, etc.)

### 2. Caddy Configuration
- **Location**: `/mnt/stateful_partition/caddy/`
- **Contains**: `Caddyfile` (reverse proxy configuration)
- **Mounted to**: Container's `/etc/caddy/` directory
- **Purpose**: HTTPS/SSL proxy configuration

### 3. Caddy SSL Certificates
- **Location**: Docker volumes `caddy_data` and `caddy_config`
- **Purpose**: Let's Encrypt SSL certificates and Caddy runtime data
- **Persistence**: Managed by Docker volume system

## Container Configuration

### Application Container (sswpa-web)
```bash
docker run -d \
  --name sswpa-web \
  --restart unless-stopped \
  --network sswpa-net \
  -v /mnt/stateful_partition/sswpa-data:/data \
  [image]
```

### Caddy Proxy Container (caddy-proxy)
```bash
docker run -d \
  --name caddy-proxy \
  --restart unless-stopped \
  --network sswpa-net \
  -p 80:80 -p 443:443 \
  -v /mnt/stateful_partition/caddy:/etc/caddy \
  -v caddy_data:/data \
  -v caddy_config:/config \
  caddy:latest
```

## What Survives VM Reboots

✅ **Persistent Data:**
- Database records (SQLite file)
- Caddy configuration (Caddyfile)
- SSL certificates (Docker volumes)
- Application code (in Docker image)

❌ **Non-Persistent (gets recreated):**
- Container runtime state
- `/tmp/` directory contents
- Container logs (unless configured otherwise)

## Deployment Process

1. **Build & Push**: `./build-and-push.sh`
   - Builds Docker image
   - Pushes to Artifact Registry

2. **Update Application**: `./update-vm.sh`
   - Pulls latest image
   - Stops old container
   - Starts new container with persistent mounts

3. **Setup Caddy** (one-time): `./setup-caddy.sh`
   - Creates persistent Caddyfile
   - Sets up Caddy container with proper mounts

## VM Reboot Recovery

When a VM reboots:
1. COS starts Docker service
2. Containers with `--restart unless-stopped` start automatically
3. Persistent volumes are remounted
4. Application resumes with all data intact

## Testing Persistence

```bash
# Write test data
curl -X POST "https://sswpa.org/test-db-write?message=Test before reboot"

# Reboot VM
gcloud compute instances reset ngo-backend --zone=us-central1-c

# Wait 1-2 minutes, then verify data survived
curl "https://sswpa.org/test-db-read"
```

## Troubleshooting

If services don't start after reboot:
1. Check container status: `sudo docker ps -a`
2. Check Caddy logs: `sudo docker logs caddy-proxy`
3. Check app logs: `sudo docker logs sswpa-web`
4. Verify mounts exist: `ls -la /mnt/stateful_partition/`

## File Locations Summary

```
/mnt/stateful_partition/
├── sswpa-data/          # Database storage
│   └── sswpa.db         # SQLite database file
└── caddy/               # Caddy configuration
    └── Caddyfile        # Reverse proxy config
```