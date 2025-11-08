#!/usr/bin/env python3
"""
GitHub MCP Server
Provides access to GitHub repositories, issues, pull requests, and more

Features:
- Repository management (list, create, search)
- Issue tracking (create, update, search, comment)
- Pull requests (create, review, merge)
- File operations (read, create, update)
- Commit and branch management
- Search across GitHub
"""

import os
import json
import asyncio
from typing import Any, Optional
from mcp.server import Server
from mcp.server.stdio import stdio_server

# GitHub API import
try:
    from github import Github, GithubException
except ImportError:
    print("ERROR: PyGithub library not installed!")
    print("Install with: pip install PyGithub")
    exit(1)

# ============================================================================
# Configuration
# ============================================================================

SERVER_NAME = "github"
SERVER_VERSION = "1.0.0"

# Get GitHub token from environment
GITHUB_TOKEN = os.getenv('GITHUB_TOKEN')
if not GITHUB_TOKEN:
    print("ERROR: GITHUB_TOKEN environment variable not set!")
    print("Create a token at: https://github.com/settings/tokens")
    print("Scopes needed: repo, read:user, read:org")
    exit(1)

# Initialize GitHub client
try:
    gh = Github(GITHUB_TOKEN)
    user = gh.get_user()
except Exception as e:
    print(f"ERROR: Failed to connect to GitHub: {e}")
    exit(1)

# ============================================================================
# Repository Functions
# ============================================================================

def list_repos(username: Optional[str] = None, max_results: int = 20) -> list[dict]:
    """List repositories for a user (default: authenticated user)"""
    try:
        if username:
            target_user = gh.get_user(username)
        else:
            target_user = user

        repos = target_user.get_repos(sort='updated')[:max_results]

        return [{
            'name': repo.name,
            'full_name': repo.full_name,
            'description': repo.description or '',
            'private': repo.private,
            'url': repo.html_url,
            'stars': repo.stargazers_count,
            'forks': repo.forks_count,
            'language': repo.language,
            'updated_at': repo.updated_at.isoformat() if repo.updated_at else None
        } for repo in repos]

    except GithubException as e:
        return [{'error': f'GitHub API error: {e}'}]

def get_repo_info(repo_name: str) -> dict:
    """Get detailed information about a repository"""
    try:
        repo = gh.get_repo(repo_name)

        return {
            'name': repo.name,
            'full_name': repo.full_name,
            'description': repo.description or '',
            'private': repo.private,
            'url': repo.html_url,
            'clone_url': repo.clone_url,
            'stars': repo.stargazers_count,
            'watchers': repo.watchers_count,
            'forks': repo.forks_count,
            'open_issues': repo.open_issues_count,
            'language': repo.language,
            'default_branch': repo.default_branch,
            'created_at': repo.created_at.isoformat(),
            'updated_at': repo.updated_at.isoformat() if repo.updated_at else None,
            'topics': repo.get_topics()
        }

    except GithubException as e:
        return {'error': f'GitHub API error: {e}'}

def search_repos(query: str, max_results: int = 10) -> list[dict]:
    """Search for repositories"""
    try:
        repos = gh.search_repositories(query=query)[:max_results]

        return [{
            'name': repo.name,
            'full_name': repo.full_name,
            'description': repo.description or '',
            'url': repo.html_url,
            'stars': repo.stargazers_count,
            'language': repo.language
        } for repo in repos]

    except GithubException as e:
        return [{'error': f'GitHub API error: {e}'}]

# ============================================================================
# Issue Functions
# ============================================================================

def list_issues(repo_name: str, state: str = 'open', max_results: int = 20) -> list[dict]:
    """List issues in a repository"""
    try:
        repo = gh.get_repo(repo_name)
        issues = repo.get_issues(state=state)[:max_results]

        return [{
            'number': issue.number,
            'title': issue.title,
            'state': issue.state,
            'user': issue.user.login,
            'labels': [label.name for label in issue.labels],
            'created_at': issue.created_at.isoformat(),
            'updated_at': issue.updated_at.isoformat() if issue.updated_at else None,
            'url': issue.html_url,
            'comments': issue.comments
        } for issue in issues]

    except GithubException as e:
        return [{'error': f'GitHub API error: {e}'}]

