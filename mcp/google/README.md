# Google Services MCP Server

Provides MCP access to Gmail, Google Drive, Google Calendar, and Google Photos from any device.

## Features

### Gmail
- 📧 Search emails with advanced queries
- 📤 Send emails
- 📨 Read inbox messages

### Google Drive
- 📁 List and search files
- 📄 Read file content (text files)
- 🔍 Advanced Drive queries

### Google Calendar
- 📅 List upcoming events
- ➕ Create new events
- 🔍 Search calendar

### Google Photos
- 📷 List photo albums
- 🔍 Search photos
- 🖼️ View photo details and metadata

## Prerequisites

1. Google Cloud Project with APIs enabled
2. OAuth 2.0 credentials
3. Python 3.11+

## Setup Instructions

### Step 1: Create Google Cloud Project

1. Go to [Google Cloud Console](https://console.cloud.google.com/)
2. Create a new project (or select existing)
3. Enable APIs:
   - Gmail API
   - Google Drive API
   - Google Calendar API
   - Google Photos Library API

### Step 2: Create OAuth Credentials

1. Go to **APIs & Services** → **Credentials**
2. Click **Create Credentials** → **OAuth client ID**
3. Application type: **Desktop app**
4. Download the credentials JSON file
5. Save it as `credentials.json` in this directory

### Step 3: Install Dependencies

```bash
# Install Python dependencies
pip install -r requirements.txt
```

### Step 4: First-Time Authentication

```bash
# Run the server once to authenticate
python server.py
```

This will:
1. Open your browser for Google OAuth
2. Ask you to grant permissions
3. Save the token to `token.json`

### Step 5: Test Locally

Once authenticated, test the tools:

```bash
# The server will run in stdio mode
python server.py
```

## Docker Deployment

For deployment in your Proxmox LXC:

### Build Image

```bash
docker build -t mcp-google:latest .
```

### Run Container

```bash
docker run -d \
  --name mcp-google \
  -v $(pwd)/credentials:/app/credentials:ro \
  -p 3004:3000 \
  mcp-google:latest
```

**Important**: Mount your credentials directory with the authenticated `token.json` and `credentials.json` files.

## Credentials Setup

### For Proxmox LXC Deployment

1. **On your local machine**, run the server once to authenticate:
   ```bash
   python server.py
   ```

2. This creates `token.json` (your authenticated session)

3. **Copy both files to your Proxmox LXC**:
   ```bash
   # Create credentials directory on LXC
   mkdir -p /opt/mcp-servers/google/credentials

   # Copy files (adjust paths)
   scp credentials.json token.json root@proxmox-lxc:/opt/mcp-servers/google/credentials/
   ```

4. Run Docker container with volume mount to credentials

### Security Notes

- `credentials.json` = OAuth client configuration (semi-sensitive)
- `token.json` = Your authenticated session (VERY sensitive!)
- **Never commit these files to Git!**
- Set proper file permissions: `chmod 600 token.json`

## Available Tools

### Gmail Tools

| Tool | Description | Parameters |
|------|-------------|------------|
| `gmail_search` | Search emails | `query`, `max_results` |
| `gmail_send` | Send email | `to`, `subject`, `body` |

**Example queries**:
- `from:someone@email.com`
- `subject:important`
- `is:unread`
- `after:2025/11/01`

### Google Drive Tools

| Tool | Description | Parameters |
|------|-------------|------------|
| `drive_list_files` | List files | `query`, `max_results` |
| `drive_search_files` | Search by name | `name` |
| `drive_get_file` | Get file content | `file_id` |

**Example Drive queries**:
- `name contains 'report'`
- `mimeType='application/pdf'`
- `modifiedTime > '2025-11-01T00:00:00'`

### Google Calendar Tools

| Tool | Description | Parameters |
|------|-------------|------------|
| `calendar_list_events` | List events | `max_results`, `days_ahead` |
| `calendar_create_event` | Create event | `summary`, `start_time`, `end_time`, `description`, `location` |

**Date format**: ISO 8601 - `2025-11-09T10:00:00Z`

### Google Photos Tools

| Tool | Description | Parameters |
|------|-------------|------------|
| `photos_list_albums` | List photo albums | `max_results` |
| `photos_search` | Search photos | `album_id` (optional), `max_results` |
| `photos_get_media` | Get photo/video details | `media_id` |

**Note**: Returns photo URLs that are valid for 60 minutes. Use `baseUrl` for viewing photos.

## Resources

| URI | Description |
|-----|-------------|
| `gmail://inbox` | Recent inbox messages |
| `drive://files` | Recent Drive files |
| `calendar://events` | Upcoming calendar events |
| `photos://albums` | Photo albums |
| `photos://recent` | Recently added photos |

## Usage Examples

### From Claude Desktop

```json
{
  "mcpServers": {
    "google": {
      "command": "python",
      "args": ["/path/to/mcp/google/server.py"]
    }
  }
}
```

### From Claude Code/iPhone (Remote)

After deploying to your Proxmox LXC with Cloudflare Tunnel:

```json
{
  "mcpServers": {
    "google": {
      "url": "https://google-mcp.yourdomain.com",
      "transport": "http"
    }
  }
}
```

## Troubleshooting

### "Credentials file not found"
- Download `credentials.json` from Google Cloud Console
- Place it in the same directory as `server.py`

### "Token expired" or authentication errors
- Delete `token.json`
- Run `python server.py` to re-authenticate

### "API not enabled" errors
- Go to Google Cloud Console
- Enable Gmail API, Drive API, and Calendar API

### Docker container can't authenticate
- You must authenticate locally first to create `token.json`
- Then mount it into the container via volume

## Scopes Used

The server requests these OAuth scopes:

```
gmail.readonly     - Read emails
gmail.send         - Send emails
gmail.modify       - Modify emails (labels, etc.)
drive.readonly     - Read Drive files
drive.file         - Manage Drive files
calendar.readonly  - Read calendar
calendar.events    - Manage calendar events
```

## Rate Limits

Google APIs have rate limits:
- Gmail: 250 quota units/user/second
- Drive: 12,000 queries/minute
- Calendar: 1,000,000 queries/day

The server doesn't implement rate limiting - use responsibly!

## Next Steps

1. ✅ Authenticate locally
2. ✅ Test tools
3. ✅ Copy credentials to Proxmox LXC
4. ✅ Deploy via Docker
5. ✅ Configure Cloudflare Tunnel
6. ✅ Add to Claude apps

---

**Security Reminder**: This server has full access to your Gmail, Drive, and Calendar. Only expose it via Cloudflare Zero Trust with authentication enabled!
