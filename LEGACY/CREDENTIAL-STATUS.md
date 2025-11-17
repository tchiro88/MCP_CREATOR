# MCP Services Credential Status & Deployment Plan

**Date:** 2025-11-10

---

## Credential Status by Service

### ✅ Google (mcp-google) - READY
**Status:** Credentials exist and tested
**Location:**
- Dev: `/root/OBSIDIAN/MCP_CREATOR/mcp/google/`
- Container 200: `/opt/MCP_CREATOR/deployment/credentials/google/`

**Files:**
- ✓ credentials.json (409 bytes)
- ✓ token.json (1029 bytes)

**Action Required:** Deploy and test

---

### ✅ Hydraulic (mcp-hydraulic) - READY
**Status:** No credentials needed (uses OpenAI API key only)
**Environment Variables:**
- `OPENAI_API_KEY` (set in .env)

**Action Required:** Deploy and test

---

### ⚠️ Todoist (mcp-todoist) - CHECK NEEDED
**Status:** Has API token but needs verification
**Environment Variables:**
- `TODOIST_API_TOKEN` (set in .env)

**To Verify:**
```bash
# On container 200
cat /opt/MCP_CREATOR/deployment/.env | grep TODOIST_API_TOKEN
# Should show: TODOIST_API_TOKEN=<your-token>
```

**Get Token:** https://todoist.com/prefs/integrations

**Action Required:** Verify token is valid

---

### ❌ iCloud (mcp-icloud) - NEEDS FIX
**Status:** Invalid credentials
**Error:** `Invalid email/password combination`

**Problem:** Using regular password instead of app-specific password

**Fix Required:**
1. Go to: https://appleid.apple.com/account/manage
2. Navigate to: Security → App-Specific Passwords
3. Generate new password labeled "MCP Server"
4. Update .env file

**Environment Variables Needed:**
- `ICLOUD_USERNAME=tchi_ro@me.com` (already set)
- `ICLOUD_PASSWORD=<app-specific-password>` (needs update)

**Action Required:** Generate app-specific password and update .env

---

### ⚠️ Outlook (mcp-outlook) - CHECK NEEDED
**Status:** Has credentials but needs verification
**Environment Variables:**
- `OUTLOOK_EMAIL` (set in .env)
- `OUTLOOK_PASSWORD` (set in .env)

**To Verify:**
```bash
# On container 200
cat /opt/MCP_CREATOR/deployment/.env | grep OUTLOOK
```

**Note:** May need app-specific password if 2FA enabled

**Action Required:** Verify credentials

---

### ⚠️ Integrator (mcp-integrator) - DEPENDS ON OTHERS
**Status:** No credentials needed (connects to other services)
**Dependencies:** Requires other MCP services to be running

**Action Required:** Deploy after other services are working

---

## Deployment Strategy

### Phase 1: Deploy Working Services (NOW)

Deploy only services with confirmed working credentials:

**Services to Deploy:**
1. ✅ mcp-google (credentials confirmed)
2. ✅ mcp-hydraulic (no credentials needed)

**Command:**
```bash
# Stop all services
ssh root@192.168.1.32 "pct exec 200 -- bash -c 'cd /opt/MCP_CREATOR/deployment && docker compose -f docker-compose.autosapien.yml down'"

# Start only working services
ssh root@192.168.1.32 "pct exec 200 -- bash -c 'cd /opt/MCP_CREATOR/deployment && docker compose -f docker-compose.autosapien.yml up -d mcp-google mcp-hydraulic'"

# Check status
ssh root@192.168.1.32 "pct exec 200 -- docker ps --filter 'name=mcp-'"

# View logs
ssh root@192.168.1.32 "pct exec 200 -- docker logs mcp-google -f"
```

---

### Phase 2: Fix & Add Remaining Services

#### 2A. Fix iCloud Credentials

```bash
# On container 200
pct exec 200 -- bash

# Edit .env
nano /opt/MCP_CREATOR/deployment/.env

# Find and update this line:
ICLOUD_PASSWORD=<your-current-password>

# Replace with app-specific password from:
# https://appleid.apple.com/account/manage → Security → App-Specific Passwords

# Save and exit (Ctrl+X, Y, Enter)

# Restart service
cd /opt/MCP_CREATOR/deployment
docker compose -f docker-compose.autosapien.yml up -d mcp-icloud

# Check logs
docker logs mcp-icloud -f
```

#### 2B. Verify Todoist Token

```bash
# On container 200
pct exec 200 -- bash

# Check current token
cat /opt/MCP_CREATOR/deployment/.env | grep TODOIST_API_TOKEN

# If token is missing or invalid, get new one from:
# https://todoist.com/prefs/integrations

# Update .env
nano /opt/MCP_CREATOR/deployment/.env
# Update: TODOIST_API_TOKEN=<your-token>

# Restart service
cd /opt/MCP_CREATOR/deployment
docker compose -f docker-compose.autosapien.yml up -d mcp-todoist

# Check logs
docker logs mcp-todoist -f
```

