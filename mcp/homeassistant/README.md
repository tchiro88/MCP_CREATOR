# Home Assistant MCP Server

Provides MCP access to your Home Assistant smart home platform from any device.

## Features

### Entity Control
- 🏠 List all entities (lights, switches, sensors, etc.)
- 💡 Turn on/off lights and switches
- 🎚️ Set brightness and colors
- 🌡️ Read sensor data
- 📊 Get entity history

### Automation & Scripts
- 🤖 List and trigger automations
- 📝 Run scripts
- 🔧 Call any Home Assistant service

### Device Types Supported
- Lights (on/off, brightness, RGB colors)
- Switches
- Sensors (temperature, humidity, etc.)
- Climate (thermostats)
- Media players
- Covers (blinds, garage doors)
- Locks
- Cameras
- And all other Home Assistant entities!

## Prerequisites

1. Home Assistant instance (running locally or remotely)
2. Long-lived access token
3. Python 3.11+

## Setup Instructions

### Step 1: Get Home Assistant Access Token

1. **Log in to Home Assistant** (web interface)

2. **Go to your profile**:
   - Click your username (bottom left)
   - Scroll down to **Long-Lived Access Tokens**

3. **Create token**:
   - Click "**CREATE TOKEN**"
   - Name: `MCP Server`
   - Click "**OK**"
   - **Copy the token immediately** (you won't see it again!)

Token format: `eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...` (very long)

### Step 2: Set Environment Variables

```bash
# Your Home Assistant URL
export HA_URL="http://homeassistant.local:8123"
# Or if using custom domain/IP:
# export HA_URL="http://192.168.1.100:8123"
# export HA_URL="https://ha.yourdomain.com"

# Your access token
export HA_TOKEN="eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9..."
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
Starting homeassistant v1.0.0
Home Assistant URL: http://homeassistant.local:8123
✓ Connected to Home Assistant (version 2024.11.0)
✓ Location: Home
Server is ready for connections...
```

## Docker Deployment

For deployment in your Proxmox LXC:

### Build Image

```bash
docker build -t mcp-homeassistant:latest .
```

### Run Container

```bash
docker run -d \
  --name mcp-homeassistant \
  -e HA_URL="http://homeassistant.local:8123" \
  -e HA_TOKEN="your-token-here" \
  -p 3006:3000 \
  mcp-homeassistant:latest
```

### Using .env File

```bash
# Create .env file
cat > .env << EOF
HA_URL=http://homeassistant.local:8123
HA_TOKEN=eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...
EOF

# Run with env file
docker run -d \
  --name mcp-homeassistant \
  --env-file .env \
  -p 3006:3000 \
  mcp-homeassistant:latest
```

## Available Tools

### Entity Management

| Tool | Description | Parameters |
|------|-------------|------------|
| `list_entities` | List all entities | `domain` (optional filter) |
| `get_entity_state` | Get entity details | `entity_id` |

### Control

| Tool | Description | Parameters |
|------|-------------|------------|
| `turn_on` | Turn on entity | `entity_id`, `brightness`, `rgb_color` (optional) |
| `turn_off` | Turn off entity | `entity_id` |
| `toggle` | Toggle entity | `entity_id` |
| `call_service` | Call any HA service | `domain`, `service`, `entity_id`, `data` |
| `list_services` | List all services | None |

### Automation & Scripts

| Tool | Description | Parameters |
|------|-------------|------------|
| `list_automations` | List automations | None |
| `trigger_automation` | Trigger automation | `entity_id` |
| `list_scripts` | List scripts | None |
| `run_script` | Run script | `entity_id` |

### Data & History

| Tool | Description | Parameters |
|------|-------------|------------|
| `get_sensor_data` | Get sensor data | `entity_id` |
| `get_history` | Get entity history | `entity_id`, `hours` |

## Entity ID Format

Home Assistant entities use the format: `domain.entity_name`

**Examples**:
- `light.living_room`
- `switch.bedroom_fan`
- `sensor.outdoor_temperature`
- `climate.main_thermostat`
- `automation.lights_on_sunset`
- `script.bedtime_routine`

## Common Use Cases

### List All Lights
```python
list_entities(domain="light")
```

### Turn On Light with Color
```python
turn_on(
    entity_id="light.bedroom",
    brightness=200,
    rgb_color=[255, 100, 0]  # Orange
)
```

### Get Temperature Sensor
```python
get_sensor_data(entity_id="sensor.living_room_temperature")
```

### Run Bedtime Script
```python
run_script(entity_id="script.bedtime")
```

### Trigger Automation
```python
trigger_automation(entity_id="automation.arrive_home")
```

## Resources

| URI | Description |
|-----|-------------|
| `ha://entities/all` | All entities |
| `ha://entities/lights` | All lights |
| `ha://entities/switches` | All switches |
| `ha://entities/sensors` | All sensors |
| `ha://automations` | All automations |

## Usage Examples

### From Claude Desktop (Local)

Edit: `~/Library/Application Support/Claude/claude_desktop_config.json`

```json
{
  "mcpServers": {
    "homeassistant": {
      "command": "python",
      "args": ["/path/to/mcp/homeassistant/server.py"],
      "env": {
        "HA_URL": "http://homeassistant.local:8123",
        "HA_TOKEN": "your-token-here"
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
    "homeassistant": {
      "url": "https://ha-mcp.yourdomain.com",
      "transport": "http"
    }
  }
}
```

## Example Commands

Ask Claude:

### Control Devices
> "Turn on the living room lights"
> "Set bedroom light to 50% brightness"
> "Turn off all switches"
> "What's the temperature in the kitchen?"

### Automations
> "List all my automations"
> "Trigger the bedtime automation"
> "Run the morning routine script"

### Status & Monitoring
> "What lights are currently on?"
> "Show me all sensor readings"
> "What was the temperature over the last 12 hours?"

### Advanced
> "Turn on the porch light and set it to blue"
> "List all battery-powered sensors and their levels"
> "Show me which doors are open"

## Troubleshooting

### "HA_TOKEN not set"
**Solution**: Set the environment variable:
```bash
export HA_TOKEN="your-token-here"
```

### "Failed to connect to Home Assistant"
**Check**:
1. Is Home Assistant running?
2. Is the URL correct? (check http vs https, port number)
3. Can you ping the address?
4. Is your token valid?

```bash
# Test connection manually
curl -X GET \
  -H "Authorization: Bearer YOUR_TOKEN" \
  -H "Content-Type: application/json" \
  http://homeassistant.local:8123/api/
```

### "Entity not found"
- Check entity ID spelling
- Verify entity exists: `list_entities()`
- Entity IDs are case-sensitive

### Connection timeout
- Check firewall rules
- Verify Home Assistant is accessible from MCP server
- Try increasing timeout in code (currently 10s)

## Security Notes

- **Long-lived access token = full Home Assistant access** - protect it!
- Never commit tokens to Git
- Use environment variables
- Rotate tokens periodically
- Expose only via Cloudflare Zero Trust if remote

## Finding Your Home Assistant URL

**Common URLs**:
- Local: `http://homeassistant.local:8123`
- IP address: `http://192.168.1.100:8123`
- Nabu Casa: `https://abcdefgh.ui.nabu.casa`
- Custom domain: `https://ha.yourdomain.com`

**To find it**:
1. Check your Home Assistant config
2. Look at the URL in your browser when accessing HA
3. Check your router's DHCP leases for "homeassistant"

## Advanced: Custom Service Calls

You can call any Home Assistant service:

```python
# Set thermostat mode
call_service(
    domain="climate",
    service="set_hvac_mode",
    entity_id="climate.main",
    data={"hvac_mode": "heat"}
)

# Play media
call_service(
    domain="media_player",
    service="play_media",
    entity_id="media_player.living_room",
    data={
        "media_content_type": "music",
        "media_content_id": "spotify:playlist:xxxxx"
    }
)

# Send notification
call_service(
    domain="notify",
    service="mobile_app_iphone",
    data={"message": "Hello from MCP!"}
)
```

## Next Steps

1. ✅ Get your Home Assistant access token
2. ✅ Test locally with `python server.py`
3. ✅ Deploy to Proxmox LXC via Docker
4. ✅ Configure Cloudflare Tunnel
5. ✅ Add to Claude apps

---

**Tip**: Combine with Google Calendar to create location-based automations!

**Example**: "When I leave home (detected by iPhone), turn off all lights and set thermostat to eco mode"
