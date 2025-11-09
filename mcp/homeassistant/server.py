#!/usr/bin/env python3
"""
Home Assistant MCP Server
Provides access to Home Assistant smart home platform

Features:
- List and control entities (lights, switches, sensors, etc.)
- Call services (turn on/off, set brightness, etc.)
- Get entity states and attributes
- Trigger automations and scripts
- View sensor data and history
"""

import os
import json
import asyncio
from typing import Any, Optional
from mcp.server import Server
from mcp.server.stdio import stdio_server

# Home Assistant API import
try:
    import requests
except ImportError:
    print("ERROR: requests library not installed!")
    print("Install with: pip install requests")
    exit(1)

# ============================================================================
# Configuration
# ============================================================================

SERVER_NAME = "homeassistant"
SERVER_VERSION = "1.0.0"

# Get Home Assistant details from environment
HA_URL = os.getenv('HA_URL', 'http://homeassistant.local:8123')
HA_TOKEN = os.getenv('HA_TOKEN')

if not HA_TOKEN:
    print("ERROR: HA_TOKEN environment variable not set!")
    print("Get your long-lived access token from Home Assistant:")
    print("Profile → Long-Lived Access Tokens → Create Token")
    exit(1)

# Home Assistant API headers
HEADERS = {
    "Authorization": f"Bearer {HA_TOKEN}",
    "Content-Type": "application/json"
}

# ============================================================================
# Home Assistant API Functions
# ============================================================================

def api_request(method: str, endpoint: str, data: Optional[dict] = None) -> dict:
    """Make a request to Home Assistant API"""
    url = f"{HA_URL}/api/{endpoint}"

    try:
        if method == "GET":
            response = requests.get(url, headers=HEADERS, params=data, timeout=10)
        elif method == "POST":
            response = requests.post(url, headers=HEADERS, json=data, timeout=10)
        else:
            return {"error": f"Unsupported HTTP method: {method}"}

        response.raise_for_status()
        return response.json()

    except requests.exceptions.RequestException as e:
        return {"error": str(e)}

# ============================================================================
# Entity Functions
# ============================================================================

def list_entities(domain: Optional[str] = None) -> list[dict]:
    """List all entities, optionally filtered by domain"""
    result = api_request("GET", "states")

    if isinstance(result, dict) and 'error' in result:
        return [result]

    entities = []
    for entity in result:
        entity_id = entity['entity_id']

        # Filter by domain if specified
        if domain and not entity_id.startswith(f"{domain}."):
            continue

        entities.append({
            'entity_id': entity_id,
            'state': entity['state'],
            'friendly_name': entity.get('attributes', {}).get('friendly_name', entity_id),
            'last_changed': entity['last_changed'],
            'last_updated': entity['last_updated']
        })

    return entities

def get_entity_state(entity_id: str) -> dict:
    """Get detailed state and attributes of an entity"""
    result = api_request("GET", f"states/{entity_id}")

    if isinstance(result, dict) and 'error' in result:
        return result

    return {
        'entity_id': result['entity_id'],
        'state': result['state'],
        'attributes': result.get('attributes', {}),
        'last_changed': result['last_changed'],
        'last_updated': result['last_updated'],
        'context': result.get('context', {})
    }

# ============================================================================
# Service Functions
# ============================================================================

def list_services() -> dict:
    """List all available services"""
    result = api_request("GET", "services")

    if isinstance(result, dict) and 'error' in result:
        return result

    services = {}
    for domain, domain_services in result.items():
        services[domain] = list(domain_services.keys())

    return services

def call_service(domain: str, service: str, entity_id: Optional[str] = None,
                data: Optional[dict] = None) -> dict:
    """Call a Home Assistant service"""
    payload = data or {}

    if entity_id:
        payload['entity_id'] = entity_id

    result = api_request("POST", f"services/{domain}/{service}", payload)

    if isinstance(result, list) and len(result) > 0:
        return {
            'success': True,
            'entities_affected': [e['entity_id'] for e in result]
        }
    elif isinstance(result, dict) and 'error' not in result:
        return {'success': True, 'result': result}
    else:
        return result

