# GitHub MCP Server

Provides MCP access to GitHub repositories, issues, pull requests, and more from any device.

## Features

### Repositories
- 📚 List and search repositories
- ℹ️ Get repository details
- 📁 Browse repository files and directories
- 📝 Read file contents

### Issues
- 🐛 Create, update, and close issues
- 💬 Add comments to issues
- 🏷️ Manage labels
- 🔍 Search issues

### Pull Requests
- 🔀 List, create, and merge pull requests
- 👀 Review code changes
- 💬 Comment on PRs
- ✅ Check merge status

### Code & Commits
- 📜 View commit history
- 🌿 List branches
- 🔍 Search code across repositories
- 📊 View repository statistics

## Prerequisites

1. GitHub account
2. Personal Access Token
3. Python 3.11+

## Setup Instructions

### Step 1: Create Personal Access Token

1. **Go to GitHub Settings**:
   - Click your profile → **Settings**
   - Scroll to **Developer settings** (bottom left)
   - Click **Personal access tokens** → **Tokens (classic)**

2. **Generate new token**:
   - Click "**Generate new token (classic)**"
   - Note: `MCP Server`
   - Expiration: Choose your preference (90 days recommended)

3. **Select scopes**:
   - ✅ `repo` - Full repository access
   - ✅ `read:user` - Read user profile
   - ✅ `read:org` - Read organization data (if needed)
   - ✅ `workflow` - Update GitHub Actions workflows (optional)