#### 2C. Verify Outlook Credentials

```bash
# On container 200
pct exec 200 -- bash

# Check credentials
cat /opt/MCP_CREATOR/deployment/.env | grep OUTLOOK

# If using Microsoft account with 2FA, you may need app password:
# https://account.microsoft.com/security → App passwords

# Update if needed
nano /opt/MCP_CREATOR/deployment/.env

# Restart service
cd /opt/MCP_CREATOR/deployment
docker compose -f docker-compose.autosapien.yml up -d mcp-outlook

# Check logs
docker logs mcp-outlook -f
```

#### 2D. Deploy Integrator (Last)

```bash
# Only after other services are working
ssh root@192.168.1.32 "pct exec 200 -- bash -c 'cd /opt/MCP_CREATOR/deployment && docker compose -f docker-compose.autosapien.yml up -d mcp-integrator'"
```

---

## Quick Reference Commands

### Check All Credentials
```bash
ssh root@192.168.1.32 "pct exec 200 -- bash -c 'cat /opt/MCP_CREATOR/deployment/.env | grep -E \"(ICLOUD|OUTLOOK|TODOIST|OPENAI)\"'"
```

### Check Service Status
```bash
ssh root@192.168.1.32 "pct exec 200 -- docker ps -a --filter 'name=mcp-' --format 'table {{.Names}}\t{{.Status}}'"
```

### View All Logs
```bash
ssh root@192.168.1.32 "pct exec 200 -- bash -c 'cd /opt/MCP_CREATOR/deployment && docker compose -f docker-compose.autosapien.yml logs --tail=50'"
```

### Restart All Services
```bash
ssh root@192.168.1.32 "pct exec 200 -- bash -c 'cd /opt/MCP_CREATOR/deployment && docker compose -f docker-compose.autosapien.yml restart'"
```

### Stop All Services
```bash
ssh root@192.168.1.32 "pct exec 200 -- bash -c 'cd /opt/MCP_CREATOR/deployment && docker compose -f docker-compose.autosapien.yml down'"
```

---

## Expected Behavior After Deployment

### Working Services (Phase 1)

**mcp-google:**
- Should show: "✓ Google authentication successful"
- Status: Up (may restart initially due to stdio architecture)
- Port: 3004

**mcp-hydraulic:**
- Should show: "Hydraulic Analysis MCP Server initialized"
- Status: Up
- Port: 3012

### After Credential Fixes (Phase 2)

**mcp-icloud:**
- Should show: "✓ Connected to iCloud as: tchi_ro@me.com"
- Status: Up (may restart due to stdio architecture)
- Port: 3009

**mcp-todoist:**
- Should show: "✓ Connected to Todoist (found X projects)"
- Status: Up (may restart due to stdio architecture)
- Port: 3005

**mcp-outlook:**
- Should show: "Starting Outlook MCP Server (Read-Only)"
- Status: Up (may restart due to stdio architecture)
- Port: 3010

**mcp-integrator:**
- Should show: "Starting MCP Integrator Server"
- Status: Up (may restart due to stdio architecture)
- Port: 3011

---

## Note on "Restarting" Status

**This is EXPECTED behavior** for stdio-based MCP servers in Docker. They:
1. Start successfully
2. Initialize connections
3. Wait for stdin (which closes immediately in Docker)
4. Exit gracefully
5. Docker restarts them (restart: unless-stopped)

**This is NOT an error** - these services are designed to be connected to by clients (like Claude) via stdio, not run standalone.

**To verify they're working:**
- Check logs show successful initialization
- No error messages
- Exit code 0 (clean exit)
- Services initialize their APIs/connections before exiting

---

## Troubleshooting

### If mcp-google fails with OAuth error:
```bash
# On container 200
rm /opt/MCP_CREATOR/deployment/credentials/google/token.json
# Re-authenticate will be required on next start
```

### If services show "no such file or directory":
```bash
# Verify credentials exist
ssh root@192.168.1.32 "pct exec 200 -- ls -la /opt/MCP_CREATOR/deployment/credentials/google/"
```

### If .env changes don't take effect:
```bash
# Must recreate containers after .env changes
ssh root@192.168.1.32 "pct exec 200 -- bash -c 'cd /opt/MCP_CREATOR/deployment && docker compose -f docker-compose.autosapien.yml up -d --force-recreate'"
```

---

## Summary

**Ready to Deploy:**
- ✅ Google (credentials confirmed)
- ✅ Hydraulic (no credentials needed)

**Need Credential Fixes:**
- ❌ iCloud (app-specific password required)
- ⚠️ Todoist (verify token)
- ⚠️ Outlook (verify credentials)

**Deploy Last:**
- ⚠️ Integrator (depends on other services)

**Next Action:** Run Phase 1 deployment commands above
