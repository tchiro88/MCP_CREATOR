#!/bin/bash
################################################################################
# Google MCP Server Launcher
#
# This script runs the Google MCP server with the correct environment
# and ensures it finds the token.json and credentials.json files.
################################################################################

set -e

PROJECT_ROOT="/root/OBSIDIAN/MCP_CREATOR"
CREDENTIALS_DIR="${PROJECT_ROOT}/deployment/credentials/google"
MCP_DIR="${PROJECT_ROOT}/mcp/google"
VENV_PYTHON="${PROJECT_ROOT}/.venv/bin/python"

# Color codes
GREEN='\033[0;32m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

echo -e "${BLUE}Starting Google MCP Server...${NC}"
echo

# Check if token exists
if [ ! -f "${CREDENTIALS_DIR}/token.json" ]; then
    echo "ERROR: token.json not found at ${CREDENTIALS_DIR}/token.json"
    echo
    echo "Please complete OAuth authorization first:"
    echo "  1. Read WHEN-YOU-RETURN.md"
    echo "  2. Run ./complete_oauth_and_deploy.sh"
    exit 1
fi

# Check if credentials exist
if [ ! -f "${CREDENTIALS_DIR}/credentials.json" ]; then
    echo "ERROR: credentials.json not found at ${CREDENTIALS_DIR}/credentials.json"
    exit 1
fi

echo -e "${GREEN}✓ Credentials found${NC}"
echo -e "${GREEN}✓ Token found${NC}"
echo

# Set environment variables to point to the token and credentials
export GOOGLE_TOKEN_FILE="${CREDENTIALS_DIR}/token.json"
export GOOGLE_CREDENTIALS_FILE="${CREDENTIALS_DIR}/credentials.json"

# Run the server
echo "Starting server with:"
echo "  Token: $GOOGLE_TOKEN_FILE"
echo "  Credentials: $GOOGLE_CREDENTIALS_FILE"
echo

cd "$MCP_DIR"
exec "$VENV_PYTHON" server.py
