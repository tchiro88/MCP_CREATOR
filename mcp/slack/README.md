# Slack MCP Server

Provides MCP access to your Slack workspace from any device.

## Features

### Channel Management
- 📋 List all channels (public, private, DMs)
- 📊 Get channel details and metadata
- 👥 View channel members and topics

### Messaging
- 💬 Send messages to channels
- 🧵 Reply to threads
- 📜 Read channel history
- 🔍 Get thread replies

### User Management
- 👤 List all workspace users
- 📇 Get user profiles and details
- 📧 Access user emails and contact info

### Search
- 🔎 Search messages across workspace
- 🎯 Filter by channel, user, date
- 📊 Sort by relevance or timestamp

### Files
- 📎 Upload files to channels
- 📁 List workspace files
- 🔗 Get file permalinks

### Reactions
- 😊 Add emoji reactions to messages
- ❤️ Full emoji support

## Prerequisites

1. Slack workspace (free or paid)
2. Slack bot token with appropriate scopes
3. Python 3.11+

## Setup Instructions

### Step 1: Create Slack App

1. **Go to Slack API**:
   - Visit: https://api.slack.com/apps
   - Click "**Create New App**"
   - Select "**From scratch**"

2. **Configure App**:
   - **App Name**: `MCP Server`
   - **Workspace**: Select your workspace
   - Click "**Create App**"

### Step 2: Configure Bot Token Scopes

1. **Navigate to OAuth & Permissions** (left sidebar)

2. **Scroll to "Bot Token Scopes"**

3. **Add the following scopes**:

   **Channels:**
   - `channels:history` - View messages in public channels
   - `channels:read` - View basic channel info
   - `channels:write` - Manage public channels

   **Groups (Private Channels):**
   - `groups:history` - View messages in private channels
   - `groups:read` - View basic private channel info
   - `groups:write` - Manage private channels

   **IM & MPIM:**
   - `im:history` - View direct message history
   - `im:read` - View basic DM info
   - `im:write` - Send direct messages
   - `mpim:history` - View group DM history
   - `mpim:read` - View group DM info
   - `mpim:write` - Send group messages

   **Chat:**
   - `chat:write` - Send messages as bot

   **Files:**
   - `files:read` - View files
   - `files:write` - Upload files

   **Reactions:**
   - `reactions:read` - View reactions
   - `reactions:write` - Add reactions

   **Search:**
   - `search:read` - Search workspace messages

   **Users:**
   - `users:read` - View user info
   - `users:read.email` - View user emails

### Step 3: Install App to Workspace

1. **Scroll to top of OAuth & Permissions page**
2. Click "**Install to Workspace**"
3. Review permissions and click "**Allow**"

### Step 4: Copy Bot Token

After installation, you'll see:
- **Bot User OAuth Token**: `xoxb-xxxxxxxxxxxx-xxxxxxxxxxxx-xxxxxxxxxxxxxxxxxxxxxxxx`

**Copy this token** - you'll need it for the MCP server.

### Step 5: Set Environment Variable

```bash
export SLACK_BOT_TOKEN="xoxb-your-token-here"
```

### Step 6: Install Dependencies

```bash
pip install -r requirements.txt
```

### Step 7: Test Locally

```bash
python server.py
```

You should see:
```
Starting slack v1.0.0
Slack Bot Token: xoxb-****...****
✓ Connected to Slack workspace: Your Workspace
✓ Bot user: mcp_server
Server is ready for connections...
```

## Docker Deployment

For deployment in your Proxmox LXC:

### Build Image

```bash
docker build -t mcp-slack:latest .
```

### Run Container

```bash
docker run -d \
  --name mcp-slack \
  -e SLACK_BOT_TOKEN="xoxb-your-token-here" \
  -p 3008:3000 \
  mcp-slack:latest
```

### Using .env File

```bash
# Create .env file
cat > .env << EOF
SLACK_BOT_TOKEN=xoxb-your-token-here
EOF

# Run with env file
docker run -d \
  --name mcp-slack \
  --env-file .env \
  -p 3008:3000 \
  mcp-slack:latest
```

## Available Tools

### Channel Management

| Tool | Description | Parameters |
|------|-------------|------------|
| `list_channels` | List all channels | `include_archived`, `types` |
| `get_channel_info` | Get channel details | `channel_id` |

### Messaging

| Tool | Description | Parameters |
|------|-------------|------------|
| `send_message` | Send message to channel | `channel`, `text`, `thread_ts` (optional) |
| `get_channel_history` | Get message history | `channel_id`, `limit`, `oldest` |
| `get_thread_replies` | Get thread messages | `channel_id`, `thread_ts` |

