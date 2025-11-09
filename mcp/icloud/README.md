# iCloud MCP Server

Provides MCP access to your complete Apple iCloud ecosystem from any device.

## Features

### 📧 Mail (IMAP/SMTP)
- 📬 Search and read emails
- 📤 Send emails
- 📂 Browse mail folders
- 🔍 Advanced search queries

### 📅 Calendar
- 📋 List all calendars
- 📆 Get upcoming events
- ➕ Create new events
- 🎯 Full calendar management

### ✅ Reminders
- 📝 List reminders from any list
- ➕ Create new reminders
- 📧 **Create reminders from emails** (your use case!)
- ⏰ Set due dates and priorities

### 📁 iCloud Drive
- 📂 List files and folders
- 📊 View file metadata
- 🔍 Browse directory structure

### 👥 Contacts
- 🔍 Search contacts by name, email, phone
- 📇 Get contact details
- 📊 Full contact information

### 🎯 Special Feature: Email-to-Reminder Workflow
**Create calendar reminders directly from your iCloud emails!**

Example: "Create a reminder from this email to follow up next Tuesday"

## Prerequisites

1. Apple ID with iCloud account
2. **App-specific password** (REQUIRED - see setup below)
3. iCloud services enabled (Mail, Calendar, Reminders)
4. Python 3.11+

## Setup Instructions

### Step 1: Generate App-Specific Password

Apple requires app-specific passwords for third-party access (security best practice).

1. **Go to Apple ID Account Page**:
   - Visit: https://appleid.apple.com/account/manage
   - Sign in with your Apple ID

2. **Navigate to Security**:
   - Click "**Security**" section
   - Scroll to "**App-Specific Passwords**"

3. **Generate Password**:
   - Click "**Generate Password**" or "**+**"
   - Label: `MCP Server` (or any name you prefer)
   - Click "**Create**"

4. **Copy Password**:
   - You'll see a password like: `xxxx-xxxx-xxxx-xxxx`
   - **Copy this immediately** - you can't see it again!
   - Format: Remove dashes when using (e.g., `xxxxxxxxxxxxxxxx`)

5. **Save Securely**:
   - Store in password manager
   - You'll use this as `ICLOUD_PASSWORD`

### Step 2: Set Environment Variables

```bash
export ICLOUD_USERNAME="your-apple-id@icloud.com"
export ICLOUD_PASSWORD="xxxx-xxxx-xxxx-xxxx"  # App-specific password
```

**Important Notes**:
- `ICLOUD_USERNAME` = Your full Apple ID email
- `ICLOUD_PASSWORD` = App-specific password (NOT your regular Apple ID password)
- Never use your regular Apple ID password for third-party apps!

### Step 3: Enable Required iCloud Services

1. **Go to iCloud Settings**:
   - iPhone: Settings → [Your Name] → iCloud
   - Mac: System Settings → Apple ID → iCloud

2. **Enable Services**:
   - ✅ iCloud Mail
   - ✅ Calendars
   - ✅ Reminders
   - ✅ iCloud Drive
   - ✅ Contacts

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
Starting icloud v1.0.0
iCloud Username: your-apple-id@icloud.com
✓ Connected to iCloud as: your-apple-id@icloud.com
Server is ready for connections...
```

## Docker Deployment

For deployment in your Proxmox LXC:

### Build Image

```bash
docker build -t mcp-icloud:latest .
```

### Run Container

```bash
docker run -d \
  --name mcp-icloud \
  -e ICLOUD_USERNAME="your-apple-id@icloud.com" \
  -e ICLOUD_PASSWORD="xxxx-xxxx-xxxx-xxxx" \
  -p 3009:3000 \
  mcp-icloud:latest
```

### Using .env File

```bash
# Create .env file
cat > .env << EOF
ICLOUD_USERNAME=your-apple-id@icloud.com
ICLOUD_PASSWORD=xxxx-xxxx-xxxx-xxxx
EOF

# Run with env file
docker run -d \
  --name mcp-icloud \
  --env-file .env \
  -p 3009:3000 \
  mcp-icloud:latest
```

## Available Tools

### Calendar Tools

| Tool | Description | Parameters |
|------|-------------|------------|
| `list_calendars` | List all calendars | None |
| `get_calendar_events` | Get upcoming events | `calendar_title`, `days_ahead` |
| `create_calendar_event` | Create new event | `title`, `start_time`, `end_time`, `calendar`, `location`, `description` |

### Reminder Tools

| Tool | Description | Parameters |
|------|-------------|------------|
| `list_reminders` | List reminders | `list_name`, `completed` |
| `create_reminder` | Create new reminder | `title`, `list_name`, `description`, `due_date`, `priority` |
| `create_reminder_from_email` | **Create reminder from email** | `email_subject`, `email_from`, `email_date`, `list_name`, `due_date` |

### Mail Tools

| Tool | Description | Parameters |
|------|-------------|------------|
| `list_mail_folders` | List all mail folders | None |
| `search_emails` | Search emails | `folder`, `query`, `max_results` |
| `get_email` | Get full email content | `email_id`, `folder` |
| `send_email` | Send email | `to`, `subject`, `body`, `cc`, `bcc` |

### Drive Tools

| Tool | Description | Parameters |
|------|-------------|------------|
| `list_drive_files` | List Drive files | `folder_path` |

### Contact Tools

| Tool | Description | Parameters |
|------|-------------|------------|
| `search_contacts` | Search contacts | `query` |

## Common Use Cases

### 🎯 Create Reminder from Email (Your Main Use Case!)

**Scenario**: You receive an important email and want to create a reminder to follow up.

**Method 1: Manual**
```python
# First, search for the email
search_emails(folder="INBOX", query="FROM boss@company.com", max_results=5)

