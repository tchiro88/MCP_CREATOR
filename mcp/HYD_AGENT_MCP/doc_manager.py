"""
Manufacturer documentation manager
Indexes and searches through manufacturer datasheets and manuals
"""
import logging
import re
from pathlib import Path
from typing import Dict, List, Optional, Any
import json

try:
    import openai
    import PyPDF2
except ImportError:
    openai = None
    PyPDF2 = None

from config import config

logger = logging.getLogger(__name__)


class DocumentationManager:
    """Manage and search manufacturer documentation"""

    def __init__(self, docs_directory: Path):
        self.docs_dir = docs_directory
        self.config = config

        if openai is None:
            logger.warning("openai package not installed")

        if PyPDF2 is None:
            logger.warning("PyPDF2 package not installed")

        self.client = openai.OpenAI(
            api_key=self.config.api_key,
            base_url=self.config.api_base
        ) if openai else None

        self.indexed_docs = {}

    def index_documentation(self, force_reindex: bool = False) -> Dict[str, Any]:
        """
        Index all documentation in the docs directory

        Args:
            force_reindex: Force re-indexing of all documents

        Returns:
            Summary of indexing results
        """
        logger.info(f"Indexing documentation in {self.docs_dir}")

        pdf_files = list(self.docs_dir.glob("**/*.pdf"))
        results = {
            'total_files': len(pdf_files),
            'indexed': 0,
            'skipped': 0,
            'errors': 0,
            'files': []
        }

        for pdf_file in pdf_files:
            try:
                # Check if already indexed
                if not force_reindex and pdf_file in self.indexed_docs:
                    results['skipped'] += 1
                    continue

                # Extract text from PDF
                extracted_data = self._extract_pdf_data(pdf_file)

                if extracted_data:
                    self.indexed_docs[pdf_file] = extracted_data
                    results['indexed'] += 1
                    results['files'].append({
                        'file': str(pdf_file),
                        'manufacturer': extracted_data.get('manufacturer'),
                        'component_types': extracted_data.get('component_types', []),
                        'part_numbers': extracted_data.get('part_numbers', [])
                    })
                else:
                    results['errors'] += 1

            except Exception as e:
                logger.error(f"Error indexing {pdf_file}: {e}")
                results['errors'] += 1

        logger.info(f"Indexing complete: {results['indexed']} indexed, {results['skipped']} skipped, {results['errors']} errors")
        return results

    def _extract_pdf_data(self, pdf_path: Path) -> Optional[Dict[str, Any]]:
        """
        Extract data from PDF using PyPDF2 and AI analysis

        Args:
            pdf_path: Path to PDF file

        Returns:
            Extracted data dictionary
        """
        if PyPDF2 is None:
            logger.error("PyPDF2 not available")
            return None

        try:
            # Extract text from PDF
            with open(pdf_path, 'rb') as file:
                pdf_reader = PyPDF2.PdfReader(file)
                text = ""
                # Get first few pages (usually contain key info)
                for page_num in range(min(3, len(pdf_reader.pages))):
                    page = pdf_reader.pages[page_num]
                    text += page.extract_text()

            # Use AI to extract structured data from text
            if self.client and text:
                extracted = self._ai_extract_specs(text)
                extracted['file_path'] = str(pdf_path)
                extracted['page_count'] = len(pdf_reader.pages)
                return extracted
            else:
                # Fallback to regex extraction
                return self._regex_extract_specs(text, pdf_path)

        except Exception as e:
            logger.error(f"Error extracting from PDF {pdf_path}: {e}")
            return None

    def _ai_extract_specs(self, text: str) -> Dict[str, Any]:
        """Use AI to extract specifications from document text"""
        try:
            response = self.client.chat.completions.create(
                model="gpt-4-turbo-preview",  # Use text model for PDF text
                messages=[
                    {
                        "role": "system",
                        "content": "Extract hydraulic component specifications from technical documentation."
                    },
                    {
                        "role": "user",
                        "content": f"""Analyze this technical document text and extract:

{text[:4000]}  # Limit text length

Return JSON format:
{{
  "manufacturer": "Manufacturer name",
  "component_types": ["List of component types (VALVE, CYLINDER, etc.)"],
  "part_numbers": ["List of part numbers found"],
  "specifications": {{
    "pressure_max_bar": "Max pressure in bar",
    "flow_max_lpm": "Max flow in LPM",
    "port_sizes": ["Port sizes available"],
    "voltage": "Voltage if applicable",
    "other_specs": {{}}
  }},
  "applications": ["Typical applications"],
  "key_features": ["Key features"]
}}

Return ONLY valid JSON, no additional text."""
                    }
                ],
                max_tokens=1000
            )

            response_text = response.choices[0].message.content

            # Parse JSON from response
            json_match = re.search(r'\{.*\}', response_text, re.DOTALL)
            if json_match:
                return json.loads(json_match.group(0))
            else:
                return self._regex_extract_specs(text, None)

        except Exception as e:
            logger.error(f"AI extraction failed: {e}")
            return self._regex_extract_specs(text, None)

    def _regex_extract_specs(self, text: str, pdf_path: Optional[Path]) -> Dict[str, Any]:
        """Fallback: Extract specifications using regex patterns"""
        data = {
            'manufacturer': None,
            'component_types': [],
            'part_numbers': [],
            'specifications': {},
            'applications': [],
            'key_features': []
        }

        if pdf_path:
            data['file_path'] = str(pdf_path)

        # Extract manufacturer (common names)
        manufacturers = ['Parker', 'Danfoss', 'Bosch', 'Rexroth', 'Eaton', 'Hydac',
                        'Sun', 'Vickers', 'Moog', 'Nordon', 'Torque', 'Walvoil']
        for mfr in manufacturers:
            if mfr.lower() in text.lower():
                data['manufacturer'] = mfr
                break

        # Extract part numbers (common patterns)
        # Pattern: Letters followed by numbers, dashes, etc.
        part_patterns = [
            r'\b[A-Z]{2,}-\d{3,}[A-Z0-9-]*\b',  # E.g., STH-200-003-C
            r'\b[A-Z]\d{2,}[A-Z0-9-]*\b',        # E.g., H203, V12-3A
        ]

        for pattern in part_patterns:
            matches = re.findall(pattern, text)
            data['part_numbers'].extend(matches)

        # Remove duplicates
        data['part_numbers'] = list(set(data['part_numbers']))

        # Extract pressure ratings
        pressure_matches = re.findall(r'(\d+)\s*bar', text, re.IGNORECASE)
        if pressure_matches:
            data['specifications']['pressure_ratings_bar'] = [int(p) for p in pressure_matches]

        # Extract flow rates
        flow_matches = re.findall(r'(\d+)\s*L/min|(\d+)\s*LPM', text, re.IGNORECASE)
        if flow_matches:
            flows = [int(f[0] or f[1]) for f in flow_matches]
            data['specifications']['flow_ratings_lpm'] = flows

        # Identify component types
        component_keywords = {
            'VALVE': ['valve', 'directional', 'proportional', 'relief', 'check'],
            'CYLINDER': ['cylinder', 'actuator', 'ram'],
            'PUMP': ['pump', 'piston pump', 'vane pump'],
            'MOTOR': ['motor', 'hydraulic motor'],
            'FILTER': ['filter', 'filtration'],
            'TRANSDUCER': ['transducer', 'sensor', 'pressure sensor']
        }

        for comp_type, keywords in component_keywords.items():
            for keyword in keywords:
                if keyword.lower() in text.lower():
                    data['component_types'].append(comp_type)
                    break

        # Remove duplicates
        data['component_types'] = list(set(data['component_types']))

        return data

    def search_docs(self, query: str, component_type: Optional[str] = None) -> List[Dict[str, Any]]:
        """
        Search indexed documentation

        Args:
            query: Search query (component ID, part number, manufacturer, etc.)
            component_type: Optional filter by component type

        Returns:
            List of matching documents with relevance scores
        """
        results = []
        query_lower = query.lower()

        for pdf_path, doc_data in self.indexed_docs.items():
            score = 0

            # Check manufacturer
            if doc_data.get('manufacturer') and query_lower in doc_data['manufacturer'].lower():
                score += 10

            # Check part numbers
            for part_num in doc_data.get('part_numbers', []):
                if query_lower in part_num.lower():
                    score += 20

            # Check component types
            if component_type:
                if component_type in doc_data.get('component_types', []):
                    score += 15

            for comp_type in doc_data.get('component_types', []):
                if query_lower in comp_type.lower():
                    score += 5

            # Check file path
            if query_lower in str(pdf_path).lower():
                score += 5

            if score > 0:
                results.append({
                    'file_path': str(pdf_path),
                    'relevance_score': score,
                    'manufacturer': doc_data.get('manufacturer'),
                    'component_types': doc_data.get('component_types', []),
                    'part_numbers': doc_data.get('part_numbers', []),
                    'specifications': doc_data.get('specifications', {})
                })

        # Sort by relevance
        results.sort(key=lambda x: x['relevance_score'], reverse=True)

        return results

    def get_component_datasheet(self, component_id: str, manufacturer: Optional[str] = None) -> Optional[Dict[str, Any]]:
        """
        Find datasheet for specific component

        Args:
            component_id: Component ID (e.g., H203, V12-3A)
            manufacturer: Optional manufacturer filter

        Returns:
            Datasheet information if found
        """
        # Search for component ID
        results = self.search_docs(component_id)

        # Filter by manufacturer if provided
        if manufacturer and results:
            results = [r for r in results if r['manufacturer'] and
                      manufacturer.lower() in r['manufacturer'].lower()]

        return results[0] if results else None
