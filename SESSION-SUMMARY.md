# MCP Services Debugging Session Summary

**Date:** 2025-11-10
**Session:** Continuation from previous deployment

---

## Issues Fixed

### 1. iCloud Service - FastMCP Version Parameter Error
**Problem:**
```python
TypeError: FastMCP.__init__() got an unexpected keyword argument 'version'
```

**Solution:**
- Removed `version="1.0.0"` parameter from `FastMCP("icloud")` initialization (line 39)
- Removed reference to `mcp.version` in startup message (line 719)

**Status:** ✅ FIXED - Service now starts (but has credential issues - see below)

---

### 2. Google Service - Async Server Startup Error
**Problem:**
- Used incorrect pattern: `asyncio.run(stdio_server(app))`
- Should use async context manager pattern

**Solution:**
Changed from:
```python
def main():
    asyncio.run(stdio_server(app))
```

To:
```python
async def main():
    async with stdio_server() as (read_stream, write_stream):
        await app.run(read_stream, write_stream, app.create_initialization_options())

asyncio.run(main())
```

**Additional Fixes:**
- Removed problematic OAuth scope: `https://www.googleapis.com/auth/photoslibrary.readonly`
- Changed Google credentials volume mount from read-only (`:ro`) to read-write

**Status:** ✅ FIXED - Code corrected

---

### 3. Todoist Service - Async Server Startup Error
**Problem:**
- Same async pattern issue as Google

**Solution:**
- Applied same async context manager fix as Google service

**Status:** ✅ FIXED - Code corrected

---

## Remaining Issues

### 1. Stdio-Based Server Architecture
**Problem:**
All MCP servers (except those specifically needing HTTP) are designed to communicate via stdio (standard input/output). In Docker containers without persistent stdin, they:
1. Start up successfully
2. Initialize their connections/services
3. Wait for stdin input
4. Exit immediately when stdin pipe closes

**Affected Services:**
- Google
- Todoist
- Outlook
- Integrator
- Hydraulic (but seems more stable)

**Why This Happens:**
MCP (Model Context Protocol) servers are designed to be connected to by clients (like Claude) via stdio pipes. They're not meant to run as standalone HTTP servers.

**Evidence:**
- All services show proper initialization logs
- They log "Starting..." messages
- No error messages on exit (exit code 0)
- Docker shows them repeatedly restarting

**Potential Solutions:**
1. **Convert to HTTP servers:** Modify each service to listen on HTTP instead of stdio
2. **Keep stdin open:** Implement a dummy stdin keeper process
3. **Accept current behavior:** These services are meant to be used via Claude/client connection, not as standalone services
4. **Use MCP_TRANSPORT=http:** Check if the MCP libraries support HTTP transport natively

---

### 2. Credential Issues

#### iCloud Service
**Error:** `Invalid email/password combination`
**Cause:** Using regular iCloud password instead of app-specific password
**Fix Needed:**
- Generate app-specific password at: https://appleid.apple.com/account/manage
- Update `ICLOUD_PASSWORD` in `/opt/MCP_CREATOR/deployment/.env`

#### Google Service
**Error:** `Read-only file system: '/app/credentials/token.json'` (FIXED)
**Status:** Volume mount changed from read-only to read-write
**Additional Requirements:**
- Valid OAuth credentials in `/opt/MCP_CREATOR/deployment/credentials/google/`
- May need to re-authenticate after scope changes

---

## Files Modified

### On Dev Machine
1. `/root/OBSIDIAN/MCP_CREATOR/mcp/icloud/server.py`
   - Removed version parameter
   - Fixed version reference in startup message

2. `/root/OBSIDIAN/MCP_CREATOR/mcp/google/server.py`
   - Fixed async server startup pattern
   - Removed problematic OAuth scope

3. `/root/OBSIDIAN/MCP_CREATOR/mcp/todoist/server.py`
   - Fixed async server startup pattern

4. `/root/OBSIDIAN/MCP_CREATOR/deployment/docker-compose.autosapien.yml`
   - Changed Google credentials mount from `:ro` to read-write

### On Container 200
- All above files synchronized via tar transfer

---

## Current Service Status

| Service | Container Status | Issue | Fix Priority |
|---------|-----------------|-------|--------------|
| **mcp-google** | Restarting | Stdio architecture + credentials | High |
| **mcp-icloud** | Restarting | Invalid credentials | High |
| **mcp-todoist** | Restarting | Stdio architecture | Medium |
| **mcp-outlook** | Restarting | Stdio architecture | Medium |
| **mcp-integrator** | Restarting | Stdio architecture | Low |
| **mcp-hydraulic** | Up (intermittent) | Stdio architecture | Low |

