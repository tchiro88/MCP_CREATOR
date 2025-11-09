#!/usr/bin/env python3
"""
Hydraulic Schematic Analysis MCP Server

Provides AI-powered analysis of hydraulic schematics including:
- Component identification and extraction
- Flow path analysis
- Restriction and bottleneck identification
- Machine comparison
- Manufacturer documentation lookup
"""
import asyncio
import json
import logging
from pathlib import Path
from typing import Any, Sequence

from mcp.server import Server
from mcp.server.stdio import stdio_server
from mcp.types import (
    Tool,
    TextContent,
    ImageContent,
    EmbeddedResource,
)

from config import config
from database_interface import HydraulicDatabase
from schematic_parser import SchematicParser
from flow_analyzer import FlowAnalyzer
from doc_manager import DocumentationManager

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Initialize server
app = Server("hydraulic-analysis-server")

# Initialize components
db = HydraulicDatabase(config.db_path)
parser = SchematicParser()
analyzer = FlowAnalyzer()
doc_manager = DocumentationManager(config.manufacturer_docs_dir)

logger.info("Hydraulic Analysis MCP Server initialized")


# === MCP Tool Definitions ===

@app.list_tools()
async def list_tools() -> list[Tool]:
    """List available hydraulic analysis tools"""
    return [
        Tool(
            name="analyze_schematic",
            description="Analyze a hydraulic schematic image/PDF and extract components, connections, and flow paths. Provide the file path to the schematic.",
            inputSchema={
                "type": "object",
                "properties": {
                    "file_path": {
                        "type": "string",
                        "description": "Path to schematic file (PNG, JPG, or PDF)"
                    },
                    "machine_name": {
                        "type": "string",
                        "description": "Name of the machine this schematic belongs to"
                    }
                },
                "required": ["file_path", "machine_name"]
            }
        ),
        Tool(
            name="find_flow_path",
            description="Find and analyze the flow path between two components in a schematic. Identifies all components in the path and calculates restrictions.",
            inputSchema={
                "type": "object",
                "properties": {
                    "schematic_id": {
                        "type": "integer",
                        "description": "ID of the schematic to analyze"
                    },
                    "start_component": {
                        "type": "string",
                        "description": "Starting component ID (e.g., P1 for pump)"
                    },
                    "end_component": {
                        "type": "string",
                        "description": "Ending component ID (e.g., H203 for cylinder)"
                    },
                    "flow_rate_lpm": {
                        "type": "number",
                        "description": "Design flow rate in liters per minute (default: 100)",
                        "default": 100
                    },
                    "pressure_bar": {
                        "type": "number",
                        "description": "System pressure in bar (default: 200)",
                        "default": 200
                    }
                },
                "required": ["schematic_id", "start_component", "end_component"]
            }
        ),
        Tool(
            name="analyze_restrictions",
            description="Analyze a schematic for flow restrictions and bottlenecks. Identifies components that restrict oil flow.",
            inputSchema={
                "type": "object",
                "properties": {
                    "schematic_id": {
                        "type": "integer",
                        "description": "ID of the schematic to analyze"
                    },
                    "flow_rate_lpm": {
                        "type": "number",
                        "description": "Design flow rate in liters per minute (default: 100)",
                        "default": 100
                    }
                },
                "required": ["schematic_id"]
            }
        ),
        Tool(
            name="get_component_impact",
            description="Analyze what components impact or are impacted by a specific component. Shows upstream supply and downstream affected components.",
            inputSchema={
                "type": "object",
                "properties": {
                    "schematic_id": {
                        "type": "integer",
                        "description": "ID of the schematic"
                    },
                    "component_id": {
                        "type": "string",
                        "description": "Component ID to analyze (e.g., H203, V12)"
                    }
                },
                "required": ["schematic_id", "component_id"]
            }
        ),
        Tool(
            name="compare_machines",
            description="Compare hydraulic schematics from two different machines. Identifies differences in components, flow paths, and performance.",
            inputSchema={
                "type": "object",
                "properties": {
                    "schematic_id_1": {
                        "type": "integer",
                        "description": "First schematic ID"
                    },
                    "schematic_id_2": {
                        "type": "integer",
                        "description": "Second schematic ID"
                    },
                    "flow_rate_lpm": {
                        "type": "number",
                        "description": "Flow rate for comparison analysis (default: 100)",
                        "default": 100
                    }
                },
                "required": ["schematic_id_1", "schematic_id_2"]
            }
        ),
        Tool(
            name="search_manufacturer_docs",
            description="Search manufacturer documentation for component specifications, datasheets, and manuals.",
            inputSchema={
                "type": "object",
                "properties": {
                    "query": {
                        "type": "string",
                        "description": "Search query (component ID, part number, manufacturer name)"
                    },
                    "component_type": {
                        "type": "string",
                        "description": "Optional: Filter by component type (VALVE, CYLINDER, PUMP, etc.)",
                        "enum": ["VALVE", "CYLINDER", "PUMP", "MOTOR", "FILTER", "TRANSDUCER"]
                    }
                },
                "required": ["query"]
            }
        ),
        Tool(
            name="list_schematics",
            description="List all available hydraulic schematics that have been analyzed.",
            inputSchema={
                "type": "object",
                "properties": {}
            }
        ),
        Tool(
            name="get_schematic_summary",
            description="Get a summary of a schematic including all components, flow paths, and analysis results.",
            inputSchema={
                "type": "object",
                "properties": {
                    "schematic_id": {
                        "type": "integer",
                        "description": "ID of the schematic"
                    }
                },
                "required": ["schematic_id"]
            }
        ),
        Tool(
            name="index_manufacturer_docs",
            description="Index all manufacturer documentation PDFs in the manufacturer_docs folder. Run this after adding new documentation.",
            inputSchema={
                "type": "object",
                "properties": {
                    "force_reindex": {
                        "type": "boolean",
                        "description": "Force re-indexing of all documents (default: false)",
                        "default": False
                    }
                },
                "required": []
            }
        )
    ]