# Get the email details
get_email(email_id="12345", folder="INBOX")

# Create reminder from that email
create_reminder_from_email(
    email_subject="Q4 Budget Review",
    email_from="boss@company.com",
    email_date="2025-01-09",
    list_name="Work",
    due_date="2025-01-15T09:00:00"
)
```

**Method 2: Natural Language with Claude**

Just ask Claude:
> "Search my inbox for emails from boss@company.com and create a reminder for the most recent one, due next Tuesday at 9am"

Claude will:
1. Search your emails
2. Find the most recent one
3. Extract subject, sender, date
4. Create a reminder with those details
5. Set the due date you specified

The reminder will include:
- Title: "Follow up: [Email Subject]"
- Description: Full email details (from, date, subject)
- Due Date: When you want to be reminded
- Priority: Medium (5)

### Search Emails

**Search unread emails:**
```python
search_emails(folder="INBOX", query="UNSEEN", max_results=20)
```

**Search by sender:**
```python
search_emails(folder="INBOX", query='FROM "sender@example.com"', max_results=10)
```

**Search by subject:**
```python
search_emails(folder="INBOX", query='SUBJECT "meeting"', max_results=10)
```

**Search by date:**
```python
search_emails(folder="INBOX", query='SINCE 01-Jan-2025', max_results=20)
```

### Get Email Details

```python
# After searching, get full email
get_email(email_id="12345", folder="INBOX")
```

### Send Email

```python
send_email(
    to="recipient@example.com",
    subject="Follow up on meeting",
    body="Hi,\n\nJust following up on our meeting yesterday...",
    cc="manager@example.com"
)
```

### Manage Calendar

**List upcoming events:**
```python
get_calendar_events(calendar_title="Work", days_ahead=7)
```

**Create meeting:**
```python
create_calendar_event(
    title="Team Standup",
    start_time="2025-01-15T10:00:00",
    end_time="2025-01-15T10:30:00",
    calendar="Work",
    location="Zoom",
    description="Daily team sync"
)
```

### Manage Reminders

**List work reminders:**
```python
list_reminders(list_name="Work", completed=False)
```

**Create reminder with due date:**
```python
create_reminder(
    title="Submit expense report",
    list_name="Work",
    description="Q4 expenses due",
    due_date="2025-01-20T17:00:00",
    priority=9  # High priority
)
```

### Search Contacts

```python
# Search by name
search_contacts(query="John Smith")

# Search by email
search_contacts(query="john@example.com")

# Search by phone
search_contacts(query="555-1234")
```

### Browse Drive

```python
list_drive_files(folder_path="/")
```

## IMAP Search Query Examples

The `search_emails` tool supports full IMAP search syntax:

### By Status
```
ALL                 - All messages
UNSEEN             - Unread messages
SEEN               - Read messages
FLAGGED            - Starred/flagged messages
UNFLAGGED          - Not starred
ANSWERED           - Replied to
UNANSWERED         - Not replied to
DELETED            - In trash
```

### By Sender/Recipient
```
FROM "sender@example.com"
TO "recipient@example.com"
CC "person@example.com"
BCC "person@example.com"
```

### By Subject/Body
```
SUBJECT "meeting"
BODY "important"
TEXT "keyword"     - Search subject and body
```

### By Date
```
SINCE 01-Jan-2025
BEFORE 31-Dec-2024
ON 15-Jan-2025
SENTBEFORE 01-Jan-2025
SENTON 15-Jan-2025
SENTSINCE 01-Jan-2025
```

### By Size
```
LARGER 1000000     - Larger than 1MB
SMALLER 100000     - Smaller than 100KB
```

### Combine Queries
```
FROM "boss@company.com" UNSEEN
SUBJECT "urgent" SINCE 01-Jan-2025
FROM "client@example.com" UNFLAGGED UNSEEN
```

## Resources

| URI | Description |
|-----|-------------|
| `icloud://calendars` | All iCloud calendars |
| `icloud://reminders` | All reminders |
| `icloud://mail/inbox` | Inbox emails (50 most recent) |

## Usage Examples

### From Claude Desktop (Local)

Edit: `~/Library/Application Support/Claude/claude_desktop_config.json`

```json
{
  "mcpServers": {
    "icloud": {
      "command": "python",
      "args": ["/path/to/mcp/icloud/server.py"],
      "env": {
        "ICLOUD_USERNAME": "your-apple-id@icloud.com",
        "ICLOUD_PASSWORD": "xxxx-xxxx-xxxx-xxxx"
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
    "icloud": {
      "url": "https://icloud.yourdomain.com",
      "transport": "http"
    }
  }
}
```

