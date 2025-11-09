"""
Schematic parser using vision AI to extract hydraulic components and connections
"""
import base64
import hashlib
import logging
from pathlib import Path
from typing import Dict, List, Optional, Any
import json
import re

try:
    import openai
except ImportError:
    openai = None

from config import config

logger = logging.getLogger(__name__)


class SchematicParser:
    """Parse hydraulic schematics using vision AI"""

    def __init__(self):
        self.config = config

        if openai is None:
            raise ImportError("openai package not installed. Run: pip install openai")

        # Configure OpenAI client
        self.client = openai.OpenAI(
            api_key=self.config.api_key,
            base_url=self.config.api_base
        )

    def encode_image(self, image_path: Path) -> str:
        """Encode image to base64"""
        with open(image_path, "rb") as image_file:
            return base64.b64encode(image_file.read()).decode('utf-8')

    def calculate_file_hash(self, file_path: Path) -> str:
        """Calculate SHA256 hash of file"""
        sha256_hash = hashlib.sha256()
        with open(file_path, "rb") as f:
            for byte_block in iter(lambda: f.read(4096), b""):
                sha256_hash.update(byte_block)
        return sha256_hash.hexdigest()

    def parse_schematic(self, image_path: Path) -> Dict[str, Any]:
        """
        Parse hydraulic schematic from image file

        Returns:
            Dictionary containing:
            - components: List of identified components
            - connections: List of connections between components
            - flow_paths: Identified major flow paths
            - metadata: Schematic metadata (title, machine type, etc.)
        """
        logger.info(f"Parsing schematic: {image_path}")

        # Encode image
        if image_path.suffix.lower() in ['.pdf']:
            # For PDFs, we'd need to convert to images first
            # For now, assume images only
            raise ValueError("PDF parsing not yet implemented. Convert to PNG/JPG first.")

        base64_image = self.encode_image(image_path)

        # Prepare the analysis prompt
        analysis_prompt = self._get_analysis_prompt()

        # Call vision AI
        try:
            response = self.client.chat.completions.create(
                model=self.config.vision_model,
                messages=[
                    {
                        "role": "user",
                        "content": [
                            {
                                "type": "text",
                                "text": analysis_prompt
                            },
                            {
                                "type": "image_url",
                                "image_url": {
                                    "url": f"data:image/jpeg;base64,{base64_image}"
                                }
                            }
                        ]
                    }
                ],
                max_tokens=4000
            )

            # Extract response
            raw_response = response.choices[0].message.content
            logger.debug(f"AI Response: {raw_response}")

            # Parse structured data from response
            parsed_data = self._parse_ai_response(raw_response)

            # Add file metadata
            parsed_data['file_hash'] = self.calculate_file_hash(image_path)
            parsed_data['file_path'] = str(image_path)
            parsed_data['raw_response'] = raw_response

            return parsed_data

        except Exception as e:
            logger.error(f"Error parsing schematic: {e}")
            raise

    def _get_analysis_prompt(self) -> str:
        """Get the prompt for schematic analysis"""
        return """Analyze this hydraulic schematic diagram and extract the following information in JSON format:

{
  "metadata": {
    "machine_name": "Machine name or model if visible",
    "schematic_title": "Title of the schematic",
    "sheet_number": "Sheet number if visible",
    "revision": "Revision number if visible",
    "company": "Company name if visible"
  },
  "components": [
    {
      "id": "Component ID (e.g., H203, V12, P1)",
      "type": "Component type (CYLINDER, VALVE, PUMP, MOTOR, FILTER, TRANSDUCER, etc.)",
      "description": "Component description",
      "grid_location": "Grid location on schematic (e.g., A-5, B-12)",
      "manufacturer": "Manufacturer if visible",
      "part_number": "Part number if visible",
      "specifications": {
        "bore_mm": "Cylinder bore in mm (if applicable)",
        "stroke_mm": "Cylinder stroke in mm (if applicable)",
        "pressure_bar": "Max pressure in bar (if applicable)",
        "flow_lpm": "Flow rate in LPM (if applicable)",
        "size": "Port size or valve size"
      },
      "connections": ["List of component IDs this connects to"]
    }
  ],
  "connections": [
    {
      "from": "Source component ID",
      "to": "Destination component ID",
      "type": "Connection type (PRESSURE, TANK, SIGNAL, DRAIN)",
      "line_size": "Line size if labeled (e.g., 1/2\", 3/4\")",
      "flow_direction": "Direction of flow if indicated (FORWARD, REVERSE, BIDIRECTIONAL)"
    }
  ],
  "flow_paths": [
    {
      "name": "Flow path name (e.g., Main Press Circuit, Eject Circuit)",
      "components": ["Ordered list of component IDs in flow path"],
      "description": "Brief description of what this flow path does"
    }
  ],
  "notes": [
    "Any important notes, warnings, or special instructions visible on the schematic"
  ]
}

IMPORTANT INSTRUCTIONS:
1. Be thorough - identify ALL components visible on the schematic
2. Capture component IDs exactly as labeled (H203, V12-3A, etc.)
3. Trace connections carefully - every line represents a connection
4. Identify standard hydraulic symbols:
   - Cylinders (rectangle with piston)
   - Valves (squares with internal symbols)
   - Pumps (circle with arrow)
   - Motors (circle with M)
   - Filters (diamond shape)
   - Pressure/flow lines (solid lines)
   - Pilot/signal lines (dashed lines)
   - Drain/tank lines (dotted lines)
5. Note grid locations to help locate components
6. Extract specifications from labels where visible
7. Identify major flow paths through the system

Return ONLY the JSON structure, no additional commentary."""

    def _parse_ai_response(self, response: str) -> Dict[str, Any]:
        """Parse AI response into structured data"""
        # Try to extract JSON from response
        # Sometimes the model wraps JSON in markdown code blocks
        json_match = re.search(r'```json\s*(.*?)\s*```', response, re.DOTALL)
        if json_match:
            json_str = json_match.group(1)
        else:
            # Try to find raw JSON
            json_match = re.search(r'\{.*\}', response, re.DOTALL)
            if json_match:
                json_str = json_match.group(0)
            else:
                # Fallback: use entire response
                json_str = response

        try:
            data = json.loads(json_str)
            return data
        except json.JSONDecodeError as e:
            logger.error(f"Failed to parse JSON from AI response: {e}")
            logger.debug(f"Response was: {response}")

            # Return minimal structure
            return {
                "metadata": {},
                "components": [],
                "connections": [],
                "flow_paths": [],
                "notes": [],
                "parse_error": str(e),
                "raw_response": response
            }

    def analyze_component_impact(self, schematic_data: Dict, component_id: str) -> Dict[str, Any]:
        """
        Analyze what components impact or are impacted by a specific component

        Args:
            schematic_data: Parsed schematic data
            component_id: Component to analyze

        Returns:
            Dictionary with upstream and downstream components
        """
        components = {c['id']: c for c in schematic_data.get('components', [])}
        connections = schematic_data.get('connections', [])

        if component_id not in components:
            return {"error": f"Component {component_id} not found"}

        # Find upstream (supply) connections
        upstream = []
        for conn in connections:
            if conn['to'] == component_id:
                upstream.append({
                    'component_id': conn['from'],
                    'component': components.get(conn['from'], {}),
                    'connection_type': conn.get('type'),
                    'line_size': conn.get('line_size')
                })

        # Find downstream (affected) connections
        downstream = []
        for conn in connections:
            if conn['from'] == component_id:
                downstream.append({
                    'component_id': conn['to'],
                    'component': components.get(conn['to'], {}),
                    'connection_type': conn.get('type'),
                    'line_size': conn.get('line_size')
                })

        return {
            'component': components[component_id],
            'upstream_components': upstream,
            'downstream_components': downstream,
            'total_upstream': len(upstream),
            'total_downstream': len(downstream)
        }

    def find_flow_path(self, schematic_data: Dict, start_component: str,
                      end_component: str, max_depth: int = 20) -> Dict[str, Any]:
        """
        Find flow path between two components

        Args:
            schematic_data: Parsed schematic data
            start_component: Starting component ID
            end_component: Ending component ID
            max_depth: Maximum path depth

        Returns:
            Dictionary with path information
        """
        components = {c['id']: c for c in schematic_data.get('components', [])}
        connections = schematic_data.get('connections', [])

        if start_component not in components or end_component not in components:
            return {"error": "Start or end component not found"}

        # Build adjacency graph
        graph = {}
        for conn in connections:
            if conn['from'] not in graph:
                graph[conn['from']] = []
            graph[conn['from']].append({
                'to': conn['to'],
                'type': conn.get('type'),
                'line_size': conn.get('line_size')
            })

        # BFS to find path
        from collections import deque

        queue = deque([(start_component, [start_component])])
        visited = {start_component}

        while queue:
            current, path = queue.popleft()

            if len(path) > max_depth:
                continue

            if current == end_component:
                # Found path!
                path_details = []
                for i, comp_id in enumerate(path):
                    comp_data = components.get(comp_id, {})
                    path_details.append({
                        'position': i,
                        'component_id': comp_id,
                        'type': comp_data.get('type'),
                        'description': comp_data.get('description'),
                        'specifications': comp_data.get('specifications', {})
                    })

                return {
                    'path_found': True,
                    'path': path,
                    'path_length': len(path),
                    'path_details': path_details
                }

            # Explore neighbors
            for neighbor in graph.get(current, []):
                neighbor_id = neighbor['to']
                if neighbor_id not in visited:
                    visited.add(neighbor_id)
                    queue.append((neighbor_id, path + [neighbor_id]))

        return {
            'path_found': False,
            'error': f'No path found between {start_component} and {end_component}'
        }