### Users

| Tool | Description | Parameters |
|------|-------------|------------|
| `list_users` | List workspace users | `include_bots` |
| `get_user_info` | Get user details | `user_id` |

### Search

| Tool | Description | Parameters |
|------|-------------|------------|
| `search_messages` | Search messages | `query`, `count`, `sort` |

### Files

| Tool | Description | Parameters |
|------|-------------|------------|
| `upload_file` | Upload file to channel | `channel`, `file_path`, `title`, `initial_comment` |
| `list_files` | List workspace files | `channel`, `user`, `count` |

### Reactions

| Tool | Description | Parameters |
|------|-------------|------------|
| `add_reaction` | Add emoji reaction | `channel`, `timestamp`, `emoji` |

## Finding IDs

### Channel ID
Two methods:

**Method 1: From Slack Desktop**
1. Right-click channel name
2. Select "View channel details"
3. Scroll down - ID shown at bottom
4. Format: `C1234567890`

**Method 2: Use MCP**
```python
list_channels()
# Returns all channels with IDs
```

### User ID
**Method 1: From Slack Desktop**
1. Click user profile
2. Click "••• More"
3. Select "Copy member ID"
4. Format: `U1234567890`

**Method 2: Use MCP**
```python
list_users()
# Returns all users with IDs
```

### Message Timestamp
When you get messages from history, each message has a `ts` field:
```python
get_channel_history(channel_id="C1234567890")
# Returns messages with ts like "1704834567.123456"
```

## Common Use Cases

### Send Message to Channel

**By channel ID:**
```python
send_message(
    channel="C1234567890",
    text="Hello from MCP! 👋"
)
```

**By channel name:**
```python
send_message(
    channel="#general",
    text="Hello everyone!"
)
```

**With Slack markdown:**
```python
send_message(
    channel="#general",
    text="""
*Bold text* and _italic text_
`code` and ```code block```
<https://example.com|Link text>
> Quote
• Bullet point
    """
)
```

### Reply to Thread
```python
send_message(
    channel="C1234567890",
    text="Thread reply!",
    thread_ts="1704834567.123456"
)
```

### Search for Messages
```python
search_messages(
    query="meeting notes from:@john",
    count=20,
    sort="timestamp"
)
```

**Search query syntax:**
- `meeting notes` - Search text
- `from:@john` - From specific user
- `in:#general` - In specific channel
- `after:2024-01-01` - After date
- `before:2024-12-31` - Before date
- `has:link` - Messages with links
- `has:file` - Messages with files

### Get Recent Messages
```python
get_channel_history(
    channel_id="C1234567890",
    limit=50
)
```

### Upload File
```python
upload_file(
    channel="#general",
    file_path="/path/to/document.pdf",
    title="Q1 Report",
    initial_comment="Here's the quarterly report"
)
```

### Add Reaction
```python
add_reaction(
    channel="C1234567890",
    timestamp="1704834567.123456",
    emoji="thumbsup"
)
```

**Popular emoji names:**
- `thumbsup`, `thumbsdown`
- `heart`, `fire`, `rocket`
- `tada`, `party`, `celebrate`
- `eyes`, `raised_hands`
- `white_check_mark`, `x`

### List All Channels
```python
# Public and private channels
list_channels()

# Include archived
list_channels(include_archived=True)

# Only public channels
list_channels(types="public_channel")

# Include DMs
list_channels(types="public_channel,private_channel,im,mpim")
```

### Get User Info
```python
get_user_info(user_id="U1234567890")
```

### List Active Users
```python
# Exclude bots
list_users(include_bots=False)

# Include bots
list_users(include_bots=True)
```

## Resources

| URI | Description |
|-----|-------------|
| `slack://channels` | All workspace channels |
| `slack://users` | All workspace users |

## Usage Examples

### From Claude Desktop (Local)

Edit: `~/Library/Application Support/Claude/claude_desktop_config.json`

```json
{
  "mcpServers": {
    "slack": {
      "command": "python",
      "args": ["/path/to/mcp/slack/server.py"],
      "env": {
        "SLACK_BOT_TOKEN": "xoxb-your-token-here"
      }
    }
  }
}
```

### From Claude Code/iPhone (Remote)

After deploying to your Proxmox LXC with Cloudflare Tunnel:

```json
{
  "mcpServers": {
    "slack": {
      "url": "https://slack.yourdomain.com",
      "transport": "http"
    }
  }
}
```

## Example Commands

Ask Claude:

### Messaging
> "Send a message to #general saying the deployment is complete"
> "Reply to the thread in #engineering about the bug fix"
> "Read the last 20 messages from #support"

