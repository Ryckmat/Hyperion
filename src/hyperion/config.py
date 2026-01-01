"""
Configuration centralisée Hyperion - Module de compatibilité.

DEPRECATED: Ce module est maintenu pour compatibilité.
Utilisez src/hyperion/settings.py pour les nouvelles configurations.
"""

import warnings

# Import from new settings module
from .settings import (
    # Performance compatibilité
    settings,
)

# Backward compatibility exports
DATA_DIR = settings.data_dir
OUTPUT_DIR = settings.output_dir
CONFIG_DIR = settings.config_dir

# Neo4j compatibility
NEO4J_URI = settings.neo4j_uri
NEO4J_USER = settings.neo4j_user
NEO4J_PASSWORD = settings.neo4j_password
NEO4J_DATABASE = settings.neo4j_database

# RAG compatibility
QDRANT_HOST = settings.qdrant_host
QDRANT_PORT = settings.qdrant_port
QDRANT_COLLECTION = settings.qdrant_collection

# LLM compatibility
OLLAMA_BASE_URL = settings.ollama_base_url
OLLAMA_MODEL = settings.ollama_model
LLM_TEMPERATURE = settings.llm_temperature
LLM_MAX_TOKENS = settings.llm_max_tokens

# Git compatibility
DEFAULT_MAIN_CANDIDATES = settings.git_main_candidates
DEFAULT_TAGS_REGEX = settings.git_tags_regex

# Filters compatibility
FILTERS = settings.load_filters()

# Additional compatibility exports
PROJECT_ROOT = settings.project_root
TEMPLATES_DIR = settings.templates_dir

# Avertissement de dépréciation
warnings.warn(
    "hyperion.config module is deprecated. Use hyperion.settings instead.",
    DeprecationWarning,
    stacklevel=2,
)


# Function de compatibilité
def load_filters():
    """DEPRECATED: Utilise settings.load_filters() à la place."""
    warnings.warn(
        "load_filters() is deprecated. Use settings.load_filters() instead.",
        DeprecationWarning,
        stacklevel=2,
    )
    return settings.load_filters()
