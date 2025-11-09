"""
Database interface for hydraulic component data and analysis results
"""
import sqlite3
import json
from pathlib import Path
from typing import List, Dict, Optional, Any
from datetime import datetime
import logging

logger = logging.getLogger(__name__)


class HydraulicDatabase:
    """Interface for hydraulic component and schematic database"""

    def __init__(self, db_path: Path):
        self.db_path = db_path
        self.conn: Optional[sqlite3.Connection] = None
        self.initialize_database()

    def connect(self):
        """Connect to database"""
        if self.conn is None:
            self.conn = sqlite3.connect(str(self.db_path))
            self.conn.row_factory = sqlite3.Row
        return self.conn

    def close(self):
        """Close database connection"""
        if self.conn:
            self.conn.close()
            self.conn = None

    def initialize_database(self):
        """Create database schema"""
        conn = self.connect()
        cursor = conn.cursor()

        # Schematics table
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS schematics (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                machine_name TEXT NOT NULL,
                file_path TEXT NOT NULL UNIQUE,
                file_hash TEXT,
                parsed_date TIMESTAMP,
                raw_analysis TEXT,
                metadata TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)

        # Components table (extracted from schematics)
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS components (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                schematic_id INTEGER,
                component_id TEXT NOT NULL,
                component_type TEXT,
                description TEXT,
                manufacturer TEXT,
                part_number TEXT,
                grid_location TEXT,
                specifications TEXT,
                connections TEXT,
                FOREIGN KEY (schematic_id) REFERENCES schematics(id),
                UNIQUE(schematic_id, component_id)
            )
        """)

        # Flow paths table
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS flow_paths (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                schematic_id INTEGER,
                path_name TEXT,
                start_component TEXT,
                end_component TEXT,
                components_in_path TEXT,
                total_restrictions REAL,
                bottleneck_component TEXT,
                analysis_data TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (schematic_id) REFERENCES schematics(id)
            )
        """)

        # Component relationships (connections between components)
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS component_relationships (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                schematic_id INTEGER,
                from_component TEXT,
                to_component TEXT,
                relationship_type TEXT,
                connection_type TEXT,
                line_size TEXT,
                metadata TEXT,
                FOREIGN KEY (schematic_id) REFERENCES schematics(id),
                UNIQUE(schematic_id, from_component, to_component, relationship_type)
            )
        """)

        # Manufacturer documentation
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS manufacturer_docs (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                file_path TEXT NOT NULL UNIQUE,
                manufacturer TEXT,
                component_types TEXT,
                part_numbers TEXT,
                extracted_specs TEXT,
                indexed_date TIMESTAMP,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)

        # Analysis cache (for performance)
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS analysis_cache (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                cache_key TEXT UNIQUE,
                cache_type TEXT,
                cache_data TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                expires_at TIMESTAMP
            )
        """)

        # Create indexes
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_components_schematic ON components(schematic_id)")
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_components_id ON components(component_id)")
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_flow_paths_schematic ON flow_paths(schematic_id)")
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_relationships_schematic ON component_relationships(schematic_id)")

        conn.commit()
        logger.info(f"Database initialized at {self.db_path}")

    # === Schematic Management ===

    def add_schematic(self, machine_name: str, file_path: str, file_hash: str,
                     raw_analysis: dict, metadata: Optional[dict] = None) -> int:
        """Add a new schematic to database"""
        conn = self.connect()
        cursor = conn.cursor()

        cursor.execute("""
            INSERT OR REPLACE INTO schematics
            (machine_name, file_path, file_hash, parsed_date, raw_analysis, metadata)
            VALUES (?, ?, ?, ?, ?, ?)
        """, (
            machine_name,
            file_path,
            file_hash,
            datetime.now(),
            json.dumps(raw_analysis),
            json.dumps(metadata or {})
        ))

        conn.commit()
        return cursor.lastrowid

    def get_schematic(self, schematic_id: int) -> Optional[Dict]:
        """Get schematic by ID"""
        conn = self.connect()
        cursor = conn.cursor()

        cursor.execute("SELECT * FROM schematics WHERE id = ?", (schematic_id,))
        row = cursor.fetchone()

        if row:
            return dict(row)
        return None

    def get_schematic_by_path(self, file_path: str) -> Optional[Dict]:
        """Get schematic by file path"""
        conn = self.connect()
        cursor = conn.cursor()

        cursor.execute("SELECT * FROM schematics WHERE file_path = ?", (file_path,))
        row = cursor.fetchone()

        if row:
            return dict(row)
        return None

    def list_schematics(self) -> List[Dict]:
        """List all schematics"""
        conn = self.connect()
        cursor = conn.cursor()

        cursor.execute("""
            SELECT id, machine_name, file_path, parsed_date, created_at
            FROM schematics
            ORDER BY created_at DESC
        """)

        return [dict(row) for row in cursor.fetchall()]

    # === Component Management ===

    def add_component(self, schematic_id: int, component_data: Dict) -> int:
        """Add component extracted from schematic"""
        conn = self.connect()
        cursor = conn.cursor()

        cursor.execute("""
            INSERT OR REPLACE INTO components
            (schematic_id, component_id, component_type, description, manufacturer,
             part_number, grid_location, specifications, connections)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            schematic_id,
            component_data.get('component_id'),
            component_data.get('component_type'),
            component_data.get('description'),
            component_data.get('manufacturer'),
            component_data.get('part_number'),
            component_data.get('grid_location'),
            json.dumps(component_data.get('specifications', {})),
            json.dumps(component_data.get('connections', []))
        ))

        conn.commit()
        return cursor.lastrowid

    def get_components_for_schematic(self, schematic_id: int) -> List[Dict]:
        """Get all components for a schematic"""
        conn = self.connect()
        cursor = conn.cursor()

        cursor.execute("""
            SELECT * FROM components WHERE schematic_id = ?
        """, (schematic_id,))

        components = []
        for row in cursor.fetchall():
            comp = dict(row)
            comp['specifications'] = json.loads(comp['specifications']) if comp['specifications'] else {}
            comp['connections'] = json.loads(comp['connections']) if comp['connections'] else []
            components.append(comp)

        return components

    def find_component(self, schematic_id: int, component_id: str) -> Optional[Dict]:
        """Find specific component in schematic"""
        conn = self.connect()
        cursor = conn.cursor()

        cursor.execute("""
            SELECT * FROM components
            WHERE schematic_id = ? AND component_id = ?
        """, (schematic_id, component_id))

        row = cursor.fetchone()
        if row:
            comp = dict(row)
            comp['specifications'] = json.loads(comp['specifications']) if comp['specifications'] else {}
            comp['connections'] = json.loads(comp['connections']) if comp['connections'] else []
            return comp
        return None

    # === Flow Path Management ===

    def add_flow_path(self, schematic_id: int, path_data: Dict) -> int:
        """Add analyzed flow path"""
        conn = self.connect()
        cursor = conn.cursor()

        cursor.execute("""
            INSERT INTO flow_paths
            (schematic_id, path_name, start_component, end_component,
             components_in_path, total_restrictions, bottleneck_component, analysis_data)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            schematic_id,
            path_data.get('path_name'),
            path_data.get('start_component'),
            path_data.get('end_component'),
            json.dumps(path_data.get('components_in_path', [])),
            path_data.get('total_restrictions', 0.0),
            path_data.get('bottleneck_component'),
            json.dumps(path_data.get('analysis_data', {}))
        ))

        conn.commit()
        return cursor.lastrowid

    def get_flow_paths(self, schematic_id: int) -> List[Dict]:
        """Get all flow paths for a schematic"""
        conn = self.connect()
        cursor = conn.cursor()

        cursor.execute("""
            SELECT * FROM flow_paths WHERE schematic_id = ?
        """, (schematic_id,))

        paths = []
        for row in cursor.fetchall():
            path = dict(row)
            path['components_in_path'] = json.loads(path['components_in_path']) if path['components_in_path'] else []
            path['analysis_data'] = json.loads(path['analysis_data']) if path['analysis_data'] else {}
            paths.append(path)

        return paths

    # === Component Relationships ===

    def add_relationship(self, schematic_id: int, relationship_data: Dict) -> int:
        """Add component relationship/connection"""
        conn = self.connect()
        cursor = conn.cursor()

        cursor.execute("""
            INSERT OR REPLACE INTO component_relationships
            (schematic_id, from_component, to_component, relationship_type,
             connection_type, line_size, metadata)
            VALUES (?, ?, ?, ?, ?, ?, ?)
        """, (
            schematic_id,
            relationship_data.get('from_component'),
            relationship_data.get('to_component'),
            relationship_data.get('relationship_type'),
            relationship_data.get('connection_type'),
            relationship_data.get('line_size'),
            json.dumps(relationship_data.get('metadata', {}))
        ))

        conn.commit()
        return cursor.lastrowid

    def get_relationships(self, schematic_id: int, component_id: Optional[str] = None) -> List[Dict]:
        """Get component relationships, optionally filtered by component"""
        conn = self.connect()
        cursor = conn.cursor()

        if component_id:
            cursor.execute("""
                SELECT * FROM component_relationships
                WHERE schematic_id = ? AND (from_component = ? OR to_component = ?)
            """, (schematic_id, component_id, component_id))
        else:
            cursor.execute("""
                SELECT * FROM component_relationships WHERE schematic_id = ?
            """, (schematic_id,))

        relationships = []
        for row in cursor.fetchall():
            rel = dict(row)
            rel['metadata'] = json.loads(rel['metadata']) if rel['metadata'] else {}
            relationships.append(rel)

        return relationships

    # === Manufacturer Documentation ===

    def add_manufacturer_doc(self, file_path: str, doc_data: Dict) -> int:
        """Add manufacturer documentation"""
        conn = self.connect()
        cursor = conn.cursor()

        cursor.execute("""
            INSERT OR REPLACE INTO manufacturer_docs
            (file_path, manufacturer, component_types, part_numbers, extracted_specs, indexed_date)
            VALUES (?, ?, ?, ?, ?, ?)
        """, (
            file_path,
            doc_data.get('manufacturer'),
            json.dumps(doc_data.get('component_types', [])),
            json.dumps(doc_data.get('part_numbers', [])),
            json.dumps(doc_data.get('extracted_specs', {})),
            datetime.now()
        ))

        conn.commit()
        return cursor.lastrowid

    def search_manufacturer_docs(self, query: str) -> List[Dict]:
        """Search manufacturer documentation"""
        conn = self.connect()
        cursor = conn.cursor()

        # Simple search - can be enhanced with FTS
        cursor.execute("""
            SELECT * FROM manufacturer_docs
            WHERE manufacturer LIKE ?
               OR component_types LIKE ?
               OR part_numbers LIKE ?
        """, (f'%{query}%', f'%{query}%', f'%{query}%'))

        docs = []
        for row in cursor.fetchall():
            doc = dict(row)
            doc['component_types'] = json.loads(doc['component_types']) if doc['component_types'] else []
            doc['part_numbers'] = json.loads(doc['part_numbers']) if doc['part_numbers'] else []
            doc['extracted_specs'] = json.loads(doc['extracted_specs']) if doc['extracted_specs'] else {}
            docs.append(doc)

        return docs

    # === Caching ===

    def get_cache(self, cache_key: str) -> Optional[Any]:
        """Get cached analysis result"""
        conn = self.connect()
        cursor = conn.cursor()

        cursor.execute("""
            SELECT cache_data FROM analysis_cache
            WHERE cache_key = ?
            AND (expires_at IS NULL OR expires_at > ?)
        """, (cache_key, datetime.now()))

        row = cursor.fetchone()
        if row:
            return json.loads(row['cache_data'])
        return None

    def set_cache(self, cache_key: str, cache_type: str, cache_data: Any,
                  expires_in_hours: Optional[int] = None):
        """Set cache entry"""
        conn = self.connect()
        cursor = conn.cursor()

        expires_at = None
        if expires_in_hours:
            from datetime import timedelta
            expires_at = datetime.now() + timedelta(hours=expires_in_hours)

        cursor.execute("""
            INSERT OR REPLACE INTO analysis_cache
            (cache_key, cache_type, cache_data, expires_at)
            VALUES (?, ?, ?, ?)
        """, (cache_key, cache_type, json.dumps(cache_data), expires_at))

        conn.commit()