def create_issue(repo_name: str, title: str, body: str = '',
                labels: Optional[list[str]] = None) -> dict:
    """Create a new issue"""
    try:
        repo = gh.get_repo(repo_name)
        issue = repo.create_issue(title=title, body=body, labels=labels or [])

        return {
            'success': True,
            'number': issue.number,
            'url': issue.html_url,
            'title': issue.title
        }

    except GithubException as e:
        return {'error': f'Failed to create issue: {e}'}

def update_issue(repo_name: str, issue_number: int, state: Optional[str] = None,
                title: Optional[str] = None, body: Optional[str] = None,
                labels: Optional[list[str]] = None) -> dict:
    """Update an existing issue"""
    try:
        repo = gh.get_repo(repo_name)
        issue = repo.get_issue(number=issue_number)

        if state:
            issue.edit(state=state)
        if title:
            issue.edit(title=title)
        if body is not None:
            issue.edit(body=body)
        if labels is not None:
            issue.edit(labels=labels)

        return {
            'success': True,
            'number': issue.number,
            'url': issue.html_url
        }

    except GithubException as e:
        return {'error': f'Failed to update issue: {e}'}

def add_issue_comment(repo_name: str, issue_number: int, body: str) -> dict:
    """Add a comment to an issue"""
    try:
        repo = gh.get_repo(repo_name)
        issue = repo.get_issue(number=issue_number)
        comment = issue.create_comment(body=body)

        return {
            'success': True,
            'comment_id': comment.id,
            'url': comment.html_url
        }

    except GithubException as e:
        return {'error': f'Failed to add comment: {e}'}

# ============================================================================
# Pull Request Functions
# ============================================================================

def list_pull_requests(repo_name: str, state: str = 'open',
                      max_results: int = 20) -> list[dict]:
    """List pull requests in a repository"""
    try:
        repo = gh.get_repo(repo_name)
        prs = repo.get_pulls(state=state)[:max_results]

        return [{
            'number': pr.number,
            'title': pr.title,
            'state': pr.state,
            'user': pr.user.login,
            'head': pr.head.ref,
            'base': pr.base.ref,
            'created_at': pr.created_at.isoformat(),
            'updated_at': pr.updated_at.isoformat() if pr.updated_at else None,
            'url': pr.html_url,
            'mergeable': pr.mergeable,
            'merged': pr.merged,
            'comments': pr.comments,
            'review_comments': pr.review_comments
        } for pr in prs]

    except GithubException as e:
        return [{'error': f'GitHub API error: {e}'}]

def create_pull_request(repo_name: str, title: str, head: str, base: str,
                       body: str = '') -> dict:
    """Create a new pull request"""
    try:
        repo = gh.get_repo(repo_name)
        pr = repo.create_pull(title=title, body=body, head=head, base=base)

        return {
            'success': True,
            'number': pr.number,
            'url': pr.html_url,
            'title': pr.title
        }

    except GithubException as e:
        return {'error': f'Failed to create PR: {e}'}

def merge_pull_request(repo_name: str, pr_number: int, commit_message: Optional[str] = None) -> dict:
    """Merge a pull request"""
    try:
        repo = gh.get_repo(repo_name)
        pr = repo.get_pull(number=pr_number)

        result = pr.merge(commit_message=commit_message)

        return {
            'success': result.merged,
            'message': result.message,
            'sha': result.sha if result.merged else None
        }

    except GithubException as e:
        return {'error': f'Failed to merge PR: {e}'}

# ============================================================================
# File Operations
# ============================================================================

def get_file_contents(repo_name: str, path: str, branch: Optional[str] = None) -> dict:
    """Get contents of a file from a repository"""
    try:
        repo = gh.get_repo(repo_name)
        ref = branch or repo.default_branch

        contents = repo.get_contents(path, ref=ref)

        if contents.encoding == 'base64':
            import base64
            content = base64.b64decode(contents.content).decode('utf-8')
        else:
            content = contents.content

        return {
            'path': contents.path,
            'name': contents.name,
            'size': contents.size,
            'sha': contents.sha,
            'url': contents.html_url,
            'content': content[:5000]  # Limit to first 5000 chars
        }

    except GithubException as e:
        return {'error': f'Failed to get file: {e}'}

def list_directory(repo_name: str, path: str = '', branch: Optional[str] = None) -> list[dict]:
    """List contents of a directory"""
    try:
        repo = gh.get_repo(repo_name)
        ref = branch or repo.default_branch

        contents = repo.get_contents(path, ref=ref)

        if not isinstance(contents, list):
            contents = [contents]

        return [{
            'name': item.name,
            'path': item.path,
            'type': item.type,
            'size': item.size if item.type == 'file' else 0,
            'url': item.html_url
        } for item in contents]

    except GithubException as e:
        return [{'error': f'Failed to list directory: {e}'}]