4. **Generate and copy**:
   - Click "**Generate token**"
   - **Copy the token immediately!** (you won't see it again)
   - Format: `ghp_xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx`

### Step 2: Set Environment Variable

```bash
export GITHUB_TOKEN="ghp_your_token_here"
```

### Step 3: Install Dependencies

```bash
pip install -r requirements.txt
```

### Step 4: Test Locally

```bash
python server.py
```

You should see:
```
Starting github v1.0.0
✓ Connected to GitHub as: yourusername
✓ Name: Your Name
✓ Public repos: 42
Server is ready for connections...
```

## Docker Deployment

For deployment in your Proxmox LXC:

### Build Image

```bash
docker build -t mcp-github:latest .
```

### Run Container

```bash
docker run -d \
  --name mcp-github \
  -e GITHUB_TOKEN="ghp_your_token_here" \
  -p 3001:3000 \
  mcp-github:latest
```

### Using .env File

```bash
# Create .env file
echo "GITHUB_TOKEN=ghp_your_token_here" > .env

# Run with env file
docker run -d \
  --name mcp-github \
  --env-file .env \
  -p 3001:3000 \
  mcp-github:latest
```

## Available Tools

### Repository Management

| Tool | Description | Parameters |
|------|-------------|------------|
| `list_repos` | List repositories | `username`, `max_results` |
| `get_repo_info` | Get repo details | `repo_name` |
| `search_repos` | Search repositories | `query`, `max_results` |
| `list_directory` | List directory contents | `repo_name`, `path`, `branch` |
| `get_file_contents` | Read file | `repo_name`, `path`, `branch` |

### Issue Management

| Tool | Description | Parameters |
|------|-------------|------------|
| `list_issues` | List issues | `repo_name`, `state`, `max_results` |
| `create_issue` | Create new issue | `repo_name`, `title`, `body`, `labels` |
| `update_issue` | Update issue | `repo_name`, `issue_number`, `state`, `title`, `body`, `labels` |
| `add_issue_comment` | Comment on issue | `repo_name`, `issue_number`, `body` |
| `search_issues` | Search issues/PRs | `query`, `repo_name`, `max_results` |

### Pull Requests

| Tool | Description | Parameters |
|------|-------------|------------|
| `list_pull_requests` | List PRs | `repo_name`, `state`, `max_results` |
| `create_pull_request` | Create PR | `repo_name`, `title`, `head`, `base`, `body` |
| `merge_pull_request` | Merge PR | `repo_name`, `pr_number`, `commit_message` |

### Code & Commits

| Tool | Description | Parameters |
|------|-------------|------------|
| `list_commits` | List commits | `repo_name`, `branch`, `max_results` |
| `list_branches` | List branches | `repo_name` |
| `search_code` | Search code | `query`, `repo_name`, `max_results` |

## Repository Name Format

Use `owner/repo` format for all repository operations.

**Examples**:
- `torvalds/linux`
- `facebook/react`
- `your-username/your-repo`

## Resources

| URI | Description |
|-----|-------------|
| `github://repos/my` | Your repositories |
| `github://issues/my` | Your issues across all repos |
| `github://prs/my` | Your pull requests |

## Usage Examples

### From Claude Desktop (Local)

Edit: `~/Library/Application Support/Claude/claude_desktop_config.json`

```json
{
  "mcpServers": {
    "github": {
      "command": "python",
      "args": ["/path/to/mcp/github/server.py"],
      "env": {
        "GITHUB_TOKEN": "ghp_your_token_here"
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
    "github": {
      "url": "https://github-mcp.yourdomain.com",
      "transport": "http"
    }
  }
}
```

## Example Commands

Ask Claude:

### Repository Management
> "List my GitHub repositories"
> "Show me details about the MCP_CREATOR repo"
> "Search for repositories about machine learning"
> "Show me the contents of the src directory in my project"
> "Read the README file from tchiro88/MCP_CREATOR"

### Issues
> "List open issues in my project"
> "Create an issue in MCP_CREATOR titled 'Add Slack integration' with label 'enhancement'"
> "Close issue #5 in my repo"
> "Add a comment to issue #10 explaining the solution"
> "Search for issues about authentication"

### Pull Requests
> "List open pull requests in my repo"
> "Create a PR from feature-branch to main with title 'Add new feature'"
> "Merge pull request #15"
> "Show me all my pending PRs across all repos"

### Code & Commits
> "Show me recent commits in the main branch"
> "List all branches in my repository"
> "Search for code containing 'authentication' in my repo"
> "What are the latest commits by user tchiro88?"

## Search Query Syntax

### Repository Search
- `language:python` - Python repositories
- `stars:>1000` - Repos with over 1000 stars
- `topic:machine-learning` - By topic
- `user:username` - User's repositories

### Code Search
- `filename:config.json` - Specific filename
- `extension:py` - By file extension
- `language:javascript` - By language
- `org:github` - In organization

### Issue Search
- `is:open` - Open issues
- `is:closed` - Closed issues
- `label:bug` - By label
- `author:username` - By author
- `state:open assignee:me` - My assigned issues

## Troubleshooting

### "GITHUB_TOKEN not set"
**Solution**: Set the environment variable:
```bash
export GITHUB_TOKEN="ghp_your_token_here"
```

### "Bad credentials"
**Check**:
- Token hasn't expired
- Token has correct scopes
- Token hasn't been revoked

**Test manually**:
```bash
curl -H "Authorization: token ghp_your_token" https://api.github.com/user
```

### "Repository not found"
**Check**:
- Repository name format is correct (`owner/repo`)
- You have access to the repository
- Repository exists and isn't deleted

### Rate Limit Errors
GitHub API has rate limits:
- **Authenticated**: 5,000 requests/hour
- **Search**: 30 requests/minute

**Check your rate limit**:
```bash
curl -H "Authorization: token ghp_your_token" https://api.github.com/rate_limit
```

## Security Notes

- **Personal Access Token = full GitHub access** - protect it!
- Never commit tokens to Git
- Use environment variables
- Rotate tokens regularly (every 90 days recommended)
- Use fine-grained tokens when possible (beta feature)
- Limit scopes to what you actually need

## Advanced Usage

### Working with Organizations

```python
# List organization repos
list_repos(username="your-org-name")

# Create issue in org repo
create_issue(repo_name="org-name/repo-name", title="Issue", body="Description")
```

### Branch Operations

```python
# List branches
list_branches(repo_name="owner/repo")

# Get commits from specific branch
list_commits(repo_name="owner/repo", branch="develop")

# Read file from specific branch
get_file_contents(repo_name="owner/repo", path="README.md", branch="develop")
```

### Complex Searches

```python
# Find Python ML repos with >100 stars
search_repos(query="language:python topic:machine-learning stars:>100")

# Search code in specific repo
search_code(query="authentication", repo_name="owner/repo")

# Find all open bugs assigned to you
search_issues(query="is:open label:bug assignee:@me")
```

## API Rate Limits

The server doesn't implement caching or rate limiting. Be mindful of:

- 5,000 requests/hour for authenticated requests
- 30 requests/minute for search endpoints
- Check remaining quota: `gh.rate_limiting`

## Next Steps

1. ✅ Create Personal Access Token on GitHub
2. ✅ Test locally with `python server.py`
3. ✅ Deploy to Proxmox LXC via Docker
4. ✅ Configure Cloudflare Tunnel
5. ✅ Add to Claude apps

---

**Tip**: Combine with Todoist to create GitHub issues from tasks, or with Slack to get PR notifications!
