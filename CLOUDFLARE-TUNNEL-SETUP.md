# Cloudflare Tunnel Setup for Remote MCP Access

## Overview

This guide walks you through setting up Cloudflare Tunnel to access your MCP servers remotely from any device (iPhone, laptop, desktop) without opening ports on your firewall.

**What you'll accomplish:**
- ✅ Securely expose your MCP services to the internet
- ✅ Access services from `google.autosapien.ai`, `outlook.autosapien.ai`, etc.
- ✅ No port forwarding required
- ✅ Free DDoS protection and SSL certificates
- ✅ Use Claude on any device with your self-hosted MCPs

**Time required:** 30-45 minutes

## Prerequisites

✅ Domain name added to Cloudflare (free account works)
✅ MCP services running on your server (see [SETUP.md](SETUP.md))
✅ SSH access to your Proxmox LXC container 200
✅ Cloudflare account (sign up at https://dash.cloudflare.com)

## Architecture

```
Your iPhone/Laptop
        ↓ HTTPS
Cloudflare Edge (DDoS protection, SSL)
        ↓ Encrypted Tunnel
cloudflared daemon (on your server)
        ↓ localhost
Docker Containers (MCP services)
```

**Services that will be exposed:**
- `google.autosapien.ai` → Google MCP (Gmail, Drive, Calendar)
- `todoist.autosapien.ai` → Todoist MCP (Tasks)
- `icloud.autosapien.ai` → iCloud MCP (Mail, Calendar, Contacts)
- `outlook.autosapien.ai` → Outlook MCP (Email, Calendar)
- `integrator.autosapien.ai` → Integrator MCP (Unified interface)
- `hydraulic.autosapien.ai` → Hydraulic MCP (Schematic analysis)

---

## Part 1: Install cloudflared on Your Server

### Step 1.1: SSH into LXC Container 200

```bash
# From your Proxmox host
pct enter 200
```

### Step 1.2: Install cloudflared

**For Debian/Ubuntu (LXC Container 200):**
```bash
# Download cloudflared
cd /tmp
wget https://github.com/cloudflare/cloudflared/releases/latest/download/cloudflared-linux-amd64.deb

# Install
sudo dpkg -i cloudflared-linux-amd64.deb

# Verify installation
cloudflared --version
# Should output: cloudflared version 2024.x.x
```

**Alternative: Install via package manager**
```bash
# Add Cloudflare GPG key
sudo mkdir -p --mode=0755 /usr/share/keyrings
curl -fsSL https://pkg.cloudflare.com/cloudflare-main.gpg | sudo tee /usr/share/keyrings/cloudflare-main.gpg >/dev/null

# Add repository
echo "deb [signed-by=/usr/share/keyrings/cloudflare-main.gpg] https://pkg.cloudflare.com/cloudflared $(lsb_release -cs) main" | sudo tee /etc/apt/sources.list.d/cloudflared.list

# Install
sudo apt-get update && sudo apt-get install cloudflared
```

---

## Part 2: Authenticate with Cloudflare

### Step 2.1: Login to Cloudflare

```bash
cloudflared tunnel login
```

**What happens:**
1. A URL will be displayed in your terminal
2. Copy the URL and open it in a browser
3. Log in to your Cloudflare account
4. Select your domain: `autosapien.ai`
5. Click "Authorize"

**Expected output:**
```
You have successfully logged in.
If you wish to copy your credentials to a server, they have been saved to:
/root/.cloudflared/cert.pem
```

### Step 2.2: Verify Certificate

```bash
ls -la ~/.cloudflared/cert.pem
# Should show: -rw------- 1 root root [size] [date] /root/.cloudflared/cert.pem
```

---

## Part 3: Create Your Tunnel

### Step 3.1: Create Named Tunnel

```bash
cloudflared tunnel create autosapien-mcp
```

**Expected output:**
```
Created tunnel autosapien-mcp with id: 12345678-1234-1234-1234-123456789abc
Credentials file: /root/.cloudflared/12345678-1234-1234-1234-123456789abc.json
```

**IMPORTANT:** Save this tunnel ID! You'll need it in the next steps.

### Step 3.2: Verify Tunnel Creation

```bash
# List all tunnels
cloudflared tunnel list

# Should show:
# ID                                   NAME              CREATED
# 12345678-1234-1234-1234-123456789abc autosapien-mcp    2024-11-17T10:00:00Z
```

---

## Part 4: Configure DNS Routes

### Step 4.1: Route All Service Domains

Run these commands to create CNAME records for each service:

```bash
cloudflared tunnel route dns autosapien-mcp google.autosapien.ai
cloudflared tunnel route dns autosapien-mcp todoist.autosapien.ai
cloudflared tunnel route dns autosapien-mcp icloud.autosapien.ai
cloudflared tunnel route dns autosapien-mcp outlook.autosapien.ai
cloudflared tunnel route dns autosapien-mcp integrator.autosapien.ai
cloudflared tunnel route dns autosapien-mcp hydraulic.autosapien.ai
```

**Expected output for each command:**
```
Created CNAME record for google.autosapien.ai, pointing to 12345678-1234-1234-1234-123456789abc.cfargotunnel.com
```

### Step 4.2: Verify DNS Records in Cloudflare Dashboard

1. Go to: https://dash.cloudflare.com
2. Select your domain: `autosapien.ai`
3. Click: **DNS** → **Records**
4. You should see 6 CNAME records:

| Type  | Name        | Content                                              |
|-------|-------------|------------------------------------------------------|
| CNAME | google      | 12345678-1234-1234-1234-123456789abc.cfargotunnel.com |
| CNAME | todoist     | 12345678-1234-1234-1234-123456789abc.cfargotunnel.com |
| CNAME | icloud      | 12345678-1234-1234-1234-123456789abc.cfargotunnel.com |
| CNAME | outlook     | 12345678-1234-1234-1234-123456789abc.cfargotunnel.com |
| CNAME | integrator  | 12345678-1234-1234-1234-123456789abc.cfargotunnel.com |
| CNAME | hydraulic   | 12345678-1234-1234-1234-123456789abc.cfargotunnel.com |

---

## Part 5: Configure Tunnel

### Step 5.1: Copy Configuration File

```bash
# Create cloudflared config directory
mkdir -p ~/.cloudflared

# Copy the autosapien.ai configuration
cp /opt/MCP_CREATOR/deployment/cloudflared-config.autosapien.yml ~/.cloudflared/config.yml
```

### Step 5.2: Update Configuration with Your Tunnel ID

```bash
# Open config file
nano ~/.cloudflared/config.yml
```

**Update these two lines:**

```yaml
# Before (line 14):
tunnel: YOUR_TUNNEL_ID_HERE

# After (replace with your actual tunnel ID):
tunnel: 12345678-1234-1234-1234-123456789abc

# Before (line 15):
credentials-file: /root/.cloudflared/YOUR_TUNNEL_ID_HERE.json

# After (replace with your actual tunnel ID):
credentials-file: /root/.cloudflared/12345678-1234-1234-1234-123456789abc.json
```

**Save and exit:** Press `Ctrl+X`, then `Y`, then `Enter`

### Step 5.3: Verify Configuration

```bash
# Check syntax
cloudflared tunnel ingress validate

# Expected output:
# Validating rules...
# OK
```

---

## Part 6: Start the Tunnel

### Step 6.1: Test Tunnel (Manual Run)

Before installing as a service, test that everything works:

```bash
cloudflared tunnel run autosapien-mcp
```

**Expected output:**
```
2024-11-17T10:00:00Z INF Starting tunnel id=12345678-1234-1234-1234-123456789abc
2024-11-17T10:00:01Z INF Connection registered connIndex=0
2024-11-17T10:00:01Z INF Connection registered connIndex=1
2024-11-17T10:00:01Z INF Connection registered connIndex=2
2024-11-17T10:00:01Z INF Connection registered connIndex=3
```

**Leave this running** and open a new terminal to test.

### Step 6.2: Test Connectivity

**In a new terminal or from your local machine:**

```bash
# Test each service endpoint
curl -I https://google.autosapien.ai
curl -I https://todoist.autosapien.ai
curl -I https://icloud.autosapien.ai
curl -I https://outlook.autosapien.ai
curl -I https://integrator.autosapien.ai
curl -I https://hydraulic.autosapien.ai
```

**Expected response:**
```
HTTP/2 200
```

Or if MCP is running correctly, you might see:
```
HTTP/2 404  # Normal if no health endpoint
```

**If you get 502 Bad Gateway:**
- Check that Docker containers are running: `pct exec 200 -- docker ps`
- Verify ports match in config.yml and docker-compose

### Step 6.3: Stop Test Run

Go back to the terminal running cloudflared and press `Ctrl+C` to stop it.

---

## Part 7: Install as System Service

### Step 7.1: Install Service

```bash
sudo cloudflared service install
```

**Expected output:**
```
systemd detected, installing cloudflared as systemd service
Successfully installed cloudflared service
```

### Step 7.2: Enable and Start Service

```bash
# Start the service
sudo systemctl start cloudflared

# Enable auto-start on boot
sudo systemctl enable cloudflared
```

### Step 7.3: Verify Service Status

```bash
sudo systemctl status cloudflared
```

**Expected output:**
```
● cloudflared.service - Cloudflare Tunnel
     Loaded: loaded (/etc/systemd/system/cloudflared.service; enabled)
     Active: active (running) since Sun 2024-11-17 10:00:00 UTC
   Main PID: 12345 (cloudflared)
      Tasks: 12
     Memory: 50M
     CGroup: /system.slice/cloudflared.service
             └─12345 /usr/local/bin/cloudflared tunnel run autosapien-mcp
```

### Step 7.4: Check Logs

```bash
# View live logs
sudo journalctl -u cloudflared -f

# View last 50 lines
sudo journalctl -u cloudflared -n 50
```

---

## Part 8: Verify in Cloudflare Dashboard

### Step 8.1: Check Tunnel Status

1. Go to: https://one.dash.cloudflare.com
2. Navigate to: **Networks** → **Tunnels**
3. You should see: `autosapien-mcp` with status **Healthy** (green)
4. Click on the tunnel to see:
   - Active connections (should be 4)
   - Traffic metrics
   - Connected services

### Step 8.2: View Analytics

- **Traffic** → View requests, bandwidth
- **Analytics** → See request rates, errors
- **Logs** → View access logs (requires Zero Trust plan)

---

## Part 9: Update Claude Desktop Configuration

Now that your services are accessible via Cloudflare Tunnel, update Claude Desktop to use the remote URLs.

### Step 9.1: Update Configuration

**Location:** `~/Library/Application Support/Claude/claude_desktop_config.json` (macOS)

```json
{
  "mcpServers": {
    "google": {
      "command": "npx",
      "args": ["-y", "@modelcontextprotocol/server-http", "https://google.autosapien.ai"]
    },
    "outlook": {
      "command": "npx",
      "args": ["-y", "@modelcontextprotocol/server-http", "https://outlook.autosapien.ai"]
    },
    "todoist": {
      "command": "npx",
      "args": ["-y", "@modelcontextprotocol/server-http", "https://todoist.autosapien.ai"]
    },
    "icloud": {
      "command": "npx",
      "args": ["-y", "@modelcontextprotocol/server-http", "https://icloud.autosapien.ai"]
    },
    "integrator": {
      "command": "npx",
      "args": ["-y", "@modelcontextprotocol/server-http", "https://integrator.autosapien.ai"]
    },
    "hydraulic": {
      "command": "npx",
      "args": ["-y", "@modelcontextprotocol/server-http", "https://hydraulic.autosapien.ai"]
    }
  }
}
```

### Step 9.2: Restart Claude Desktop

1. Quit Claude Desktop completely
2. Reopen Claude Desktop
3. Start a new conversation

### Step 9.3: Test MCP Connection

In Claude Desktop, try:

```
"Check my unread emails"
"What tasks do I have today?"
"List my Google Drive files"
```

You should see Claude accessing your services via the remote URLs! 🎉

---

## Troubleshooting

### Issue: 502 Bad Gateway

**Causes:**
- Docker containers not running
- Port mismatch in configuration
- Service crashed

**Solutions:**
```bash
# Check Docker containers
pct exec 200 -- docker ps --filter 'name=mcp-'

# Check logs
pct exec 200 -- docker logs mcp-google
pct exec 200 -- docker logs mcp-outlook

# Restart containers
pct exec 200 -- bash -c 'cd /opt/MCP_CREATOR/deployment && docker compose -f docker-compose.autosapien.yml restart'
```

### Issue: Tunnel Not Starting

**Check logs:**
```bash
sudo journalctl -u cloudflared -f
```

**Common issues:**
- Incorrect tunnel ID in config.yml
- Credentials file not found
- Config file syntax error

**Solution:**
```bash
# Validate config
cloudflared tunnel ingress validate

# Check credentials file exists
ls -la ~/.cloudflared/*.json
```

### Issue: DNS Not Resolving

**Check DNS propagation:**
```bash
# Check DNS records
dig google.autosapien.ai
nslookup google.autosapien.ai

# Should show CNAME to .cfargotunnel.com
```

**Wait time:** DNS propagation can take 1-5 minutes

### Issue: Claude Desktop Can't Connect

**Check:**
1. Services are running: `docker ps`
2. Tunnel is healthy: https://one.dash.cloudflare.com
3. URLs are accessible: `curl https://google.autosapien.ai`
4. Claude Desktop config is correct
5. Restart Claude Desktop

### Issue: Certificate Errors

**Solution:**
```bash
# Re-authenticate
cloudflared tunnel login

# Verify certificate
ls -la ~/.cloudflared/cert.pem
```

---

## Security Best Practices

### 1. Enable Cloudflare Zero Trust (Optional but Recommended)

Add authentication to your MCP services:

1. Go to: https://one.dash.cloudflare.com
2. Navigate to: **Access** → **Applications**
3. Click: **Add an application** → **Self-hosted**
4. Configure:
   - **Application name:** MCP Services
   - **Session duration:** 24 hours
   - **Application domain:** `*.autosapien.ai`
5. Add policy:
   - **Policy name:** Allow My Email
   - **Action:** Allow
   - **Include:** Your email address

### 2. Enable Rate Limiting

1. Go to: **Security** → **WAF** → **Rate limiting rules**
2. Create rule:
   - **Name:** MCP Rate Limit
   - **If hostname contains:** `autosapien.ai`
   - **Then:** Block for 10 minutes if > 100 requests/minute

### 3. Monitor Access Logs

1. Enable logs: **Analytics** → **Logs**
2. Set up alerts for suspicious activity
3. Review periodically

### 4. Secure Credentials

```bash
# Ensure correct permissions
chmod 600 ~/.cloudflared/*.json
chmod 600 ~/.cloudflared/cert.pem

# Never commit to git
ls ~/.cloudflared/
# Files should NOT be in git repository
```

---

## Maintenance

### Update cloudflared

```bash
# Download latest version
wget https://github.com/cloudflare/cloudflared/releases/latest/download/cloudflared-linux-amd64.deb
sudo dpkg -i cloudflared-linux-amd64.deb

# Restart service
sudo systemctl restart cloudflared

# Verify new version
cloudflared --version
```

### Backup Configuration

```bash
# Backup tunnel credentials and config
mkdir -p ~/backups/cloudflared
cp ~/.cloudflared/*.json ~/backups/cloudflared/
cp ~/.cloudflared/config.yml ~/backups/cloudflared/
cp ~/.cloudflared/cert.pem ~/backups/cloudflared/

# Set proper permissions
chmod 600 ~/backups/cloudflared/*
```

### Monitor Tunnel Health

```bash
# Check service status
sudo systemctl status cloudflared

# View metrics (if enabled in config)
curl http://localhost:9090/metrics

# Check Cloudflare dashboard
# https://one.dash.cloudflare.com -> Networks -> Tunnels
```

---

## Useful Commands

```bash
# Tunnel Management
cloudflared tunnel list                    # List all tunnels
cloudflared tunnel info autosapien-mcp     # Show tunnel details
cloudflared tunnel delete <tunnel-id>      # Delete tunnel

# Service Management
sudo systemctl start cloudflared           # Start service
sudo systemctl stop cloudflared            # Stop service
sudo systemctl restart cloudflared         # Restart service
sudo systemctl status cloudflared          # Check status
sudo journalctl -u cloudflared -f          # View logs

# Configuration
cloudflared tunnel ingress validate        # Validate config
cloudflared tunnel ingress rule <url>      # Test routing rules

# DNS Management
cloudflared tunnel route dns <tunnel> <hostname>   # Add DNS route
cloudflared tunnel route ip show                   # List routes
```

---

## Cost Summary

| Item | Cost |
|------|------|
| Cloudflare Tunnel | **Free** ✅ |
| SSL Certificates | **Free** ✅ |
| DDoS Protection | **Free** ✅ |
| DNS Hosting | **Free** ✅ |
| Zero Trust (up to 50 users) | **Free** ✅ |
| Domain Name | ~$10-15/year |

**Total:** ~$10-15/year for domain only!

---

## Next Steps

✅ Tunnel is now running!

**What you can do now:**
1. ✅ Access your MCP services from any device
2. ✅ Use Claude on your iPhone with self-hosted MCPs
3. ✅ Configure Zero Trust for enhanced security
4. ✅ Set up monitoring and alerts
5. ✅ Add more MCP services as needed

**Related Guides:**
- [SETUP.md](SETUP.md) - Complete MCP setup guide
- [CLAUDE-DESKTOP-SETUP.md](CLAUDE-DESKTOP-SETUP.md) - Claude Desktop configuration
- [architecture/cloudflare-tunnel-setup.md](architecture/cloudflare-tunnel-setup.md) - Advanced Cloudflare Tunnel features

---

## Additional Resources

- **Cloudflare Tunnel Docs:** https://developers.cloudflare.com/cloudflare-one/connections/connect-networks/
- **Zero Trust Docs:** https://developers.cloudflare.com/cloudflare-one/
- **MCP Specification:** https://modelcontextprotocol.io
- **Troubleshooting:** https://developers.cloudflare.com/cloudflare-one/connections/connect-networks/troubleshoot/

---

**Document Version:** 1.0
**Last Updated:** 2024-11-17
**Tested On:** Proxmox LXC Container 200 (Debian 12)
