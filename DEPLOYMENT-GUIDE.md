# Complete MCP Deployment Guide

**Everything you need to deploy MCP connectors on Proxmox with remote access**

This guide consolidates all deployment steps in one place, from initial setup to accessing your MCP servers from any device.

---

## Table of Contents

1. [Overview](#overview)
2. [Prerequisites](#prerequisites)
3. [Architecture](#architecture)
4. [Step 1: Prepare Credentials on Your Laptop](#step-1-prepare-credentials-on-your-laptop)
5. [Step 2: Setup Proxmox LXC Container](#step-2-setup-proxmox-lxc-container)
6. [Step 3: Copy Credentials from Laptop to Proxmox](#step-3-copy-credentials-from-laptop-to-proxmox)
7. [Step 4: Setup Cloudflare Tunnel](#step-4-setup-cloudflare-tunnel)
8. [Step 5: Deploy MCP Servers](#step-5-deploy-mcp-servers)
9. [Step 6: Configure Claude Apps](#step-6-configure-claude-apps)
10. [Testing & Verification](#testing--verification)
11. [Security Setup](#security-setup)
12. [Maintenance](#maintenance)
13. [Troubleshooting](#troubleshooting)

---

## Overview

### What You're Deploying

A complete MCP (Model Context Protocol) server infrastructure that provides:
- 🌐 Remote access from iPhone, laptop, and any device
- 🔐 Secure connections via Cloudflare Tunnel
- 🏠 Self-hosted on your Proxmox server
- 🔌 7 powerful connectors

### Available Connectors

| Connector | Services | Port | Documentation |
|-----------|----------|------|---------------|
| **GitHub** | Repos, Issues, PRs, Actions | 3001 | [mcp/github/README.md](mcp/github/README.md) |
| **Google** | Gmail, Drive, Calendar, Photos | 3004 | [mcp/google/README.md](mcp/google/README.md) |
| **Todoist** | Tasks, Projects, Labels | 3005 | [mcp/todoist/README.md](mcp/todoist/README.md) |
| **Home Assistant** | Smart Home Control | 3006 | [mcp/homeassistant/README.md](mcp/homeassistant/README.md) |
| **Notion** | Databases, Pages, Blocks | 3007 | [mcp/notion/README.md](mcp/notion/README.md) |
| **Slack** | Messages, Channels, Files | 3008 | [mcp/slack/README.md](mcp/slack/README.md) |
| **iCloud** | Mail, Calendar, Contacts, Drive | 3009 | [mcp/icloud/README.md](mcp/icloud/README.md) |

---

## Prerequisites

### What You Need

- ✅ **Proxmox server** - Running and accessible on your network
- ✅ **Domain name** - Added to Cloudflare (free account works)
- ✅ **Laptop/Desktop** - For initial credential setup
- ✅ **SSH access** - To your Proxmox host
- ✅ **Basic knowledge** - Linux commands, Docker basics

### Estimated Time

- **Minimal setup** (2-3 connectors): 30-45 minutes
- **Full setup** (all 7 connectors): 1-2 hours

---

## Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                     Your Devices                             │
│              iPhone  •  Laptop  •  Tablet                    │
└────────────────────────┬────────────────────────────────────┘
                         │ HTTPS
                         ▼
┌─────────────────────────────────────────────────────────────┐
│                  Cloudflare Edge Network                     │
│              (Zero Trust + Tunnel Encryption)                │
└────────────────────────┬────────────────────────────────────┘
                         │ Encrypted Tunnel
                         ▼
┌─────────────────────────────────────────────────────────────┐
│                    Proxmox Host                              │
│   ┌─────────────────────────────────────────────────────┐   │
│   │            LXC Container (Debian 12)                 │   │
│   │                                                       │   │
│   │  ┌─────────────────────────────────────────────┐    │   │
│   │  │       Docker Compose Network                │    │   │
│   │  │                                              │    │   │
│   │  │  ┌──────────┐  ┌──────────┐  ┌──────────┐  │    │   │
│   │  │  │  GitHub  │  │  Google  │  │ Todoist  │  │    │   │
│   │  │  │   :3001  │  │   :3004  │  │   :3005  │  │    │   │
│   │  │  └──────────┘  └──────────┘  └──────────┘  │    │   │
│   │  │                                              │    │   │
│   │  │  ┌──────────┐  ┌──────────┐  ┌──────────┐  │    │   │
│   │  │  │  Home    │  │  Notion  │  │  Slack   │  │    │   │
│   │  │  │Assistant │  │   :3007  │  │   :3008  │  │    │   │
│   │  │  │   :3006  │  └──────────┘  └──────────┘  │    │   │
│   │  │  └──────────┘                               │    │   │
│   │  │                                              │    │   │
│   │  │  ┌──────────┐  ┌──────────────────────┐    │    │   │
│   │  │  │  iCloud  │  │    cloudflared       │    │    │   │
│   │  │  │   :3009  │  │   (tunnel daemon)    │    │    │   │
│   │  │  └──────────┘  └──────────────────────┘    │    │   │
│   │  └─────────────────────────────────────────────┘    │   │
│   └─────────────────────────────────────────────────────┘   │
└─────────────────────────────────────────────────────────────┘
```

---

## Step 1: Prepare Credentials on Your Laptop

Before deploying to Proxmox, set up all credentials on your laptop. This makes it easy to test and then copy everything over.

### 1.1 Clone Repository on Laptop

```bash
# Clone the repository
git clone https://github.com/tchiro88/MCP_CREATOR.git
cd MCP_CREATOR
```

### 1.2 Get Credentials for Each Service

For detailed instructions on obtaining each credential, see [CREDENTIALS-GUIDE.md](CREDENTIALS-GUIDE.md).

Quick reference for obtaining credentials:

#### GitHub (Optional)
```bash
# 1. Go to: https://github.com/settings/tokens
# 2. Generate new token (classic)
# 3. Scopes: repo, read:user, write:repo_hook
# 4. Copy token: ghp_xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx
```

#### Google (Gmail, Drive, Calendar)
```bash
# 1. Go to: https://console.cloud.google.com/
# 2. Create project & enable APIs (Gmail, Drive, Calendar)
# 3. Create OAuth Desktop credentials
# 4. Download as credentials.json
# 5. Run authentication locally (see below)
```

**Authenticate Google locally** (must do on laptop):
```bash
cd mcp/google
pip install -r requirements.txt
cp ~/Downloads/credentials.json .
python server.py
# Opens browser, authenticate, creates token.json
```

#### Todoist
```bash
# 1. Go to: https://todoist.com/prefs/integrations
# 2. Copy API token: xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx
```

#### Home Assistant
```bash
# 1. Open Home Assistant
# 2. Profile → Long-Lived Access Tokens → Create
# 3. Name: "MCP Server"
# 4. Copy token: eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...
```

#### Notion
```bash
# 1. Go to: https://www.notion.so/my-integrations
# 2. Create new integration: "MCP Server"
# 3. Copy integration token: secret_xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx
# 4. Share your databases/pages with the integration
```

#### Slack
```bash
# 1. Go to: https://api.slack.com/apps
# 2. Create new app: "MCP Server"
# 3. Add bot token scopes (channels, chat, users, files)
# 4. Install to workspace
# 5. Copy bot token: xoxb-xxxxxxxxxxxx-xxxxxxxxxxxx-xxxxxxxxxxxxxxxxxxxxxxxx
```

#### iCloud
```bash
# 1. Go to: https://appleid.apple.com/account/manage
# 2. Security → App-Specific Passwords → Generate
# 3. Label: "MCP Server"
# 4. Copy password: xxxx-xxxx-xxxx-xxxx
```

### 1.3 Create .env File on Laptop

```bash
cd deployment
cp .env.minimal.example .env
nano .env
```

Fill in your credentials:

```bash
# Cloudflare Tunnel (will get this in Step 4)
CLOUDFLARE_TUNNEL_TOKEN=

# GitHub
GITHUB_TOKEN=ghp_xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx

# Todoist
TODOIST_API_TOKEN=xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx

# Home Assistant
HA_URL=http://homeassistant.local:8123
HA_TOKEN=eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...

# Notion
NOTION_TOKEN=secret_xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx

# Slack
SLACK_BOT_TOKEN=xoxb-xxxxxxxxxxxx-xxxxxxxxxxxx-xxxxxxxxxxxxxxxxxxxxxxxx

# iCloud
ICLOUD_USERNAME=your-apple-id@icloud.com
ICLOUD_PASSWORD=xxxx-xxxx-xxxx-xxxx
```

### 1.4 Setup Google Credentials Directory

```bash
# Create credentials directory structure
mkdir -p deployment/credentials/google

# Copy Google credentials (after authenticating locally)
cp mcp/google/credentials.json deployment/credentials/google/
cp mcp/google/token.json deployment/credentials/google/

# Verify files exist
ls -la deployment/credentials/google/
# Should see: credentials.json and token.json
```

### 1.5 Verify Everything Locally (Optional but Recommended)

Test that your credentials work before copying to Proxmox:

```bash
# Test Google MCP
cd mcp/google
python server.py
# Should start without errors

# Test Todoist MCP
cd ../todoist
export TODOIST_API_TOKEN=your_token_here
python server.py
# Should start without errors
```

Press `Ctrl+C` to stop each test.

---

## Step 2: Setup Proxmox LXC Container

### 2.1 Create LXC Container

SSH into your Proxmox host:

```bash
ssh root@your-proxmox-ip
```

Create a Debian 12 LXC container:

```bash
# Create LXC (adjust parameters as needed)
pct create 200 local:vztmpl/debian-12-standard_12.2-1_amd64.tar.zst \
  --hostname mcp-server \
  --memory 4096 \
  --swap 2048 \
  --cores 2 \
  --net0 name=eth0,bridge=vmbr0,ip=dhcp \
  --storage local-lvm \
  --rootfs local-lvm:32 \
  --unprivileged 1 \
  --features nesting=1

# Start the container
pct start 200

# Verify it's running
pct status 200
```

**Note**: Container ID `200` is used throughout this guide. Adjust if you use a different ID.

### 2.2 Get LXC IP Address

```bash
# Get the IP address of your LXC
pct exec 200 -- ip addr show eth0 | grep "inet "
# Example output: inet 192.168.1.150/24

# Save this IP - you'll need it later!
export LXC_IP=192.168.1.150  # Replace with your actual IP
```

### 2.3 Enter LXC and Install Docker

```bash
# Enter the container
pct enter 200
```

Inside the LXC, run:

```bash
# Update system
apt update && apt upgrade -y

# Install required packages
apt install -y curl git nano

# Install Docker
curl -fsSL https://get.docker.com -o get-docker.sh
sh get-docker.sh

# Install Docker Compose
apt install -y docker-compose

# Verify installations
docker --version
docker-compose --version

# Exit LXC (we'll come back later)
exit
```

### 2.4 Clone Repository in LXC

```bash
# Still on Proxmox host
# Clone repository into LXC
pct exec 200 -- mkdir -p /opt
pct exec 200 -- bash -c "cd /opt && git clone https://github.com/tchiro88/MCP_CREATOR.git"

# Verify
pct exec 200 -- ls -la /opt/MCP_CREATOR
```

---

## Step 3: Copy Credentials from Laptop to Proxmox

**This is the critical step!** Here we'll copy all your prepared credentials from your laptop to the Proxmox LXC.

### 3.1 Copy Files from Laptop to Proxmox Host

On your **laptop**, run these commands:

```bash
# Navigate to your repository
cd /path/to/MCP_CREATOR

# Copy .env file to Proxmox host
scp deployment/.env root@your-proxmox-ip:/tmp/mcp-env

# Copy Google credentials directory to Proxmox host
scp -r deployment/credentials root@your-proxmox-ip:/tmp/mcp-credentials

# Verify transfer completed
ssh root@your-proxmox-ip "ls -la /tmp/mcp-*"
```

**Expected output:**
```
-rw-r--r-- 1 root root  XXX Dec  1 12:00 /tmp/mcp-env

/tmp/mcp-credentials/google:
total 16
drwxr-xr-x 2 root root 4096 Dec  1 12:00 .
drwxr-xr-x 3 root root 4096 Dec  1 12:00 ..
-rw-r--r-- 1 root root  XXX Dec  1 12:00 credentials.json
-rw-r--r-- 1 root root  XXX Dec  1 12:00 token.json
```

### 3.2 Copy Files from Proxmox Host to LXC

On your **Proxmox host**, run these commands:

```bash
# Push .env file into LXC
pct push 200 /tmp/mcp-env /opt/MCP_CREATOR/deployment/.env

# Create credentials directory in LXC
pct exec 200 -- mkdir -p /opt/MCP_CREATOR/deployment/credentials/google

# Push Google credentials into LXC
pct push 200 /tmp/mcp-credentials/google/credentials.json /opt/MCP_CREATOR/deployment/credentials/google/credentials.json
pct push 200 /tmp/mcp-credentials/google/token.json /opt/MCP_CREATOR/deployment/credentials/google/token.json

# Verify files are in LXC
pct exec 200 -- ls -la /opt/MCP_CREATOR/deployment/.env
pct exec 200 -- ls -la /opt/MCP_CREATOR/deployment/credentials/google/
```

### 3.3 Set Proper Permissions

```bash
# Set restrictive permissions for security
pct exec 200 -- chmod 600 /opt/MCP_CREATOR/deployment/.env
pct exec 200 -- chmod 600 /opt/MCP_CREATOR/deployment/credentials/google/credentials.json
pct exec 200 -- chmod 600 /opt/MCP_CREATOR/deployment/credentials/google/token.json

# Verify permissions
pct exec 200 -- ls -la /opt/MCP_CREATOR/deployment/.env
# Should show: -rw------- (600)
```

### 3.4 Clean Up Temporary Files

```bash
# Remove temporary files from Proxmox host
rm /tmp/mcp-env
rm -rf /tmp/mcp-credentials/

# Verify cleanup
ls /tmp/mcp-*
# Should show: No such file or directory
```

### 3.5 Alternative: Direct SCP to LXC (if LXC has SSH)

If you've enabled SSH in your LXC, you can copy directly:

```bash
# From your laptop
cd /path/to/MCP_CREATOR

# Copy directly to LXC
scp deployment/.env root@lxc-ip:/opt/MCP_CREATOR/deployment/
scp -r deployment/credentials root@lxc-ip:/opt/MCP_CREATOR/deployment/

# Set permissions remotely
ssh root@lxc-ip "chmod 600 /opt/MCP_CREATOR/deployment/.env"
ssh root@lxc-ip "chmod 600 /opt/MCP_CREATOR/deployment/credentials/google/*"
```

### 3.6 Alternative: Using rsync (Preserves Permissions)

```bash
# From your laptop - if rsync is available
rsync -avz --progress deployment/.env root@your-proxmox-ip:/tmp/
rsync -avz --progress deployment/credentials/ root@your-proxmox-ip:/tmp/mcp-credentials/

# Then push to LXC as shown in Step 3.2
```

---

## Step 4: Setup Cloudflare Tunnel

### 4.1 Install cloudflared (on your laptop or LXC)

**Option A: On your laptop** (recommended for easier setup):

```bash
# macOS
brew install cloudflare/cloudflare/cloudflared

# Linux
wget https://github.com/cloudflare/cloudflared/releases/latest/download/cloudflared-linux-amd64.deb
sudo dpkg -i cloudflared-linux-amd64.deb

# Verify
cloudflared --version
```

**Option B: Inside LXC**:

```bash
pct exec 200 -- bash -c "wget https://github.com/cloudflare/cloudflared/releases/latest/download/cloudflared-linux-amd64.deb && dpkg -i cloudflared-linux-amd64.deb"
```

### 4.2 Authenticate with Cloudflare

```bash
# This opens a browser window
cloudflared tunnel login

# Select your domain when prompted
# Certificate saved to ~/.cloudflared/cert.pem
```

### 4.3 Create Tunnel

```bash
cloudflared tunnel create mcp-tunnel
```

**Output example:**
```
Created tunnel mcp-tunnel with id a1b2c3d4-e5f6-g7h8-i9j0-k1l2m3n4o5p6
Credentials written to: /root/.cloudflared/a1b2c3d4-e5f6-g7h8-i9j0-k1l2m3n4o5p6.json
```

**Save the tunnel ID!** You'll need it.

### 4.4 Get Tunnel Token

```bash
cloudflared tunnel token mcp-tunnel
```

**Copy the entire token** (starts with `eyJh...`). This is your `CLOUDFLARE_TUNNEL_TOKEN`.

### 4.5 Add Token to .env File

**On your laptop:**

```bash
# Edit your local .env file
cd MCP_CREATOR/deployment
nano .env

# Add this line at the top:
CLOUDFLARE_TUNNEL_TOKEN=eyJh...your-very-long-token...
```

**Copy updated .env to Proxmox:**

```bash
# From laptop
scp deployment/.env root@your-proxmox-ip:/tmp/mcp-env

# On Proxmox host
pct push 200 /tmp/mcp-env /opt/MCP_CREATOR/deployment/.env
rm /tmp/mcp-env

# Verify token is in LXC
pct exec 200 -- grep CLOUDFLARE_TUNNEL_TOKEN /opt/MCP_CREATOR/deployment/.env
```

### 4.6 Configure DNS Routes

Replace `yourdomain.com` with your actual domain:

```bash
cloudflared tunnel route dns mcp-tunnel github.yourdomain.com
cloudflared tunnel route dns mcp-tunnel google.yourdomain.com
cloudflared tunnel route dns mcp-tunnel todoist.yourdomain.com
cloudflared tunnel route dns mcp-tunnel ha.yourdomain.com
cloudflared tunnel route dns mcp-tunnel notion.yourdomain.com
cloudflared tunnel route dns mcp-tunnel slack.yourdomain.com
cloudflared tunnel route dns mcp-tunnel icloud.yourdomain.com
```

**Verify DNS records:**
```bash
# Wait 30 seconds for DNS propagation
nslookup github.yourdomain.com
# Should resolve to Cloudflare IPs
```

---

## Step 5: Deploy MCP Servers

### 5.1 Verify Configuration

```bash
# Enter LXC
pct enter 200

cd /opt/MCP_CREATOR/deployment

# Verify .env file has all tokens
cat .env | grep -v "^#" | grep -v "^$"

# Verify Google credentials exist
ls -la credentials/google/
# Should see: credentials.json, token.json

# Verify docker-compose file exists
ls -la docker-compose.minimal.yml
```

### 5.2 Build and Start Services

```bash
# Still inside LXC
cd /opt/MCP_CREATOR/deployment

# Build and start all services
docker-compose -f docker-compose.minimal.yml up -d --build

# This will:
# - Build Docker images for each MCP connector
# - Start containers
# - Start Cloudflare Tunnel
# Takes 2-5 minutes depending on your server
```

### 5.3 Monitor Startup

```bash
# Watch logs in real-time
docker-compose -f docker-compose.minimal.yml logs -f

# Press Ctrl+C to stop watching

# Check container status
docker-compose -f docker-compose.minimal.yml ps
```

**Expected output:**
```
NAME                  STATE     PORTS
cloudflared           running
mcp-github            running   0.0.0.0:3001->3000/tcp
mcp-google            running   0.0.0.0:3004->3000/tcp
mcp-todoist           running   0.0.0.0:3005->3000/tcp
mcp-homeassistant     running   0.0.0.0:3006->3000/tcp
mcp-notion            running   0.0.0.0:3007->3000/tcp
mcp-slack             running   0.0.0.0:3008->3000/tcp
mcp-icloud            running   0.0.0.0:3009->3000/tcp
```

### 5.4 Test Local Connectivity

```bash
# Still inside LXC
# Test each connector locally

curl http://localhost:3001/health  # GitHub
curl http://localhost:3004/health  # Google
curl http://localhost:3005/health  # Todoist
curl http://localhost:3006/health  # Home Assistant
curl http://localhost:3007/health  # Notion
curl http://localhost:3008/health  # Slack
curl http://localhost:3009/health  # iCloud

# All should return: {"status": "healthy"} or similar
```

### 5.5 Exit LXC

```bash
exit  # Back to Proxmox host
```

---

## Step 6: Configure Claude Apps

Now configure Claude apps on your devices to use your MCP servers.

### 6.1 Claude Desktop (Mac/Linux)

**macOS:**
```bash
nano ~/Library/Application\ Support/Claude/claude_desktop_config.json
```

**Linux:**
```bash
nano ~/.config/Claude/claude_desktop_config.json
```

**Configuration** (replace `yourdomain.com`):

```json
{
  "mcpServers": {
    "github": {
      "url": "https://github.yourdomain.com",
      "transport": "http"
    },
    "google": {
      "url": "https://google.yourdomain.com",
      "transport": "http"
    },
    "todoist": {
      "url": "https://todoist.yourdomain.com",
      "transport": "http"
    },
    "homeassistant": {
      "url": "https://ha.yourdomain.com",
      "transport": "http"
    },
    "notion": {
      "url": "https://notion.yourdomain.com",
      "transport": "http"
    },
    "slack": {
      "url": "https://slack.yourdomain.com",
      "transport": "http"
    },
    "icloud": {
      "url": "https://icloud.yourdomain.com",
      "transport": "http"
    }
  }
}
```

**Restart Claude Desktop** for changes to take effect.

### 6.2 Claude Code

```bash
nano ~/.config/claude-code/config.json
```

Use the same configuration as Claude Desktop above.

### 6.3 Claude iPhone/iPad App

1. Open **Claude app**
2. Tap **Settings** (bottom right)
3. Tap **Integrations**
4. Tap **Add MCP Server**
5. For each connector:
   - **Name**: GitHub (or Google, Todoist, etc.)
   - **URL**: `https://github.yourdomain.com`
   - Tap **Add**
6. Repeat for all connectors

### 6.4 Verify MCP Connection

Open Claude and ask:
```
Can you see any MCP servers? List them.
```

Claude should respond with all configured MCP servers.

---

## Testing & Verification

### Test from Outside Your Network

From your laptop (not Proxmox):

```bash
# Test each public endpoint
curl https://github.yourdomain.com/health
curl https://google.yourdomain.com/health
curl https://todoist.yourdomain.com/health
curl https://ha.yourdomain.com/health
curl https://notion.yourdomain.com/health
curl https://slack.yourdomain.com/health
curl https://icloud.yourdomain.com/health

# All should return healthy status
```

### Test from iPhone

Open Safari on iPhone:
```
https://github.yourdomain.com/health
```

Should see: `{"status": "healthy"}`

### Test with Claude

Ask Claude to perform actual operations:

```
GitHub:
"List my GitHub repositories"
"Show open issues in my main repository"

Google:
"Check my Gmail inbox for unread emails"
"List files in my Google Drive"

Todoist:
"What tasks are due today?"
"Create a new task: Test MCP deployment"

Home Assistant:
"What's the temperature in my living room?"
"Turn on the living room lights"

Notion:
"List my Notion databases"
"Create a new page in my Notes database"

Slack:
"Show recent messages in #general"
"Send a message to #general: MCP is live!"

iCloud:
"Check my iCloud email"
"List my iCloud calendar events for today"
```

---

## Security Setup

### Enable Cloudflare Zero Trust Authentication

Add an authentication layer so only you can access MCP servers:

#### 1. Go to Cloudflare Zero Trust

https://one.dash.cloudflare.com/

#### 2. Create Access Application

- Navigate to: **Access** → **Applications**
- Click: **Add an application**
- Select: **Self-hosted**

#### 3. Configure Application

**Application Configuration:**
- **Application name**: MCP Servers
- **Session Duration**: 24 hours
- **Application domain**: `*.yourdomain.com` (wildcard covers all MCP servers)

**Identity Providers:**
- Add: Google, GitHub, or email OTP

#### 4. Add Access Policy

- **Policy name**: Allow My Access
- **Action**: Allow
- **Include**:
  - Add rule: **Emails** → `your-email@gmail.com`

#### 5. Save and Test

- Try accessing: https://github.yourdomain.com/health
- Should redirect to Cloudflare authentication
- After login, you'll have access for 24 hours

### Additional Security Measures

#### Restrict LXC Firewall (Optional)

```bash
# On Proxmox host
pct enter 200

# Install UFW
apt install -y ufw

# Allow only internal traffic and Cloudflare tunnel
ufw default deny incoming
ufw default allow outgoing
ufw allow from 192.168.1.0/24  # Your local network
ufw enable

# Check status
ufw status
```

#### Rotate Credentials Regularly

Set a reminder to rotate all tokens every 90 days:

- GitHub: Regenerate personal access token
- Google: Re-authenticate OAuth
- Todoist: Regenerate API token
- All others: Regenerate tokens/passwords

---

## Maintenance

### View Logs

```bash
# Enter LXC
pct enter 200
cd /opt/MCP_CREATOR/deployment

# View all logs
docker-compose -f docker-compose.minimal.yml logs -f

# View specific connector
docker-compose -f docker-compose.minimal.yml logs -f mcp-github
docker-compose -f docker-compose.minimal.yml logs -f mcp-google

# Last 100 lines only
docker-compose -f docker-compose.minimal.yml logs --tail=100
```

### Restart Services

```bash
# Restart all services
docker-compose -f docker-compose.minimal.yml restart

# Restart specific service
docker-compose -f docker-compose.minimal.yml restart mcp-github

# Stop all services
docker-compose -f docker-compose.minimal.yml down

# Start all services
docker-compose -f docker-compose.minimal.yml up -d
```

### Update MCP Servers

```bash
# Enter LXC
pct enter 200
cd /opt/MCP_CREATOR

# Pull latest code
git pull origin main

# Rebuild and restart
cd deployment
docker-compose -f docker-compose.minimal.yml down
docker-compose -f docker-compose.minimal.yml up -d --build
```

### Backup Credentials

**From Proxmox host:**

```bash
# Create backup directory
mkdir -p ~/mcp-backups

# Backup .env file
pct pull 200 /opt/MCP_CREATOR/deployment/.env ~/mcp-backups/env-$(date +%Y%m%d)

# Backup Google credentials
pct exec 200 -- tar -czf /tmp/google-creds.tar.gz /opt/MCP_CREATOR/deployment/credentials/google/
pct pull 200 /tmp/google-creds.tar.gz ~/mcp-backups/google-creds-$(date +%Y%m%d).tar.gz

# Clean up temp file
pct exec 200 -- rm /tmp/google-creds.tar.gz

# List backups
ls -lh ~/mcp-backups/
```

**Store backups securely** (encrypted USB drive, password manager, etc.)

### Monitor Resource Usage

```bash
# On Proxmox host
pct exec 200 -- htop

# Check disk usage
pct exec 200 -- df -h

# Check Docker disk usage
pct exec 200 -- docker system df
```

---

## Troubleshooting

### Cloudflare Tunnel Not Connecting

**Symptoms:** 502 Bad Gateway when accessing MCP URLs

**Solutions:**

```bash
# Check tunnel status
pct exec 200 -- docker-compose -f /opt/MCP_CREATOR/deployment/docker-compose.minimal.yml logs cloudflared

# Verify token is set
pct exec 200 -- grep CLOUDFLARE_TUNNEL_TOKEN /opt/MCP_CREATOR/deployment/.env

# Restart cloudflared
pct exec 200 -- docker-compose -f /opt/MCP_CREATOR/deployment/docker-compose.minimal.yml restart cloudflared
```

### Google MCP Not Working

**Symptoms:** Google connector shows errors or won't authenticate

**Solutions:**

```bash
# Check credentials exist
pct exec 200 -- ls -la /opt/MCP_CREATOR/deployment/credentials/google/

# Check credentials are readable
pct exec 200 -- cat /opt/MCP_CREATOR/deployment/credentials/google/credentials.json

# Re-copy token.json from laptop (if expired)
# On laptop:
cd MCP_CREATOR/mcp/google
python server.py  # Re-authenticate
# Then copy new token.json to Proxmox (see Step 3)
```

### Container Won't Start

**Symptoms:** Container shows "Exited" status

**Solutions:**

```bash
# Check logs for specific container
pct exec 200 -- docker-compose -f /opt/MCP_CREATOR/deployment/docker-compose.minimal.yml logs mcp-todoist

# Common issues:
# - Missing environment variable
# - Invalid credentials
# - Port already in use

# Verify .env has all required variables
pct exec 200 -- cat /opt/MCP_CREATOR/deployment/.env
```

### Home Assistant Connection Refused

**Symptoms:** Home Assistant MCP can't connect to HA instance

**Solutions:**

```bash
# Test connectivity from LXC to Home Assistant
pct exec 200 -- ping homeassistant.local

# If ping fails, use IP instead
pct exec 200 -- ping 192.168.1.100  # Your HA IP

# Update .env with IP instead of hostname
pct exec 200 -- nano /opt/MCP_CREATOR/deployment/.env
# Change: HA_URL=http://homeassistant.local:8123
# To:     HA_URL=http://192.168.1.100:8123

# Restart container
pct exec 200 -- docker-compose -f /opt/MCP_CREATOR/deployment/docker-compose.minimal.yml restart mcp-homeassistant
```

### DNS Not Resolving

**Symptoms:** `nslookup github.yourdomain.com` returns no results

**Solutions:**

```bash
# Check Cloudflare DNS dashboard
# Go to: https://dash.cloudflare.com → Select your domain → DNS → Records

# Verify CNAME records exist for each subdomain
# Each should point to: [TUNNEL-ID].cfargotunnel.com

# If missing, recreate DNS routes:
cloudflared tunnel route dns mcp-tunnel github.yourdomain.com
# Repeat for all subdomains

# Wait 5 minutes for DNS propagation
```

### Claude Can't See MCP Servers

**Symptoms:** Claude says no MCP servers are available

**Solutions:**

1. **Verify configuration file syntax** (JSON must be valid)
2. **Restart Claude Desktop/App**
3. **Test URLs manually** in browser
4. **Check firewall/Zero Trust** isn't blocking access
5. **Verify HTTPS** (must use https://, not http://)

```bash
# Test from command line
curl https://github.yourdomain.com/health

# Should return: {"status": "healthy"}
```

### Permission Denied Errors

**Symptoms:** Container logs show "permission denied" when reading credentials

**Solutions:**

```bash
# Fix file permissions
pct exec 200 -- chmod 600 /opt/MCP_CREATOR/deployment/.env
pct exec 200 -- chmod 600 /opt/MCP_CREATOR/deployment/credentials/google/*

# Fix ownership (if needed)
pct exec 200 -- chown -R root:root /opt/MCP_CREATOR/deployment/credentials/

# Restart services
pct exec 200 -- docker-compose -f /opt/MCP_CREATOR/deployment/docker-compose.minimal.yml restart
```

---

## Quick Reference

### File Locations

| Location | Path | Description |
|----------|------|-------------|
| **Laptop** | `~/MCP_CREATOR/deployment/.env` | Environment variables (all tokens) |
| **Laptop** | `~/MCP_CREATOR/deployment/credentials/google/` | Google OAuth files |
| **Proxmox LXC** | `/opt/MCP_CREATOR/deployment/.env` | Environment variables (copied) |
| **Proxmox LXC** | `/opt/MCP_CREATOR/deployment/credentials/google/` | Google OAuth files (copied) |

### Port Mapping

| Connector | Internal | LXC External | Public URL |
|-----------|----------|--------------|------------|
| GitHub | 3000 | 3001 | github.yourdomain.com |
| Google | 3000 | 3004 | google.yourdomain.com |
| Todoist | 3000 | 3005 | todoist.yourdomain.com |
| Home Assistant | 3000 | 3006 | ha.yourdomain.com |
| Notion | 3000 | 3007 | notion.yourdomain.com |
| Slack | 3000 | 3008 | slack.yourdomain.com |
| iCloud | 3000 | 3009 | icloud.yourdomain.com |

### Common Commands

```bash
# Enter LXC
pct enter 200

# View logs
docker-compose -f docker-compose.minimal.yml logs -f

# Restart all
docker-compose -f docker-compose.minimal.yml restart

# Stop all
docker-compose -f docker-compose.minimal.yml down

# Start all
docker-compose -f docker-compose.minimal.yml up -d

# Rebuild and start
docker-compose -f docker-compose.minimal.yml up -d --build

# View status
docker-compose -f docker-compose.minimal.yml ps
```

---

## Additional Resources

- **Credentials Guide**: [CREDENTIALS-GUIDE.md](CREDENTIALS-GUIDE.md) - Detailed credential setup for all services
- **Quickstart Guide**: [QUICKSTART-MINIMAL.md](QUICKSTART-MINIMAL.md) - Fast minimal setup
- **Individual Connector Docs**:
  - [GitHub](mcp/github/README.md)
  - [Google](mcp/google/README.md)
  - [Todoist](mcp/todoist/README.md)
  - [Home Assistant](mcp/homeassistant/README.md)
  - [Notion](mcp/notion/README.md)
  - [Slack](mcp/slack/README.md)
  - [iCloud](mcp/icloud/README.md)

---

## Support & Community

- **Issues**: https://github.com/tchiro88/MCP_CREATOR/issues
- **Discussions**: https://github.com/tchiro88/MCP_CREATOR/discussions
- **MCP Protocol**: https://modelcontextprotocol.io

---

**Congratulations!** 🎉

You now have a fully functional, self-hosted MCP infrastructure accessible from any device!

**What you've built:**
- ✅ 7 powerful MCP connectors
- ✅ Secure Cloudflare Tunnel access
- ✅ Accessible from iPhone, laptop, any device
- ✅ Self-hosted on your Proxmox server
- ✅ Optional Zero Trust authentication

**Next steps:**
- Explore what each connector can do
- Set up automations
- Add more connectors as needed
- Share with your team (if applicable)

---

**Last Updated**: 2025-11-09
**Version**: 1.0