# ============================================================================
# Common Service Shortcuts
# ============================================================================

def turn_on(entity_id: str, **kwargs) -> dict:
    """Turn on an entity (light, switch, etc.)"""
    return call_service('homeassistant', 'turn_on', entity_id, kwargs)

def turn_off(entity_id: str) -> dict:
    """Turn off an entity"""
    return call_service('homeassistant', 'turn_off', entity_id)

def toggle(entity_id: str) -> dict:
    """Toggle an entity"""
    return call_service('homeassistant', 'toggle', entity_id)

def set_light_brightness(entity_id: str, brightness: int) -> dict:
    """Set light brightness (0-255)"""
    return call_service('light', 'turn_on', entity_id, {'brightness': brightness})

def set_light_color(entity_id: str, rgb: list[int]) -> dict:
    """Set light color via RGB [r, g, b]"""
    return call_service('light', 'turn_on', entity_id, {'rgb_color': rgb})

def set_temperature(entity_id: str, temperature: float) -> dict:
    """Set climate temperature"""
    return call_service('climate', 'set_temperature', entity_id, {'temperature': temperature})

# ============================================================================
# Automation & Script Functions
# ============================================================================

def list_automations() -> list[dict]:
    """List all automations"""
    return list_entities('automation')

def trigger_automation(entity_id: str) -> dict:
    """Trigger an automation"""
    return call_service('automation', 'trigger', entity_id)

def list_scripts() -> list[dict]:
    """List all scripts"""
    return list_entities('script')

def run_script(entity_id: str) -> dict:
    """Run a script"""
    # Scripts are called by their entity_id without the domain prefix
    script_name = entity_id.replace('script.', '')
    return call_service('script', script_name)

# ============================================================================
# History & Sensor Functions
# ============================================================================

def get_history(entity_id: str, hours: int = 24) -> dict:
    """Get history for an entity"""
    from datetime import datetime, timedelta

    end_time = datetime.now()
    start_time = end_time - timedelta(hours=hours)

    endpoint = f"history/period/{start_time.isoformat()}"
    params = {
        'filter_entity_id': entity_id,
        'end_time': end_time.isoformat()
    }

    result = api_request("GET", endpoint, params)

    if isinstance(result, dict) and 'error' in result:
        return result

    return {
        'entity_id': entity_id,
        'history': result[0] if result else [],
        'period_hours': hours
    }

def get_sensor_data(entity_id: str) -> dict:
    """Get current sensor data with attributes"""
    return get_entity_state(entity_id)

# ============================================================================
# MCP Server
# ============================================================================

app = Server(SERVER_NAME)

@app.list_resources()
async def list_resources() -> list[dict[str, Any]]:
    """List available Home Assistant resources"""
    return [
        {
            "uri": "ha://entities/all",
            "name": "All Entities",
            "description": "All Home Assistant entities",
            "mimeType": "application/json"
        },
        {
            "uri": "ha://entities/lights",
            "name": "Lights",
            "description": "All light entities",
            "mimeType": "application/json"
        },
        {
            "uri": "ha://entities/switches",
            "name": "Switches",
            "description": "All switch entities",
            "mimeType": "application/json"
        },
        {
            "uri": "ha://entities/sensors",
            "name": "Sensors",
            "description": "All sensor entities",
            "mimeType": "application/json"
        },
        {
            "uri": "ha://automations",
            "name": "Automations",
            "description": "All automations",
            "mimeType": "application/json"
        }
    ]

@app.read_resource()
async def read_resource(uri: str) -> str:
    """Read a Home Assistant resource"""
    if uri == "ha://entities/all":
        entities = list_entities()
        return json.dumps(entities, indent=2)

    elif uri == "ha://entities/lights":
        entities = list_entities('light')
        return json.dumps(entities, indent=2)

    elif uri == "ha://entities/switches":
        entities = list_entities('switch')
        return json.dumps(entities, indent=2)

    elif uri == "ha://entities/sensors":
        entities = list_entities('sensor')
        return json.dumps(entities, indent=2)

    elif uri == "ha://automations":
        automations = list_automations()
        return json.dumps(automations, indent=2)

    raise ValueError(f"Unknown resource: {uri}")

