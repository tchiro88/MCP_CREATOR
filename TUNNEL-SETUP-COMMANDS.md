# Cloudflare Tunnel Setup - Command Reference
## Quick Commands for Claude Code Terminal

This file contains all commands needed to set up Cloudflare Tunnel on Proxmox LXC Container 200.

---

## Step 1: SSH into Proxmox Host and Enter Container

```bash
# SSH into your Proxmox host (adjust IP/hostname as needed)
ssh root@192.168.1.X

# Once connected, enter LXC container 200
pct enter 200
```

---

## Step 2: Install cloudflared

```bash
# Navigate to tmp directory
cd /tmp

# Download cloudflared
wget https://github.com/cloudflare/cloudflared/releases/latest/download/cloudflared-linux-amd64.deb

# Install
dpkg -i cloudflared-linux-amd64.deb

# Verify installation
cloudflared --version
```

---

## Step 3: Authenticate with Cloudflare

```bash
# This will open a browser window - copy the URL if needed
cloudflared tunnel login
```

**Action Required:**
1. Copy the URL displayed in terminal
2. Open it in your browser
3. Login to Cloudflare
4. Select domain: `autosapien.ai`
5. Click "Authorize"

---

## Step 4: Create Tunnel

```bash
# Create the tunnel
cloudflared tunnel create autosapien-mcp

# ⚠️ IMPORTANT: Note the tunnel ID from the output!
# It will look like: 12345678-1234-1234-1234-123456789abc

# List tunnels to verify
cloudflared tunnel list
```

---

## Step 5: Route DNS for All Services

```bash
# Route all 6 MCP services to the tunnel
# Replace 'autosapien-mcp' with your tunnel name if different

cloudflared tunnel route dns autosapien-mcp google.autosapien.ai
cloudflared tunnel route dns autosapien-mcp outlook.autosapien.ai
cloudflared tunnel route dns autosapien-mcp todoist.autosapien.ai
cloudflared tunnel route dns autosapien-mcp icloud.autosapien.ai
cloudflared tunnel route dns autosapien-mcp integrator.autosapien.ai
cloudflared tunnel route dns autosapien-mcp hydraulic.autosapien.ai
```

---

## Step 6: Configure Tunnel

```bash
# Create cloudflared directory
mkdir -p ~/.cloudflared

# Copy the configuration template
cp /opt/MCP_CREATOR/deployment/cloudflared-config.autosapien.yml ~/.cloudflared/config.yml

# Edit the configuration file
nano ~/.cloudflared/config.yml
```

**In nano editor:**
1. Find line 14: `tunnel: YOUR_TUNNEL_ID_HERE`
2. Replace with your actual tunnel ID
3. Find line 15: `credentials-file: /root/.cloudflared/YOUR_TUNNEL_ID_HERE.json`
4. Replace with your actual tunnel ID
5. Save: `Ctrl+X`, then `Y`, then `Enter`

**Or use sed to replace automatically (recommended):**
```bash
# Set your tunnel ID (replace with your actual tunnel ID)
TUNNEL_ID="12345678-1234-1234-1234-123456789abc"

# Update config file
sed -i "s/YOUR_TUNNEL_ID_HERE/$TUNNEL_ID/g" ~/.cloudflared/config.yml

# Verify the changes
grep -E "tunnel:|credentials-file:" ~/.cloudflared/config.yml
```

---

## Step 7: Validate Configuration

```bash
# Validate the configuration
cloudflared tunnel ingress validate

# Should output: "OK"
```

---

## Step 8: Test Tunnel (Optional but Recommended)

```bash
# Run tunnel manually to test
cloudflared tunnel run autosapien-mcp

# Leave it running and test from another terminal/device:
# curl -I https://google.autosapien.ai
# curl -I https://outlook.autosapien.ai

# Stop with: Ctrl+C
```

---

## Step 9: Install as System Service

```bash
# Install service
cloudflared service install

# Start the service
systemctl start cloudflared

# Enable auto-start on boot
systemctl enable cloudflared

# Check status
systemctl status cloudflared

# View logs
journalctl -u cloudflared -f
# Stop logs with: Ctrl+C
```

---

## Step 10: Verify Everything Works

