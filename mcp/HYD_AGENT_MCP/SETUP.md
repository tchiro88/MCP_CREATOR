# Hydraulic Analysis MCP Server - Detailed Setup Guide

This guide walks you through setting up the Hydraulic Analysis MCP Server from scratch, including Docker deployment and integration with Claude Desktop and Cursor.

## Table of Contents

1. [Prerequisites](#prerequisites)
2. [Initial Setup](#initial-setup)
3. [Docker Deployment](#docker-deployment)
4. [Claude Desktop Integration](#claude-desktop-integration)
5. [Cursor Integration](#cursor-integration)
6. [Cloudflare Worker Deployment](#cloudflare-worker-deployment)
7. [Troubleshooting](#troubleshooting)

## Prerequisites

### Required

- **Docker** (version 20.0+) and **Docker Compose**
  - Install from: https://docs.docker.com/get-docker/
  - Verify: `docker --version` and `docker-compose --version`

- **API Key** - ONE of:
  - OpenAI API key (https://platform.openai.com/api-keys)
  - OpenRouter API key (https://openrouter.ai/keys)

- **MCP Client** - ONE of:
  - Claude Desktop (https://claude.ai/download)
  - Cursor IDE (https://cursor.sh/)
  - Any MCP-compatible AI client

### Optional

- Python 3.11+ (for local development without Docker)
- PostgreSQL 15+ (for production database)
- Git (for version control)

## Initial Setup

### Step 1: Navigate to Directory

```bash
cd /path/to/HYD_AGENT_MCP
```

Or if starting fresh:

```bash
mkdir HYD_AGENT_MCP
cd HYD_AGENT_MCP
# Copy all files from the repository
```

### Step 2: Configure Environment

Create your environment file:

```bash
cp .env.example .env
```

Edit `.env` with your settings:

```bash
# Linux/macOS
nano .env

# Windows
notepad .env
```

**Minimal configuration:**

```bash
# Add your API key (choose one)
OPENAI_API_KEY=sk-your-key-here
# OR
OPENROUTER_API_KEY=your-key-here

# Use SQLite (default)
DB_TYPE=sqlite
```

**Advanced configuration:**

```bash
# Use OpenRouter with specific model
OPENROUTER_API_KEY=your-key-here

# PostgreSQL database
DB_TYPE=postgresql
POSTGRES_HOST=localhost
POSTGRES_PORT=5432
POSTGRES_DB=hydraulic_analysis
POSTGRES_USER=postgres
POSTGRES_PASSWORD=your-secure-password

# Folder watching
WATCH_SCHEMATICS=true
WATCH_INTERVAL=5
```

### Step 3: Verify Directory Structure

Ensure these directories exist:

```bash
ls -la
```

You should see:

```
HYD_AGENT_MCP/
├── schematics/              # For schematic files
├── manufacturer_docs/       # For PDF manuals
├── machines/                # For organized machine data
├── database/                # For SQLite database
├── config.py
├── database_interface.py
├── schematic_parser.py
├── flow_analyzer.py
├── doc_manager.py
├── server.py
├── requirements.txt
├── Dockerfile
├── docker-compose.yml
├── .env
└── README.md
```

If directories are missing:

```bash
mkdir -p schematics manufacturer_docs machines database
```

## Docker Deployment

### Step 1: Build Docker Image

```bash
docker-compose build
```

Expected output:
```
Building hydraulic-mcp-server
Step 1/10 : FROM python:3.11-slim
...
Successfully built abc123def456
Successfully tagged hyd_agent_mcp_hydraulic-mcp-server:latest
```

### Step 2: Test the Server

```bash
docker-compose run --rm hydraulic-mcp-server python server.py
```

Expected output:
```
INFO - Hydraulic Analysis MCP Server initialized
INFO - Starting Hydraulic Analysis MCP Server
INFO - Schematics directory: /app/schematics
INFO - Manufacturer docs directory: /app/manufacturer_docs
INFO - Database: /app/database/hydraulic_analysis.db
```

Press `Ctrl+C` to stop.

### Step 3: Run as Background Service (Optional)

To run the server continuously:

```bash
docker-compose up -d
```

Check status:

```bash
docker-compose ps
```

View logs:

```bash
docker-compose logs -f
```

Stop service:

```bash
docker-compose down
```

## Claude Desktop Integration

### Step 1: Locate Config File

**macOS:**
```bash
~/Library/Application Support/Claude/claude_desktop_config.json
```

**Windows:**
```
%APPDATA%\Claude\claude_desktop_config.json
```

**Linux:**
```bash
~/.config/Claude/claude_desktop_config.json
```

Create directory if it doesn't exist:

```bash
# macOS
mkdir -p ~/Library/Application\ Support/Claude

# Linux
mkdir -p ~/.config/Claude
```

### Step 2: Get Absolute Path

Get the absolute path to your HYD_AGENT_MCP directory:

```bash
# macOS/Linux
cd /path/to/HYD_AGENT_MCP
pwd
```

Copy this path. Example: `/Users/yourname/projects/HYD_AGENT_MCP`

### Step 3: Configure Claude Desktop

Edit the config file:

```bash
# macOS
nano ~/Library/Application\ Support/Claude/claude_desktop_config.json

# Linux
nano ~/.config/Claude/claude_desktop_config.json

# Windows - use Notepad
```

Add this configuration (replace `/absolute/path/to/HYD_AGENT_MCP` with your actual path):

```json
{
  "mcpServers": {
    "hydraulic-analysis": {
      "command": "docker",
      "args": [
        "run",
        "-i",
        "--rm",
        "-v", "/absolute/path/to/HYD_AGENT_MCP/schematics:/app/schematics",
        "-v", "/absolute/path/to/HYD_AGENT_MCP/manufacturer_docs:/app/manufacturer_docs",
        "-v", "/absolute/path/to/HYD_AGENT_MCP/machines:/app/machines",
        "-v", "/absolute/path/to/HYD_AGENT_MCP/database:/app/database",
        "-e", "OPENAI_API_KEY=your-api-key-here",
        "hydraulic-mcp-server"
      ]
    }
  }
}
```

**IMPORTANT**:
- Replace ALL instances of `/absolute/path/to/HYD_AGENT_MCP`
- Replace `your-api-key-here` with your actual API key
- Use forward slashes `/` even on Windows in Docker paths

### Step 4: Restart Claude Desktop

Completely quit and restart Claude Desktop.

### Step 5: Verify Integration

In Claude Desktop, start a new conversation and type:

```
List available schematics
```

If configured correctly, you should see a response about available schematics (or a message saying none have been analyzed yet).

## Cursor Integration

### Step 1: Open Cursor Settings

1. Open Cursor IDE
2. Go to Settings (Cmd+, on Mac, Ctrl+, on Windows/Linux)
3. Search for "MCP" in settings

### Step 2: Add MCP Server Configuration

Add the following to your Cursor MCP settings:

```json
{
  "mcp": {
    "servers": {
      "hydraulic-analysis": {
        "command": "docker",
        "args": [
          "run",
          "-i",
          "--rm",
          "-v", "${workspaceFolder}/HYD_AGENT_MCP/schematics:/app/schematics",
          "-v", "${workspaceFolder}/HYD_AGENT_MCP/manufacturer_docs:/app/manufacturer_docs",
          "-v", "${workspaceFolder}/HYD_AGENT_MCP/machines:/app/machines",
          "-v", "${workspaceFolder}/HYD_AGENT_MCP/database:/app/database",
          "-e", "OPENAI_API_KEY=${env:OPENAI_API_KEY}",
          "hydraulic-mcp-server"
        ]
      }
    }
  }
}
```

**Note**: This assumes HYD_AGENT_MCP is in your workspace. Adjust paths if different.

### Step 3: Set Environment Variable

Add `OPENAI_API_KEY` to your system environment:

**macOS/Linux:**
```bash
# Add to ~/.bashrc or ~/.zshrc
export OPENAI_API_KEY=your-api-key-here
```

**Windows:**
```powershell
# PowerShell
[System.Environment]::SetEnvironmentVariable('OPENAI_API_KEY', 'your-api-key-here', 'User')
```

### Step 4: Restart Cursor

Restart Cursor for changes to take effect.

### Step 5: Test

Open a workspace containing HYD_AGENT_MCP and ask Cursor:

```
Use the hydraulic-analysis MCP server to list available schematics
```

## Cloudflare Worker Deployment

### Overview

For remote/cloud deployment, you can deploy the MCP server as a Cloudflare Worker for global access.

### Step 1: Install Wrangler

```bash
npm install -g wrangler
```

### Step 2: Login to Cloudflare

```bash
wrangler login
```

### Step 3: Create Worker Configuration

Create `wrangler.toml`:

```toml
name = "hydraulic-mcp-server"
type = "javascript"
account_id = "your-account-id"
workers_dev = true

[env.production]
route = "https://hydraulic-mcp.your-domain.com/*"

[vars]
DB_TYPE = "sqlite"
```

### Step 4: Deploy

```bash
wrangler publish
```

### Step 5: Configure Secrets

```bash
wrangler secret put OPENAI_API_KEY
# Enter your API key when prompted
```

### Step 6: Test Deployment

```bash
curl https://hydraulic-mcp.your-domain.com/health
```

Expected response:
```json
{"status": "ok", "service": "hydraulic-mcp-server"}
```

## Troubleshooting

### Issue: "ERROR: No API key configured"

**Solution:**
1. Check `.env` file contains `OPENAI_API_KEY` or `OPENROUTER_API_KEY`
2. Ensure no extra spaces or quotes
3. Rebuild Docker image: `docker-compose build`

### Issue: "Cannot connect to MCP server"

**Solutions:**
1. Verify Docker is running: `docker ps`
2. Check container logs: `docker-compose logs`
3. Ensure paths in config are absolute, not relative
4. Restart MCP client (Claude Desktop/Cursor)

### Issue: "Permission denied" on directories

**Solution:**
```bash
# Fix permissions
chmod -R 755 schematics manufacturer_docs machines database
```

### Issue: "Database is locked"

**Solutions:**
1. Stop all containers: `docker-compose down`
2. Remove database lock: `rm database/*.db-shm database/*.db-wal`
3. Restart: `docker-compose up`

### Issue: "Image parsing failed"

**Solutions:**
1. Ensure image is high-resolution (min 1920x1080)
2. Check file format (PNG/JPG supported)
3. Verify image contains labeled components
4. Try enhancing image contrast before upload

### Issue: Claude Desktop doesn't show MCP tools

**Solutions:**
1. Verify config file path is correct
2. Check JSON syntax (use JSONLint.com)
3. Ensure absolute paths in config
4. Completely restart Claude Desktop (Quit, not just close window)
5. Check Claude Desktop logs:
   - macOS: `~/Library/Logs/Claude/`
   - Windows: `%APPDATA%\Claude\Logs\`

### Issue: Docker build fails

**Solutions:**
1. Update Docker: `docker version`
2. Clear Docker cache: `docker system prune -a`
3. Check internet connection
4. Retry build: `docker-compose build --no-cache`

## Performance Optimization

### For Large Schematics

Increase Docker memory:

```yaml
# In docker-compose.yml, add:
services:
  hydraulic-mcp-server:
    deploy:
      resources:
        limits:
          memory: 4G
```

### For Multiple Users

Use PostgreSQL instead of SQLite:

```bash
# In .env
DB_TYPE=postgresql
POSTGRES_HOST=your-db-host
# ... other PostgreSQL settings
```

### For Faster Analysis

Cache analysis results - already implemented in database.

## Security Best Practices

1. **Never commit `.env` file**
   ```bash
   # Verify .gitignore includes .env
   cat .gitignore | grep .env
   ```

2. **Use environment-specific API keys**
   - Development: Lower-tier API key
   - Production: Higher-tier with rate limits

3. **Restrict file access**
   ```bash
   chmod 600 .env
   ```

4. **Regular updates**
   ```bash
   docker-compose pull
   docker-compose build
   ```

## Next Steps

After successful setup:

1. Read [USAGE.md](USAGE.md) for usage examples
2. Drop test schematic into `schematics/`
3. Add manufacturer PDFs to `manufacturer_docs/`
4. Start analyzing!

## Getting Help

If you encounter issues not covered here:

1. Check container logs: `docker-compose logs -f`
2. Verify configuration: `cat .env` (hide API key)
3. Test connection: `docker-compose run --rm hydraulic-mcp-server python -c "from config import config; print(config.validate())"`

## Maintenance

### Backup Database

```bash
# SQLite
cp database/hydraulic_analysis.db database/hydraulic_analysis.db.backup

# PostgreSQL
pg_dump hydraulic_analysis > backup.sql
```

### Update Server

```bash
git pull  # If using git
docker-compose build
docker-compose up -d
```

### Clean Old Data

```bash
# Clean old analysis cache (optional)
sqlite3 database/hydraulic_analysis.db "DELETE FROM analysis_cache WHERE expires_at < datetime('now')"
```