### Search & Discovery
> "Search for messages about 'budget approval' from Sarah"
> "Find all messages in #marketing from last week"
> "Show me recent messages with links to GitHub"

### File Management
> "Upload the report.pdf to #leadership with a summary"
> "List all files shared in #design this month"

### User Info
> "Who is on the engineering team?"
> "Get contact info for John Smith"
> "List all workspace admins"

### Reactions
> "Add a checkmark reaction to that message"
> "React with fire emoji to the latest message in #wins"

### Advanced Workflows
> "Read #support messages, summarize urgent issues, and post summary to #support-leads"
> "Find all unanswered questions in #help and list them"
> "Search for meeting notes from yesterday and create a task list"

## Slack Markdown Reference

Slack uses its own markdown-like formatting:

### Text Formatting
```
*bold text*
_italic text_
~strikethrough~
`code`
```

### Links
```
<https://example.com>
<https://example.com|Link Text>
<@U1234567890> - Mention user
<#C1234567890> - Link channel
```

### Lists
```
• Bullet point (use actual bullet)
1. Numbered list
2. Another item
```

### Quotes
```
> Single line quote
>>> Multi-line
quote block
```

### Code Blocks
````
```
Code block
Multiple lines
```
````

## Troubleshooting

### "SLACK_BOT_TOKEN not set"
**Solution**: Set the environment variable:
```bash
export SLACK_BOT_TOKEN="xoxb-your-token-here"
```

### "Failed to connect to Slack"
**Check**:
1. Is your token valid? (starts with `xoxb-`)
2. Is the app still installed in workspace?
3. Token not revoked?

**Test manually:**
```bash
curl -X GET https://slack.com/api/auth.test \
  -H "Authorization: Bearer xoxb-your-token-here"
```

### "missing_scope" error
**Solution**:
1. Go to https://api.slack.com/apps
2. Select your app
3. Go to "OAuth & Permissions"
4. Add the missing scope
5. Reinstall app to workspace
6. Use the new token

### "channel_not_found"
**Check**:
1. Is the channel ID correct?
2. Is the bot a member of the channel?

**Solution for private channels**:
1. Go to the channel in Slack
2. Click channel name → Integrations
3. Add your MCP Server app

### "not_in_channel"
**Solution**: Invite the bot to the channel:
```
/invite @mcp_server
```

### "File not found" when uploading
**Check**:
1. Is the file path correct?
2. Does the file exist?
3. Does the server have read permissions?

## Security Notes

- **Bot token = full workspace access** - protect it!
- Never commit tokens to Git
- Use environment variables
- Rotate tokens if compromised
- Only grant necessary scopes
- Expose only via Cloudflare Zero Trust if remote
- Review app permissions regularly

## Search Query Tips

**By user:**
```
from:@username
from:me
```

**By channel:**
```
in:#channel-name
```

**By date:**
```
after:2024-01-01
before:2024-12-31
on:2024-01-15
```

**By content:**
```
has:link
has:file
has:pin
has:star
```

**Boolean:**
```
term1 OR term2
term1 AND term2
-exclude_this
```

**Combine:**
```
from:@john in:#engineering has:link after:2024-01-01
```

## Common Channel Types

| Type | Description | In list_channels |
|------|-------------|------------------|
| `public_channel` | Public channels | Default |
| `private_channel` | Private channels | Default |
| `im` | Direct messages | Use `types="im"` |
| `mpim` | Group DMs | Use `types="mpim"` |

## Bot User vs App

This MCP server uses a **Bot User** (not User Token):
- ✅ Can post as bot
- ✅ Can read public channels (with scope)
- ✅ Can read private channels if invited
- ✅ Can search workspace
- ❌ Cannot act as a specific user
- ❌ Cannot read DMs unless involved

## Rate Limits

Slack has rate limits (Tier 2 for most methods):
- ~1 request per second per method
- Bursts allowed
- Server handles rate limit errors automatically

**Tips:**
- Use pagination for large datasets
- Batch operations when possible
- Cache frequently accessed data

## Next Steps

1. ✅ Create Slack app at https://api.slack.com/apps
2. ✅ Add bot token scopes
3. ✅ Install app to workspace
4. ✅ Copy bot token
5. ✅ Test locally with `python server.py`
6. ✅ Deploy to Proxmox LXC via Docker
7. ✅ Configure Cloudflare Tunnel
8. ✅ Add to Claude apps

---

**Tip**: Combine with GitHub MCP to post deployment notifications to Slack!

**Example**: "When a PR is merged, send a message to #engineering with the PR details"
