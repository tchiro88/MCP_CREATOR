# Notion MCP Server

Provides MCP access to your Notion workspace from any device.

## Features

### Database Management
- 📊 List all databases in workspace
- 🔍 Query databases with filters and sorting
- 📈 Full property support (text, number, select, date, etc.)

### Page Operations
- 📄 Get page details and properties
- ✏️ Create new pages in databases
- 🔧 Update existing page properties
- 📖 Read page content (blocks)
- ➕ Append content to pages

### Search & Discovery
- 🔎 Search across all workspace content
- 👥 List workspace users
- 🏷️ Filter by page type

### Supported Content Types
- Text blocks
- Headings (H1, H2, H3)
- Bullet and numbered lists
- To-do lists
- Code blocks
- Quotes
- Callouts
- And all other Notion block types!

## Prerequisites

1. Notion workspace (free or paid)
2. Notion integration token
3. Python 3.11+

## Setup Instructions

### Step 1: Create Notion Integration

1. **Go to Notion Integrations**:
   - Visit: https://www.notion.so/my-integrations
   - Click "**+ New integration**"

2. **Configure Integration**:
   - **Name**: `MCP Server`
   - **Associated workspace**: Select your workspace
   - **Type**: Internal integration
   - Click "**Submit**"

3. **Copy Integration Token**:
   - After creation, you'll see "**Internal Integration Token**"
   - Click "**Show**" then "**Copy**"
   - Format: `secret_xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx`

4. **Set Capabilities** (confirm these are enabled):
   - ✅ Read content
   - ✅ Update content
   - ✅ Insert content
   - ✅ Read user information (without email)

### Step 2: Share Databases/Pages with Integration

**IMPORTANT**: Your integration can only access pages/databases you explicitly share with it.

For each database or page you want to access:

1. Open the page/database in Notion
2. Click "**•••**" (top right)
3. Scroll to "**Connections**"
4. Click "**Add connections**"
5. Search for "**MCP Server**" and select it
6. Click "**Confirm**"

**Tip**: Share your root workspace page to give access to everything!

### Step 3: Set Environment Variable

```bash
export NOTION_TOKEN="secret_xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx"
```

### Step 4: Install Dependencies

```bash
pip install -r requirements.txt
```

### Step 5: Test Locally

```bash
python server.py
```

You should see:
```
Starting notion v1.0.0
Notion Token: secret_****...****
✓ Connected to Notion API
✓ Workspace: Your Workspace Name
Server is ready for connections...
```

## Docker Deployment

For deployment in your Proxmox LXC:

### Build Image

```bash
docker build -t mcp-notion:latest .
```

### Run Container

```bash
docker run -d \
  --name mcp-notion \
  -e NOTION_TOKEN="secret_your-token-here" \
  -p 3007:3000 \
  mcp-notion:latest
```

### Using .env File

```bash
# Create .env file
cat > .env << EOF
NOTION_TOKEN=secret_xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx
EOF

# Run with env file
docker run -d \
  --name mcp-notion \
  --env-file .env \
  -p 3007:3000 \
  mcp-notion:latest
```

## Available Tools

### Database Tools

| Tool | Description | Parameters |
|------|-------------|------------|
| `list_databases` | List all accessible databases | None |
| `query_database` | Query database with filters/sorts | `database_id`, `filter_obj` (optional), `sorts` (optional), `max_results` |

### Page Tools

| Tool | Description | Parameters |
|------|-------------|------------|
| `get_page` | Get page properties | `page_id` |
| `create_page` | Create new page in database | `database_id`, `properties`, `content` (optional) |
| `update_page` | Update page properties | `page_id`, `properties` |

### Content Tools

| Tool | Description | Parameters |
|------|-------------|------------|
| `get_page_content` | Read page blocks | `page_id` |
| `append_blocks` | Add content to page | `page_id`, `blocks` |

### Utility Tools

| Tool | Description | Parameters |
|------|-------------|------------|
| `search` | Search workspace | `query`, `filter_type` (page/database), `max_results` |
| `list_users` | List workspace users | None |

