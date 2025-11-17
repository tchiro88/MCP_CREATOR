#!/bin/bash
################################################################################
# Google OAuth Complete & Deploy Automation
#
# This script automates the entire OAuth token generation and deployment process
# Usage: ./complete_oauth_and_deploy.sh '<redirect-url-from-browser>'
################################################################################

set -e  # Exit on error

# Color codes for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Configuration
PORT=8080
PROJECT_ROOT="/root/OBSIDIAN/MCP_CREATOR"
TOKEN_SOURCE="${PROJECT_ROOT}/deployment/credentials/google/token.json"
TOKEN_DEST="${PROJECT_ROOT}/deployment/credentials/google/token.json"
GOOGLE_MCP_SERVER="${PROJECT_ROOT}/mcp/google/server.py"
VENV_PYTHON="${PROJECT_ROOT}/oauth_venv/bin/python"
GENERATE_SCRIPT="${PROJECT_ROOT}/generate_token_port.py"

# Banner
echo "================================================================================"
echo -e "${BLUE}Google OAuth Complete & Deploy Automation${NC}"
echo "================================================================================"
echo

# Check if redirect URL was provided
if [ -z "$1" ]; then
    echo -e "${RED}ERROR: No redirect URL provided${NC}"
    echo
    echo "Usage:"
    echo "  $0 '<redirect-url>'"
    echo
    echo "Example:"
    echo "  $0 'http://localhost:8080/?state=xxx&code=xxx&scope=xxx'"
    echo
    echo -e "${YELLOW}Tip: Make sure to wrap the URL in quotes!${NC}"
    exit 1
fi

REDIRECT_URL="$1"

# Validate the redirect URL format
if [[ ! "$REDIRECT_URL" =~ ^http://localhost:${PORT}/\?.*code= ]]; then
    echo -e "${RED}ERROR: Invalid redirect URL format${NC}"
    echo
    echo "Expected format: http://localhost:${PORT}/?state=xxx&code=xxx&scope=xxx"
    echo "Received: $REDIRECT_URL"
    echo
    echo "Make sure you:"
    echo "  1. Copied the COMPLETE URL from your browser"
    echo "  2. Wrapped the URL in quotes"
    echo "  3. Used the correct port (${PORT})"
    exit 1
fi

echo -e "${BLUE}[1/5]${NC} Generating OAuth token..."
echo "----------------------------------------"

# Generate the token
if ! "$VENV_PYTHON" "$GENERATE_SCRIPT" complete "$PORT" "$REDIRECT_URL"; then
    echo
    echo -e "${RED}ERROR: Token generation failed${NC}"
    echo
    echo "Common issues:"
    echo "  - Authorization code has expired (they expire quickly)"
    echo "  - URL was not copied correctly"
    echo "  - OAuth client configuration issue"
    echo
    echo "Try:"
    echo "  1. Generate a new auth URL: oauth_venv/bin/python generate_token_port.py 8080"
    echo "  2. Complete authorization in browser again"
    echo "  3. Run this script with the new redirect URL"
    exit 1
fi

echo
echo -e "${GREEN}✓ Token generated successfully${NC}"
echo

# Verify token file exists
if [ ! -f "$TOKEN_SOURCE" ]; then
    echo -e "${RED}ERROR: Token file not found at: $TOKEN_SOURCE${NC}"
    exit 1
fi

echo -e "${BLUE}[2/5]${NC} Verifying token file..."
echo "----------------------------------------"

# Check token file has required fields
if ! grep -q "refresh_token" "$TOKEN_SOURCE"; then
    echo -e "${YELLOW}WARNING: No refresh token found in token.json${NC}"
    echo "The access token will expire and cannot be refreshed automatically."
    echo "You may need to re-authorize later."
    echo
else
    echo -e "${GREEN}✓ Refresh token present${NC}"
fi

echo -e "${GREEN}✓ Token file verified${NC}"
echo

echo -e "${BLUE}[3/5]${NC} Setting correct permissions..."
echo "----------------------------------------"

# Set secure permissions on token file
chmod 600 "$TOKEN_SOURCE"
echo -e "${GREEN}✓ Permissions set to 600 (owner read/write only)${NC}"
echo

echo -e "${BLUE}[4/5]${NC} Checking Google MCP server..."
echo "----------------------------------------"

# Verify Google MCP server exists
if [ ! -f "$GOOGLE_MCP_SERVER" ]; then
    echo -e "${YELLOW}WARNING: Google MCP server not found at: $GOOGLE_MCP_SERVER${NC}"
    echo "You may need to manually configure the server location."
    echo
else
    echo -e "${GREEN}✓ Google MCP server found${NC}"

    # Check if it's configured for FastMCP
    if grep -q "FastMCP" "$GOOGLE_MCP_SERVER"; then
        echo -e "${GREEN}✓ Server is configured for FastMCP HTTP mode${NC}"
    else
        echo -e "${YELLOW}WARNING: Server may not be configured for FastMCP${NC}"
    fi
fi

echo

echo -e "${BLUE}[5/5]${NC} Service restart (if applicable)..."
echo "----------------------------------------"

# Check for systemd service
SERVICE_NAME="google-mcp"
if systemctl list-units --all -t service --full --no-legend "${SERVICE_NAME}.service" | grep -Fq "${SERVICE_NAME}.service"; then
    echo "Found systemd service: ${SERVICE_NAME}.service"
    echo "Restarting service..."

    if systemctl restart "${SERVICE_NAME}.service" 2>/dev/null; then
        echo -e "${GREEN}✓ Service restarted successfully${NC}"
        sleep 2

        # Check service status
        if systemctl is-active --quiet "${SERVICE_NAME}.service"; then
            echo -e "${GREEN}✓ Service is running${NC}"
        else
            echo -e "${YELLOW}WARNING: Service may not be running${NC}"
            echo "Check status with: systemctl status ${SERVICE_NAME}.service"
        fi
    else
        echo -e "${YELLOW}WARNING: Could not restart service (may need sudo)${NC}"
    fi
else
    echo -e "${YELLOW}No systemd service found for Google MCP${NC}"
    echo "If you're running the server manually, restart it now to use the new token."
fi

echo

# Final summary
echo "================================================================================"
echo -e "${GREEN}DEPLOYMENT COMPLETE!${NC}"
echo "================================================================================"
echo
echo "Token location:    $TOKEN_SOURCE"
echo "Permissions:       $(ls -l "$TOKEN_SOURCE" | awk '{print $1}')"
echo "Token size:        $(wc -c < "$TOKEN_SOURCE") bytes"
echo

# Display token info
echo "Token details:"
if command -v jq &> /dev/null; then
    echo "  Scopes: $(jq -r '.scopes | length' "$TOKEN_SOURCE") scopes granted"
    echo "  Has refresh token: $(jq -r 'has("refresh_token")' "$TOKEN_SOURCE")"
    echo "  Expiry: $(jq -r '.expiry' "$TOKEN_SOURCE")"
else
    echo "  (Install jq for detailed token info: apt install jq)"
fi

echo
echo "Next steps:"
echo "  1. The token is ready to use with your Google MCP server"
echo "  2. If running the server manually, restart it with:"
echo "     python3 $GOOGLE_MCP_SERVER"
echo "  3. Test the connection from Claude Desktop"
echo
echo "================================================================================"
