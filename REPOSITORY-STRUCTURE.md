# MCP_CREATOR - Repository Structure

```
MCP_CREATOR/
├── README.md
├── CREDENTIALS-GUIDE.md
├── PRODUCTION-READY.md
│
├── deployment/
│   ├── .env.minimal.example          # Environment variables for all 7 MCPs
│   ├── docker-compose.minimal.yml    # Docker Compose for all 7 services
│   ├── cloudflared-minimal.example.yml  # Cloudflare Tunnel routes
│   ├── DEPLOYMENT-COMPLETE.md        # Complete deployment guide
│   └── PROXMOX-SETUP.md             # Proxmox LXC setup guide
│
└── mcp/                              # MCP Connectors (7 total)
    │
    ├── github/                       # GitHub MCP (Port 3001)
    │   ├── server.py                 # 17 tools for repos, issues, PRs
    │   ├── Dockerfile
    │   ├── requirements.txt
    │   └── README.md
    │
    ├── google/                       # Google Services MCP (Port 3004)
    │   ├── server.py                 # 12 tools for Gmail, Drive, Calendar, Photos
    │   ├── Dockerfile
    │   ├── requirements.txt
    │   └── README.md
    │
    ├── todoist/                      # Todoist MCP (Port 3005)
    │   ├── server.py                 # 9 tools for tasks and projects
    │   ├── Dockerfile
    │   ├── requirements.txt
    │   └── README.md
    │
    ├── homeassistant/                # Home Assistant MCP (Port 3006)
    │   ├── server.py                 # 12 tools for smart home control
    │   ├── Dockerfile
    │   ├── requirements.txt
    │   └── README.md
    │
    ├── notion/                       # Notion MCP (Port 3007)
    │   ├── server.py                 # 9 tools for databases and pages
    │   ├── Dockerfile
    │   ├── requirements.txt
    │   └── README.md
    │
    ├── slack/                        # Slack MCP (Port 3008)
    │   ├── server.py                 # 12 tools for team messaging
    │   ├── Dockerfile
    │   ├── requirements.txt
    │   └── README.md
    │
    └── icloud/                       # iCloud MCP (Port 3009) ⭐ NEW!
        ├── server.py                 # 14 tools for Apple ecosystem
        ├── Dockerfile                #   - Mail (IMAP/SMTP)
        ├── requirements.txt          #   - Calendar
        └── README.md                 #   - Reminders (including email→reminder!)
                                      #   - Drive
                                      #   - Contacts

```

## File Counts

```
Total MCP Connectors: 7
Total Files: 28 (4 files per connector)

Each connector includes:
├── server.py          # MCP server implementation
├── Dockerfile         # Docker container configuration
├── requirements.txt   # Python dependencies
└── README.md         # Setup and usage guide
```

## Port Mapping

```
3001 → GitHub MCP
3004 → Google MCP
3005 → Todoist MCP
3006 → Home Assistant MCP
3007 → Notion MCP
3008 → Slack MCP
3009 → iCloud MCP ⭐ NEWEST
```

## Current Branch Status

```
Branch: claude/explore-repo-011CUuxYzJXKjoEcgWWz4rz6
Status: All changes committed and pushed
Last Commit: c36ecc7 - Add iCloud MCP connector for Apple ecosystem access
```

## iCloud Connector Files

```
mcp/icloud/
├── server.py          (683 lines) - Complete implementation
│   ├── Mail tools (5):
│   │   ├── search_emails
│   │   ├── get_email
│   │   ├── send_email
│   │   └── list_mail_folders
│   │
│   ├── Calendar tools (3):
│   │   ├── list_calendars
│   │   ├── get_calendar_events
│   │   └── create_calendar_event
│   │
│   ├── Reminder tools (3):
│   │   ├── list_reminders
│   │   ├── create_reminder
│   │   └── create_reminder_from_email ⭐
│   │
│   ├── Drive tools (1):
│   │   └── list_drive_files
│   │
│   └── Contact tools (1):
│       └── search_contacts
│
├── Dockerfile         - Docker container setup
├── requirements.txt   - Dependencies: mcp>=0.9.0, pyicloud>=1.0.0
└── README.md         - Complete setup guide with app-specific password instructions
```

## Verification Commands

Check files exist:
```bash
ls -la mcp/icloud/
# Expected output:
# server.py
# Dockerfile
# requirements.txt
# README.md
```

View iCloud server code:
```bash
wc -l mcp/icloud/server.py
# Expected: 683 lines
```

Check git status:
```bash
git log --oneline --all | grep icloud
# Expected: c36ecc7 Add iCloud MCP connector for Apple ecosystem access
```

Check pushed to remote:
```bash
git ls-remote origin claude/explore-repo-011CUuxYzJXKjoEcgWWz4rz6
# Should show the commit with iCloud
```

## Why You Might Not See It On GitHub

If you're looking at the **main** branch on GitHub, the iCloud connector won't be there yet because:

1. ✅ Code is written and committed
2. ✅ Code is pushed to: `claude/explore-repo-011CUuxYzJXKjoEcgWWz4rz6`
3. ❌ Not yet merged to `main` branch

**To see it on GitHub:**
- Go to: https://github.com/tchiro88/MCP_CREATOR
- Switch branch from `main` to `claude/explore-repo-011CUuxYzJXKjoEcgWWz4rz6`
- Or look at the Pull Requests tab

**To merge to main:**
- Create a Pull Request from `claude/explore-repo-011CUuxYzJXKjoEcgWWz4rz6` → `main`
- Review and merge via GitHub web interface

All files are safely committed and available on the feature branch! 🎯
