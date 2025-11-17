# 🚀 Deploy Now - Autosapien.ai MCP (6 Services)

**Active Services:** Google, iCloud, Outlook, Todoist, Integrator, Hydraulic
**Skipped:** Home Assistant (will add later)

---

## Step 1: Create Proxmox LXC (5 min)

**On your local machine, SSH to Proxmox:**

```bash
ssh root@192.168.1.32
```

**Create the container:**

```bash
# Download template if needed
pveam update
pveam download local ubuntu-22.04-standard_22.04-1_amd64.tar.zst

# Create LXC container ID 200
pct create 200 local:vztmpl/ubuntu-22.04-standard_22.04-1_amd64.tar.zst \
  --hostname mcp-autosapien \
  --memory 4096 \
  --cores 4 \
  --rootfs local-lvm:20 \
  --net0 name=eth0,bridge=vmbr0,ip=dhcp \
  --features nesting=1 \
  --unprivileged 1 \
  --password YourSecurePassword123

# Start it
pct start 200

# Get its IP address (note this down!)
pct exec 200 -- ip addr show eth0 | grep "inet "
```

**Expected output:** `inet 192.168.1.XXX/24` - **SAVE THIS IP!**

---

## Step 2: Setup LXC (3 min)

**Enter the container:**

```bash
pct enter 200
```

**Install Docker:**

```bash
apt update && apt upgrade -y
apt install -y curl git docker.io docker-compose
systemctl enable docker
systemctl start docker
docker --version
```

**Create directories:**

```bash
mkdir -p /opt/MCP_CREATOR/deployment/credentials/google
```

**Exit container:**

```bash
exit
```

---

## Step 3: Transfer Files (2 min)

**From your dev machine (where Claude Code is running):**

```bash
cd /root/OBSIDIAN/MCP_CREATOR

# Copy to Proxmox host
scp -r deployment root@192.168.1.32:/tmp/mcp-deployment
scp -r mcp root@192.168.1.32:/tmp/mcp-services
```

**Then on Proxmox host:**

```bash
ssh root@192.168.1.32

# Push to LXC
pct push 200 /tmp/mcp-deployment /opt/MCP_CREATOR/deployment
pct push 200 /tmp/mcp-services /opt/MCP_CREATOR/mcp

# Set permissions
pct exec 200 -- chmod 600 /opt/MCP_CREATOR/deployment/.env
pct exec 200 -- chmod -R 600 /opt/MCP_CREATOR/deployment/credentials/google/*

# Cleanup
rm -rf /tmp/mcp-deployment /tmp/mcp-services

# Verify transfer
pct exec 200 -- ls -la /opt/MCP_CREATOR/deployment/
```

---

## Step 4: Create Cloudflare Tunnel (5 min)

**SSH to your Cloudflare Tunnel LXC:**

```bash
ssh root@192.168.1.19
```

**Create tunnel:**

```bash
cloudflared tunnel create mcp-autosapien
```

**IMPORTANT:** Copy the tunnel ID from the output!

**Get tunnel token:**

```bash
cloudflared tunnel token mcp-autosapien
```

**IMPORTANT:** Copy the entire token (starts with `eyJ...`)

**Create DNS routes (replace with your actual MCP LXC IP):**

```bash
# Use the IP from Step 1
cloudflared tunnel route dns mcp-autosapien google.autosapien.ai
cloudflared tunnel route dns mcp-autosapien todoist.autosapien.ai
cloudflared tunnel route dns mcp-autosapien icloud.autosapien.ai
cloudflared tunnel route dns mcp-autosapien outlook.autosapien.ai
cloudflared tunnel route dns mcp-autosapien integrator.autosapien.ai
cloudflared tunnel route dns mcp-autosapien hydraulic.autosapien.ai
```

**Create tunnel config:**

```bash
nano /etc/cloudflared/config-mcp.yml
```

**Paste this (replace TUNNEL-ID and MCP_IP):**

```yaml
tunnel: mcp-autosapien
credentials-file: /root/.cloudflared/YOUR-TUNNEL-ID.json

ingress:
  - hostname: google.autosapien.ai
    service: http://YOUR_MCP_IP:3004
  - hostname: todoist.autosapien.ai
    service: http://YOUR_MCP_IP:3005
  - hostname: icloud.autosapien.ai
    service: http://YOUR_MCP_IP:3009
  - hostname: outlook.autosapien.ai
    service: http://YOUR_MCP_IP:3010
  - hostname: integrator.autosapien.ai
    service: http://YOUR_MCP_IP:3011
  - hostname: hydraulic.autosapien.ai
    service: http://YOUR_MCP_IP:3012
  - service: http_status:404
```