## Finding Database and Page IDs

### Method 1: From URL
When viewing a database or page in Notion, the URL contains the ID:

```
https://www.notion.so/My-Database-abc123def456?v=xyz
                              └─ database_id ─┘
```

The ID is the 32-character hex string (with or without hyphens).

### Method 2: Use MCP Tools
```python
# List all databases
list_databases()

# Search for a page
search(query="Project Planning")
```

## Common Use Cases

### List All Databases
```python
list_databases()
```

### Query Database with Filter
```python
query_database(
    database_id="abc123def456",
    filter_obj={
        "property": "Status",
        "select": {"equals": "In Progress"}
    },
    sorts=[{"property": "Due Date", "direction": "ascending"}],
    max_results=50
)
```

### Create New Task
```python
create_page(
    database_id="abc123def456",
    properties={
        "Name": {"title": [{"text": {"content": "New Task"}}]},
        "Status": {"select": {"name": "To Do"}},
        "Priority": {"select": {"name": "High"}},
        "Due Date": {"date": {"start": "2025-01-15"}}
    },
    content=[
        {
            "type": "paragraph",
            "paragraph": {
                "rich_text": [{"text": {"content": "Task description here"}}]
            }
        }
    ]
)
```

### Update Page Properties
```python
update_page(
    page_id="xyz789",
    properties={
        "Status": {"select": {"name": "Done"}},
        "Completed": {"checkbox": True}
    }
)
```

### Read Page Content
```python
get_page_content(page_id="xyz789")
```

### Add Content to Page
```python
append_blocks(
    page_id="xyz789",
    blocks=[
        {
            "type": "heading_2",
            "heading_2": {
                "rich_text": [{"text": {"content": "New Section"}}]
            }
        },
        {
            "type": "paragraph",
            "paragraph": {
                "rich_text": [{"text": {"content": "Some content here"}}]
            }
        },
        {
            "type": "to_do",
            "to_do": {
                "rich_text": [{"text": {"content": "Task item"}}],
                "checked": False
            }
        }
    ]
)
```

### Search Workspace
```python
# Search all content
search(query="meeting notes", max_results=10)

# Search only pages
search(query="project", filter_type="page")

# Search only databases
search(query="tasks", filter_type="database")
```

## Resources

| URI | Description |
|-----|-------------|
| `notion://databases` | All databases |
| `notion://pages` | All pages |
| `notion://users` | Workspace users |

## Usage Examples

### From Claude Desktop (Local)

Edit: `~/Library/Application Support/Claude/claude_desktop_config.json`

```json
{
  "mcpServers": {
    "notion": {
      "command": "python",
      "args": ["/path/to/mcp/notion/server.py"],
      "env": {
        "NOTION_TOKEN": "secret_your-token-here"
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
    "notion": {
      "url": "https://notion.yourdomain.com",
      "transport": "http"
    }
  }
}
```

## Example Commands

Ask Claude:

### Database Operations
> "List all my Notion databases"
> "Show me tasks with status 'In Progress'"
> "Create a new task in my Projects database"
> "Update the task status to Done"

### Content Management
> "Read the content of my Project Planning page"
> "Add a new section to the meeting notes"
> "Create a to-do list in my goals page"

### Search & Discovery
> "Search for all pages about marketing"
> "Find my database for tracking clients"
> "Show me pages I created this week"

### Advanced Workflows
> "Create a new project in my Projects database with 3 tasks"
> "Find all tasks due this week and list them by priority"
> "Update all tasks in 'Backlog' status to include today's date"

## Property Type Reference

When creating or updating pages, use these property formats:

### Text Properties
```python
"Name": {"title": [{"text": {"content": "Page Title"}}]}
"Description": {"rich_text": [{"text": {"content": "Some text"}}]}
```

### Select & Multi-Select
```python
"Status": {"select": {"name": "In Progress"}}
"Tags": {"multi_select": [{"name": "urgent"}, {"name": "important"}]}
```