@app.call_tool()
async def call_tool(name: str, arguments: Any) -> Sequence[TextContent]:
    """Handle tool calls"""
    try:
        logger.info(f"Tool called: {name} with arguments: {arguments}")

        if name == "analyze_schematic":
            return await analyze_schematic_tool(arguments)

        elif name == "find_flow_path":
            return await find_flow_path_tool(arguments)

        elif name == "analyze_restrictions":
            return await analyze_restrictions_tool(arguments)

        elif name == "get_component_impact":
            return await get_component_impact_tool(arguments)

        elif name == "compare_machines":
            return await compare_machines_tool(arguments)

        elif name == "search_manufacturer_docs":
            return await search_manufacturer_docs_tool(arguments)

        elif name == "list_schematics":
            return await list_schematics_tool(arguments)

        elif name == "get_schematic_summary":
            return await get_schematic_summary_tool(arguments)

        elif name == "index_manufacturer_docs":
            return await index_manufacturer_docs_tool(arguments)

        else:
            return [TextContent(
                type="text",
                text=f"Unknown tool: {name}"
            )]

    except Exception as e:
        logger.error(f"Error in tool {name}: {e}", exc_info=True)
        return [TextContent(
            type="text",
            text=f"Error: {str(e)}"
        )]


# === Tool Implementations ===