**Save and create systemd service:**

```bash
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

## Step 5: Update Tunnel Token in MCP LXC (1 min)

**From Proxmox host:**

```bash
ssh root@192.168.1.32

# Edit .env file
pct exec 200 -- nano /opt/MCP_CREATOR/deployment/.env
```

**Add the tunnel token at the top:**

```
CLOUDFLARE_TUNNEL_TOKEN=eyJhIjoiXXXXXXXXXXXXXXXXXXXXXXX...
```

**Save:** Ctrl+X, Y, Enter

---

## Step 6: Build and Deploy (15-20 min)

**Enter MCP LXC:**

```bash
pct enter 200
cd /opt/MCP_CREATOR/deployment
```

**Build all containers:**

```bash
docker-compose -f docker-compose.autosapien.yml build --no-cache
```

**This will take 15-20 minutes. You'll see:**
- Building mcp-google
- Building mcp-icloud
- Building mcp-outlook
- Building mcp-todoist
- Building mcp-integrator
- Building mcp-hydraulic

**Start all services:**

```bash
docker-compose -f docker-compose.autosapien.yml up -d
```

**Check status:**

```bash
docker-compose -f docker-compose.autosapien.yml ps
```

**Expected: 6 containers showing "Up"**

---

## Step 7: Test (5 min)

**Test local connectivity:**

```bash
curl http://localhost:3004/health  # Google
curl http://localhost:3005/health  # Todoist
curl http://localhost:3009/health  # iCloud
curl http://localhost:3010/health  # Outlook
curl http://localhost:3011/health  # Integrator
curl http://localhost:3012/health  # Hydraulic
```

**Exit container and test from Proxmox:**

```bash
exit
curl http://YOUR_MCP_IP:3004/health
curl http://YOUR_MCP_IP:3011/health
```

**Test remote (from anywhere):**

```bash
curl https://google.autosapien.ai/health
curl https://integrator.autosapien.ai/health
curl https://hydraulic.autosapien.ai/health
```

---

## ✅ Success Checklist

- [ ] Proxmox LXC created (ID 200)
- [ ] Docker installed and running
- [ ] Files transferred to /opt/MCP_CREATOR
- [ ] Cloudflare tunnel created and running
- [ ] Tunnel token added to .env
- [ ] All 6 containers built successfully
- [ ] All 6 containers running (docker ps)
- [ ] Local health checks pass
- [ ] Remote health checks pass
- [ ] DNS resolving correctly

---

## 🎯 Your 6 Active Services

| Service | URL | Purpose |
|---------|-----|---------|
| Google | https://google.autosapien.ai | Gmail, Drive, Calendar |
| Todoist | https://todoist.autosapien.ai | Task management |
| iCloud | https://icloud.autosapien.ai | Apple Mail, Calendar, Contacts |
| Outlook | https://outlook.autosapien.ai | Outlook email/calendar (read-only) |
| Integrator | https://integrator.autosapien.ai | Unified interface to all services |
| Hydraulic | https://hydraulic.autosapien.ai | AI schematic analysis |

---

## 📝 Quick Commands Reference

**View logs:**
```bash
docker-compose -f docker-compose.autosapien.yml logs -f
```

**Restart services:**
```bash
docker-compose -f docker-compose.autosapien.yml restart
```

**Stop all:**
```bash
docker-compose -f docker-compose.autosapien.yml down
```

**Rebuild single service:**
```bash
docker-compose -f docker-compose.autosapien.yml up -d --build mcp-google
```

---

## 🏠 To Add Home Assistant Later

1. Uncomment Home Assistant in docker-compose.autosapien.yml
2. Add to Cloudflare tunnel config
3. Add DNS route: `cloudflared tunnel route dns mcp-autosapien homeassistant.autosapien.ai`
4. Rebuild: `docker-compose -f docker-compose.autosapien.yml up -d --build mcp-homeassistant`

---

**Estimated Total Time: ~40 minutes**
**Let's go! 🚀**
