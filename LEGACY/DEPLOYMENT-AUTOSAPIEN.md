# Autosapien.ai MCP Deployment Guide

Complete step-by-step deployment to Proxmox with Cloudflare Tunnel

## Infrastructure Summary

- **Proxmox Host**: 192.168.1.32
- **Cloudflare Tunnel LXC**: 192.168.1.19 (existing)
- **New MCP LXC**: Will be created (suggested ID: 200)
- **Domain**: autosapien.ai

## Services to Deploy

| Service | Port | Route |
|---------|------|-------|
| Google (Gmail/Drive/Calendar) | 3004 | google.autosapien.ai |
| Todoist | 3005 | todoist.autosapien.ai |
| Home Assistant | 3006 | homeassistant.autosapien.ai |
| iCloud | 3009 | icloud.autosapien.ai |
| Outlook | 3010 | outlook.autosapien.ai |
| Integrator (Meta) | 3011 | integrator.autosapien.ai |
| Hydraulic Analysis | 3012 | hydraulic.autosapien.ai |

---

## Phase 1: Create Proxmox LXC Container

### Step 1.1: SSH into Proxmox Host

```bash
ssh root@192.168.1.32
```

### Step 1.2: Download Ubuntu LXC Template (if not already present)

```bash
pveam update
pveam available | grep ubuntu
pveam download local ubuntu-22.04-standard_22.04-1_amd64.tar.zst
```

### Step 1.3: Create LXC Container

```bash
pct create 200 local:vztmpl/ubuntu-22.04-standard_22.04-1_amd64.tar.zst \
  --hostname mcp-autosapien \
  --memory 4096 \
  --cores 4 \
  --rootfs local-lvm:20 \
  --net0 name=eth0,bridge=vmbr0,ip=dhcp \
  --features nesting=1 \
  --unprivileged 1 \
  --password YourSecurePassword123
```

**Note**: Replace `YourSecurePassword123` with a secure password.

### Step 1.4: Start the Container

```bash
pct start 200
```

### Step 1.5: Get the Container's IP Address

```bash
pct exec 200 -- ip addr show eth0 | grep "inet "
```

**Note the IP address** - you'll need it for Cloudflare Tunnel configuration.
Let's assume it's: **192.168.1.200**

---

## Phase 2: Setup MCP LXC Container

### Step 2.1: Enter the Container

```bash
pct enter 200
```

### Step 2.2: Update System and Install Dependencies

```bash
apt update && apt upgrade -y
apt install -y curl git docker.io docker-compose

# Enable and start Docker
systemctl enable docker
systemctl start docker

# Verify Docker is running
docker --version
docker-compose --version
```

### Step 2.3: Clone Repository

```bash
cd /opt
git clone https://github.com/YOUR-USERNAME/MCP_CREATOR.git
cd MCP_CREATOR
```

**IMPORTANT**: Replace with your actual repository URL, or use the commands in Phase 3 to copy files from your development machine.

### Step 2.4: Create Required Directories

```bash
mkdir -p /opt/MCP_CREATOR/deployment/credentials/google
```

### Step 2.5: Exit the Container

```bash
exit
```

---

## Phase 3: Transfer Credentials from Development Machine