# ============================================================================
# Commit & Branch Functions
# ============================================================================

def list_commits(repo_name: str, branch: Optional[str] = None,
                max_results: int = 20) -> list[dict]:
    """List recent commits"""
    try:
        repo = gh.get_repo(repo_name)
        sha = branch or repo.default_branch

        commits = repo.get_commits(sha=sha)[:max_results]

        return [{
            'sha': commit.sha[:7],
            'message': commit.commit.message.split('\n')[0],  # First line only
            'author': commit.commit.author.name,
            'date': commit.commit.author.date.isoformat(),
            'url': commit.html_url
        } for commit in commits]

    except GithubException as e:
        return [{'error': f'GitHub API error: {e}'}]

def list_branches(repo_name: str) -> list[dict]:
    """List all branches"""
    try:
        repo = gh.get_repo(repo_name)
        branches = repo.get_branches()

        return [{
            'name': branch.name,
            'protected': branch.protected,
            'commit_sha': branch.commit.sha[:7]
        } for branch in branches]

    except GithubException as e:
        return [{'error': f'GitHub API error: {e}'}]

# ============================================================================
# Search Functions
# ============================================================================

def search_code(query: str, repo_name: Optional[str] = None,
               max_results: int = 10) -> list[dict]:
    """Search for code across GitHub"""
    try:
        full_query = f"{query} repo:{repo_name}" if repo_name else query
        results = gh.search_code(query=full_query)[:max_results]

        return [{
            'name': code.name,
            'path': code.path,
            'repository': code.repository.full_name,
            'url': code.html_url
        } for code in results]

    except GithubException as e:
        return [{'error': f'GitHub API error: {e}'}]

def search_issues(query: str, repo_name: Optional[str] = None,
                 max_results: int = 10) -> list[dict]:
    """Search for issues and pull requests"""
    try:
        full_query = f"{query} repo:{repo_name}" if repo_name else query
        results = gh.search_issues(query=full_query)[:max_results]

        return [{
            'number': issue.number,
            'title': issue.title,
            'state': issue.state,
            'repository': issue.repository.full_name,
            'url': issue.html_url,
            'is_pr': issue.pull_request is not None
        } for issue in results]

    except GithubException as e:
        return [{'error': f'GitHub API error: {e}'}]

# ============================================================================
# MCP Server
# ============================================================================

app = Server(SERVER_NAME)

@app.list_resources()
async def list_resources() -> list[dict[str, Any]]:
    """List available GitHub resources"""
    return [
        {
            "uri": "github://repos/my",
            "name": "My Repositories",
            "description": "Repositories for authenticated user",
            "mimeType": "application/json"
        },
        {
            "uri": "github://issues/my",
            "name": "My Issues",
            "description": "Issues assigned to authenticated user",
            "mimeType": "application/json"
        },
        {
            "uri": "github://prs/my",
            "name": "My Pull Requests",
            "description": "Pull requests created by authenticated user",
            "mimeType": "application/json"
        }
    ]

@app.read_resource()
async def read_resource(uri: str) -> str:
    """Read a GitHub resource"""
    if uri == "github://repos/my":
        repos = list_repos()
        return json.dumps(repos, indent=2)

    elif uri == "github://issues/my":
        # Get issues across all user's repos
        issues = []
        for repo in user.get_repos()[:10]:  # Limit to first 10 repos
            repo_issues = list_issues(repo.full_name, max_results=5)
            issues.extend(repo_issues)
        return json.dumps(issues[:20], indent=2)

    elif uri == "github://prs/my":
        # Get PRs across all user's repos
        prs = []
        for repo in user.get_repos()[:10]:
            repo_prs = list_pull_requests(repo.full_name, max_results=5)
            prs.extend(repo_prs)
        return json.dumps(prs[:20], indent=2)

    raise ValueError(f"Unknown resource: {uri}")

