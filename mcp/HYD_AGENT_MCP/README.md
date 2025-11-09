# Hydraulic Schematic Analysis MCP Server

An AI-powered Model Context Protocol (MCP) server for analyzing hydraulic schematics. Drop in schematic images, ask questions about flow paths, find restrictions, compare machines, and leverage manufacturer documentation - all through natural language interaction with AI assistants like Claude Desktop or Cursor.

## Features

🔍 **Schematic Analysis**
- Vision AI-powered component extraction from schematics
- Automatic identification of valves, cylinders, pumps, motors, sensors
- Connection and flow path mapping
- Grid location tracking

🌊 **Flow Path Analysis**
- Trace flow between any two components
- Calculate pressure drops through paths
- Identify bottlenecks and restrictions
- Efficiency analysis

⚠️ **Restriction Detection**
- Identify undersized ports and lines
- High velocity warnings
- Turbulent flow detection
- Component-specific recommendations

🔬 **Component Impact Analysis**
- Understand what affects a component (upstream)
- See what's affected by a component (downstream)
- Visualize component relationships

🏭 **Machine Comparison**
- Compare schematics from different machines
- Identify component differences
- Performance comparisons
- Design evolution tracking

📚 **Manufacturer Documentation**
- Index PDF datasheets and manuals
- Search by component, part number, or manufacturer
- Extract specifications automatically
- Link docs to components

## Architecture

```
HYD_AGENT_MCP/
├── server.py                  # Main MCP server
├── schematic_parser.py        # Vision AI schematic parsing
├── flow_analyzer.py           # Flow path & restriction analysis
├── database_interface.py      # SQLite database management
├── doc_manager.py             # Manufacturer doc indexing
├── config.py                  # Configuration management
├── requirements.txt           # Python dependencies
├── Dockerfile                 # Docker container config
├── docker-compose.yml         # Docker Compose setup
├── README.md                  # This file
├── SETUP.md                   # Detailed setup guide
├── USAGE.md                   # Usage examples
├── schematics/                # Drop folder for schematics
├── manufacturer_docs/         # Drop folder for PDF manuals
├── machines/                  # Organized by machine name
└── database/                  # SQLite database storage
```

## Quick Start

### Prerequisites

- Docker and Docker Compose
- OpenAI API key OR OpenRouter API key
- Claude Desktop, Cursor, or any MCP-compatible client

### Installation

1. **Clone or navigate to the HYD_AGENT_MCP directory**

```bash
cd HYD_AGENT_MCP
```

2. **Configure environment**

Copy the example environment file and add your API key:

```bash
cp .env.example .env
# Edit .env and add your OPENAI_API_KEY or OPENROUTER_API_KEY
```

3. **Build the Docker image**

```bash
docker-compose build
```

4. **Test the server**

```bash
docker-compose run --rm hydraulic-mcp-server python server.py
```

If you see "Hydraulic Analysis MCP Server initialized", you're ready!

### Integration with Claude Desktop

1. **Locate your Claude Desktop config**
   - macOS: `~/Library/Application Support/Claude/claude_desktop_config.json`
   - Windows: `%APPDATA%\Claude\claude_desktop_config.json`
   - Linux: `~/.config/Claude/claude_desktop_config.json`

2. **Add the MCP server configuration**

Open the config file and merge in the configuration from `claude_desktop_config.json`:

```json
{
  "mcpServers": {
    "hydraulic-analysis": {
      "command": "docker",
      "args": [
        "run",
        "-i",
        "--rm",
        "-v", "/absolute/path/to/HYD_AGENT_MCP/schematics:/app/schematics",
        "-v", "/absolute/path/to/HYD_AGENT_MCP/manufacturer_docs:/app/manufacturer_docs",
        "-v", "/absolute/path/to/HYD_AGENT_MCP/machines:/app/machines",
        "-v", "/absolute/path/to/HYD_AGENT_MCP/database:/app/database",
        "-e", "OPENAI_API_KEY=your-api-key-here",
        "hydraulic-mcp-server"
      ]
    }
  }
}
```

