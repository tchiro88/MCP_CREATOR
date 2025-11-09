"""
Configuration management for Hydraulic Agent MCP Server
"""
import os
from pathlib import Path
from typing import Optional
import json

class Config:
    """Configuration for Hydraulic Analysis MCP Server"""

    def __init__(self):
        # Base paths
        self.base_dir = Path(__file__).parent
        self.schematics_dir = self.base_dir / "schematics"
        self.manufacturer_docs_dir = self.base_dir / "manufacturer_docs"
        self.machines_dir = self.base_dir / "machines"
        self.database_dir = self.base_dir / "database"

        # Ensure directories exist
        self.schematics_dir.mkdir(exist_ok=True)
        self.manufacturer_docs_dir.mkdir(exist_ok=True)
        self.machines_dir.mkdir(exist_ok=True)
        self.database_dir.mkdir(exist_ok=True)

        # API Configuration
        self.openai_api_key = os.getenv("OPENAI_API_KEY", "")
        self.openrouter_api_key = os.getenv("OPENROUTER_API_KEY", "")

        # Prefer OpenRouter if available, fall back to OpenAI
        self.use_openrouter = bool(self.openrouter_api_key)

        # Vision model configuration
        if self.use_openrouter:
            self.vision_model = "anthropic/claude-3.5-sonnet"  # or other vision models
            self.api_base = "https://openrouter.ai/api/v1"
            self.api_key = self.openrouter_api_key
        else:
            self.vision_model = "gpt-4-vision-preview"
            self.api_base = "https://api.openai.com/v1"
            self.api_key = self.openai_api_key

        # Database configuration
        self.db_type = os.getenv("DB_TYPE", "sqlite")  # sqlite or postgresql
        self.db_path = self.database_dir / "hydraulic_analysis.db"

        # PostgreSQL configuration (if using existing AL DAHRA database)
        self.pg_host = os.getenv("POSTGRES_HOST", "localhost")
        self.pg_port = int(os.getenv("POSTGRES_PORT", "5432"))
        self.pg_database = os.getenv("POSTGRES_DB", "sparkplug_system")
        self.pg_user = os.getenv("POSTGRES_USER", "postgres")
        self.pg_password = os.getenv("POSTGRES_PASSWORD", "")

        # Analysis configuration
        self.max_flow_path_depth = 20  # Maximum recursion depth for flow path tracing
        self.restriction_threshold_percent = 20  # Flag restrictions reducing flow by >20%

        # File watching configuration
        self.watch_schematics_folder = os.getenv("WATCH_SCHEMATICS", "true").lower() == "true"
        self.watch_interval_seconds = int(os.getenv("WATCH_INTERVAL", "5"))

    def validate(self) -> tuple[bool, Optional[str]]:
        """Validate configuration"""
        if not self.api_key:
            return False, "No API key configured. Set OPENAI_API_KEY or OPENROUTER_API_KEY environment variable."

        if self.db_type == "postgresql":
            if not all([self.pg_host, self.pg_database, self.pg_user]):
                return False, "PostgreSQL configuration incomplete. Check POSTGRES_* environment variables."

        return True, None

    def to_dict(self) -> dict:
        """Export configuration as dictionary (excluding sensitive data)"""
        return {
            "schematics_dir": str(self.schematics_dir),
            "manufacturer_docs_dir": str(self.manufacturer_docs_dir),
            "machines_dir": str(self.machines_dir),
            "database_dir": str(self.database_dir),
            "vision_model": self.vision_model,
            "db_type": self.db_type,
            "max_flow_path_depth": self.max_flow_path_depth,
            "restriction_threshold_percent": self.restriction_threshold_percent,
            "use_openrouter": self.use_openrouter,
            "api_configured": bool(self.api_key)
        }

    def save_config(self, filepath: Optional[Path] = None):
        """Save configuration to JSON file"""
        if filepath is None:
            filepath = self.base_dir / "config.json"

        with open(filepath, 'w') as f:
            json.dump(self.to_dict(), f, indent=2)

    @classmethod
    def load_config(cls, filepath: Optional[Path] = None) -> 'Config':
        """Load configuration from JSON file"""
        config = cls()

        if filepath is None:
            filepath = config.base_dir / "config.json"

        if filepath.exists():
            with open(filepath, 'r') as f:
                data = json.load(f)
                # Update configuration with loaded values
                for key, value in data.items():
                    if hasattr(config, key) and key not in ['api_configured']:
                        setattr(config, key, value)

        return config


# Global configuration instance
config = Config()