---

## Next Steps

### Immediate (High Priority)

1. **Fix iCloud Credentials**
   ```bash
   # On container 200
   nano /opt/MCP_CREATOR/deployment/.env
   # Update ICLOUD_PASSWORD with app-specific password
   docker compose -f /opt/MCP_CREATOR/deployment/docker-compose.autosapien.yml restart mcp-icloud
   ```

2. **Fix Google Credentials**
   ```bash
   # Ensure valid OAuth credentials exist
   ls -la /opt/MCP_CREATOR/deployment/credentials/google/
   # Should contain: credentials.json and token.json
   ```

3. **Investigate MCP HTTP Transport**
   - Check if `MCP_TRANSPORT=http` environment variable is actually used
   - Review mcp.server library documentation for HTTP support
   - May need to use different MCP library or write HTTP wrapper

### Medium Priority

4. **Convert Services to HTTP (if needed)**
   - Research if MCP protocol supports HTTP natively
   - If not, create HTTP wrapper for stdio-based servers
   - Update each service to expose HTTP endpoints

5. **Test Service Connectivity**
   - Once services are stable, test with curl:
     ```bash
     curl http://localhost:3004/health  # Google
     curl http://localhost:3005/health  # Todoist
     curl http://localhost:3009/health  # iCloud
     ```

### Low Priority

6. **Configure Cloudflare Tunnel**
   - Only after services are stable
   - Add routes for each service
   - Test external connectivity

7. **Documentation**
   - Update DEPLOYMENT-READY.md
   - Create troubleshooting guide
   - Document credential setup process

---

## Key Learnings

1. **FastMCP API Changed:** The `version` parameter is no longer supported in FastMCP initialization

2. **Async Context Managers:** MCP stdio servers must use `async with stdio_server()` pattern, not `asyncio.run(stdio_server(app))`

3. **Docker Stdio Limitation:** Stdio-based servers don't work well in Docker without persistent stdin connections

4. **Credential Mount Permissions:** OAuth services need read-write access to write token files

5. **OAuth Scope Validation:** Google OAuth scopes must be validated; some legacy scopes cause errors

---

## Commands Used

### File Transfer to Container
```bash
# Create tarball
tar -czf /tmp/mcp-fixes.tar.gz mcp/icloud/server.py mcp/google/server.py mcp/todoist/server.py

# Transfer to Proxmox
scp /tmp/mcp-fixes.tar.gz root@192.168.1.32:/tmp/

# Push to container
ssh root@192.168.1.32 "pct push 200 /tmp/mcp-fixes.tar.gz /tmp/"

# Extract in container
ssh root@192.168.1.32 "pct exec 200 -- bash -c 'cd /opt/MCP_CREATOR && tar -xzf /tmp/mcp-fixes.tar.gz'"
```

### Rebuild Services
```bash
# Rebuild specific services
ssh root@192.168.1.32 "pct exec 200 -- bash -c 'cd /opt/MCP_CREATOR/deployment && docker compose -f docker-compose.autosapien.yml up -d --build mcp-icloud mcp-google mcp-todoist'"

# Check status
ssh root@192.168.1.32 "pct exec 200 -- bash -c 'docker ps --filter \"name=mcp-\"'"

# View logs
ssh root@192.168.1.32 "pct exec 200 -- bash -c 'cd /opt/MCP_CREATOR/deployment && docker compose -f docker-compose.autosapien.yml logs --tail=50 mcp-google'"
```

---

## Architecture Decision Needed

**Question:** Should MCP services run as:
- **Option A:** Stdio-based servers (current design) - requires client connection
- **Option B:** HTTP-based servers - can run standalone in Docker
- **Option C:** Hybrid - stdio for Claude, HTTP for Docker/testing

**Recommendation:**
Investigate if MCP library supports HTTP transport via `MCP_TRANSPORT=http` environment variable. If not, consider writing a thin HTTP wrapper that translates HTTP requests to stdio communication with the MCP server.

---

## Session Statistics

- **Duration:** ~1 hour
- **Services Fixed:** 3 (iCloud, Google, Todoist)
- **Code Changes:** 4 files modified
- **Docker Rebuilds:** 4
- **Status:** Partially Complete - Code fixed, architecture issue identified
