#!/bin/bash
# Pre-Deployment Verification Script for Autosapien.ai MCP Infrastructure
# Run this script BEFORE starting deployment to catch issues early

set -e

echo "=========================================="
echo "MCP Infrastructure Pre-Deployment Check"
echo "=========================================="
echo ""

ERRORS=0
WARNINGS=0

# Color codes
RED='\033[0;31m'
YELLOW='\033[1;33m'
GREEN='\033[0;32m'
NC='\033[0m' # No Color

# Function to print status
check_pass() {
    echo -e "${GREEN}✓${NC} $1"
}

check_fail() {
    echo -e "${RED}✗${NC} $1"
    ((ERRORS++))
}

check_warn() {
    echo -e "${YELLOW}⚠${NC} $1"
    ((WARNINGS++))
}

echo "1. Checking required files..."
echo "------------------------------"

# Check .env file
if [ -f ".env" ]; then
    check_pass ".env file exists"

    # Check if file has content
    if [ -s ".env" ]; then
        check_pass ".env file has content"
    else
        check_fail ".env file is empty"
    fi

    # Check permissions
    PERM=$(stat -c %a .env 2>/dev/null || stat -f %A .env 2>/dev/null)
    if [ "$PERM" = "600" ]; then
        check_pass ".env file has secure permissions (600)"
    else
        check_warn ".env file permissions are $PERM (should be 600)"
    fi
else
    check_fail ".env file not found"
fi

# Check Google credentials
if [ -f "credentials/google/credentials.json" ]; then
    check_pass "Google credentials.json exists"

    # Validate JSON format
    if python3 -m json.tool credentials/google/credentials.json > /dev/null 2>&1; then
        check_pass "credentials.json is valid JSON"
    else
        check_fail "credentials.json is NOT valid JSON"
    fi
else
    check_fail "Google credentials.json not found"
fi

if [ -f "credentials/google/token.json" ]; then
    check_pass "Google token.json exists"

    # Validate JSON format
    if python3 -m json.tool credentials/google/token.json > /dev/null 2>&1; then
        check_pass "token.json is valid JSON"
    else
        check_fail "token.json is NOT valid JSON"
    fi
else
    check_fail "Google token.json not found"
fi

# Check docker-compose file
if [ -f "docker-compose.autosapien.yml" ]; then
    check_pass "docker-compose.autosapien.yml exists"
else
    check_fail "docker-compose.autosapien.yml not found"
fi

echo ""
echo "2. Checking required environment variables..."
echo "----------------------------------------------"

if [ -f ".env" ]; then
    # Check for required variables
    REQUIRED_VARS=(
        "ICLOUD_USERNAME"
        "ICLOUD_PASSWORD"
        "OUTLOOK_EMAIL"
        "OUTLOOK_PASSWORD"
        "TODOIST_API_TOKEN"
        "HA_URL"
        "HA_TOKEN"
        "OPENAI_API_KEY"
    )

    for var in "${REQUIRED_VARS[@]}"; do
        if grep -q "^${var}=" .env; then
            VALUE=$(grep "^${var}=" .env | cut -d'=' -f2-)
            if [ -n "$VALUE" ]; then
                check_pass "$var is set"
            else
                check_fail "$var is empty"
            fi
        else
            check_fail "$var is missing"
        fi
    done

    # Check if Cloudflare token is set (warning only)
    if grep -q "^CLOUDFLARE_TUNNEL_TOKEN=" .env; then
        VALUE=$(grep "^CLOUDFLARE_TUNNEL_TOKEN=" .env | cut -d'=' -f2-)
        if [ -n "$VALUE" ]; then
            check_pass "CLOUDFLARE_TUNNEL_TOKEN is set"
        else
            check_warn "CLOUDFLARE_TUNNEL_TOKEN is empty (will be set during deployment)"
        fi
    fi
fi

echo ""
echo "3. Checking MCP service directories..."
echo "---------------------------------------"

MCP_SERVICES=(
    "../mcp/google"
    "../mcp/icloud"
    "../mcp/outlook"
    "../mcp/todoist"
    "../mcp/homeassistant"
    "../mcp/integrator"
    "../mcp/HYD_AGENT_MCP"
)

for service in "${MCP_SERVICES[@]}"; do
    SERVICE_NAME=$(basename "$service")

    if [ -d "$service" ]; then
        check_pass "$SERVICE_NAME directory exists"

        # Check for Dockerfile
        if [ -f "$service/Dockerfile" ]; then
            check_pass "$SERVICE_NAME has Dockerfile"
        else
            check_fail "$SERVICE_NAME missing Dockerfile"
        fi

        # Check for dependency files
        if [ -f "$service/requirements.txt" ] || [ -f "$service/package.json" ]; then
            check_pass "$SERVICE_NAME has dependency file"
        else
            check_fail "$SERVICE_NAME missing requirements.txt or package.json"
        fi
    else
        check_fail "$SERVICE_NAME directory not found"
    fi
done

echo ""
echo "4. Checking Hydraulic service data directories..."
echo "--------------------------------------------------"

HYD_DIRS=(
    "../mcp/HYD_AGENT_MCP/database"
    "../mcp/HYD_AGENT_MCP/schematics"
    "../mcp/HYD_AGENT_MCP/manufacturer_docs"
    "../mcp/HYD_AGENT_MCP/machines"
)

for dir in "${HYD_DIRS[@]}"; do
    DIR_NAME=$(basename "$dir")
    if [ -d "$dir" ]; then
        check_pass "HYD_AGENT_MCP/$DIR_NAME directory exists"
    else
        check_fail "HYD_AGENT_MCP/$DIR_NAME directory missing"
    fi
done

echo ""
echo "5. Network connectivity checks..."
echo "----------------------------------"

# Check if we can resolve domain
if nslookup autosapien.ai > /dev/null 2>&1; then
    check_pass "Domain autosapien.ai resolves"
else
    check_warn "Cannot resolve autosapien.ai (expected if not yet configured)"
fi

# Check Home Assistant connectivity (if HA_URL is set)
if [ -f ".env" ]; then
    HA_URL=$(grep "^HA_URL=" .env | cut -d'=' -f2-)
    if [ -n "$HA_URL" ]; then
        echo "Testing Home Assistant connectivity to: $HA_URL"
        if curl -s -o /dev/null -w "%{http_code}" --max-time 5 "$HA_URL" > /dev/null 2>&1; then
            check_pass "Home Assistant is reachable"
        else
            check_warn "Cannot reach Home Assistant at $HA_URL (may need routing configuration)"
            echo "  Note: HA is on 192.168.15.x subnet, MCP will be on 192.168.1.x"
        fi
    fi
fi

echo ""
echo "=========================================="
echo "Pre-Deployment Check Summary"
echo "=========================================="

if [ $ERRORS -eq 0 ] && [ $WARNINGS -eq 0 ]; then
    echo -e "${GREEN}✓ All checks passed!${NC}"
    echo "You are ready to proceed with deployment."
    exit 0
elif [ $ERRORS -eq 0 ]; then
    echo -e "${YELLOW}⚠ $WARNINGS warning(s) found${NC}"
    echo "You can proceed but review warnings above."
    exit 0
else
    echo -e "${RED}✗ $ERRORS error(s) found${NC}"
    if [ $WARNINGS -gt 0 ]; then
        echo -e "${YELLOW}⚠ $WARNINGS warning(s) found${NC}"
    fi
    echo ""
    echo "Please fix the errors above before deploying."
    exit 1
fi
