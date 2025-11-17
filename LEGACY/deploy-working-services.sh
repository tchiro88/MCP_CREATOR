#!/bin/bash
# Deploy only MCP services with confirmed working credentials
# Date: 2025-11-10

echo "=================================================="
echo "Deploying MCP Services (Working Credentials Only)"
echo "=================================================="
echo ""

# Color codes
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

echo "Phase 1: Stopping all MCP services..."
ssh root@192.168.1.32 "pct exec 200 -- bash -c 'cd /opt/MCP_CREATOR/deployment && docker compose -f docker-compose.autosapien.yml down'"

if [ $? -eq 0 ]; then
    echo -e "${GREEN}✓ All services stopped${NC}"
else
    echo -e "${RED}✗ Failed to stop services${NC}"
    exit 1
fi

echo ""
echo "Phase 2: Starting services with working credentials..."
echo "  - mcp-google (Google credentials verified)"
echo "  - mcp-hydraulic (OpenAI API key)"
echo ""

ssh root@192.168.1.32 "pct exec 200 -- bash -c 'cd /opt/MCP_CREATOR/deployment && docker compose -f docker-compose.autosapien.yml up -d mcp-google mcp-hydraulic'"

if [ $? -eq 0 ]; then
    echo -e "${GREEN}✓ Services started${NC}"
else
    echo -e "${RED}✗ Failed to start services${NC}"
    exit 1
fi

echo ""
echo "Waiting 15 seconds for services to initialize..."
sleep 15

echo ""
echo "=================================================="
echo "Service Status Check"
echo "=================================================="
ssh root@192.168.1.32 "pct exec 200 -- docker ps -a --filter 'name=mcp-'"

echo ""
echo "=================================================="
echo "Google Service Logs (last 20 lines)"
echo "=================================================="
ssh root@192.168.1.32 "pct exec 200 -- docker logs mcp-google --tail=20"

echo ""
echo "=================================================="
echo "Hydraulic Service Logs (last 20 lines)"
echo "=================================================="
ssh root@192.168.1.32 "pct exec 200 -- docker logs mcp-hydraulic --tail=20"

echo ""
echo "=================================================="
echo "Next Steps"
echo "=================================================="
echo ""
echo -e "${YELLOW}Services Deployed:${NC}"
echo "  ✓ mcp-google  - Port 3004"
echo "  ✓ mcp-hydraulic - Port 3012"
echo ""
echo -e "${YELLOW}To Deploy Additional Services:${NC}"
echo "  1. Fix iCloud credentials (see CREDENTIAL-STATUS.md)"
echo "  2. Verify Todoist token"
echo "  3. Verify Outlook credentials"
echo "  4. Deploy Integrator (after others work)"
echo ""
echo -e "${YELLOW}View Logs:${NC}"
echo "  ssh root@192.168.1.32 \"pct exec 200 -- docker logs mcp-google -f\""
echo "  ssh root@192.168.1.32 \"pct exec 200 -- docker logs mcp-hydraulic -f\""
echo ""
echo "Documentation:"
echo "  - CREDENTIAL-STATUS.md - Credential setup instructions"
echo "  - SESSION-SUMMARY.md - Technical details of all fixes"
echo ""