async def analyze_schematic_tool(arguments: dict) -> Sequence[TextContent]:
    """Analyze a hydraulic schematic"""
    file_path = Path(arguments['file_path'])
    machine_name = arguments['machine_name']

    if not file_path.exists():
        return [TextContent(type="text", text=f"Error: File not found: {file_path}")]

    # Check if already analyzed
    existing = db.get_schematic_by_path(str(file_path))
    if existing:
        return [TextContent(
            type="text",
            text=f"Schematic already analyzed. Schematic ID: {existing['id']}\n\n" +
                 f"Use get_schematic_summary with schematic_id={existing['id']} for details."
        )]

    # Parse schematic
    logger.info(f"Parsing schematic: {file_path}")
    parsed_data = parser.parse_schematic(file_path)

    # Store in database
    schematic_id = db.add_schematic(
        machine_name=machine_name,
        file_path=str(file_path),
        file_hash=parsed_data['file_hash'],
        raw_analysis=parsed_data,
        metadata=parsed_data.get('metadata', {})
    )

    # Store components
    for component in parsed_data.get('components', []):
        db.add_component(schematic_id, component)

    # Store relationships
    for connection in parsed_data.get('connections', []):
        db.add_relationship(schematic_id, {
            'from_component': connection['from'],
            'to_component': connection['to'],
            'relationship_type': connection.get('type', 'CONNECTS_TO'),
            'connection_type': connection.get('type'),
            'line_size': connection.get('line_size'),
            'metadata': connection
        })

    # Create summary
    summary = f"""# Schematic Analysis Complete

**Machine**: {machine_name}
**Schematic ID**: {schematic_id}
**File**: {file_path}

## Summary
- **Components Found**: {len(parsed_data.get('components', []))}
- **Connections**: {len(parsed_data.get('connections', []))}
- **Flow Paths**: {len(parsed_data.get('flow_paths', []))}

## Components by Type
"""

    # Count by type
    components = parsed_data.get('components', [])
    type_counts = {}
    for comp in components:
        comp_type = comp.get('type', 'UNKNOWN')
        type_counts[comp_type] = type_counts.get(comp_type, 0) + 1

    for comp_type, count in sorted(type_counts.items()):
        summary += f"- {comp_type}: {count}\n"

    summary += f"\n## Identified Flow Paths\n"
    for flow_path in parsed_data.get('flow_paths', []):
        summary += f"- **{flow_path.get('name')}**: {flow_path.get('description')}\n"
        summary += f"  Components: {', '.join(flow_path.get('components', []))}\n"

    summary += f"\n## Next Steps\n"
    summary += f"- Use `find_flow_path` to analyze specific flow paths\n"
    summary += f"- Use `analyze_restrictions` to find bottlenecks\n"
    summary += f"- Use `get_component_impact` to analyze component relationships\n"

    return [TextContent(type="text", text=summary)]


async def find_flow_path_tool(arguments: dict) -> Sequence[TextContent]:
    """Find and analyze flow path"""
    schematic_id = arguments['schematic_id']
    start_component = arguments['start_component']
    end_component = arguments['end_component']
    flow_rate_lpm = arguments.get('flow_rate_lpm', 100)
    pressure_bar = arguments.get('pressure_bar', 200)

    # Get schematic data
    schematic = db.get_schematic(schematic_id)
    if not schematic:
        return [TextContent(type="text", text=f"Error: Schematic {schematic_id} not found")]

    schematic_data = json.loads(schematic['raw_analysis'])

    # Find path
    path_result = parser.find_flow_path(schematic_data, start_component, end_component)

    if not path_result.get('path_found'):
        return [TextContent(type="text", text=f"No flow path found between {start_component} and {end_component}")]

    # Analyze path
    flow_analysis = analyzer.analyze_flow_path(
        path_result['path_details'],
        flow_rate_lpm,
        pressure_bar
    )

    # Store flow path
    db.add_flow_path(schematic_id, {
        'path_name': f"{start_component} to {end_component}",
        'start_component': start_component,
        'end_component': end_component,
        'components_in_path': path_result['path'],
        'total_restrictions': flow_analysis['total_pressure_drop_bar'],
        'bottleneck_component': flow_analysis['bottleneck']['component_id'] if flow_analysis['bottleneck'] else None,
        'analysis_data': flow_analysis
    })

    # Format response
    response = f"""# Flow Path Analysis: {start_component} → {end_component}

{flow_analysis['analysis']}

## Path Details
"""

    for comp in flow_analysis['component_pressure_drops']:
        response += f"\n### {comp['component_id']} - {comp['description']}"
        response += f"\n- Type: {comp['type']}"
        response += f"\n- Pressure Drop: {comp['pressure_drop_bar']:.2f} bar ({comp['pressure_drop_psi']:.1f} PSI)"
        response += f"\n- Percent of Total: {comp['percent_of_total']:.1f}%"

    if flow_analysis['restrictions']:
        response += f"\n\n## Identified Restrictions\n"
        for restriction in flow_analysis['restrictions']:
            response += f"\n- **{restriction['component_id']}**: {restriction['restriction_type']}"
            response += f"\n  - Severity: {restriction['severity']}"
            response += f"\n  - Details: {restriction['details']}\n"

    return [TextContent(type="text", text=response)]