@app.list_tools()
async def list_tools() -> list[dict[str, Any]]:
    """List available Home Assistant tools"""
    return [
        # Entity tools
        {
            "name": "list_entities",
            "description": "List all entities, optionally filtered by domain (light, switch, sensor, etc.)",
            "inputSchema": {
                "type": "object",
                "properties": {
                    "domain": {
                        "type": "string",
                        "description": "Filter by domain (e.g., 'light', 'switch', 'sensor') (optional)"
                    }
                },
                "required": []
            }
        },
        {
            "name": "get_entity_state",
            "description": "Get detailed state and attributes of a specific entity",
            "inputSchema": {
                "type": "object",
                "properties": {
                    "entity_id": {
                        "type": "string",
                        "description": "Entity ID (e.g., 'light.living_room')"
                    }
                },
                "required": ["entity_id"]
            }
        },
        # Control tools
        {
            "name": "turn_on",
            "description": "Turn on an entity (light, switch, etc.)",
            "inputSchema": {
                "type": "object",
                "properties": {
                    "entity_id": {
                        "type": "string",
                        "description": "Entity ID to turn on"
                    },
                    "brightness": {
                        "type": "number",
                        "description": "Brightness for lights (0-255) (optional)"
                    },
                    "rgb_color": {
                        "type": "array",
                        "items": {"type": "number"},
                        "description": "RGB color [r, g, b] for lights (optional)"
                    }
                },
                "required": ["entity_id"]
            }
        },
        {
            "name": "turn_off",
            "description": "Turn off an entity",
            "inputSchema": {
                "type": "object",
                "properties": {
                    "entity_id": {
                        "type": "string",
                        "description": "Entity ID to turn off"
                    }
                },
                "required": ["entity_id"]
            }
        },
        {
            "name": "toggle",
            "description": "Toggle an entity on/off",
            "inputSchema": {
                "type": "object",
                "properties": {
                    "entity_id": {
                        "type": "string",
                        "description": "Entity ID to toggle"
                    }
                },
                "required": ["entity_id"]
            }
        },
        # Service tools
        {
            "name": "call_service",
            "description": "Call any Home Assistant service",
            "inputSchema": {
                "type": "object",
                "properties": {
                    "domain": {
                        "type": "string",
                        "description": "Service domain (e.g., 'light', 'switch')"
                    },
                    "service": {
                        "type": "string",
                        "description": "Service name (e.g., 'turn_on', 'toggle')"
                    },
                    "entity_id": {
                        "type": "string",
                        "description": "Target entity ID (optional)"
                    },
                    "data": {
                        "type": "object",
                        "description": "Additional service data (optional)"
                    }
                },
                "required": ["domain", "service"]
            }
        },
        {
            "name": "list_services",
            "description": "List all available Home Assistant services",
            "inputSchema": {
                "type": "object",
                "properties": {},
                "required": []
            }
        },
        # Automation tools
        {
            "name": "list_automations",
            "description": "List all automations",
            "inputSchema": {
                "type": "object",
                "properties": {},
                "required": []
            }
        },
        {
            "name": "trigger_automation",
            "description": "Trigger an automation",
            "inputSchema": {
                "type": "object",
                "properties": {
                    "entity_id": {
                        "type": "string",
                        "description": "Automation entity ID (e.g., 'automation.lights_on')"
                    }
                },
                "required": ["entity_id"]
            }
        },
        # Script tools
        {
            "name": "list_scripts",
            "description": "List all scripts",
            "inputSchema": {
                "type": "object",
                "properties": {},
                "required": []
            }
        },
        {
            "name": "run_script",
            "description": "Run a script",
            "inputSchema": {
                "type": "object",
                "properties": {
                    "entity_id": {
                        "type": "string",
                        "description": "Script entity ID (e.g., 'script.bedtime')"
                    }
                },
                "required": ["entity_id"]
            }
        },
        # Sensor & history
        {
            "name": "get_sensor_data",
            "description": "Get current sensor data with all attributes",
            "inputSchema": {
                "type": "object",
                "properties": {
                    "entity_id": {
                        "type": "string",
                        "description": "Sensor entity ID (e.g., 'sensor.temperature')"
                    }
                },
                "required": ["entity_id"]
            }
        },
        {
            "name": "get_history",
            "description": "Get historical data for an entity",
            "inputSchema": {
                "type": "object",
                "properties": {
                    "entity_id": {
                        "type": "string",
                        "description": "Entity ID"
                    },
                    "hours": {
                        "type": "number",
                        "description": "Number of hours of history (default: 24)",
                        "default": 24
                    }
                },
                "required": ["entity_id"]
            }
        }
    ]

