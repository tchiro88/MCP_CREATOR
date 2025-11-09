# Hydraulic Analysis MCP Server - Usage Guide

This guide provides practical examples and workflows for using the Hydraulic Analysis MCP Server with Claude Desktop, Cursor, or other MCP clients.

## Table of Contents

1. [Basic Concepts](#basic-concepts)
2. [MCP Tools Reference](#mcp-tools-reference)
3. [Common Workflows](#common-workflows)
4. [Example Conversations](#example-conversations)
5. [Advanced Usage](#advanced-usage)
6. [Tips & Tricks](#tips--tricks)

## Basic Concepts

### How It Works

1. **Drop schematics** into the `schematics/` folder
2. **Ask the AI** to analyze them using natural language
3. **The MCP server** processes your request using the appropriate tool
4. **Results** are stored in the database for future queries
5. **Continue asking** follow-up questions about the analysis

### Data Flow

```
Schematic Image → Vision AI Parser → Database → Flow Analyzer → Results
                                           ↓
                         Manufacturer Docs ← Doc Manager
```

### Key Terms

- **Schematic ID**: Unique identifier assigned when a schematic is analyzed
- **Component ID**: Component identifier from the schematic (e.g., H203, V12, P1)
- **Flow Path**: Sequence of components from start to end
- **Restriction**: Component or line that limits flow
- **Bottleneck**: Component with highest pressure drop in a path

## MCP Tools Reference

### 1. analyze_schematic

**Purpose**: Parse a schematic image and extract all components, connections, and flow paths.

**When to use**: First step with any new schematic.

**Parameters**:
- `file_path` (required): Path to schematic file relative to `schematics/` folder
- `machine_name` (required): Name of the machine

**Example**:
```
Analyze the schematic at schematics/baler_a_hydraulic.png for Baler A
```

**Returns**:
- Schematic ID
- Component count by type
- Identified flow paths
- Connection summary

---

### 2. find_flow_path

**Purpose**: Trace flow between two components and analyze pressure drops.

**When to use**: Understanding flow routes, finding pressure losses.

**Parameters**:
- `schematic_id` (required): ID from analyze_schematic
- `start_component` (required): Starting component ID (e.g., "P1")
- `end_component` (required): Ending component ID (e.g., "H203")
- `flow_rate_lpm` (optional): Design flow rate in LPM (default: 100)
- `pressure_bar` (optional): System pressure in bar (default: 200)

**Example**:
```
Find the flow path from P1 to H203 in schematic 1 at 150 LPM and 180 bar
```

**Returns**:
- Complete flow path
- Pressure drop at each component
- Total pressure loss
- Efficiency rating
- Bottleneck identification

---

### 3. analyze_restrictions

**Purpose**: Find all restrictions and bottlenecks in a schematic.

**When to use**: Identifying flow problems, optimizing hydraulic circuits.

**Parameters**:
- `schematic_id` (required): ID of schematic to analyze
- `flow_rate_lpm` (optional): Design flow rate (default: 100)

**Example**:
```
What are the biggest restrictions in schematic 1 at 200 LPM?
```

**Returns**:
- List of restrictions
- Severity ratings (HIGH/MEDIUM/LOW)
- Specific details (velocity, pressure drop, etc.)
- Recommendations

---

### 4. get_component_impact

**Purpose**: Analyze what affects a component and what it affects.

**When to use**: Understanding component relationships, troubleshooting.

**Parameters**:
- `schematic_id` (required): Schematic ID
- `component_id` (required): Component to analyze (e.g., "V12")

**Example**:
```
What components impact valve V12 in schematic 1?
```

**Returns**:
- Upstream components (supply/control)
- Downstream components (affected)
- Connection types
- Line sizes

---

### 5. compare_machines

**Purpose**: Compare hydraulic schematics from different machines.

**When to use**: Identifying design differences, evolution tracking.

**Parameters**:
- `schematic_id_1` (required): First schematic ID
- `schematic_id_2` (required): Second schematic ID
- `flow_rate_lpm` (optional): Flow rate for analysis (default: 100)

**Example**:
```
Compare schematic 1 (Baler A) and schematic 2 (Baler B)
```

**Returns**:
- Component differences
- Unique components in each
- Restriction comparison
- Performance differences

---

### 6. search_manufacturer_docs

**Purpose**: Search indexed manufacturer documentation.

**When to use**: Finding datasheets, specifications, part numbers.

**Parameters**:
- `query` (required): Search term
- `component_type` (optional): Filter by type (VALVE, CYLINDER, etc.)

**Example**:
```
Search for Parker proportional valve documentation
```

**Returns**:
- Matching documents
- Relevance scores
- Manufacturer info
- Part numbers
- File paths

---

### 7. list_schematics

**Purpose**: List all analyzed schematics in database.

**When to use**: Finding schematic IDs, checking what's available.

**Parameters**: None

**Example**:
```
List all available schematics
```

**Returns**:
- All schematics with IDs
- Machine names
- File paths
- Analysis dates

---

### 8. get_schematic_summary

**Purpose**: Get detailed overview of a schematic.

**When to use**: Understanding schematic contents, component breakdown.

**Parameters**:
- `schematic_id` (required): Schematic ID

**Example**:
```
Get summary of schematic 1
```

**Returns**:
- Component statistics
- Component breakdown by type
- Analyzed flow paths
- Connection count

---

### 9. index_manufacturer_docs

**Purpose**: Index all PDFs in manufacturer_docs folder.

**When to use**: After adding new documentation, initial setup.

**Parameters**:
- `force_reindex` (optional): Re-index all docs (default: false)

**Example**:
```
Index all manufacturer documentation
```

**Returns**:
- Indexing statistics
- Files indexed
- Extracted manufacturers
- Part numbers found

## Common Workflows

### Workflow 1: Analyzing a New Machine

**Scenario**: You receive a new hydraulic schematic and need to understand it.

**Steps**:

1. **Drop schematic** into `schematics/new_baler.png`

2. **Analyze it**:
   ```
   Analyze schematics/new_baler.png for New Baler Machine
   ```

3. **Get overview**:
   ```
   List all schematics
   Get summary of schematic 1
   ```

4. **Analyze main circuit**:
   ```
   Find the flow path from main pump P1 to press cylinder H203
   ```

5. **Check for problems**:
   ```
   What are the restrictions in this flow path?
   Analyze all restrictions in schematic 1 at 180 LPM
   ```

6. **Deep dive on specific component**:
   ```
   What components impact the main press cylinder H203?
   Search documentation for H203 specifications
   ```

---

### Workflow 2: Troubleshooting Flow Issues

**Scenario**: Machine has slow cycle times, suspected flow restriction.

**Steps**:

1. **Analyze restrictions** at operating flow rate:
   ```
   Analyze restrictions in schematic 1 at 200 LPM
   ```

2. **Check specific circuit**:
   ```
   Find flow path from pump P1 to slow cylinder H145 at 200 LPM
   ```

3. **Identify bottleneck**:
   ```
   What is the bottleneck in the path from P1 to H145?
   Which component has the highest pressure drop?
   ```

4. **Find documentation**:
   ```
   Search for documentation on the bottleneck component
   ```

5. **Compare with working machine**:
   ```
   Compare schematic 1 (problematic) with schematic 2 (working)
   What differences exist in the main press circuit?
   ```

---

### Workflow 3: Design Review

**Scenario**: Reviewing a new hydraulic design before manufacturing.

**Steps**:

1. **Analyze design**:
   ```
   Analyze schematics/new_design_rev3.png for New Design Rev 3
   ```

2. **Check all flow paths**:
   ```
   Find flow path from P1 to H203 at 150 LPM
   Find flow path from P1 to H145 at 100 LPM
   Find flow path from P2 to H302 at 80 LPM
   ```

3. **Identify issues**:
   ```
   Analyze all restrictions in schematic X at 180 LPM
   ```

4. **Compare with previous design**:
   ```
   Compare schematic X (new design) with schematic Y (old design)
   What improvements were made?
   Are there any new restrictions?
   ```

5. **Verify component selections**:
   ```
   Search documentation for valve V12-3A specifications
   Does V12-3A meet the flow requirements of 150 LPM?
   ```

---

### Workflow 4: Machine Comparison

**Scenario**: Comparing different machine models or vintages.

**Steps**:

1. **Analyze both schematics**:
   ```
   Analyze schematics/model_a.png for Model A
   Analyze schematics/model_b.png for Model B
   ```

2. **Compare overall**:
   ```
   Compare schematic 1 and schematic 2
   ```

3. **Specific comparisons**:
   ```
   What components are in Model A but not in Model B?
   How do the main press circuits differ?
   Which model has better flow efficiency?
   ```

4. **Analyze differences**:
   ```
   Find flow path from P1 to H203 in both schematics
   Compare the pressure drops
   Which design is more efficient?
   ```

---

### Workflow 5: Documentation Management

**Scenario**: Organizing and searching manufacturer documentation.

**Steps**:

1. **Add PDFs** to `manufacturer_docs/`:
   ```
   parker_valves_catalog.pdf
   danfoss_cylinders_datasheet.pdf
   nordon_press_cylinder_specs.pdf
   ```

2. **Index documentation**:
   ```
   Index all manufacturer documentation
   ```

3. **Search by manufacturer**:
   ```
   Search for Parker documentation
   ```

4. **Search by component type**:
   ```
   Search for cylinder documentation
   ```

5. **Search by part number**:
   ```
   Search for STH200-003-C specifications
   ```

6. **Component-specific**:
   ```
   What components impact H203?
   Search documentation for H203 Nordon cylinder
   ```

## Example Conversations

### Example 1: First-Time Analysis

**You**:
```
I have a hydraulic schematic for a new baler. The file is in schematics/baler_2024.png
Can you analyze it?
```

**AI**:
```
I'll analyze that schematic for you.

[Uses analyze_schematic tool]

✓ Schematic Analysis Complete

Machine: Baler 2024
Schematic ID: 1

Summary:
- Components Found: 87
- Connections: 124
- Flow Paths: 5

Components by Type:
- VALVE: 42
- CYLINDER: 8
- PUMP: 3
- MOTOR: 2
- FILTER: 4
- TRANSDUCER: 12
- MANIFOLD: 6
- Other: 10

Identified Flow Paths:
- Main Press Circuit: P1 → V12 → V15 → H203
- Eject Circuit: P1 → V18 → H145
- Feed Circuit: P2 → V25 → H180
- Auxiliary Circuit: P3 → V30 → Various

Would you like me to analyze any specific flow path or component?
```

**You**:
```
Yes, analyze the Main Press Circuit from P1 to H203 at 180 LPM operating pressure
```

**AI**:
```
[Uses find_flow_path tool with flow_rate_lpm=180, pressure_bar=180]

✓ Flow Path Analysis: P1 → H203

Total pressure drop: 12.4 bar (180 PSI)
System pressure: 180 bar
Path efficiency: 93.1%

Bottleneck: V15 - Proportional control valve
  Pressure drop: 8.2 bar (66% of total)

Path Details:

1. P1 - Main hydraulic pump
   - Pressure drop: 0 bar (source)

2. V12 - Directional control valve
   - Pressure drop: 2.1 bar (17%)

3. V15 - Proportional control valve ⚠ BOTTLENECK
   - Pressure drop: 8.2 bar (66%)

4. H203 - Main press cylinder
   - Pressure drop: 2.1 bar (17%)

⚠ NOTE: V15 accounts for 66% of pressure loss. Consider:
  - Increasing valve size
  - Checking valve for restriction
  - Verifying valve is sized for 180 LPM
```

---

### Example 2: Troubleshooting

**You**:
```
Our press is running slower than expected. Can you find restrictions in schematic 1?
What flow rate should I use for the analysis?
```

**AI**:
```
For press analysis, I'd recommend using your design or operating flow rate.
Typical press systems run at 100-200 LPM. What flow rate does your press normally operate at?
```

**You**:
```
We're running at 180 LPM
```

**AI**:
```
[Uses analyze_restrictions with flow_rate_lpm=180]

✓ Restriction Analysis at 180 LPM

Restrictions Found: 4

HIGH SEVERITY:

1. V15 - Proportional control valve
   - Type: HIGH_PRESSURE_DROP
   - Details: Component causes 15.2% pressure drop
   - Recommendation: Verify valve sizing - may be undersized for 180 LPM

2. Line L23 (V12 to V15)
   - Type: HIGH_VELOCITY
   - Details: Flow velocity 6.8 m/s exceeds recommended 5.0 m/s
   - Recommendation: Increase line size from 1/2" to 3/4"

MEDIUM SEVERITY:

3. V18 - Check valve
   - Type: TURBULENT_FLOW
   - Details: Reynolds number 8500 indicates turbulent flow
   - Recommendation: Review circuit design

4. Manifold M3
   - Type: SERIES_RESTRICTION
   - Details: Multiple restrictions in series
   - Recommendation: Consider parallel paths

Primary recommendations:
1. Upsize line L23 to 3/4" to reduce velocity
2. Verify V15 is sized correctly for 180 LPM
3. Check V15 for partial restriction or contamination
```

**You**:
```
Can you search for the V15 valve datasheet?
```

**AI**:
```
[Uses search_manufacturer_docs with query="V15"]

Documentation Search: 'V15'

Results Found: 2

1. parker_proportional_valves_D1FP.pdf
   - Relevance: 85
   - Manufacturer: Parker
   - Component Types: VALVE
   - Part Numbers: D1FPE50, D1FPE75, D1FPE100
   - Path: manufacturer_docs/parker_proportional_valves_D1FP.pdf

2. parker_valve_catalog_2024.pdf
   - Relevance: 45
   - Manufacturer: Parker
   - Component Types: VALVE
   - Part Numbers: Multiple
   - Path: manufacturer_docs/parker_valve_catalog_2024.pdf

The first result (parker_proportional_valves_D1FP.pdf) appears most relevant.
According to the datasheet, the D1FP series is rated for:
- Max flow: 150 LPM (at 3.5 bar drop)
- Your requirement: 180 LPM

This confirms the valve is undersized. Consider upgrading to D1FPE100 series (200 LPM rated).
```

---

### Example 3: Machine Comparison

**You**:
```
I have schematics for two machines. Can you compare them?
Machine A: schematics/baler_a.png
Machine B: schematics/baler_b.png
```

**AI**:
```
I'll analyze both schematics and compare them.

[Uses analyze_schematic twice, then compare_machines]

✓ Machine Comparison: Baler A vs Baler B

Component Comparison:
- Baler A: 87 components
- Baler B: 92 components
- In Both: 78 components
- Only in Baler A: 9 components
- Only in Baler B: 14 components

Components Only in Baler A:
- V45: Emergency relief valve
- H301: Auxiliary cylinder
- TL5: Position transducer

Components Only in Baler B:
- V47: Load sensing valve
- V48: Priority valve
- H302: Secondary press cylinder
- TL6, TL7, TL8: Additional position sensors
- F5: Additional filter
- M4: Manifold block

Restriction Comparison (at 180 LPM):
- Baler A: 6 restrictions
- Baler B: 3 restrictions

Key Differences:
1. Baler B added load-sensing (V47) - should improve efficiency
2. Baler B has additional press cylinder (H302) - increased capacity
3. Baler B has fewer restrictions - better designed
4. Baler B added priority valve (V48) - better flow management

Would you like me to analyze specific circuits in more detail?
```

## Advanced Usage

### Custom Flow Rate Analysis

Compare performance at different flow rates:

```
Find flow path from P1 to H203 in schematic 1 at 100 LPM
Find flow path from P1 to H203 in schematic 1 at 150 LPM
Find flow path from P1 to H203 in schematic 1 at 200 LPM

How does efficiency change with flow rate?
```

### Multi-Path Analysis

Analyze all major circuits:

```
For schematic 1, analyze these flow paths at 180 LPM:
- P1 to H203 (main press)
- P1 to H145 (eject)
- P2 to H180 (feed)

Which path has the best efficiency?
Which path needs improvement?
```

### Component Investigation

Deep dive on a component:

```
What components impact H203 in schematic 1?
Find all flow paths that include V12
Search for V12 documentation
What are the specifications of V12?
Is V12 adequately sized for 180 LPM?
```

### Batch Documentation Search

Search for multiple components:

```
Search documentation for:
- Parker valves
- Danfoss cylinders
- Nordon press cylinders
- Sun cartridge valves
```

## Tips & Tricks

### 1. Use Natural Language

You don't need exact tool names. The AI understands:
- "What's the flow from the pump to the cylinder?"
- "Show me restrictions"
- "Compare these two machines"

### 2. Be Specific

Better results with specifics:
- ❌ "Analyze the schematic"
- ✓ "Analyze schematics/baler_2024.png for Production Baler 2024"

### 3. Iterate

Start broad, then narrow down:
1. Analyze schematic
2. Get summary
3. Identify problem areas
4. Deep dive on specific paths

### 4. Remember IDs

Note schematic IDs for reuse:
- Schematic 1 = Baler A
- Schematic 2 = Baler B
- Schematic 3 = New Design

### 5. Use Context

The AI remembers conversation context:
```
You: "Analyze schematic 1"
AI: [analyzes]
You: "Now find the main press flow path"
AI: [understands "schematic 1"]
You: "What are the restrictions?"
AI: [understands "in that flow path"]
```

### 6. Combine Tools

Ask complex questions:
```
Analyze schematic 1, find the main press circuit from P1 to H203,
identify all restrictions, and search for documentation on any
problematic components
```

### 7. Export Results

Ask for formatted output:
```
Create a summary report of schematic 1 including:
- Component count
- All flow paths analyzed
- Top 5 restrictions
- Recommendations
```

### 8. Validation

Cross-check results:
```
You identified V15 as the bottleneck. Can you verify this is correct
by checking if V15 has the highest pressure drop in the path?
```

## Common Questions

**Q: How accurate is the pressure drop calculation?**

A: Pressure drops are estimated using standard hydraulic formulas and component K-factors. For precise values, consult manufacturer data.

**Q: Can I analyze the same schematic twice?**

A: The system detects duplicate files. To re-analyze, delete the database entry or use a different file name.

**Q: What if component IDs aren't detected correctly?**

A: Ensure schematics have clear, high-contrast labels. You can manually specify component IDs in queries if needed.

**Q: How do I organize multiple machines?**

A: Use descriptive machine names when analyzing:
- "Production Line 1 Baler"
- "Warehouse Baler - Serial 12345"
- "Backup Press Machine"

**Q: Can I export the database?**

A: Yes, the SQLite database is at `database/hydraulic_analysis.db`. Use any SQLite tool to export data.

**Q: What if the AI doesn't find a flow path?**

A: Possible reasons:
1. Components aren't connected in schematic
2. Component IDs are incorrect
3. Vision AI didn't detect connection

Try: "List all components in schematic 1" to verify IDs.

## Next Steps

- Review [SETUP.md](SETUP.md) for installation help
- Check [README.md](README.md) for overview
- Start with simple analysis and build complexity
- Provide feedback on accuracy and usability

Happy analyzing! 🔧
