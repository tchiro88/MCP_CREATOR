# MCP Integrator - Cross-Service Intelligence

**Meta-MCP that aggregates data from all your MCP services**

The Integrator is a special MCP connector that acts as an orchestration layer, calling other MCP services and aggregating their data to provide unified, cross-service intelligence.

## What It Does

Instead of asking Claude to check Outlook, then Gmail, then Slack separately, the Integrator lets Claude get everything in one request:

```
❌ OLD WAY:
You: "Check my unread emails"
Claude calls: outlook.get_unread_emails
Claude calls: google.get_unread_emails
Claude calls: slack.get_unread_messages
(3 separate requests, Claude must aggregate manually)

✅ NEW WAY:
You: "Check my unread messages"
Claude calls: integrator.unified_inbox
(1 request, auto-aggregated, sorted, and formatted)
```

## Features

### 🔄 Unified Inbox
Get unread messages from ALL services in one view:
- Outlook emails
- Gmail emails
- Slack messages
- Auto-sorted by date
- Aggregated counts per service

### 📅 Unified Calendar
See all calendar events in one place:
- Outlook Calendar
- Google Calendar
- Sorted by time
- Shows service source

### ✅ Unified Tasks
All tasks from every service:
- Todoist
- Google Tasks
- Notion (if configured with tasks database)

### ☀️ Comprehensive Briefing
**The killer feature!** Morning briefing across ALL services:
- Total unread messages (all services)
- Today's calendar (all services)
- Active tasks (all services)
- Smart recommendations based on workload

### 🔍 Search Everywhere
Search for a keyword across ALL services:
- Outlook emails
- Gmail
- Slack messages
- Notion pages
- GitHub code/issues
- Returns aggregated results

### 🏥 Service Health Check
Check connectivity to all MCP services:
- Which services are online
- Which are having issues
- Tool counts per service

## Available Tools

### `unified_inbox`
Get unified unread messages view

**Arguments:**
```json
{
  "limit": 50  // Optional: max messages per service
}
```

**Returns:**
```json
{
  "total_unread": 127,
  "by_service": {
    "outlook": 45,
    "google": 62,
    "slack": 20
  },
  "all_messages": [/* sorted by date */]
}
```

### `unified_calendar`
Get unified calendar view

**Arguments:**
```json
{
  "date": "2024-11-11"  // Optional: YYYY-MM-DD, default today
}
```

**Returns:**
```json
{
  "date": "2024-11-11",
  "all_events": [/* sorted by time */],
  "by_service": {
    "outlook": 5,
    "google": 3
  }
}
```

### `unified_tasks`
Get all tasks from all services

**Arguments:** None

**Returns:**
```json
{
  "total_tasks": 42,
  "by_service": {
    "todoist": 25,
    "google": 12,
    "notion": 5
  },
  "all_tasks": [/* all tasks */]
}
```

### `comprehensive_briefing` ⭐
Generate complete daily briefing

**Arguments:** None

**Returns:**
```json
{
  "date": "2024-11-11",
  "summary": {
    "unread_messages": 127,
    "meetings_today": 8,
    "active_tasks": 42
  },
  "inbox_overview": {/* top messages */},
  "calendar_overview": {/* today's events */},
  "tasks_overview": {/* top tasks */},
  "recommendations": [
    "⚠️ High inbox volume (127 unread)",
    "📅 Heavy meeting day (8 meetings)",
    "📋 Many active tasks (42)"
  ]
}
```

### `search_everywhere`
Search across all services

**Arguments:**
```json
{
  "query": "project update",  // Required
  "days": 30                   // Optional: days to search back
}
```

**Returns:**
```json
{
  "query": "project update",
  "total_results": 45,
  "by_service": {
    "outlook_emails": {"count": 12, "results": [...]},
    "google_emails": {"count": 8, "results": [...]},
    "slack_messages": {"count": 15, "results": [...]},
    "notion_pages": {"count": 5, "results": [...]},
    "github_code": {"count": 5, "results": [...]}
  }
}
```

### `service_health_check`
Check all MCP services

**Arguments:** None

**Returns:**
```json
{
  "timestamp": "2024-11-11T09:00:00",
  "total_services": 8,
  "healthy_services": 7,
  "unhealthy_services": 1,
  "services": {
    "outlook": {"status": "healthy", "tools_available": 13},
    "google": {"status": "healthy", "tools_available": 20},
    "slack": {"status": "unhealthy", "error": "Connection timeout"}
  }
}
```

## Configuration

### Environment Variables

The integrator needs to know where each MCP service is:

```bash
# In deployment/.env
MCP_OUTLOOK_URL=http://mcp-outlook:3000
MCP_GOOGLE_URL=http://mcp-google:3000
MCP_TODOIST_URL=http://mcp-todoist:3000
MCP_SLACK_URL=http://mcp-slack:3000
MCP_NOTION_URL=http://mcp-notion:3000
MCP_GITHUB_URL=http://mcp-github:3000
MCP_HA_URL=http://mcp-homeassistant:3000
MCP_ICLOUD_URL=http://mcp-icloud:3000
```

**Note:** Uses internal Docker network names by default. Services auto-discover each other.

## Deployment

### Docker Compose

