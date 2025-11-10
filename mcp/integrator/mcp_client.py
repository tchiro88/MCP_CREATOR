"""
MCP Client - Make requests to other MCP servers
"""

import aiohttp
import json
from typing import Dict, List, Any, Optional


class MCPClient:
    """Client to interact with other MCP servers"""

    def __init__(self, base_urls: Dict[str, str]):
        """
        Initialize with base URLs for each MCP service

        Args:
            base_urls: Dict mapping service names to base URLs
                      e.g., {"outlook": "http://localhost:3010", "google": "http://localhost:3004"}
        """
        self.base_urls = base_urls
        self.session = None

    async def _ensure_session(self):
        """Ensure aiohttp session exists"""
        if self.session is None:
            self.session = aiohttp.ClientSession()

    async def close(self):
        """Close aiohttp session"""
        if self.session:
            await self.session.close()
            self.session = None

    async def call_tool(self, service: str, tool_name: str, arguments: Dict[str, Any]) -> Any:
        """
        Call a tool on a specific MCP service

        Args:
            service: Service name (e.g., "outlook", "google", "todoist")
            tool_name: Tool to call (e.g., "get_unread_emails")
            arguments: Tool arguments

        Returns:
            Tool response data
        """
        await self._ensure_session()

        if service not in self.base_urls:
            raise Exception(f"Unknown service: {service}")

        url = f"{self.base_urls[service]}/tools/call"

        payload = {
            "method": "tools/call",
            "params": {
                "name": tool_name,
                "arguments": arguments
            }
        }

        try:
            async with self.session.post(url, json=payload, timeout=30) as response:
                if response.status == 200:
                    data = await response.json()
                    return data
                else:
                    error_text = await response.text()
                    raise Exception(f"Error calling {service}.{tool_name}: {response.status} - {error_text}")
        except aiohttp.ClientError as e:
            raise Exception(f"Network error calling {service}.{tool_name}: {str(e)}")
        except Exception as e:
            raise Exception(f"Error calling {service}.{tool_name}: {str(e)}")

    async def list_tools(self, service: str) -> List[Dict]:
        """List available tools for a service"""
        await self._ensure_session()

        if service not in self.base_urls:
            raise Exception(f"Unknown service: {service}")

        url = f"{self.base_urls[service]}/tools/list"

        try:
            async with self.session.get(url, timeout=10) as response:
                if response.status == 200:
                    data = await response.json()
                    return data.get("tools", [])
                else:
                    return []
        except:
            return []
