#!/bin/bash
#
# Cloudflare Tunnel Setup Script for autosapien.ai MCP Services
# Run this script inside LXC Container 200
#
# Usage:
#   1. SSH into Proxmox host
#   2. pct enter 200
#   3. cd /opt/MCP_CREATOR/deployment
#   4. bash setup-cloudflare-tunnel.sh
#

set -e  # Exit on error

echo "=================================================="
echo "Cloudflare Tunnel Setup for autosapien.ai"
echo "=================================================="
echo ""

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Check if running as root
if [ "$EUID" -eq 0 ]; then
    echo -e "${GREEN}✓${NC} Running as root"
else
    echo -e "${RED}✗${NC} This script must be run as root"
    echo "Please run: sudo bash setup-cloudflare-tunnel.sh"
    exit 1
fi

# Step 1: Install cloudflared
echo ""
echo -e "${BLUE}Step 1:${NC} Installing cloudflared..."

if command -v cloudflared &> /dev/null; then
    echo -e "${YELLOW}!${NC} cloudflared is already installed"
    cloudflared --version
else
    cd /tmp
    echo "Downloading cloudflared..."
    wget -q https://github.com/cloudflare/cloudflared/releases/latest/download/cloudflared-linux-amd64.deb
    echo "Installing cloudflared..."
    dpkg -i cloudflared-linux-amd64.deb
    echo -e "${GREEN}✓${NC} cloudflared installed successfully"
    cloudflared --version
fi

# Step 2: Authenticate
echo ""
echo -e "${BLUE}Step 2:${NC} Cloudflare Authentication"
echo ""

if [ -f ~/.cloudflared/cert.pem ]; then
    echo -e "${YELLOW}!${NC} Certificate already exists at ~/.cloudflared/cert.pem"
    read -p "Do you want to re-authenticate? (y/N): " -n 1 -r
    echo
    if [[ $REPLY =~ ^[Yy]$ ]]; then
        cloudflared tunnel login
    fi
else
    echo "Opening browser for Cloudflare authentication..."
    echo "Please:"
    echo "  1. Login to your Cloudflare account"
    echo "  2. Select domain: autosapien.ai"
    echo "  3. Click 'Authorize'"
    echo ""
    cloudflared tunnel login
fi

# Verify certificate
if [ -f ~/.cloudflared/cert.pem ]; then
    echo -e "${GREEN}✓${NC} Authentication successful"
else
    echo -e "${RED}✗${NC} Authentication failed - cert.pem not found"
    exit 1
fi

# Step 3: Create or use existing tunnel
echo ""
echo -e "${BLUE}Step 3:${NC} Creating Cloudflare Tunnel"
echo ""

TUNNEL_NAME="autosapien-mcp"

# Check if tunnel already exists
if cloudflared tunnel list | grep -q "$TUNNEL_NAME"; then
    echo -e "${YELLOW}!${NC} Tunnel '$TUNNEL_NAME' already exists"
    TUNNEL_ID=$(cloudflared tunnel list | grep "$TUNNEL_NAME" | awk '{print $1}')
    echo "Using existing tunnel ID: $TUNNEL_ID"
else
    echo "Creating new tunnel: $TUNNEL_NAME"
    cloudflared tunnel create $TUNNEL_NAME
    TUNNEL_ID=$(cloudflared tunnel list | grep "$TUNNEL_NAME" | awk '{print $1}')
    echo -e "${GREEN}✓${NC} Tunnel created with ID: $TUNNEL_ID"
fi

# Verify tunnel ID
if [ -z "$TUNNEL_ID" ]; then
    echo -e "${RED}✗${NC} Failed to get tunnel ID"
    exit 1
fi

# Step 4: Route DNS
echo ""
echo -e "${BLUE}Step 4:${NC} Routing DNS for all services"
echo ""

SERVICES=(
    "google.autosapien.ai"
    "outlook.autosapien.ai"
    "todoist.autosapien.ai"
    "icloud.autosapien.ai"
    "integrator.autosapien.ai"
    "hydraulic.autosapien.ai"
)

