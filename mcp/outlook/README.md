# Outlook MCP Connector (Read-Only)

**Smart read-only access to Outlook email and calendar with AI-powered priority analysis**

This MCP connector provides read-only access to your Outlook/Office 365 account via IMAP and Exchange Web Services (EWS), with intelligent tools to generate priority action lists based on your emails and calendar.

## Features

### Email Access (Read-Only)
- ✅ Get unread emails
- ✅ Get recent emails (last N days)
- ✅ Search emails by keyword
- ✅ Get full email content
- ✅ Count unread emails
- ✅ View email attachments (names/sizes)

### Calendar Access (Read-Only)
- ✅ Get today's events
- ✅ Get this week's events
- ✅ Get events in date range
- ✅ Search events by keyword
- ✅ Check availability (free time blocks)

### Smart Analysis Tools (The Killer Features!)
- 🎯 **Generate Priority List** - Analyzes unread emails and calendar to create prioritized action list with time block suggestions
- ☀️ **Daily Briefing** - Morning summary with priorities, meetings, and recommendations
- 📊 **Workload Analysis** - Analyze email and meeting volume trends

## How It Works

### Priority List Generator

The priority list generator is the most powerful feature. It:

1. **Reads all unread emails** (up to 100 most recent)
2. **Scores each email** based on:
   - Urgency keywords ("urgent", "asap", "deadline", etc.)
   - Action keywords ("please", "need", "review", etc.)
   - Sender (VIP detection)
   - How recent the email is
3. **Extracts action items** with deadlines
4. **Analyzes your calendar** for today
5. **Finds free time blocks** between meetings
6. **Assigns high-priority items** to available time slots
7. **Returns structured priority list** with recommendations

### Example Usage

```
You: "Build my priority action list for today"

Claude:
📋 Priority Action List - Monday, Nov 11, 2024

HIGH PRIORITY (Scheduled):
1. [10:00-10:30] Respond to Sarah's budget approval request
   From: sarah@company.com
   Urgency: HIGH (score: 85)
   Deadline: EOD today

2. [10:30-11:00] Review Q4 proposal from John
   From: john@company.com
   Urgency: HIGH (score: 75)

MEETINGS TODAY:
- 9:00-9:30: Team standup
- 11:00-12:00: Client call
- 2:00-3:00: Project review

AVAILABLE TIME:
- 10:00-11:00 (1 hour) ⭐ Best for focused work
- 12:00-2:00 (2 hours)
- 3:00-5:00 (2 hours)

RECOMMENDATION:
Balanced day. Tackle high-priority items between meetings.
```

## Credentials Setup

### Step 1: Enable IMAP in Outlook

1. Go to Outlook settings
2. **Mail** → **Sync email** → **POP and IMAP**
3. Enable **IMAP**
4. Save

### Step 2: Get App Password (Recommended)

For security, use an app-specific password instead of your main password:

**For Office 365/Microsoft Account:**
1. Go to: https://account.microsoft.com/security
2. Navigate to: **Security** → **Advanced security options**
3. Click: **App passwords**
4. Create new app password: "MCP Server"
5. Copy the generated password

### Step 3: Add to .env File

```bash
# In your deployment/.env file
OUTLOOK_EMAIL=your-email@outlook.com
OUTLOOK_PASSWORD=your-app-password-here
```

**Security Note:** Use app-specific password, NOT your main account password!

## Available Tools

### Email Tools

#### `get_unread_emails`
Get unread emails from inbox
```json
{
  "limit": 50  // Optional: max emails to return (default: 50)
}
```

#### `get_recent_emails`
Get recent emails from last N days
```json
{
  "days": 7,    // Optional: days to look back (default: 7)
  "limit": 100  // Optional: max emails (default: 100)
}
```

#### `search_emails`
Search emails by keyword
```json
{
  "query": "project update",  // Required: search term
  "days": 30                   // Optional: days to search (default: 30)
}
```

#### `get_email_content`
Get full content of specific email
```json
{
  "email_id": "12345"  // Required: email ID from previous queries
}
```

#### `count_unread`
Count total unread emails
```json
{}  // No parameters
```

### Calendar Tools

#### `get_today_events`
Get today's calendar events
```json
{}  // No parameters
```

#### `get_week_events`
Get this week's calendar events
```json
{}  // No parameters
```

#### `get_events_range`
Get events in specific date range
```json
{
  "start_date": "2024-11-01",  // Required: YYYY-MM-DD
  "end_date": "2024-11-15"     // Required: YYYY-MM-DD
}
```

#### `search_events`
Search calendar events by keyword
```json
{
  "query": "client meeting",  // Required: search term
  "days": 30                   // Optional: days forward/back (default: 30)
}
```