@app.call_tool()
async def call_tool(name: str, arguments: dict) -> list[dict[str, Any]]:
    """Execute a Home Assistant tool"""

    # Entity tools
    if name == "list_entities":
        result = list_entities(arguments.get("domain"))
        return [{"type": "text", "text": json.dumps(result, indent=2)}]

    elif name == "get_entity_state":
        result = get_entity_state(arguments["entity_id"])
        return [{"type": "text", "text": json.dumps(result, indent=2)}]

    # Control tools
    elif name == "turn_on":
        kwargs = {}
        if "brightness" in arguments:
            kwargs["brightness"] = arguments["brightness"]
        if "rgb_color" in arguments:
            kwargs["rgb_color"] = arguments["rgb_color"]
        result = turn_on(arguments["entity_id"], **kwargs)
        return [{"type": "text", "text": json.dumps(result, indent=2)}]

    elif name == "turn_off":
        result = turn_off(arguments["entity_id"])
        return [{"type": "text", "text": json.dumps(result, indent=2)}]

    elif name == "toggle":
        result = toggle(arguments["entity_id"])
        return [{"type": "text", "text": json.dumps(result, indent=2)}]

    # Service tools
    elif name == "call_service":
        result = call_service(
            domain=arguments["domain"],
            service=arguments["service"],
            entity_id=arguments.get("entity_id"),
            data=arguments.get("data")
        )
        return [{"type": "text", "text": json.dumps(result, indent=2)}]

    elif name == "list_services":
        result = list_services()
        return [{"type": "text", "text": json.dumps(result, indent=2)}]

    # Automation tools
    elif name == "list_automations":
        result = list_automations()
        return [{"type": "text", "text": json.dumps(result, indent=2)}]

    elif name == "trigger_automation":
        result = trigger_automation(arguments["entity_id"])
        return [{"type": "text", "text": json.dumps(result, indent=2)}]

    # Script tools
    elif name == "list_scripts":
        result = list_scripts()
        return [{"type": "text", "text": json.dumps(result, indent=2)}]

    elif name == "run_script":
        result = run_script(arguments["entity_id"])
        return [{"type": "text", "text": json.dumps(result, indent=2)}]

    # Sensor & history
    elif name == "get_sensor_data":
        result = get_sensor_data(arguments["entity_id"])
        return [{"type": "text", "text": json.dumps(result, indent=2)}]

    elif name == "get_history":
        hours = arguments.get("hours", 24)
        result = get_history(arguments["entity_id"], hours)
        return [{"type": "text", "text": json.dumps(result, indent=2)}]

    raise ValueError(f"Unknown tool: {name}")

# ============================================================================
# Main Entry Point
# ============================================================================

def main():
    """Run the Home Assistant MCP server"""
    print(f"Starting {SERVER_NAME} v{SERVER_VERSION}")
    print(f"Home Assistant URL: {HA_URL}")
    print(f"Token: {HA_TOKEN[:8]}..." if HA_TOKEN else "No token")

    # Test API connection
    try:
        result = api_request("GET", "config")
        if isinstance(result, dict) and 'error' in result:
            print(f"ERROR: Failed to connect to Home Assistant: {result['error']}")
            exit(1)
        print(f"✓ Connected to Home Assistant (version {result.get('version', 'unknown')})")
        print(f"✓ Location: {result.get('location_name', 'unknown')}")
        print("Server is ready for connections...")

        # Run the server
        asyncio.run(stdio_server(app))

    except Exception as e:
        print(f"ERROR: {e}")
        exit(1)

if __name__ == "__main__":
    main()
