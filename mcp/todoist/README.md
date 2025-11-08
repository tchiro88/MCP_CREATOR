# Todoist MCP Server

Provides MCP access to Todoist tasks, projects, and comments from any device.

## Features

### Tasks
- ✅ List tasks (with filters)
- ➕ Create tasks
- ✏️ Update tasks
- ✔️ Complete tasks
- 🗑️ Delete tasks

### Projects
- 📋 List projects
- ➕ Create projects

### Comments
- 💬 Add comments to tasks
- 👀 View task comments

## Prerequisites

1. Todoist account (Free or Premium)
2. Todoist API token
3. Python 3.11+

## Setup Instructions

### Step 1: Get Your API Token

1. Go to [Todoist Integrations Settings](https://todoist.com/prefs/integrations)
2. Scroll to **API token** section
3. Copy your API token (looks like: `a1b2c3d4e5f6...`)

### Step 2: Set Environment Variable

```bash
export TODOIST_API_TOKEN="your-api-token-here"
```

### Step 3: Install Dependencies

```bash
pip install -r requirements.txt
```

### Step 4: Test Locally

```bash
# Run the server
python server.py
```

You should see:
```
Starting todoist v1.0.0
✓ Connected to Todoist (found X projects)
Server is ready for connections...
```

## Docker Deployment

For deployment in your Proxmox LXC:

### Build Image

```bash
docker build -t mcp-todoist:latest .
```

### Run Container

```bash
docker run -d \
  --name mcp-todoist \
  -e TODOIST_API_TOKEN="your-api-token-here" \
  -p 3005:3000 \
  mcp-todoist:latest
```

### Using .env File

```bash
# Create .env file
echo "TODOIST_API_TOKEN=your-token-here" > .env

# Run with env file
docker run -d \
  --name mcp-todoist \
  --env-file .env \
  -p 3005:3000 \
  mcp-todoist:latest
```

## Available Tools

### Task Management

| Tool | Description | Required Parameters |
|------|-------------|---------------------|
| `list_tasks` | List tasks with filters | None (all optional) |
| `create_task` | Create new task | `content` |
| `update_task` | Update existing task | `task_id` |
| `complete_task` | Mark task complete | `task_id` |
| `delete_task` | Delete a task | `task_id` |

### Project Management

| Tool | Description | Required Parameters |
|------|-------------|---------------------|
| `list_projects` | List all projects | None |
| `create_project` | Create new project | `name` |

### Comments

| Tool | Description | Required Parameters |
|------|-------------|---------------------|
| `add_comment` | Add comment to task | `task_id`, `content` |
| `get_comments` | Get task comments | `task_id` |

## Task Filters

The `list_tasks` tool supports Todoist's filter syntax:

| Filter | Description |
|--------|-------------|
| `today` | Tasks due today |
| `tomorrow` | Tasks due tomorrow |
| `overdue` | Overdue tasks |
| `priority 1` | High priority tasks (1-4) |
| `no date` | Tasks with no due date |
| `@label` | Tasks with specific label |
| `#project` | Tasks in specific project |

**Examples**:
```
today & priority 1       - Urgent tasks due today
overdue | today          - Overdue or due today
#Work & @urgent          - Urgent work tasks
```

## Priority Levels

Todoist uses priority 1-4:
- **1** = Normal (default)
- **2** = Medium
- **3** = High
- **4** = Urgent

## Due Date Formats

Natural language dates work great:
- `today`
- `tomorrow`
- `next Monday`
- `Nov 10`
- `2025-11-10`
- `every day` (recurring)
- `every Monday` (recurring)

## Resources

| URI | Description |
|-----|-------------|
| `todoist://tasks/today` | Tasks due today |
| `todoist://tasks/all` | All active tasks |
| `todoist://projects` | All projects |

## Usage Examples

### From Claude Desktop (Local)

Edit: `~/Library/Application Support/Claude/claude_desktop_config.json`

```json
{
  "mcpServers": {
    "todoist": {
      "command": "python",
      "args": ["/path/to/mcp/todoist/server.py"],
      "env": {
        "TODOIST_API_TOKEN": "your-api-token-here"
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
    "todoist": {
      "url": "https://todoist-mcp.yourdomain.com",
      "transport": "http"
    }
  }
}
```

## Example Commands

Ask Claude:

### List Tasks
> "Show me my tasks for today"
> "What are my high priority tasks?"
> "List all overdue tasks"

### Create Tasks
> "Add a task: Buy groceries tomorrow"
> "Create an urgent task to call client"
> "Add task 'Review PR' in project Work with label @code"

### Manage Tasks
> "Mark task [ID] as complete"
> "Update task [ID] to be due next Monday"
> "Change task [ID] priority to urgent"

### Projects
> "List all my projects"
> "Create a new project called 'Home Renovation'"

### Comments
> "Add comment to task [ID]: This is blocked by X"
> "Show me all comments on task [ID]"

## Troubleshooting

### "TODOIST_API_TOKEN not set"
- Set the environment variable before running
- Or pass it via Docker: `-e TODOIST_API_TOKEN=...`

### "Failed to connect to Todoist API"
- Check your API token is correct
- Verify internet connectivity
- Check Todoist API status: https://status.todoist.com/

### Task ID not found
- Get task ID from `list_tasks` output
- Task IDs are strings, not numbers

## API Rate Limits

Todoist API limits:
- **450 requests per 15 minutes** per token
- The server doesn't implement rate limiting

For heavy usage, consider adding delays between requests.

## Security Notes

- **API token = full account access** - protect it!
- Never commit tokens to Git
- Use environment variables or secrets management
- Expose only via Cloudflare Zero Trust if remote

## Next Steps

1. ✅ Get API token from Todoist
2. ✅ Test locally with `python server.py`
3. ✅ Deploy to Proxmox LXC via Docker
4. ✅ Configure Cloudflare Tunnel
5. ✅ Add to Claude apps

---

**Tip**: Combine with Google Calendar MCP to sync tasks and events!