**Run these commands on your development machine** (where you're running Claude Code):

### Option A: Via Proxmox Host (Recommended)

```bash
# From your development machine to Proxmox host
cd /root/OBSIDIAN/MCP_CREATOR/deployment
scp .env root@192.168.1.32:/tmp/mcp-env
scp -r credentials root@192.168.1.32:/tmp/mcp-credentials

# Then SSH into Proxmox and push to LXC
ssh root@192.168.1.32

# From Proxmox host to LXC
pct push 200 /tmp/mcp-env /opt/MCP_CREATOR/deployment/.env
pct push 200 /tmp/mcp-credentials /opt/MCP_CREATOR/deployment/credentials

# Set proper permissions
pct exec 200 -- chmod 600 /opt/MCP_CREATOR/deployment/.env
pct exec 200 -- chmod -R 600 /opt/MCP_CREATOR/deployment/credentials/google/*

# Clean up temporary files
rm /tmp/mcp-env
rm -rf /tmp/mcp-credentials
```

### Option B: Direct to LXC (if SSH enabled on LXC)

```bash
cd /root/OBSIDIAN/MCP_CREATOR/deployment
scp .env root@192.168.1.200:/opt/MCP_CREATOR/deployment/
scp -r credentials root@192.168.1.200:/opt/MCP_CREATOR/deployment/

# Set permissions
ssh root@192.168.1.200 "chmod 600 /opt/MCP_CREATOR/deployment/.env"
ssh root@192.168.1.200 "chmod -R 600 /opt/MCP_CREATOR/deployment/credentials/google/*"
```

### Option C: Copy Docker Compose File

Either way, also copy the custom docker-compose file:

```bash
# Via Proxmox host
scp /root/OBSIDIAN/MCP_CREATOR/deployment/docker-compose.autosapien.yml root@192.168.1.32:/tmp/
ssh root@192.168.1.32
pct push 200 /tmp/docker-compose.autosapien.yml /opt/MCP_CREATOR/deployment/
rm /tmp/docker-compose.autosapien.yml
```

---

## Phase 4: Create and Configure Cloudflare Tunnel

### Step 4.1: SSH into Cloudflare Tunnel LXC

```bash
ssh root@192.168.1.19
```

### Step 4.2: Create New Tunnel for MCP Services

```bash
cloudflared tunnel create mcp-autosapien
```

**IMPORTANT**: Copy the tunnel ID that is displayed. It will look like:
`Created tunnel mcp-autosapien with id XXXXXXXX-XXXX-XXXX-XXXX-XXXXXXXXXXXX`

### Step 4.3: Get the Tunnel Token

```bash
cloudflared tunnel token mcp-autosapien
```

**Copy the entire token** - it will be a long string starting with `eyJ...`

### Step 4.4: Update .env File on MCP LXC

SSH back into the MCP LXC and add the tunnel token:

```bash
ssh root@192.168.1.32
pct enter 200

# Edit the .env file
nano /opt/MCP_CREATOR/deployment/.env
```

Add this line at the top (replace with your actual token):

```
CLOUDFLARE_TUNNEL_TOKEN=eyJhIjoiXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXX...
```

Save and exit (Ctrl+X, Y, Enter).

### Step 4.5: Create DNS Routes

**Back on the Cloudflare Tunnel LXC** (192.168.1.19):

```bash
cloudflared tunnel route dns mcp-autosapien google.autosapien.ai
cloudflared tunnel route dns mcp-autosapien todoist.autosapien.ai
cloudflared tunnel route dns mcp-autosapien homeassistant.autosapien.ai
cloudflared tunnel route dns mcp-autosapien icloud.autosapien.ai
cloudflared tunnel route dns mcp-autosapien outlook.autosapien.ai
cloudflared tunnel route dns mcp-autosapien integrator.autosapien.ai
cloudflared tunnel route dns mcp-autosapien hydraulic.autosapien.ai
```

### Step 4.6: Configure Tunnel Ingress Rules

Create or edit the Cloudflare config file:

```bash
nano /etc/cloudflared/config-mcp.yml
```

Add this configuration:

```yaml
tunnel: mcp-autosapien
credentials-file: /root/.cloudflared/TUNNEL-ID.json

ingress:
  # Google Services
  - hostname: google.autosapien.ai
    service: http://192.168.1.200:3004

  # Todoist
  - hostname: todoist.autosapien.ai
    service: http://192.168.1.200:3005

  # Home Assistant
  - hostname: homeassistant.autosapien.ai
    service: http://192.168.1.200:3006

  # iCloud
  - hostname: icloud.autosapien.ai
    service: http://192.168.1.200:3009

  # Outlook
  - hostname: outlook.autosapien.ai
    service: http://192.168.1.200:3010

  # Integrator (Meta)
  - hostname: integrator.autosapien.ai
    service: http://192.168.1.200:3011

  # Hydraulic Analysis
  - hostname: hydraulic.autosapien.ai
    service: http://192.168.1.200:3012

  # Catch-all rule
  - service: http_status:404
```

**IMPORTANT**:
1. Replace `TUNNEL-ID` with your actual tunnel ID from Step 4.2
2. Replace `192.168.1.200` with your actual MCP LXC IP

### Step 4.7: Run the Tunnel with the New Config

```bash
cloudflared tunnel --config /etc/cloudflared/config-mcp.yml run mcp-autosapien &
```

Or add it to systemd for automatic startup:

```bash
cat > /etc/systemd/system/cloudflared-mcp.service <<EOF
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

## Phase 5: Build and Deploy MCP Services

### Step 5.1: Enter MCP LXC

```bash
ssh root@192.168.1.32
pct enter 200
cd /opt/MCP_CREATOR/deployment
```

### Step 5.2: Build and Start Services

```bash
docker-compose -f docker-compose.autosapien.yml build --no-cache
```

This will take 10-15 minutes as it builds all 6 service containers.

### Step 5.3: Start All Services

```bash
docker-compose -f docker-compose.autosapien.yml up -d
```

### Step 5.4: Check Service Status

```bash
docker-compose -f docker-compose.autosapien.yml ps
```

You should see all 7 containers running:
- mcp-google
- mcp-icloud
- mcp-outlook
- mcp-todoist
- mcp-homeassistant
- mcp-integrator
- mcp-hydraulic

### Step 5.5: View Logs

```bash
# View all logs
docker-compose -f docker-compose.autosapien.yml logs -f

# View specific service logs
docker-compose -f docker-compose.autosapien.yml logs -f mcp-google
docker-compose -f docker-compose.autosapien.yml logs -f mcp-integrator
```

Press Ctrl+C to exit logs.

---

## Phase 6: Testing and Verification

### Test 1: Local Connectivity (from MCP LXC)

```bash
curl http://localhost:3004/health
curl http://localhost:3005/health
curl http://localhost:3006/health
curl http://localhost:3009/health
curl http://localhost:3010/health
curl http://localhost:3011/health
curl http://localhost:3012/health
```

Expected response: HTTP 200 OK or JSON health status.

### Test 2: LAN Connectivity (from Proxmox host)

```bash
exit  # Exit the LXC
curl http://192.168.1.200:3004/health
curl http://192.168.1.200:3011/health
```

### Test 3: Remote Connectivity (from anywhere)

```bash
curl https://google.autosapien.ai/health
curl https://integrator.autosapien.ai/health
curl https://hydraulic.autosapien.ai/health
```

### Test 4: DNS Resolution

```bash
nslookup google.autosapien.ai
nslookup integrator.autosapien.ai
```

Should resolve to Cloudflare IPs.

---

## Phase 7: Configure Claude Desktop / Claude Code

### For Claude Desktop

Edit your Claude Desktop config:

**macOS**: `~/Library/Application Support/Claude/claude_desktop_config.json`
**Windows**: `%APPDATA%\Claude\claude_desktop_config.json`
**Linux**: `~/.config/Claude/claude_desktop_config.json`

Add these servers:

```json
{
  "mcpServers": {
    "google": {
      "url": "https://google.autosapien.ai"
    },
    "todoist": {
      "url": "https://todoist.autosapien.ai"
    },
    "homeassistant": {
      "url": "https://homeassistant.autosapien.ai"
    },
    "icloud": {
      "url": "https://icloud.autosapien.ai"
    },
    "outlook": {
      "url": "https://outlook.autosapien.ai"
    },
    "integrator": {
      "url": "https://integrator.autosapien.ai"
    },
    "hydraulic": {
      "url": "https://hydraulic.autosapien.ai"
    }
  }
}
```

Restart Claude Desktop.

### For Claude Code

If using Claude Code CLI, you can configure MCP servers similarly or use the integrator endpoint for unified access.

---

## Maintenance Commands

### Restart All Services

```bash
cd /opt/MCP_CREATOR/deployment
docker-compose -f docker-compose.autosapien.yml restart
```

### Restart Single Service

```bash
docker-compose -f docker-compose.autosapien.yml restart mcp-google
```

### Update Services (after code changes)

```bash
cd /opt/MCP_CREATOR
git pull
cd deployment
docker-compose -f docker-compose.autosapien.yml down
docker-compose -f docker-compose.autosapien.yml build --no-cache
docker-compose -f docker-compose.autosapien.yml up -d
```

### View Resource Usage

```bash
docker stats
```

### Backup Credentials

```bash
tar -czf mcp-credentials-backup-$(date +%Y%m%d).tar.gz /opt/MCP_CREATOR/deployment/credentials /opt/MCP_CREATOR/deployment/.env
```

---

## Troubleshooting

### Container Won't Start

```bash
# Check logs
docker-compose -f docker-compose.autosapien.yml logs mcp-google

# Check if credentials are mounted correctly
docker exec mcp-google ls -la /app/credentials
```

### Tunnel Connection Fails

```bash
# On Cloudflare Tunnel LXC
systemctl status cloudflared-mcp
journalctl -u cloudflared-mcp -f

# Test tunnel connectivity
cloudflared tunnel info mcp-autosapien
```

### DNS Not Resolving

Check Cloudflare dashboard → Zero Trust → Access → Tunnels → mcp-autosapien
Ensure all DNS routes are showing as "Healthy".

### Service Returns 502

1. Check if container is running: `docker ps`
2. Check if port is accessible: `curl http://localhost:3004/health`
3. Check tunnel config has correct IP: `cat /etc/cloudflared/config-mcp.yml`

---

## Security Notes

1. **.env file contains sensitive credentials** - always set permissions to 600
2. **Google tokens expire** - you may need to re-authenticate periodically
3. **Cloudflare Tunnel provides encryption** - no need for additional SSL on containers
4. **Consider enabling Cloudflare Access** for additional authentication layer
5. **Backup credentials regularly** to a secure location

---

## Next Steps

Once deployed:

1. Test each MCP service individually
2. Test the Integrator meta-service for unified access
3. Configure your Claude applications to use the endpoints
4. Set up monitoring (optional but recommended)
5. Configure log rotation for Docker containers

---

## Hydraulic Analysis Service

The Hydraulic Schematic Analysis service (HYD_AGENT_MCP) is **ENABLED** by default in this deployment.

**What it does:**
- Vision AI-powered analysis of hydraulic schematics
- Flow path tracing and optimization
- Restriction detection and pressure drop calculations
- Component impact analysis
- Machine comparison tools
- Manufacturer documentation indexing

**Usage:**
1. Drop schematic images into `/opt/MCP_CREATOR/mcp/HYD_AGENT_MCP/schematics/`
2. Drop manufacturer PDFs into `/opt/MCP_CREATOR/mcp/HYD_AGENT_MCP/manufacturer_docs/`
3. Access via Claude at `https://hydraulic.autosapien.ai`
4. Ask questions like: "Analyze the schematic in the schematics folder" or "Find the flow path from P1 to H203"

**Database Location:** `/opt/MCP_CREATOR/mcp/HYD_AGENT_MCP/database/hydraulic_analysis.db`

---

## Support

For issues:
1. Check container logs
2. Verify credentials are correct
3. Test connectivity at each layer (local → LAN → tunnel)
4. Review Cloudflare Tunnel status

**Deployment Complete!** 🎉