@app.list_tools()
async def list_tools() -> list[dict[str, Any]]:
    """List available GitHub tools"""
    return [
        # Repository tools
        {
            "name": "list_repos",
            "description": "List repositories for a user",
            "inputSchema": {
                "type": "object",
                "properties": {
                    "username": {
                        "type": "string",
                        "description": "GitHub username (optional, defaults to authenticated user)"
                    },
                    "max_results": {
                        "type": "number",
                        "description": "Maximum number of repositories (default: 20)",
                        "default": 20
                    }
                },
                "required": []
            }
        },
        {
            "name": "get_repo_info",
            "description": "Get detailed information about a repository",
            "inputSchema": {
                "type": "object",
                "properties": {
                    "repo_name": {
                        "type": "string",
                        "description": "Repository name (format: owner/repo)"
                    }
                },
                "required": ["repo_name"]
            }
        },
        {
            "name": "search_repos",
            "description": "Search for repositories on GitHub",
            "inputSchema": {
                "type": "object",
                "properties": {
                    "query": {
                        "type": "string",
                        "description": "Search query"
                    },
                    "max_results": {
                        "type": "number",
                        "description": "Maximum results (default: 10)",
                        "default": 10
                    }
                },
                "required": ["query"]
            }
        },
        # Issue tools
        {
            "name": "list_issues",
            "description": "List issues in a repository",
            "inputSchema": {
                "type": "object",
                "properties": {
                    "repo_name": {
                        "type": "string",
                        "description": "Repository name (owner/repo)"
                    },
                    "state": {
                        "type": "string",
                        "description": "Issue state: 'open', 'closed', or 'all' (default: 'open')",
                        "default": "open"
                    },
                    "max_results": {
                        "type": "number",
                        "description": "Maximum results (default: 20)",
                        "default": 20
                    }
                },
                "required": ["repo_name"]
            }
        },
        {
            "name": "create_issue",
            "description": "Create a new issue",
            "inputSchema": {
                "type": "object",
                "properties": {
                    "repo_name": {
                        "type": "string",
                        "description": "Repository name (owner/repo)"
                    },
                    "title": {
                        "type": "string",
                        "description": "Issue title"
                    },
                    "body": {
                        "type": "string",
                        "description": "Issue description (optional)"
                    },
                    "labels": {
                        "type": "array",
                        "items": {"type": "string"},
                        "description": "Labels to add (optional)"
                    }
                },
                "required": ["repo_name", "title"]
            }
        },
        {
            "name": "update_issue",
            "description": "Update an existing issue",
            "inputSchema": {
                "type": "object",
                "properties": {
                    "repo_name": {
                        "type": "string",
                        "description": "Repository name (owner/repo)"
                    },
                    "issue_number": {
                        "type": "number",
                        "description": "Issue number"
                    },
                    "state": {
                        "type": "string",
                        "description": "New state: 'open' or 'closed' (optional)"
                    },
                    "title": {
                        "type": "string",
                        "description": "New title (optional)"
                    },
                    "body": {
                        "type": "string",
                        "description": "New body (optional)"
                    },
                    "labels": {
                        "type": "array",
                        "items": {"type": "string"},
                        "description": "New labels (optional)"
                    }
                },
                "required": ["repo_name", "issue_number"]
            }
        },
        {
            "name": "add_issue_comment",
            "description": "Add a comment to an issue",
            "inputSchema": {
                "type": "object",
                "properties": {
                    "repo_name": {
                        "type": "string",
                        "description": "Repository name (owner/repo)"
                    },
                    "issue_number": {
                        "type": "number",
                        "description": "Issue number"
                    },
                    "body": {
                        "type": "string",
                        "description": "Comment text"
                    }
                },
                "required": ["repo_name", "issue_number", "body"]
            }
        },
        # Pull Request tools
        {
            "name": "list_pull_requests",
            "description": "List pull requests in a repository",
            "inputSchema": {
                "type": "object",
                "properties": {
                    "repo_name": {
                        "type": "string",
                        "description": "Repository name (owner/repo)"
                    },
                    "state": {
                        "type": "string",
                        "description": "PR state: 'open', 'closed', or 'all' (default: 'open')",
                        "default": "open"
                    },
                    "max_results": {
                        "type": "number",
                        "description": "Maximum results (default: 20)",
                        "default": 20
                    }
                },
                "required": ["repo_name"]
            }
        },
        {
            "name": "create_pull_request",
            "description": "Create a new pull request",
            "inputSchema": {
                "type": "object",
                "properties": {
                    "repo_name": {
                        "type": "string",
                        "description": "Repository name (owner/repo)"
                    },
                    "title": {
                        "type": "string",
                        "description": "PR title"
                    },
                    "head": {
                        "type": "string",
                        "description": "Head branch (the branch with changes)"
                    },
                    "base": {
                        "type": "string",
                        "description": "Base branch (usually 'main' or 'master')"
                    },
                    "body": {
                        "type": "string",
                        "description": "PR description (optional)"
                    }
                },
                "required": ["repo_name", "title", "head", "base"]
            }
        },
        {
            "name": "merge_pull_request",
            "description": "Merge a pull request",
            "inputSchema": {
                "type": "object",
                "properties": {
                    "repo_name": {
                        "type": "string",
                        "description": "Repository name (owner/repo)"
                    },
                    "pr_number": {
                        "type": "number",
                        "description": "Pull request number"
                    },
                    "commit_message": {
                        "type": "string",
                        "description": "Merge commit message (optional)"
                    }
                },
                "required": ["repo_name", "pr_number"]
            }
        },
        # File operations
        {
            "name": "get_file_contents",
            "description": "Get contents of a file from a repository",
            "inputSchema": {
                "type": "object",
                "properties": {
                    "repo_name": {
                        "type": "string",
                        "description": "Repository name (owner/repo)"
                    },
                    "path": {
                        "type": "string",
                        "description": "File path in repository"
                    },
                    "branch": {
                        "type": "string",
                        "description": "Branch name (optional, defaults to default branch)"
                    }
                },
                "required": ["repo_name", "path"]
            }
        },
        {
            "name": "list_directory",
            "description": "List contents of a directory in a repository",
            "inputSchema": {
                "type": "object",
                "properties": {
                    "repo_name": {
                        "type": "string",
                        "description": "Repository name (owner/repo)"
                    },
                    "path": {
                        "type": "string",
                        "description": "Directory path (empty for root)",
                        "default": ""
                    },
                    "branch": {
                        "type": "string",
                        "description": "Branch name (optional)"
                    }
                },
                "required": ["repo_name"]
            }
        },
        # Commit & branch tools
        {
            "name": "list_commits",
            "description": "List recent commits in a repository",
            "inputSchema": {
                "type": "object",
                "properties": {
                    "repo_name": {
                        "type": "string",
                        "description": "Repository name (owner/repo)"
                    },
                    "branch": {
                        "type": "string",
                        "description": "Branch name (optional)"
                    },
                    "max_results": {
                        "type": "number",
                        "description": "Maximum results (default: 20)",
                        "default": 20
                    }
                },
                "required": ["repo_name"]
            }
        },
        {
            "name": "list_branches",
            "description": "List all branches in a repository",
            "inputSchema": {
                "type": "object",
                "properties": {
                    "repo_name": {
                        "type": "string",
                        "description": "Repository name (owner/repo)"
                    }
                },
                "required": ["repo_name"]
            }
        },
        # Search tools
        {
            "name": "search_code",
            "description": "Search for code across GitHub",
            "inputSchema": {
                "type": "object",
                "properties": {
                    "query": {
                        "type": "string",
                        "description": "Search query"
                    },
                    "repo_name": {
                        "type": "string",
                        "description": "Limit to specific repository (optional)"
                    },
                    "max_results": {
                        "type": "number",
                        "description": "Maximum results (default: 10)",
                        "default": 10
                    }
                },
                "required": ["query"]
            }
        },
        {
            "name": "search_issues",
            "description": "Search for issues and pull requests",
            "inputSchema": {
                "type": "object",
                "properties": {
                    "query": {
                        "type": "string",
                        "description": "Search query"
                    },
                    "repo_name": {
                        "type": "string",
                        "description": "Limit to specific repository (optional)"
                    },
                    "max_results": {
                        "type": "number",
                        "description": "Maximum results (default: 10)",
                        "default": 10
                    }
                },
                "required": ["query"]
            }
        }
    ]

