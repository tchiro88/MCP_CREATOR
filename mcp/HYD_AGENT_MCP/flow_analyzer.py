"""
Flow path and restriction analysis for hydraulic systems
"""
import logging
import math
from typing import Dict, List, Optional, Any, Tuple

logger = logging.getLogger(__name__)


class FlowAnalyzer:
    """Analyze hydraulic flow paths and calculate restrictions"""

    # Standard hydraulic fluid properties (ISO VG 46 at 40°C)
    FLUID_DENSITY = 870  # kg/m³
    FLUID_VISCOSITY = 0.046  # Pa·s (46 cSt)

    # Component resistance coefficients (K factors)
    COMPONENT_K_FACTORS = {
        'VALVE_BALL': 0.1,
        'VALVE_CHECK': 2.0,
        'VALVE_PROPORTIONAL': 1.5,
        'VALVE_DIRECTIONAL': 3.0,
        'VALVE_RELIEF': 0.5,
        'FILTER': 5.0,
        'ELBOW_90': 0.9,
        'TEE_BRANCH': 1.8,
        'CYLINDER': 0.5,
        'MANIFOLD': 2.0,
    }

    def __init__(self):
        pass

    def analyze_flow_path(self, path_details: List[Dict], flow_rate_lpm: float,
                         pressure_bar: float) -> Dict[str, Any]:
        """
        Analyze a flow path for restrictions and pressure drops

        Args:
            path_details: List of components in path (from find_flow_path)
            flow_rate_lpm: Design flow rate in liters per minute
            pressure_bar: System pressure in bar

        Returns:
            Analysis including total pressure drop, restrictions, bottlenecks
        """
        logger.info(f"Analyzing flow path with {len(path_details)} components at {flow_rate_lpm} LPM")

        # Convert units
        flow_rate_m3s = flow_rate_lpm / 60000  # L/min to m³/s
        pressure_pa = pressure_bar * 1e5  # bar to Pa

        total_pressure_drop = 0
        component_drops = []
        restrictions = []

        for comp in path_details:
            comp_id = comp['component_id']
            comp_type = comp.get('type', 'UNKNOWN')
            specs = comp.get('specifications', {})

            # Calculate pressure drop for this component
            pressure_drop, restriction_info = self._calculate_component_pressure_drop(
                comp_type, specs, flow_rate_m3s, pressure_pa
            )

            total_pressure_drop += pressure_drop

            component_drops.append({
                'component_id': comp_id,
                'type': comp_type,
                'description': comp.get('description'),
                'pressure_drop_bar': pressure_drop / 1e5,
                'pressure_drop_psi': pressure_drop / 6894.76,
                'percent_of_total': 0  # Will calculate after
            })

            if restriction_info:
                restrictions.append({
                    'component_id': comp_id,
                    'restriction_type': restriction_info['type'],
                    'severity': restriction_info['severity'],
                    'details': restriction_info['details']
                })

        # Calculate percentages
        for drop in component_drops:
            if total_pressure_drop > 0:
                drop['percent_of_total'] = (drop['pressure_drop_bar'] * 1e5 / total_pressure_drop) * 100

        # Find bottleneck (component with highest pressure drop)
        bottleneck = max(component_drops, key=lambda x: x['pressure_drop_bar']) if component_drops else None

        # Overall assessment
        total_drop_bar = total_pressure_drop / 1e5
        efficiency = self._calculate_path_efficiency(total_drop_bar, pressure_bar)

        return {
            'flow_rate_lpm': flow_rate_lpm,
            'system_pressure_bar': pressure_bar,
            'total_pressure_drop_bar': total_drop_bar,
            'total_pressure_drop_psi': total_pressure_drop / 6894.76,
            'efficiency_percent': efficiency,
            'component_pressure_drops': component_drops,
            'bottleneck': bottleneck,
            'restrictions': restrictions,
            'analysis': self._generate_analysis_text(
                total_drop_bar, pressure_bar, efficiency, bottleneck, restrictions
            )
        }

    def _calculate_component_pressure_drop(self, comp_type: str, specs: Dict,
                                          flow_rate: float, pressure: float) -> Tuple[float, Optional[Dict]]:
        """
        Calculate pressure drop through a component

        Returns:
            (pressure_drop_pa, restriction_info)
        """
        # Get K factor for component type
        k_factor = self.COMPONENT_K_FACTORS.get(
            comp_type,
            self.COMPONENT_K_FACTORS.get(f'VALVE_{comp_type}', 3.0)  # Default to directional valve
        )

        # Try to get actual port size or valve size
        port_size = self._parse_size(specs.get('size', specs.get('port_size', '1/2"')))

        # Calculate flow area
        area = math.pi * (port_size / 2) ** 2

        # Calculate velocity
        velocity = flow_rate / area if area > 0 else 0

        # Pressure drop using Darcy-Weisbach style equation with K factor
        # ΔP = K * (ρ * v²) / 2
        pressure_drop = k_factor * (self.FLUID_DENSITY * velocity ** 2) / 2

        # Check for restrictions
        restriction_info = None

        # High velocity indicates restriction
        if velocity > 5.0:  # m/s - typical max recommended is 4-5 m/s
            restriction_info = {
                'type': 'HIGH_VELOCITY',
                'severity': 'HIGH' if velocity > 7.0 else 'MEDIUM',
                'details': f'Flow velocity {velocity:.2f} m/s exceeds recommended 5.0 m/s'
            }

        # Small port size relative to flow rate
        reynolds = (self.FLUID_DENSITY * velocity * port_size) / self.FLUID_VISCOSITY
        if reynolds > 4000:  # Turbulent flow
            restriction_info = {
                'type': 'TURBULENT_FLOW',
                'severity': 'MEDIUM',
                'details': f'Reynolds number {reynolds:.0f} indicates turbulent flow'
            }

        # High pressure drop
        if pressure_drop > pressure * 0.1:  # More than 10% of system pressure
            restriction_info = {
                'type': 'HIGH_PRESSURE_DROP',
                'severity': 'HIGH',
                'details': f'Component causes {(pressure_drop/pressure)*100:.1f}% pressure drop'
            }

        return pressure_drop, restriction_info

    def _parse_size(self, size_str: str) -> float:
        """
        Parse size string to diameter in meters

        Examples: "1/2\"", "3/4\"", "20mm", "DN25"
        """
        size_str = str(size_str).strip().upper()

        # Fractional inches (e.g., "1/2\"", "3/4\"")
        if '/' in size_str:
            try:
                parts = size_str.replace('"', '').split('/')
                numerator = float(parts[0])
                denominator = float(parts[1])
                inches = numerator / denominator
                return inches * 0.0254  # Convert to meters
            except:
                pass

        # Decimal inches (e.g., "0.5\"")
        if '"' in size_str:
            try:
                inches = float(size_str.replace('"', ''))
                return inches * 0.0254
            except:
                pass

        # Millimeters (e.g., "20mm", "20MM")
        if 'MM' in size_str:
            try:
                mm = float(size_str.replace('MM', ''))
                return mm / 1000
            except:
                pass

        # DN size (e.g., "DN25")
        if 'DN' in size_str:
            try:
                dn = float(size_str.replace('DN', ''))
                return dn / 1000
            except:
                pass

        # Default to 1/2 inch (12.7mm)
        logger.warning(f"Could not parse size '{size_str}', using default 1/2 inch")
        return 0.0127

    def _calculate_path_efficiency(self, pressure_drop: float, system_pressure: float) -> float:
        """Calculate efficiency based on pressure losses"""
        if system_pressure == 0:
            return 0

        loss_percent = (pressure_drop / system_pressure) * 100
        efficiency = max(0, 100 - loss_percent)

        return efficiency

    def _generate_analysis_text(self, total_drop: float, system_pressure: float,
                                efficiency: float, bottleneck: Optional[Dict],
                                restrictions: List[Dict]) -> str:
        """Generate human-readable analysis text"""
        lines = []

        lines.append(f"Flow Path Analysis Summary:")
        lines.append(f"  Total pressure drop: {total_drop:.2f} bar ({total_drop * 14.5:.1f} PSI)")
        lines.append(f"  System pressure: {system_pressure:.2f} bar")
        lines.append(f"  Path efficiency: {efficiency:.1f}%")

        if bottleneck:
            lines.append(f"\n  Bottleneck: {bottleneck['component_id']} - {bottleneck['description']}")
            lines.append(f"    Pressure drop: {bottleneck['pressure_drop_bar']:.2f} bar ({bottleneck['percent_of_total']:.1f}% of total)")

        if restrictions:
            lines.append(f"\n  Identified restrictions:")
            for r in restrictions:
                lines.append(f"    - {r['component_id']}: {r['restriction_type']} (Severity: {r['severity']})")
                lines.append(f"      {r['details']}")

        if efficiency < 70:
            lines.append(f"\n  ⚠ WARNING: Path efficiency is below 70%. Consider:")
            lines.append(f"    - Increasing line sizes")
            lines.append(f"    - Reducing number of restrictions")
            lines.append(f"    - Using lower-restriction valves")

        return '\n'.join(lines)

    def find_restrictions(self, schematic_data: Dict, flow_rate_lpm: float = 100) -> List[Dict]:
        """
        Find all major restrictions in a schematic

        Args:
            schematic_data: Parsed schematic data
            flow_rate_lpm: Design flow rate for analysis

        Returns:
            List of restriction points with severity ratings
        """
        components = schematic_data.get('components', [])
        connections = schematic_data.get('connections', [])

        restrictions = []

        for comp in components:
            comp_type = comp.get('type', '')
            specs = comp.get('specifications', {})

            # Check for small port sizes
            size = specs.get('size', specs.get('port_size'))
            if size:
                diameter_m = self._parse_size(size)
                area = math.pi * (diameter_m / 2) ** 2
                velocity = (flow_rate_lpm / 60000) / area if area > 0 else 0

                if velocity > 5.0:
                    restrictions.append({
                        'component_id': comp['id'],
                        'type': 'UNDERSIZED_PORT',
                        'severity': 'HIGH' if velocity > 7.0 else 'MEDIUM',
                        'details': f'Port size {size} creates velocity of {velocity:.2f} m/s at {flow_rate_lpm} LPM',
                        'recommendation': f'Consider increasing to next size up for flow rates above {flow_rate_lpm * 0.7:.0f} LPM'
                    })

            # Check for series restrictions (multiple valves in series)
            comp_connections = [c for c in connections if c['from'] == comp['id']]
            if comp_type.startswith('VALVE') and len(comp_connections) > 2:
                restrictions.append({
                    'component_id': comp['id'],
                    'type': 'SERIES_RESTRICTION',
                    'severity': 'MEDIUM',
                    'details': f'Valve has {len(comp_connections)} downstream connections, may create restrictions',
                    'recommendation': 'Review circuit design for parallel paths'
                })

        # Sort by severity
        severity_order = {'HIGH': 0, 'MEDIUM': 1, 'LOW': 2}
        restrictions.sort(key=lambda x: severity_order.get(x['severity'], 3))

        return restrictions

    def compare_flow_paths(self, path1_analysis: Dict, path2_analysis: Dict,
                          path1_name: str = "Path 1", path2_name: str = "Path 2") -> Dict[str, Any]:
        """
        Compare two flow paths

        Args:
            path1_analysis: Analysis result from analyze_flow_path
            path2_analysis: Analysis result from analyze_flow_path
            path1_name: Name for first path
            path2_name: Name for second path

        Returns:
            Comparison results
        """
        comparison = {
            'path1_name': path1_name,
            'path2_name': path2_name,
            'pressure_drop_comparison': {
                path1_name: path1_analysis['total_pressure_drop_bar'],
                path2_name: path2_analysis['total_pressure_drop_bar'],
                'difference_bar': abs(path1_analysis['total_pressure_drop_bar'] -
                                    path2_analysis['total_pressure_drop_bar']),
                'better_path': path1_name if path1_analysis['total_pressure_drop_bar'] <
                              path2_analysis['total_pressure_drop_bar'] else path2_name
            },
            'efficiency_comparison': {
                path1_name: path1_analysis['efficiency_percent'],
                path2_name: path2_analysis['efficiency_percent'],
                'difference_percent': abs(path1_analysis['efficiency_percent'] -
                                        path2_analysis['efficiency_percent']),
                'better_path': path1_name if path1_analysis['efficiency_percent'] >
                              path2_analysis['efficiency_percent'] else path2_name
            },
            'restriction_comparison': {
                path1_name: len(path1_analysis['restrictions']),
                path2_name: len(path2_analysis['restrictions']),
                'better_path': path1_name if len(path1_analysis['restrictions']) <
                              len(path2_analysis['restrictions']) else path2_name
            }
        }

        # Generate summary
        summary_lines = []
        summary_lines.append(f"Flow Path Comparison: {path1_name} vs {path2_name}")
        summary_lines.append(f"\nPressure Drop:")
        summary_lines.append(f"  {path1_name}: {path1_analysis['total_pressure_drop_bar']:.2f} bar")
        summary_lines.append(f"  {path2_name}: {path2_analysis['total_pressure_drop_bar']:.2f} bar")
        summary_lines.append(f"  Winner: {comparison['pressure_drop_comparison']['better_path']}")

        summary_lines.append(f"\nEfficiency:")
        summary_lines.append(f"  {path1_name}: {path1_analysis['efficiency_percent']:.1f}%")
        summary_lines.append(f"  {path2_name}: {path2_analysis['efficiency_percent']:.1f}%")
        summary_lines.append(f"  Winner: {comparison['efficiency_comparison']['better_path']}")

        summary_lines.append(f"\nRestrictions:")
        summary_lines.append(f"  {path1_name}: {len(path1_analysis['restrictions'])} restrictions")
        summary_lines.append(f"  {path2_name}: {len(path2_analysis['restrictions'])} restrictions")
        summary_lines.append(f"  Winner: {comparison['restriction_comparison']['better_path']}")

        comparison['summary'] = '\n'.join(summary_lines)

        return comparison