#### `check_availability`
Check availability with free time blocks
```json
{
  "date": "2024-11-11"  // Optional: YYYY-MM-DD (default: today)
}
```

### Smart Analysis Tools

#### `generate_priority_list` ⭐
Generate smart priority action list
```json
{
  "date": "2024-11-11"  // Optional: YYYY-MM-DD (default: today)
}
```

Returns:
- High-priority items scheduled to time blocks
- Medium/low priority items
- Today's calendar
- Available time blocks
- Smart recommendations

#### `daily_briefing` ☀️
Generate morning briefing
```json
{}  // No parameters
```

Returns:
- Unread email count
- Urgent action count
- Meetings today
- Available time
- Top priorities
- Recommendation

#### `analyze_workload` 📊
Analyze email and meeting workload
```json
{
  "days": 7  // Optional: days to analyze (default: 7)
}
```

Returns:
- Email volume trends
- Meeting density
- Averages
- Recommendations

## Deployment

### Docker Compose

Add to your `docker-compose.minimal.yml`:

```yaml
mcp-outlook:
  build: ./mcp/outlook
  container_name: mcp-outlook
  environment:
    - OUTLOOK_EMAIL=${OUTLOOK_EMAIL}
    - OUTLOOK_PASSWORD=${OUTLOOK_PASSWORD}
  ports:
    - "3010:3000"
  restart: unless-stopped
```

### Cloudflare Tunnel Route

```bash
cloudflared tunnel route dns mcp-tunnel outlook.yourdomain.com
```

Update tunnel config to route:
```yaml
- hostname: outlook.yourdomain.com
  service: http://MCP-LXC-IP:3010
```

### Claude Configuration

Add to your Claude config:

```json
{
  "mcpServers": {
    "outlook": {
      "url": "https://outlook.yourdomain.com",
      "transport": "http"
    }
  }
}
```

## Testing

### Test Locally

```bash
cd mcp/outlook
python server.py
```

### Test Tools

Ask Claude:
```
"Check my unread emails"
"What's on my calendar today?"
"Build my priority action list"
"Give me my daily briefing"
```

## Troubleshooting

### IMAP Connection Failed

**Error:** "Failed to connect to Outlook IMAP"

**Solutions:**
1. Verify IMAP is enabled in Outlook settings
2. Check you're using app-specific password, not main password
3. Verify email/password in .env file
4. Test credentials manually: `telnet outlook.office365.com 993`

### EWS/Calendar Connection Failed

**Error:** "Failed to connect to Outlook calendar"

**Solutions:**
1. Verify Office 365 account (not basic Outlook.com)
2. Check EWS is not disabled by admin
3. Try autodiscover: https://outlook.office365.com/autodiscover/autodiscover.xml
4. Verify credentials

### No Emails Returned

**Issue:** `get_unread_emails` returns empty array

**Possible causes:**
1. No unread emails (check manually)
2. IMAP folder name different (some accounts use "Inbox" vs "INBOX")
3. Permissions issue

### Calendar Events Missing

**Issue:** `get_today_events` returns no events

**Possible causes:**
1. No events scheduled (check manually)
2. Wrong timezone
3. Calendar permissions

## Security Best Practices

1. ✅ **Use app-specific password** - Never use main account password
2. ✅ **Restrict permissions** - chmod 600 on .env file
3. ✅ **Enable Cloudflare Zero Trust** - Add authentication layer
4. ✅ **Monitor access logs** - Check for unusual activity
5. ✅ **Rotate passwords** - Change app password every 90 days
6. ✅ **Read-only access** - This connector cannot send emails or modify calendar

## Limitations

This is a **read-only** connector:
- ❌ Cannot send emails
- ❌ Cannot delete emails
- ❌ Cannot modify calendar
- ❌ Cannot mark emails as read/unread
- ✅ Perfect for analysis and information retrieval

## Integration with Other MCPs

This connector works great with:
- **Todoist MCP** - Create tasks from high-priority emails
- **Slack MCP** - Notify team about urgent items
- **Notion MCP** - Log action items to database
- **Google MCP** - Cross-reference with Gmail calendar

See cross-service integration examples in the main documentation.

## Support

- **Credentials issues?** See [CREDENTIALS-GUIDE.md](../../CREDENTIALS-GUIDE.md)
- **Deployment issues?** See [DEPLOYMENT-GUIDE.md](../../DEPLOYMENT-GUIDE.md)
- **Found a bug?** [Open an issue](https://github.com/tchiro88/MCP_CREATOR/issues)

---

**Built with:**
- Python 3.11+
- IMAP (imaplib)
- Exchange Web Services (exchangelib)
- MCP SDK

**Port:** 3010
**Endpoint:** outlook.yourdomain.com

**Last Updated:** 2025-11-10
