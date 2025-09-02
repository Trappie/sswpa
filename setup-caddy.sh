#!/bin/bash

# Setup Caddy container with HTTPS for SSWPA on Container-Optimized OS
set -e

VM_NAME="ngo-backend"
VM_ZONE="us-central1-c"
DOMAIN="sswpa.org"  # Replace with your actual domain

echo "🔧 Setting up Caddy container with HTTPS on COS VM: ${VM_NAME}"

# Execute setup commands on the VM
gcloud compute ssh ${VM_NAME} --zone=${VM_ZONE} --command="
echo '📝 Creating Caddyfile...' &&
sudo mkdir -p /mnt/stateful_partition/caddy &&
sudo tee /mnt/stateful_partition/caddy/Caddyfile > /dev/null <<EOF
sswpa.org, www.sswpa.org {
    reverse_proxy sswpa-web:8000
    encode gzip
    
    # Optional: Add security headers
    header {
        # Enable HSTS
        Strict-Transport-Security max-age=31536000;
        # Prevent MIME sniffing
        X-Content-Type-Options nosniff
        # Prevent clickjacking
        X-Frame-Options DENY
        # XSS Protection
        X-XSS-Protection \"1; mode=block\"
    }
}
EOF

echo '🔗 Creating Docker network...' &&
sudo docker network create sswpa-net 2>/dev/null || true &&

echo '🛑 Stopping existing Caddy container...' &&
sudo docker stop caddy-proxy 2>/dev/null || true &&
sudo docker rm caddy-proxy 2>/dev/null || true &&

echo '🚀 Starting Caddy container...' &&
sudo docker run -d \\
  --name caddy-proxy \\
  --restart unless-stopped \\
  --network sswpa-net \\
  -p 80:80 \\
  -p 443:443 \\
  -v /mnt/stateful_partition/caddy:/etc/caddy \\
  -v caddy_data:/data \\
  -v caddy_config:/config \\
  caddy:latest &&

echo '📊 Caddy container status:' &&
sudo docker ps | grep caddy-proxy &&

echo '✅ Caddy container setup complete!'
"

echo "🎉 Caddy container setup complete!"
echo "✅ Both sswpa.org and www.sswpa.org are now configured"
echo "✅ SSL certificates will be obtained automatically"
echo "✅ Run ./update-vm.sh to deploy your app"