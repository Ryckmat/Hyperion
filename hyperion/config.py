"""Configuration centralisée Hyperion."""

import os
from pathlib import Path
import yaml

from dotenv import load_dotenv

# ============================================================================
# Chemins projet
# ============================================================================

PROJECT_ROOT = Path(__file__).parent.parent

# Charger le .env à la racine du projet
ENV_PATH = PROJECT_ROOT / ".env"
load_dotenv(ENV_PATH, override=True)

CONFIG_DIR = PROJECT_ROOT / "config"
TEMPLATES_DIR = PROJECT_ROOT / "templates"
DATA_DIR = PROJECT_ROOT / "data"
OUTPUT_DIR = PROJECT_ROOT / "output"

# Créer les dossiers s'ils n'existent pas
for directory in [DATA_DIR, OUTPUT_DIR, CONFIG_DIR]:
    directory.mkdir(parents=True, exist_ok=True)

# ============================================================================
# Git
# ============================================================================

DEFAULT_MAIN_CANDIDATES = ["main", "master", "trunk", "develop"]
DEFAULT_TAGS_REGEX = r"^v?\d+\.\d+\.\d+$"

# ============================================================================
# Neo4j
# ============================================================================

NEO4J_URI = os.getenv("NEO4J_URI", "bolt://localhost:7687")
NEO4J_USER = os.getenv("NEO4J_USER", "neo4j")
NEO4J_PASSWORD = os.getenv("NEO4J_PASSWORD", "")
NEO4J_DATABASE = os.getenv("NEO4J_DATABASE", "neo4j")

# ============================================================================
# Batch sizes (performance)
# ============================================================================

BATCH_SIZE_COMMITS = int(os.getenv("BATCH_SIZE_COMMITS", "500"))
BATCH_SIZE_FILES = int(os.getenv("BATCH_SIZE_FILES", "2000"))

# ============================================================================
# Filtres
# ============================================================================

def load_filters() -> dict:
    """Charge les filtres depuis config/filters.yaml."""
    filters_path = CONFIG_DIR / "filters.yaml"
    if filters_path.exists():
        return yaml.safe_load(filters_path.read_text())

    # Filtres par défaut si le fichier n'existe pas
    return {
        "ignore_extensions": [
            ".pem", ".crt", ".cer", ".der", ".ai", ".psd",
            ".png", ".jpg", ".jpeg", ".gif", ".svg", ".ico", ".pdf",
            ".lock", ".min.js", ".map",
            ".ttf", ".otf", ".woff", ".woff2",
            ".gz", ".zip", ".7z", ".tar", ".bz2",
            ".exe", ".dll", ".so", ".dylib",
        ],
        "ignore_prefixes": [
            "requests/packages/", "ext/",
            "docs/_build/", "docs/_static/", "docs/_themes/",
            ".git/", ".github/", ".gitlab/",
            "node_modules/", "vendor/", "site-packages/", "dist-packages/",
        ],
        "ignore_files": [
            "HISTORY.rst", "HISTORY.md",
            "CHANGELOG", "CHANGELOG.md",
            "README", "README.md",
        ],
    }

FILTERS = load_filters()
