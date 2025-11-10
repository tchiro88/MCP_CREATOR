"""
Cross-Service Integration Tools
Aggregate data from multiple MCP services for comprehensive insights
"""

import asyncio
from datetime import datetime, timedelta
from typing import Dict, List, Any
import json


class CrossServiceTools:
    """Tools that aggregate data from multiple MCP services"""

    def __init__(self, mcp_client):
        self.client = mcp_client

    async def unified_inbox(self, limit: int = 50) -> Dict[str, Any]:
        """
        Get unified view of unread messages from all email/messaging services

        Combines:
        - Outlook unread emails
        - Gmail unread emails
        - Slack unread messages
        - (Future: Teams, Discord, etc.)
        """
        results = {
            "total_unread": 0,
            "by_service": {},
            "all_messages": [],
            "errors": []
        }

        # Fetch from all services concurrently
        tasks = []

        # Outlook
        if "outlook" in self.client.base_urls:
            tasks.append(("outlook", self.client.call_tool("outlook", "get_unread_emails", {"limit": limit})))

        # Google/Gmail
        if "google" in self.client.base_urls:
            tasks.append(("google", self.client.call_tool("google", "get_unread_emails", {"limit": limit})))

        # Slack
        if "slack" in self.client.base_urls:
            tasks.append(("slack", self.client.call_tool("slack", "get_unread_messages", {"limit": limit})))

        # Execute all requests
        for service_name, task_coro in tasks:
            try:
                data = await task_coro
                # Parse response
                if isinstance(data, dict) and "content" in data:
                    content = data["content"][0]["text"] if data["content"] else "{}"
                    messages = json.loads(content) if isinstance(content, str) else content
                else:
                    messages = data

                if isinstance(messages, list):
                    # Add service tag to each message
                    for msg in messages:
                        msg["_service"] = service_name
                    results["by_service"][service_name] = len(messages)
                    results["all_messages"].extend(messages)
                    results["total_unread"] += len(messages)
            except Exception as e:
                results["errors"].append(f"{service_name}: {str(e)}")

        # Sort by date (most recent first)
        results["all_messages"].sort(
            key=lambda x: x.get("date", "") or x.get("timestamp", ""),
            reverse=True
        )

        return results

    async def unified_calendar(self, date: str = None) -> Dict[str, Any]:
        """
        Get unified calendar view from all calendar services

        Combines:
        - Outlook calendar
        - Google Calendar
        """
        if date is None:
            date = datetime.now().date().isoformat()

        results = {
            "date": date,
            "all_events": [],
            "by_service": {},
            "errors": []
        }

        # Fetch from all services
        tasks = []

        # Outlook
        if "outlook" in self.client.base_urls:
            tasks.append(("outlook", self.client.call_tool("outlook", "get_today_events", {})))

        # Google Calendar
        if "google" in self.client.base_urls:
            tasks.append(("google", self.client.call_tool("google", "get_calendar_events", {"date": date})))

        # Execute requests
        for service_name, task_coro in tasks:
            try:
                data = await task_coro
                # Parse response
                if isinstance(data, dict) and "content" in data:
                    content = data["content"][0]["text"] if data["content"] else "[]"
                    events = json.loads(content) if isinstance(content, str) else content
                else:
                    events = data

                if isinstance(events, list):
                    # Add service tag
                    for event in events:
                        event["_service"] = service_name
                    results["by_service"][service_name] = len(events)
                    results["all_events"].extend(events)
            except Exception as e:
                results["errors"].append(f"{service_name}: {str(e)}")

        # Sort by start time
        results["all_events"].sort(key=lambda x: x.get("start", ""))

        return results

    async def unified_tasks(self) -> Dict[str, Any]:
        """
        Get unified task list from all task management services

        Combines:
        - Todoist tasks
        - Google Tasks
        - Notion tasks
        """
        results = {
            "total_tasks": 0,
            "by_service": {},
            "all_tasks": [],
            "errors": []
        }

        tasks = []

        # Todoist
        if "todoist" in self.client.base_urls:
            tasks.append(("todoist", self.client.call_tool("todoist", "get_tasks", {})))

        # Google Tasks
        if "google" in self.client.base_urls:
            tasks.append(("google", self.client.call_tool("google", "get_tasks", {})))

        # Notion (if configured with tasks database)
        if "notion" in self.client.base_urls:
            tasks.append(("notion", self.client.call_tool("notion", "query_database", {"database_id": "tasks"})))

        # Execute requests
        for service_name, task_coro in tasks:
            try:
                data = await task_coro
                # Parse response
                if isinstance(data, dict) and "content" in data:
                    content = data["content"][0]["text"] if data["content"] else "[]"
                    task_list = json.loads(content) if isinstance(content, str) else content
                else:
                    task_list = data

                if isinstance(task_list, list):
                    # Add service tag
                    for task in task_list:
                        task["_service"] = service_name
                    results["by_service"][service_name] = len(task_list)
                    results["all_tasks"].extend(task_list)
                    results["total_tasks"] += len(task_list)
            except Exception as e:
                results["errors"].append(f"{service_name}: {str(e)}")

        return results

    async def comprehensive_briefing(self) -> Dict[str, Any]:
        """
        Generate comprehensive daily briefing across ALL services

        Includes:
        - Unread messages (all services)
        - Today's calendar (all services)
        - Tasks due today (all services)
        - Priority recommendations
        """
        briefing = {
            "date": datetime.now().date().isoformat(),
            "generated_at": datetime.now().isoformat(),
            "summary": {},
            "inbox_overview": {},
            "calendar_overview": {},
            "tasks_overview": {},
            "recommendations": []
        }

        # Fetch all data concurrently
        inbox_task = self.unified_inbox(limit=100)
        calendar_task = self.unified_calendar()
        tasks_task = self.unified_tasks()

        # Wait for all
        inbox_data, calendar_data, tasks_data = await asyncio.gather(
            inbox_task,
            calendar_task,
            tasks_task,
            return_exceptions=True
        )

        # Process results
        if not isinstance(inbox_data, Exception):
            briefing["inbox_overview"] = {
                "total_unread": inbox_data.get("total_unread", 0),
                "by_service": inbox_data.get("by_service", {}),
                "top_5_messages": inbox_data.get("all_messages", [])[:5]
            }

        if not isinstance(calendar_data, Exception):
            briefing["calendar_overview"] = {
                "total_events": len(calendar_data.get("all_events", [])),
                "by_service": calendar_data.get("by_service", {}),
                "all_events": calendar_data.get("all_events", [])
            }

        if not isinstance(tasks_data, Exception):
            briefing["tasks_overview"] = {
                "total_tasks": tasks_data.get("total_tasks", 0),
                "by_service": tasks_data.get("by_service", {}),
                "top_10_tasks": tasks_data.get("all_tasks", [])[:10]
            }

        # Generate summary
        briefing["summary"] = {
            "unread_messages": briefing["inbox_overview"].get("total_unread", 0),
            "meetings_today": len(briefing["calendar_overview"].get("all_events", [])),
            "active_tasks": briefing["tasks_overview"].get("total_tasks", 0)
        }

        # Generate recommendations
        briefing["recommendations"] = self._generate_recommendations(briefing)

        return briefing

    def _generate_recommendations(self, briefing: Dict) -> List[str]:
        """Generate smart recommendations based on briefing data"""
        recommendations = []

        unread = briefing["summary"].get("unread_messages", 0)
        meetings = briefing["summary"].get("meetings_today", 0)
        tasks = briefing["summary"].get("active_tasks", 0)

        if unread > 50:
            recommendations.append(f"⚠️ High inbox volume ({unread} unread). Consider scheduling inbox zero time.")

        if meetings >= 5:
            recommendations.append(f"📅 Heavy meeting day ({meetings} meetings). Limited time for deep work.")
        elif meetings == 0:
            recommendations.append("✅ No meetings today! Great day for focused work.")

        if tasks > 20:
            recommendations.append(f"📋 Many active tasks ({tasks}). Prioritize top 3-5 for today.")

        # Check calendar density
        events = briefing["calendar_overview"].get("all_events", [])
        if len(events) > 0:
            # Calculate free time (simplified)
            total_meeting_hours = len(events)  # Rough estimate
            if total_meeting_hours >= 6:
                recommendations.append("⏰ Back-to-back meetings. Block time for breaks.")

        if not recommendations:
            recommendations.append("✨ Balanced day ahead. Start with highest priority items.")

        return recommendations

    async def search_everywhere(self, query: str, days: int = 30) -> Dict[str, Any]:
        """
        Search across ALL services for a keyword

        Searches:
        - Outlook emails
        - Gmail
        - Slack messages
        - Notion pages
        - GitHub repos/issues
        """
        results = {
            "query": query,
            "total_results": 0,
            "by_service": {},
            "errors": []
        }

        tasks = []

        # Outlook
        if "outlook" in self.client.base_urls:
            tasks.append(("outlook", "emails", self.client.call_tool("outlook", "search_emails", {"query": query, "days": days})))

        # Google/Gmail
        if "google" in self.client.base_urls:
            tasks.append(("google", "emails", self.client.call_tool("google", "search_emails", {"query": query, "days": days})))

        # Slack
        if "slack" in self.client.base_urls:
            tasks.append(("slack", "messages", self.client.call_tool("slack", "search_messages", {"query": query})))

        # Notion
        if "notion" in self.client.base_urls:
            tasks.append(("notion", "pages", self.client.call_tool("notion", "search", {"query": query})))

        # GitHub
        if "github" in self.client.base_urls:
            tasks.append(("github", "code", self.client.call_tool("github", "search_code", {"query": query})))

        # Execute all searches
        for service_name, result_type, task_coro in tasks:
            try:
                data = await task_coro
                # Parse response
                if isinstance(data, dict) and "content" in data:
                    content = data["content"][0]["text"] if data["content"] else "[]"
                    search_results = json.loads(content) if isinstance(content, str) else content
                else:
                    search_results = data

                if isinstance(search_results, list):
                    key = f"{service_name}_{result_type}"
                    results["by_service"][key] = {
                        "count": len(search_results),
                        "results": search_results
                    }
                    results["total_results"] += len(search_results)
            except Exception as e:
                results["errors"].append(f"{service_name}: {str(e)}")

        return results

    async def service_health_check(self) -> Dict[str, Any]:
        """Check connectivity to all MCP services"""
        health = {
            "timestamp": datetime.now().isoformat(),
            "services": {},
            "total_services": len(self.client.base_urls),
            "healthy_services": 0,
            "unhealthy_services": 0
        }

        for service_name, base_url in self.client.base_urls.items():
            try:
                # Try to list tools (simple health check)
                tools = await self.client.list_tools(service_name)
                health["services"][service_name] = {
                    "status": "healthy",
                    "url": base_url,
                    "tools_available": len(tools)
                }
                health["healthy_services"] += 1
            except Exception as e:
                health["services"][service_name] = {
                    "status": "unhealthy",
                    "url": base_url,
                    "error": str(e)
                }
                health["unhealthy_services"] += 1

        return health