## Example Claude Commands

### Email Management
> "Show me unread emails from the last 3 days"
> "Search for emails from my boss about the project"
> "Get the full content of the most recent email from client@example.com"
> "Send a thank you email to john@example.com"

### Email-to-Reminder Workflow
> "Find emails from sarah@company.com about the budget and create a reminder to follow up next week"
> "Create a reminder from the most recent email in my inbox, due tomorrow at 2pm"
> "Search for urgent emails and create high-priority reminders for all of them"

### Calendar
> "What's on my calendar for the next week?"
> "Create a meeting for tomorrow at 2pm titled 'Team Sync'"
> "Show me all my work calendar events for this month"

### Reminders
> "What reminders do I have in my Work list?"
> "Create a reminder to submit the report by Friday"
> "Show me all high-priority reminders"

### Contacts
> "Find the contact info for John Smith"
> "Search for contacts at @company.com domain"

### Complex Workflows
> "Search my inbox for emails about 'project alpha', create a reminder for each one, and add them to my Work calendar"
> "Find all unread emails from this week, create reminders for the important ones"

## Troubleshooting

### "Failed to login to iCloud"
**Check**:
1. Using app-specific password (NOT regular Apple ID password)?
2. Password copied correctly (remove dashes if needed)?
3. Apple ID correct?

**Test manually**:
```python
from pyicloud import PyiCloudService
api = PyiCloudService("your-apple-id@icloud.com", "your-app-password")
```

### "Two-factor authentication required"
**Solution**: You MUST use an app-specific password.
1. Go to https://appleid.apple.com/account/manage
2. Security → App-Specific Passwords
3. Generate new password
4. Use that instead of your regular password

### "IMAP connection failed"
**Check**:
1. iCloud Mail enabled in iCloud settings?
2. App-specific password is correct?
3. Using IMAP server: `imap.mail.me.com`

**Test IMAP manually**:
```bash
openssl s_client -connect imap.mail.me.com:993
```

### "Can't send email"
**Check**:
1. Using SMTP server: `smtp.mail.me.com` port 587
2. App-specific password correct?
3. From address matches your Apple ID?

### "Calendar/Reminders not working"
**Check**:
1. Services enabled in iCloud settings?
2. Wait a few minutes after enabling
3. Try logging out and back in

### "pyicloud errors"
**Update library**:
```bash
pip install --upgrade pyicloud
```

**Clear cached credentials**:
```bash
rm -rf ~/.pyicloud
```

## Security Notes

- **Never use your regular Apple ID password** - always use app-specific passwords
- App-specific passwords can be revoked anytime from appleid.apple.com
- Each app/device should have its own app-specific password
- If compromised, revoke that password immediately
- Passwords are stored in environment variables (never in code)
- Never commit credentials to Git (already in .gitignore)
- Use Cloudflare Zero Trust for remote access

## Priority Levels for Reminders

| Priority | Value | Description |
|----------|-------|-------------|
| None | 0 | No priority |
| Low | 1 | Low priority |
| Medium | 5 | Medium priority (default) |
| High | 9 | High priority |

## Folder Names

Common iCloud Mail folder names:
- `INBOX` - Inbox
- `Sent Messages` - Sent mail
- `Deleted Messages` - Trash
- `Junk` - Spam
- `Archive` - Archived messages
- `Drafts` - Draft messages

List all available folders:
```python
list_mail_folders()
```

## Limitations

- **Rate Limits**: Apple may rate-limit API requests
- **2FA**: Must use app-specific passwords
- **Regional**: Some features may vary by region
- **Mail Protocol**: Uses IMAP/SMTP (standard protocols)
- **Attachments**: Currently read-only (download not implemented)

## Advanced Features

### Email Automation Workflows

**1. Auto-create reminders for flagged emails:**
> "Search for flagged emails and create reminders for each one due tomorrow"

**2. Calendar events from meeting emails:**
> "Find emails with 'meeting' in subject and create calendar events"

**3. Daily digest:**
> "Summarize unread emails from today and create a single reminder to review them"

### Multi-Service Integration

Combine with other MCP connectors:

**Email → Todoist:**
> "Find urgent emails and create Todoist tasks for each"

**Email → Slack:**
> "Forward the most recent email from my boss to #team-updates in Slack"

**Calendar → Notion:**
> "Copy this week's calendar events to my Notion planning database"

## Next Steps

1. ✅ Generate app-specific password
2. ✅ Set environment variables
3. ✅ Enable iCloud services
4. ✅ Test locally with `python server.py`
5. ✅ Deploy to Proxmox LXC via Docker
6. ✅ Configure Cloudflare Tunnel
7. ✅ Add to Claude apps
8. 🎯 **Create your first email-to-reminder!**

---

**Perfect for**: Managing your Apple ecosystem from Claude on any device!

**Use Case**: "Create calendar reminders from emails" - Built specifically for your workflow! 📧 → ✅

**Try it**: "Find my most recent email and create a reminder to follow up tomorrow at 9am"