```bash
# Check tunnel status
cloudflared tunnel list

# Check Docker containers are running
docker ps --filter 'name=mcp-'

# Test endpoints (from any machine with internet)
curl -I https://google.autosapien.ai
curl -I https://outlook.autosapien.ai
curl -I https://todoist.autosapien.ai
curl -I https://icloud.autosapien.ai
curl -I https://integrator.autosapien.ai
curl -I https://hydraulic.autosapien.ai
```

---

## Troubleshooting Commands

```bash
# View cloudflared logs
journalctl -u cloudflared -f

# Check cloudflared service status
systemctl status cloudflared

# Restart cloudflared
systemctl restart cloudflared

# Check Docker containers
docker ps

# Check specific container logs
docker logs mcp-google
docker logs mcp-outlook

# Restart all MCP containers
cd /opt/MCP_CREATOR/deployment
docker compose -f docker-compose.autosapien.yml restart

# Validate tunnel config
cloudflared tunnel ingress validate

# Test a specific route
cloudflared tunnel ingress rule https://google.autosapien.ai
```

---

## Useful Management Commands

```bash
# Stop cloudflared
systemctl stop cloudflared

# Start cloudflared
systemctl start cloudflared

# Restart cloudflared
systemctl restart cloudflared

# Disable auto-start
systemctl disable cloudflared

# View all tunnels
cloudflared tunnel list

# Show tunnel info
cloudflared tunnel info autosapien-mcp

# Check DNS records in Cloudflare
# Go to: https://dash.cloudflare.com -> DNS -> Records
```

---

## Quick Copy-Paste Complete Setup

**If you want to run everything in one go (after SSH into container):**

```bash
# Install cloudflared
cd /tmp
wget https://github.com/cloudflare/cloudflared/releases/latest/download/cloudflared-linux-amd64.deb
dpkg -i cloudflared-linux-amd64.deb
cloudflared --version

# Authenticate (will require browser)
cloudflared tunnel login

# Create tunnel
cloudflared tunnel create autosapien-mcp

# ⚠️ STOP HERE - Note your tunnel ID from the output above!
# Then set it in the variable below and continue:

TUNNEL_ID="PASTE_YOUR_TUNNEL_ID_HERE"

# Route DNS
cloudflared tunnel route dns autosapien-mcp google.autosapien.ai
cloudflared tunnel route dns autosapien-mcp outlook.autosapien.ai
cloudflared tunnel route dns autosapien-mcp todoist.autosapien.ai
cloudflared tunnel route dns autosapien-mcp icloud.autosapien.ai
cloudflared tunnel route dns autosapien-mcp integrator.autosapien.ai
cloudflared tunnel route dns autosapien-mcp hydraulic.autosapien.ai

# Configure
mkdir -p ~/.cloudflared
cp /opt/MCP_CREATOR/deployment/cloudflared-config.autosapien.yml ~/.cloudflared/config.yml
sed -i "s/YOUR_TUNNEL_ID_HERE/$TUNNEL_ID/g" ~/.cloudflared/config.yml

# Validate
cloudflared tunnel ingress validate

# Install and start service
cloudflared service install
systemctl start cloudflared
systemctl enable cloudflared

# Check status
systemctl status cloudflared

echo "✅ Cloudflare Tunnel setup complete!"
echo "Test with: curl -I https://google.autosapien.ai"
```

---

## Environment Info

**Container:** LXC 200 (192.168.1.19)
**Location:** /opt/MCP_CREATOR
**Services:**
- google.autosapien.ai → localhost:3004
- todoist.autosapien.ai → localhost:3005
- icloud.autosapien.ai → localhost:3009
- outlook.autosapien.ai → localhost:3010
- integrator.autosapien.ai → localhost:3011
- hydraulic.autosapien.ai → localhost:3012

---

## Next Steps After Setup

1. Update Claude Desktop config with remote URLs (see SETUP.md)
2. Test MCP connections from your devices
3. Optional: Set up Cloudflare Zero Trust authentication
4. Optional: Enable monitoring and rate limiting

For detailed explanations, see: [CLOUDFLARE-TUNNEL-SETUP.md](CLOUDFLARE-TUNNEL-SETUP.md)