@app.call_tool()
async def call_tool(name: str, arguments: dict) -> list[dict[str, Any]]:
    """Execute a GitHub tool"""

    # Repository tools
    if name == "list_repos":
        result = list_repos(
            username=arguments.get("username"),
            max_results=arguments.get("max_results", 20)
        )
        return [{"type": "text", "text": json.dumps(result, indent=2)}]

    elif name == "get_repo_info":
        result = get_repo_info(arguments["repo_name"])
        return [{"type": "text", "text": json.dumps(result, indent=2)}]

    elif name == "search_repos":
        result = search_repos(
            query=arguments["query"],
            max_results=arguments.get("max_results", 10)
        )
        return [{"type": "text", "text": json.dumps(result, indent=2)}]

    # Issue tools
    elif name == "list_issues":
        result = list_issues(
            repo_name=arguments["repo_name"],
            state=arguments.get("state", "open"),
            max_results=arguments.get("max_results", 20)
        )
        return [{"type": "text", "text": json.dumps(result, indent=2)}]

    elif name == "create_issue":
        result = create_issue(
            repo_name=arguments["repo_name"],
            title=arguments["title"],
            body=arguments.get("body", ""),
            labels=arguments.get("labels")
        )
        return [{"type": "text", "text": json.dumps(result, indent=2)}]

    elif name == "update_issue":
        result = update_issue(
            repo_name=arguments["repo_name"],
            issue_number=arguments["issue_number"],
            state=arguments.get("state"),
            title=arguments.get("title"),
            body=arguments.get("body"),
            labels=arguments.get("labels")
        )
        return [{"type": "text", "text": json.dumps(result, indent=2)}]

    elif name == "add_issue_comment":
        result = add_issue_comment(
            repo_name=arguments["repo_name"],
            issue_number=arguments["issue_number"],
            body=arguments["body"]
        )
        return [{"type": "text", "text": json.dumps(result, indent=2)}]

    # Pull Request tools
    elif name == "list_pull_requests":
        result = list_pull_requests(
            repo_name=arguments["repo_name"],
            state=arguments.get("state", "open"),
            max_results=arguments.get("max_results", 20)
        )
        return [{"type": "text", "text": json.dumps(result, indent=2)}]

    elif name == "create_pull_request":
        result = create_pull_request(
            repo_name=arguments["repo_name"],
            title=arguments["title"],
            head=arguments["head"],
            base=arguments["base"],
            body=arguments.get("body", "")
        )
        return [{"type": "text", "text": json.dumps(result, indent=2)}]

    elif name == "merge_pull_request":
        result = merge_pull_request(
            repo_name=arguments["repo_name"],
            pr_number=arguments["pr_number"],
            commit_message=arguments.get("commit_message")
        )
        return [{"type": "text", "text": json.dumps(result, indent=2)}]

    # File operations
    elif name == "get_file_contents":
        result = get_file_contents(
            repo_name=arguments["repo_name"],
            path=arguments["path"],
            branch=arguments.get("branch")
        )
        return [{"type": "text", "text": json.dumps(result, indent=2)}]

    elif name == "list_directory":
        result = list_directory(
            repo_name=arguments["repo_name"],
            path=arguments.get("path", ""),
            branch=arguments.get("branch")
        )
        return [{"type": "text", "text": json.dumps(result, indent=2)}]

    # Commit & branch tools
    elif name == "list_commits":
        result = list_commits(
            repo_name=arguments["repo_name"],
            branch=arguments.get("branch"),
            max_results=arguments.get("max_results", 20)
        )
        return [{"type": "text", "text": json.dumps(result, indent=2)}]

    elif name == "list_branches":
        result = list_branches(arguments["repo_name"])
        return [{"type": "text", "text": json.dumps(result, indent=2)}]

    # Search tools
    elif name == "search_code":
        result = search_code(
            query=arguments["query"],
            repo_name=arguments.get("repo_name"),
            max_results=arguments.get("max_results", 10)
        )
        return [{"type": "text", "text": json.dumps(result, indent=2)}]

    elif name == "search_issues":
        result = search_issues(
            query=arguments["query"],
            repo_name=arguments.get("repo_name"),
            max_results=arguments.get("max_results", 10)
        )
        return [{"type": "text", "text": json.dumps(result, indent=2)}]

    raise ValueError(f"Unknown tool: {name}")

# ============================================================================
# Main Entry Point
# ============================================================================

def main():
    """Run the GitHub MCP server"""
    print(f"Starting {SERVER_NAME} v{SERVER_VERSION}")
    print(f"Token: {GITHUB_TOKEN[:8]}..." if GITHUB_TOKEN else "No token")

    try:
        # Verify connection
        print(f"✓ Connected to GitHub as: {user.login}")
        print(f"✓ Name: {user.name or user.login}")
        print(f"✓ Public repos: {user.public_repos}")
        print("Server is ready for connections...")

        # Run the server
        asyncio.run(stdio_server(app))

    except Exception as e:
        print(f"ERROR: {e}")
        exit(1)

if __name__ == "__main__":
    main()