**Important**: Replace `/absolute/path/to/HYD_AGENT_MCP` with the actual absolute path!

3. **Restart Claude Desktop**

### Integration with Cursor

1. **Create or edit Cursor settings**

In Cursor, go to Settings → MCP and add:

```json
{
  "mcp": {
    "servers": {
      "hydraulic-analysis": {
        "command": "docker",
        "args": [
          "run",
          "-i",
          "--rm",
          "-v", "${workspaceFolder}/HYD_AGENT_MCP/schematics:/app/schematics",
          "-v", "${workspaceFolder}/HYD_AGENT_MCP/manufacturer_docs:/app/manufacturer_docs",
          "-v", "${workspaceFolder}/HYD_AGENT_MCP/machines:/app/machines",
          "-v", "${workspaceFolder}/HYD_AGENT_MCP/database:/app/database",
          "-e", "OPENAI_API_KEY=${env:OPENAI_API_KEY}",
          "hydraulic-mcp-server"
        ]
      }
    }
  }
}
```

2. **Set environment variable**

Add `OPENAI_API_KEY` to your system environment or Cursor settings.

## Usage

### 1. Analyze a Schematic

Drop a schematic image (PNG, JPG) into the `schematics/` folder, then ask:

```
Analyze the schematic at schematics/machine_a_hydraulic.png for Machine A
```

The AI will:
- Extract all components (valves, cylinders, pumps, etc.)
- Identify connections
- Map flow paths
- Store in database for future queries

### 2. Find Flow Path

```
Find the flow path from P1 to H203 in schematic 1
```

Get detailed analysis including:
- All components in the path
- Pressure drop at each component
- Total pressure loss
- Efficiency rating
- Bottleneck identification

### 3. Analyze Restrictions

```
What are the biggest restrictions to oil flow in schematic 1 at 150 LPM?
```

Identifies:
- Undersized ports
- High velocity areas
- Turbulent flow zones
- Component-specific bottlenecks

### 4. Component Impact Analysis

```
What components impact the flow to cylinder H203 in schematic 1?
```

Shows:
- Upstream components (supply chain)
- Downstream components (affected by this)
- Connection types and line sizes

### 5. Compare Machines

```
Compare the hydraulic systems of schematic 1 and schematic 2
```

Compares:
- Component differences
- Unique components in each
- Restriction counts
- Design changes

### 6. Search Documentation

First, drop manufacturer PDFs into `manufacturer_docs/`, then:

```
Index the manufacturer documentation
```

Then search:

```
Search for documentation on Parker proportional valves
```

or

```
Find the datasheet for component H203
```

## Example Workflows

### Workflow 1: New Machine Analysis

1. Drop schematic into `schematics/new_machine.png`
2. "Analyze schematics/new_machine.png for New Baler"
3. "List all schematics"
4. "Get summary of schematic 1"
5. "Find flow path from main pump to press cylinder"
6. "What are the restrictions in this path?"

### Workflow 2: Troubleshooting

1. "Find all high-pressure drops in schematic 1 at 200 LPM"
2. "What components impact valve V12?"
3. "Search documentation for V12 specifications"
4. "Compare flow efficiency between main path and auxiliary path"

### Workflow 3: Machine Comparison

1. Analyze schematics for both machines
2. "Compare schematic 1 and schematic 2"
3. "List components only in schematic 1"
4. "Why does machine 2 have better flow efficiency?"

## Available MCP Tools

| Tool | Description |
|------|-------------|
| `analyze_schematic` | Parse schematic image and extract components |
| `find_flow_path` | Trace and analyze flow between components |
| `analyze_restrictions` | Find all restrictions in a schematic |
| `get_component_impact` | Analyze component relationships |
| `compare_machines` | Compare two schematics |
| `search_manufacturer_docs` | Search indexed documentation |
| `list_schematics` | List all analyzed schematics |
| `get_schematic_summary` | Get detailed schematic overview |
| `index_manufacturer_docs` | Index PDF documentation |