### Date
```python
"Due Date": {"date": {"start": "2025-01-15"}}
"Date Range": {"date": {"start": "2025-01-15", "end": "2025-01-20"}}
```

### Number & Checkbox
```python
"Priority": {"number": 5}
"Completed": {"checkbox": True}
```

### Person & Email
```python
"Assignee": {"people": [{"id": "user-id-here"}]}
"Email": {"email": "user@example.com"}
```

### URL & Phone
```python
"Website": {"url": "https://example.com"}
"Phone": {"phone_number": "+1234567890"}
```

## Troubleshooting

### "NOTION_TOKEN not set"
**Solution**: Set the environment variable:
```bash
export NOTION_TOKEN="secret_your-token-here"
```

### "Could not find database/page"
**Check**:
1. Is the ID correct? (32 hex characters)
2. Did you share the page/database with your integration?
3. Go to the page → ••• → Connections → Add "MCP Server"

### "Integration lacks required capabilities"
**Solution**:
1. Go to https://www.notion.so/my-integrations
2. Select your integration
3. Under Capabilities, enable: Read, Update, Insert content

### "API request failed"
**Check**:
1. Is your token valid? (starts with `secret_`)
2. Token not expired or revoked?
3. Integration still exists in workspace?

### Testing Connection Manually
```bash
curl -X GET https://api.notion.com/v1/users \
  -H "Authorization: Bearer secret_your-token-here" \
  -H "Notion-Version: 2022-06-28"
```

## Security Notes

- **Integration token = full workspace access** - protect it!
- Never commit tokens to Git
- Use environment variables
- Rotate tokens if compromised
- Share integration with specific pages only (principle of least privilege)
- Expose only via Cloudflare Zero Trust if remote

## Filter & Sort Examples

### Filter Examples

**Status equals "In Progress":**
```python
{
    "property": "Status",
    "select": {"equals": "In Progress"}
}
```

**Date is on or after today:**
```python
{
    "property": "Due Date",
    "date": {"on_or_after": "2025-01-09"}
}
```

**Checkbox is true:**
```python
{
    "property": "Completed",
    "checkbox": {"equals": True}
}
```

**Combine with AND:**
```python
{
    "and": [
        {"property": "Status", "select": {"equals": "In Progress"}},
        {"property": "Priority", "select": {"equals": "High"}}
    ]
}
```

### Sort Examples

**Sort by Due Date ascending:**
```python
[{"property": "Due Date", "direction": "ascending"}]
```

**Multiple sorts:**
```python
[
    {"property": "Priority", "direction": "descending"},
    {"property": "Due Date", "direction": "ascending"}
]
```

## Block Type Examples

### Text Blocks
```python
{
    "type": "paragraph",
    "paragraph": {
        "rich_text": [{"text": {"content": "Normal text"}}]
    }
}
```

### Headings
```python
{
    "type": "heading_1",
    "heading_1": {
        "rich_text": [{"text": {"content": "Main Heading"}}]
    }
}
```

### Lists
```python
{
    "type": "bulleted_list_item",
    "bulleted_list_item": {
        "rich_text": [{"text": {"content": "Bullet point"}}]
    }
}
```

### To-Do
```python
{
    "type": "to_do",
    "to_do": {
        "rich_text": [{"text": {"content": "Task item"}}],
        "checked": False
    }
}
```

### Code
```python
{
    "type": "code",
    "code": {
        "rich_text": [{"text": {"content": "print('Hello')"}}],
        "language": "python"
    }
}
```

## Next Steps

1. ✅ Create Notion integration at https://www.notion.so/my-integrations
2. ✅ Copy integration token
3. ✅ Share your databases/pages with the integration
4. ✅ Test locally with `python server.py`
5. ✅ Deploy to Proxmox LXC via Docker
6. ✅ Configure Cloudflare Tunnel
7. ✅ Add to Claude apps

---

**Tip**: Combine with Todoist and Google Calendar for unified task management across platforms!

**Example**: "Create a Notion task from my Todoist inbox and add it to my calendar"