async def analyze_restrictions_tool(arguments: dict) -> Sequence[TextContent]:
    """Analyze restrictions in schematic"""
    schematic_id = arguments['schematic_id']
    flow_rate_lpm = arguments.get('flow_rate_lpm', 100)

    # Get schematic data
    schematic = db.get_schematic(schematic_id)
    if not schematic:
        return [TextContent(type="text", text=f"Error: Schematic {schematic_id} not found")]

    schematic_data = json.loads(schematic['raw_analysis'])

    # Find restrictions
    restrictions = analyzer.find_restrictions(schematic_data, flow_rate_lpm)

    response = f"# Restriction Analysis\n\n"
    response += f"**Flow Rate**: {flow_rate_lpm} LPM\n"
    response += f"**Restrictions Found**: {len(restrictions)}\n\n"

    if not restrictions:
        response += "No significant restrictions identified at this flow rate.\n"
    else:
        for r in restrictions:
            response += f"## {r['component_id']}\n"
            response += f"- **Type**: {r['type']}\n"
            response += f"- **Severity**: {r['severity']}\n"
            response += f"- **Details**: {r['details']}\n"
            response += f"- **Recommendation**: {r.get('recommendation', 'Review component sizing')}\n\n"

    return [TextContent(type="text", text=response)]


async def get_component_impact_tool(arguments: dict) -> Sequence[TextContent]:
    """Get component impact analysis"""
    schematic_id = arguments['schematic_id']
    component_id = arguments['component_id']

    # Get schematic data
    schematic = db.get_schematic(schematic_id)
    if not schematic:
        return [TextContent(type="text", text=f"Error: Schematic {schematic_id} not found")]

    schematic_data = json.loads(schematic['raw_analysis'])

    # Analyze impact
    impact = parser.analyze_component_impact(schematic_data, component_id)

    if 'error' in impact:
        return [TextContent(type="text", text=f"Error: {impact['error']}")]

    component = impact['component']
    response = f"# Component Impact Analysis: {component_id}\n\n"
    response += f"**Type**: {component.get('type')}\n"
    response += f"**Description**: {component.get('description')}\n\n"

    response += f"## Upstream Components (Supply)\n"
    response += f"Total: {impact['total_upstream']}\n\n"
    for comp in impact['upstream_components']:
        response += f"- **{comp['component_id']}**: {comp['component'].get('description', 'N/A')}\n"
        response += f"  - Type: {comp['component'].get('type')}\n"
        response += f"  - Connection: {comp.get('connection_type')}\n"
        if comp.get('line_size'):
            response += f"  - Line Size: {comp['line_size']}\n"

    response += f"\n## Downstream Components (Affected)\n"
    response += f"Total: {impact['total_downstream']}\n\n"
    for comp in impact['downstream_components']:
        response += f"- **{comp['component_id']}**: {comp['component'].get('description', 'N/A')}\n"
        response += f"  - Type: {comp['component'].get('type')}\n"
        response += f"  - Connection: {comp.get('connection_type')}\n"
        if comp.get('line_size'):
            response += f"  - Line Size: {comp['line_size']}\n"

    return [TextContent(type="text", text=response)]


