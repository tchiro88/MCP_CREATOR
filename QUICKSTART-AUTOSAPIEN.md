# Autosapien.ai MCP - Quick Start Commands

**Infrastructure**: Proxmox 192.168.1.32 | Tunnel LXC 192.168.1.19 | MCP LXC 192.168.1.200 (to be created)

---

## 1. Create LXC on Proxmox

```bash
ssh root@192.168.1.32

# Create container
pct create 200 local:vztmpl/ubuntu-22.04-standard_22.04-1_amd64.tar.zst \
  --hostname mcp-autosapien --memory 4096 --cores 4 --rootfs local-lvm:20 \
  --net0 name=eth0,bridge=vmbr0,ip=dhcp --features nesting=1 \
  --unprivileged 1 --password YourSecurePassword123

pct start 200

# Get IP address
pct exec 200 -- ip addr show eth0 | grep "inet "
# Note: Assume IP is 192.168.1.200
```

---

## 2. Setup MCP LXC

```bash
pct enter 200

# Install dependencies
apt update && apt upgrade -y
apt install -y curl git docker.io docker-compose
systemctl enable docker && systemctl start docker

# Create directory structure
mkdir -p /opt/MCP_CREATOR/deployment/credentials/google

exit
```

---

## 3. Transfer Files from Dev Machine

**On your dev machine:**

```bash
cd /root/OBSIDIAN/MCP_CREATOR/deployment

# Copy to Proxmox host
scp .env root@192.168.1.32:/tmp/mcp-env
scp -r credentials root@192.168.1.32:/tmp/mcp-credentials
scp docker-compose.autosapien.yml root@192.168.1.32:/tmp/

# Copy entire MCP directory
scp -r ../mcp root@192.168.1.32:/tmp/
```

**On Proxmox host:**

```bash
ssh root@192.168.1.32

# Push to LXC
pct push 200 /tmp/mcp-env /opt/MCP_CREATOR/deployment/.env
pct push 200 /tmp/mcp-credentials /opt/MCP_CREATOR/deployment/credentials
pct push 200 /tmp/docker-compose.autosapien.yml /opt/MCP_CREATOR/deployment/
pct push 200 /tmp/mcp /opt/MCP_CREATOR/mcp

# Set permissions
pct exec 200 -- chmod 600 /opt/MCP_CREATOR/deployment/.env
pct exec 200 -- chmod -R 600 /opt/MCP_CREATOR/deployment/credentials/google/*

# Cleanup
rm -rf /tmp/mcp* /tmp/docker-compose.autosapien.yml
```

---

## 4. Create Cloudflare Tunnel

**On Tunnel LXC (192.168.1.19):**

```bash
ssh root@192.168.1.19

# Create tunnel
cloudflared tunnel create mcp-autosapien

# Copy the tunnel ID shown, then get token
cloudflared tunnel token mcp-autosapien
# Copy the entire token (starts with eyJ...)

# Create DNS routes
cloudflared tunnel route dns mcp-autosapien google.autosapien.ai
cloudflared tunnel route dns mcp-autosapien todoist.autosapien.ai
cloudflared tunnel route dns mcp-autosapien homeassistant.autosapien.ai
cloudflared tunnel route dns mcp-autosapien icloud.autosapien.ai
cloudflared tunnel route dns mcp-autosapien outlook.autosapien.ai
cloudflared tunnel route dns mcp-autosapien integrator.autosapien.ai
cloudflared tunnel route dns mcp-autosapien hydraulic.autosapien.ai
```

**Create tunnel config:**

```bash
nano /etc/cloudflared/config-mcp.yml
```

Paste:

```yaml
tunnel: mcp-autosapien
credentials-file: /root/.cloudflared/TUNNEL-ID.json

ingress:
  - hostname: google.autosapien.ai
    service: http://192.168.1.200:3004
  - hostname: todoist.autosapien.ai
    service: http://192.168.1.200:3005
  - hostname: homeassistant.autosapien.ai
    service: http://192.168.1.200:3006
  - hostname: icloud.autosapien.ai
    service: http://192.168.1.200:3009
  - hostname: outlook.autosapien.ai
    service: http://192.168.1.200:3010
  - hostname: integrator.autosapien.ai
    service: http://192.168.1.200:3011
  - hostname: hydraulic.autosapien.ai
    service: http://192.168.1.200:3012
  - service: http_status:404
```

**Start tunnel:**

```bash
# Test first
cloudflared tunnel --config /etc/cloudflared/config-mcp.yml run mcp-autosapien

# If works, make it a service (Ctrl+C first)
cat > /etc/systemd/system/cloudflared-mcp.service <<'EOF'
[Unit]
Description=Cloudflare Tunnel (MCP Autosapien)
After=network.target

[Service]
Type=simple
User=root
ExecStart=/usr/local/bin/cloudflared tunnel --config /etc/cloudflared/config-mcp.yml run mcp-autosapien
Restart=on-failure
RestartSec=5s

[Install]
WantedBy=multi-user.target
EOF

systemctl enable cloudflared-mcp
systemctl start cloudflared-mcp
systemctl status cloudflared-mcp
```

---

## 5. Update .env with Tunnel Token

**On MCP LXC:**

```bash
ssh root@192.168.1.32
pct enter 200

nano /opt/MCP_CREATOR/deployment/.env
```

Add at the top:

```
CLOUDFLARE_TUNNEL_TOKEN=eyJhIjoiXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXX...
```

(Use the token from step 4)

---

## 6. Deploy MCP Services

```bash
cd /opt/MCP_CREATOR/deployment

# Build (takes 10-15 minutes)
docker-compose -f docker-compose.autosapien.yml build --no-cache

# Start services
docker-compose -f docker-compose.autosapien.yml up -d

# Check status
docker-compose -f docker-compose.autosapien.yml ps

# View logs
docker-compose -f docker-compose.autosapien.yml logs -f
```

---

## 7. Test

```bash
# Local test (on MCP LXC)
curl http://localhost:3004/health
curl http://localhost:3011/health
curl http://localhost:3012/health

# Remote test (from anywhere)
curl https://google.autosapien.ai/health
curl https://integrator.autosapien.ai/health
curl https://hydraulic.autosapien.ai/health
```

---

## Quick Reference

### Restart Services

```bash
cd /opt/MCP_CREATOR/deployment
docker-compose -f docker-compose.autosapien.yml restart
```

### View Logs

```bash
docker-compose -f docker-compose.autosapien.yml logs -f mcp-google
```

### Check Tunnel Status

```bash
# On tunnel LXC
systemctl status cloudflared-mcp
journalctl -u cloudflared-mcp -f
```

### Update Services

```bash
cd /opt/MCP_CREATOR/deployment
docker-compose -f docker-compose.autosapien.yml down
docker-compose -f docker-compose.autosapien.yml build --no-cache
docker-compose -f docker-compose.autosapien.yml up -d
```

---

## Endpoints

| Service | URL |
|---------|-----|
| Google | https://google.autosapien.ai |
| Todoist | https://todoist.autosapien.ai |
| Home Assistant | https://homeassistant.autosapien.ai |
| iCloud | https://icloud.autosapien.ai |
| Outlook | https://outlook.autosapien.ai |
| **Integrator** | https://integrator.autosapien.ai |
| Hydraulic Analysis | https://hydraulic.autosapien.ai |

**Use the Integrator endpoint for unified access to all services!**

---

See **DEPLOYMENT-AUTOSAPIEN.md** for detailed explanations.