Add to `docker-compose.minimal.yml`:

```yaml
mcp-integrator:
  build: ./mcp/integrator
  container_name: mcp-integrator
  environment:
    - MCP_OUTLOOK_URL=http://mcp-outlook:3000
    - MCP_GOOGLE_URL=http://mcp-google:3000
    - MCP_TODOIST_URL=http://mcp-todoist:3000
    - MCP_SLACK_URL=http://mcp-slack:3000
    - MCP_NOTION_URL=http://mcp-notion:3000
    - MCP_GITHUB_URL=http://mcp-github:3000
    - MCP_HA_URL=http://mcp-homeassistant:3000
    - MCP_ICLOUD_URL=http://mcp-icloud:3000
  ports:
    - "3011:3000"
  depends_on:
    - mcp-outlook
    - mcp-google
    - mcp-todoist
    - mcp-slack
    - mcp-notion
    - mcp-github
  restart: unless-stopped
```

### Cloudflare Tunnel

```bash
cloudflared tunnel route dns mcp-tunnel integrator.yourdomain.com
```

### Claude Configuration

```json
{
  "mcpServers": {
    "integrator": {
      "url": "https://integrator.yourdomain.com",
      "transport": "http"
    }
  }
}
```

## Example Usage

### Morning Routine
```
You: "Give me my comprehensive briefing"

Claude: (calls integrator.comprehensive_briefing)

☀️ Good morning! Here's your briefing for Nov 11, 2024:

INBOX:
- 127 unread messages (Outlook: 45, Gmail: 62, Slack: 20)

CALENDAR TODAY:
- 8 meetings scheduled
- First meeting: 9:00 AM Team Standup
- Last meeting: 4:30 PM 1:1 with Sarah

TASKS:
- 42 active tasks
- Top priority: Q4 Budget Review (Todoist)

RECOMMENDATIONS:
⚠️ High inbox volume - schedule inbox zero time
📅 Heavy meeting day - limited focus time
📋 Many active tasks - prioritize top 3-5
```

### Search Everything
```
You: "Search everywhere for 'project alpha'"

Claude: (calls integrator.search_everywhere)

Found 67 results for "project alpha":

EMAILS (20):
- Outlook: 8 emails
- Gmail: 12 emails
Recent: "Project Alpha Q4 Update" from john@company.com

SLACK (25):
- #project-alpha channel: 18 messages
- DMs: 7 messages
Recent: "Alpha deployment ready" from @sarah

NOTION (15):
- Meeting notes: 8 pages
- Project docs: 7 pages

GITHUB (7):
- Code mentions: 5 files
- Issues: 2 open issues
```

### Unified View
```
You: "Show me all my unread messages"

Claude: (calls integrator.unified_inbox)

You have 127 unread messages:

OUTLOOK (45):
1. [2 hours ago] Sarah: "Q4 Budget Approval Needed"
2. [3 hours ago] John: "Client Meeting Prep"
...

GMAIL (62):
1. [1 hour ago] Team: "Sprint Review Notes"
2. [4 hours ago] HR: "Benefits Update"
...

SLACK (20):
1. [30 min ago] @mike in #general: "Deploy went live!"
2. [1 hour ago] @sarah: "Can we sync on alpha?"
...
```

## Architecture

```
┌──────────┐
│  Claude  │
└────┬─────┘
     │
     │ "Show me everything"
     ▼
┌────────────────┐
│  Integrator    │ ← This MCP
│    (3011)      │
└────┬───────────┘
     │
     │ Calls multiple MCPs
     ├─────────┬──────────┬─────────┐
     ▼         ▼          ▼         ▼
  Outlook   Google    Todoist   Slack
  (3010)    (3004)    (3005)    (3008)
```

## Benefits

1. **Reduced API calls** - One request instead of many
2. **Auto-aggregation** - No manual data merging needed
3. **Unified formatting** - Consistent data structure
4. **Smart recommendations** - Cross-service intelligence
5. **Simpler prompts** - "Show me everything" just works

## Troubleshooting

### Service Not Found

**Error:** "Unknown service: outlook"

**Solution:** Check that service URL is configured in environment variables and service is running.

### Connection Timeout

**Error:** "Network error calling outlook.get_unread_emails"

**Solutions:**
1. Check service is running: `docker ps | grep mcp-outlook`
2. Verify network connectivity: `docker exec mcp-integrator ping mcp-outlook`
3. Check service logs: `docker logs mcp-outlook`

### Health Check Shows Unhealthy

Run `service_health_check` to see which services have issues, then debug individually.

## Port Mapping

- **Integrator:** 3011 (integrator.yourdomain.com)
- **Calls:** All other MCP services on internal Docker network

## Dependencies

Requires these MCP services to be running (at minimum):
- At least 2 services for meaningful integration
- Recommended: outlook, google, todoist, slack

## Future Enhancements

Potential additions:
- Cross-service task creation (email → task)
- Meeting conflict detection across calendars
- Smart scheduling suggestions
- Workload balancing recommendations
- Email categorization across services

---

**Port:** 3011
**Endpoint:** integrator.yourdomain.com
**Type:** Meta-MCP (orchestrates other MCPs)

**Last Updated:** 2025-11-10