async def compare_machines_tool(arguments: dict) -> Sequence[TextContent]:
    """Compare two machine schematics"""
    schematic_id_1 = arguments['schematic_id_1']
    schematic_id_2 = arguments['schematic_id_2']
    flow_rate_lpm = arguments.get('flow_rate_lpm', 100)

    # Get schematics
    schematic1 = db.get_schematic(schematic_id_1)
    schematic2 = db.get_schematic(schematic_id_2)

    if not schematic1 or not schematic2:
        return [TextContent(type="text", text="Error: One or both schematics not found")]

    data1 = json.loads(schematic1['raw_analysis'])
    data2 = json.loads(schematic2['raw_analysis'])

    machine1 = schematic1['machine_name']
    machine2 = schematic2['machine_name']

    # Compare components
    comps1 = {c['id']: c for c in data1.get('components', [])}
    comps2 = {c['id']: c for c in data2.get('components', [])}

    only_in_1 = set(comps1.keys()) - set(comps2.keys())
    only_in_2 = set(comps2.keys()) - set(comps1.keys())
    in_both = set(comps1.keys()) & set(comps2.keys())

    response = f"# Machine Comparison: {machine1} vs {machine2}\n\n"
    response += f"## Component Comparison\n"
    response += f"- **{machine1}**: {len(comps1)} components\n"
    response += f"- **{machine2}**: {len(comps2)} components\n"
    response += f"- **In Both**: {len(in_both)} components\n"
    response += f"- **Only in {machine1}**: {len(only_in_1)} components\n"
    response += f"- **Only in {machine2}**: {len(only_in_2)} components\n\n"

    if only_in_1:
        response += f"### Components Only in {machine1}\n"
        for comp_id in sorted(only_in_1):
            comp = comps1[comp_id]
            response += f"- {comp_id}: {comp.get('description')} ({comp.get('type')})\n"

    if only_in_2:
        response += f"\n### Components Only in {machine2}\n"
        for comp_id in sorted(only_in_2):
            comp = comps2[comp_id]
            response += f"- {comp_id}: {comp.get('description')} ({comp.get('type')})\n"

    # Compare restrictions
    restrictions1 = analyzer.find_restrictions(data1, flow_rate_lpm)
    restrictions2 = analyzer.find_restrictions(data2, flow_rate_lpm)

    response += f"\n## Restriction Comparison (at {flow_rate_lpm} LPM)\n"
    response += f"- **{machine1}**: {len(restrictions1)} restrictions\n"
    response += f"- **{machine2}**: {len(restrictions2)} restrictions\n"

    return [TextContent(type="text", text=response)]


async def search_manufacturer_docs_tool(arguments: dict) -> Sequence[TextContent]:
    """Search manufacturer documentation"""
    query = arguments['query']
    component_type = arguments.get('component_type')

    results = doc_manager.search_docs(query, component_type)

    response = f"# Documentation Search: '{query}'\n\n"
    response += f"**Results Found**: {len(results)}\n\n"

    if not results:
        response += "No matching documentation found.\n\n"
        response += "Try:\n"
        response += "- Running `index_manufacturer_docs` to index new documents\n"
        response += "- Using different search terms\n"
        response += "- Adding manufacturer PDFs to the manufacturer_docs folder\n"
    else:
        for i, result in enumerate(results[:10], 1):  # Top 10
            response += f"## {i}. {Path(result['file_path']).name}\n"
            response += f"- **Relevance**: {result['relevance_score']}\n"
            if result.get('manufacturer'):
                response += f"- **Manufacturer**: {result['manufacturer']}\n"
            if result.get('component_types'):
                response += f"- **Component Types**: {', '.join(result['component_types'])}\n"
            if result.get('part_numbers'):
                response += f"- **Part Numbers**: {', '.join(result['part_numbers'][:5])}\n"
            response += f"- **Path**: {result['file_path']}\n\n"

    return [TextContent(type="text", text=response)]


async def list_schematics_tool(arguments: dict) -> Sequence[TextContent]:
    """List all schematics"""
    schematics = db.list_schematics()

    response = "# Available Schematics\n\n"
    response += f"**Total**: {len(schematics)}\n\n"

    for schematic in schematics:
        response += f"## ID: {schematic['id']} - {schematic['machine_name']}\n"
        response += f"- **File**: {schematic['file_path']}\n"
        response += f"- **Parsed**: {schematic['parsed_date']}\n\n"

    if not schematics:
        response += "No schematics analyzed yet.\n\n"
        response += "Use `analyze_schematic` to add a schematic.\n"

    return [TextContent(type="text", text=response)]