## Configuration

### Environment Variables

| Variable | Description | Default |
|----------|-------------|---------|
| `OPENAI_API_KEY` | OpenAI API key | Required |
| `OPENROUTER_API_KEY` | OpenRouter API key (alternative) | Optional |
| `DB_TYPE` | Database type (sqlite/postgresql) | sqlite |
| `WATCH_SCHEMATICS` | Auto-watch schematics folder | true |
| `WATCH_INTERVAL` | Watch interval in seconds | 5 |

### Database Options

**SQLite (Default)**
- Lightweight, no setup required
- Stored in `database/hydraulic_analysis.db`
- Perfect for single-user, local analysis

**PostgreSQL (Advanced)**
- For multi-user or production deployments
- Can integrate with existing AL DAHRA database
- Configure via environment variables

See `.env.example` for all configuration options.

## Deployment Options

### Option 1: Docker (Recommended)

```bash
docker-compose up -d
```

The server runs as a daemon and is ready for MCP connections.

### Option 2: Direct Python

```bash
pip install -r requirements.txt
python server.py
```

### Option 3: Cloudflare Worker (Advanced)

For distributed deployment, see `WORKER_DEPLOYMENT.md` (coming soon).

## Technical Details

### Vision AI Models

- **OpenAI GPT-4 Vision**: Accurate component identification
- **OpenRouter Claude 3.5 Sonnet**: Alternative with excellent vision capabilities

The system automatically selects based on available API keys.

### Flow Analysis

Uses hydraulic engineering principles:
- **Darcy-Weisbach equation** for pressure drop
- **Reynolds number** for flow regime detection
- **K-factors** for component resistance
- Industry-standard fluid properties (ISO VG 46)

### Supported File Formats

- **Schematics**: PNG, JPG, JPEG (PDF support coming soon)
- **Documentation**: PDF

## Troubleshooting

### "No API key configured"

Set `OPENAI_API_KEY` or `OPENROUTER_API_KEY` in `.env` file.

### "Cannot parse schematic"

- Ensure image is clear and high-resolution
- Check that components are labeled with IDs
- Try enhancing image contrast

### "Database locked"

Close other connections or restart the Docker container:

```bash
docker-compose restart
```

### "Tool not found"

Restart your AI client (Claude Desktop/Cursor) after configuration changes.

## Development

### Running Tests

```bash
python -m pytest tests/
```

### Adding Custom Analysis

Extend `flow_analyzer.py` with custom K-factors or analysis algorithms.

### Database Schema

See `database_interface.py` for complete schema. Key tables:
- `schematics` - Analyzed schematic files
- `components` - Extracted components
- `component_relationships` - Connections
- `flow_paths` - Analyzed paths
- `manufacturer_docs` - Indexed documentation

## Contributing

This is a specialized tool for hydraulic analysis. Contributions welcome:

1. Add support for more file formats (PDF, DWG)
2. Enhance flow analysis algorithms
3. Add more component types
4. Improve manufacturer doc extraction

## License

[Specify your license]

## Support

For issues or questions:
1. Check existing documentation
2. Review troubleshooting section
3. Open an issue with:
   - Schematic sample (if shareable)
   - Error messages
   - Environment details

## Credits

Built on:
- MCP SDK by Anthropic
- OpenAI GPT-4 Vision
- Hydraulic engineering principles from AL DAHRA industrial press analysis

## Version History

**v1.0.0** - Initial release
- Vision-based schematic parsing
- Flow path analysis
- Restriction detection
- Machine comparison
- Manufacturer doc integration
- Docker deployment
- Claude Desktop & Cursor integration