for service in "${SERVICES[@]}"; do
    echo "Routing: $service"
    if cloudflared tunnel route dns $TUNNEL_NAME $service 2>&1 | grep -q "already exists"; then
        echo -e "${YELLOW}!${NC} DNS route for $service already exists"
    else
        cloudflared tunnel route dns $TUNNEL_NAME $service
        echo -e "${GREEN}✓${NC} Routed $service"
    fi
done

# Step 5: Configure tunnel
echo ""
echo -e "${BLUE}Step 5:${NC} Configuring tunnel"
echo ""

mkdir -p ~/.cloudflared

# Copy template
if [ -f /opt/MCP_CREATOR/deployment/cloudflared-config.autosapien.yml ]; then
    cp /opt/MCP_CREATOR/deployment/cloudflared-config.autosapien.yml ~/.cloudflared/config.yml
    echo -e "${GREEN}✓${NC} Copied configuration template"
else
    echo -e "${RED}✗${NC} Configuration template not found"
    exit 1
fi

# Update tunnel ID in config
sed -i "s/YOUR_TUNNEL_ID_HERE/$TUNNEL_ID/g" ~/.cloudflared/config.yml
echo -e "${GREEN}✓${NC} Updated configuration with tunnel ID"

# Validate configuration
echo ""
echo "Validating configuration..."
if cloudflared tunnel ingress validate; then
    echo -e "${GREEN}✓${NC} Configuration is valid"
else
    echo -e "${RED}✗${NC} Configuration validation failed"
    exit 1
fi

# Step 6: Install service
echo ""
echo -e "${BLUE}Step 6:${NC} Installing as system service"
echo ""

if systemctl is-active --quiet cloudflared; then
    echo -e "${YELLOW}!${NC} cloudflared service is already running"
    read -p "Do you want to restart it? (y/N): " -n 1 -r
    echo
    if [[ $REPLY =~ ^[Yy]$ ]]; then
        systemctl restart cloudflared
        echo -e "${GREEN}✓${NC} Service restarted"
    fi
else
    if systemctl list-unit-files | grep -q cloudflared.service; then
        echo -e "${YELLOW}!${NC} Service already installed"
    else
        cloudflared service install
        echo -e "${GREEN}✓${NC} Service installed"
    fi

    systemctl start cloudflared
    systemctl enable cloudflared
    echo -e "${GREEN}✓${NC} Service started and enabled"
fi

# Step 7: Verify
echo ""
echo -e "${BLUE}Step 7:${NC} Verifying setup"
echo ""

# Check service status
if systemctl is-active --quiet cloudflared; then
    echo -e "${GREEN}✓${NC} cloudflared service is running"
else
    echo -e "${RED}✗${NC} cloudflared service is not running"
    systemctl status cloudflared
fi

# Check Docker containers
echo ""
echo "Checking Docker containers..."
if docker ps --filter 'name=mcp-' --format '{{.Names}}' | grep -q mcp-; then
    echo -e "${GREEN}✓${NC} MCP containers are running:"
    docker ps --filter 'name=mcp-' --format '  - {{.Names}} ({{.Status}})'
else
    echo -e "${YELLOW}!${NC} No MCP containers found running"
    echo "Start them with: cd /opt/MCP_CREATOR/deployment && docker compose -f docker-compose.autosapien.yml up -d"
fi

# Final summary
echo ""
echo "=================================================="
echo -e "${GREEN}✓ Cloudflare Tunnel Setup Complete!${NC}"
echo "=================================================="
echo ""
echo "Tunnel ID: $TUNNEL_ID"
echo "Tunnel Name: $TUNNEL_NAME"
echo ""
echo "Services exposed:"
for service in "${SERVICES[@]}"; do
    echo "  - https://$service"
done
echo ""
echo "Next steps:"
echo "  1. Test connectivity: curl -I https://google.autosapien.ai"
echo "  2. Update Claude Desktop config with remote URLs"
echo "  3. Check tunnel status: systemctl status cloudflared"
echo "  4. View logs: journalctl -u cloudflared -f"
echo ""
echo "Cloudflare Dashboard:"
echo "  - Tunnel: https://one.dash.cloudflare.com"
echo "  - DNS: https://dash.cloudflare.com"
echo ""
echo "For troubleshooting, see: /opt/MCP_CREATOR/CLOUDFLARE-TUNNEL-SETUP.md"
echo "=================================================="