async def get_schematic_summary_tool(arguments: dict) -> Sequence[TextContent]:
    """Get schematic summary"""
    schematic_id = arguments['schematic_id']

    schematic = db.get_schematic(schematic_id)
    if not schematic:
        return [TextContent(type="text", text=f"Error: Schematic {schematic_id} not found")]

    components = db.get_components_for_schematic(schematic_id)
    relationships = db.get_relationships(schematic_id)
    flow_paths = db.get_flow_paths(schematic_id)

    response = f"# Schematic Summary: {schematic['machine_name']}\n\n"
    response += f"**ID**: {schematic_id}\n"
    response += f"**File**: {schematic['file_path']}\n"
    response += f"**Parsed**: {schematic['parsed_date']}\n\n"

    response += f"## Statistics\n"
    response += f"- **Components**: {len(components)}\n"
    response += f"- **Connections**: {len(relationships)}\n"
    response += f"- **Analyzed Flow Paths**: {len(flow_paths)}\n\n"

    # Component breakdown
    type_counts = {}
    for comp in components:
        comp_type = comp['component_type']
        type_counts[comp_type] = type_counts.get(comp_type, 0) + 1

    response += f"## Components by Type\n"
    for comp_type, count in sorted(type_counts.items()):
        response += f"- {comp_type}: {count}\n"

    # Flow paths
    if flow_paths:
        response += f"\n## Analyzed Flow Paths\n"
        for path in flow_paths:
            response += f"\n### {path['path_name']}\n"
            response += f"- Start: {path['start_component']}\n"
            response += f"- End: {path['end_component']}\n"
            response += f"- Total Pressure Drop: {path['total_restrictions']:.2f} bar\n"
            if path['bottleneck_component']:
                response += f"- Bottleneck: {path['bottleneck_component']}\n"

    return [TextContent(type="text", text=response)]


async def index_manufacturer_docs_tool(arguments: dict) -> Sequence[TextContent]:
    """Index manufacturer documentation"""
    force_reindex = arguments.get('force_reindex', False)

    results = doc_manager.index_documentation(force_reindex)

    response = f"# Documentation Indexing Complete\n\n"
    response += f"- **Total Files**: {results['total_files']}\n"
    response += f"- **Indexed**: {results['indexed']}\n"
    response += f"- **Skipped**: {results['skipped']}\n"
    response += f"- **Errors**: {results['errors']}\n\n"

    if results['files']:
        response += f"## Indexed Files\n"
        for file_info in results['files']:
            response += f"\n### {Path(file_info['file']).name}\n"
            if file_info.get('manufacturer'):
                response += f"- Manufacturer: {file_info['manufacturer']}\n"
            if file_info.get('component_types'):
                response += f"- Component Types: {', '.join(file_info['component_types'])}\n"
            if file_info.get('part_numbers'):
                response += f"- Part Numbers: {', '.join(file_info['part_numbers'][:5])}\n"

    return [TextContent(type="text", text=response)]


# === Main Entry Point ===

async def main():
    """Main entry point for MCP server"""
    # Validate configuration
    valid, error = config.validate()
    if not valid:
        logger.error(f"Configuration error: {error}")
        print(f"ERROR: {error}")
        return

    logger.info("Starting Hydraulic Analysis MCP Server")
    logger.info(f"Schematics directory: {config.schematics_dir}")
    logger.info(f"Manufacturer docs directory: {config.manufacturer_docs_dir}")
    logger.info(f"Database: {config.db_path}")

    async with stdio_server() as (read_stream, write_stream):
        await app.run(
            read_stream,
            write_stream,
            app.create_initialization_options()
        )


if __name__ == "__main__":
    asyncio.run(main())
