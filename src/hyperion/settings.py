"""
Configuration typée Hyperion avec pydantic-settings.

Ce module remplace l'ancienne configuration pour une validation de type robuste.
"""

from __future__ import annotations

from pathlib import Path

import yaml
from pydantic import Field, validator
from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    """Configuration principale d'Hyperion avec validation typée."""

    # ============================================================================
    # Chemins projet
    # ============================================================================

    @property
    def project_root(self) -> Path:
        """Racine du projet (3 niveaux au-dessus de ce fichier)."""
        return Path(__file__).parent.parent.parent

    @property
    def config_dir(self) -> Path:
        """Dossier de configuration."""
        return self.project_root / "config"

    @property
    def templates_dir(self) -> Path:
        """Dossier des templates."""
        return self.project_root / "templates"

    @property
    def data_dir(self) -> Path:
        """Dossier des données."""
        return self.project_root / "data"

    @property
    def output_dir(self) -> Path:
        """Dossier de sortie des docs."""
        return self.project_root / "docs" / "generated"

    # ============================================================================
    # Git Configuration
    # ============================================================================

    git_main_candidates: list[str] = Field(
        default=["main", "master", "trunk", "develop"],
        description="Candidats pour la branche principale",
    )
    git_tags_regex: str = Field(
        default=r"^v?\d+\.\d+\.\d+$", description="Regex pour les tags de version"
    )

    # ============================================================================
    # Neo4j Configuration
    # ============================================================================

    neo4j_uri: str = Field(default="bolt://localhost:7687", description="URI de connexion Neo4j")
    neo4j_user: str = Field(default="neo4j", description="Utilisateur Neo4j")
    neo4j_password: str = Field(default="", description="Mot de passe Neo4j")
    neo4j_database: str = Field(default="neo4j", description="Base de données Neo4j")

    # ============================================================================
    # RAG Configuration
    # ============================================================================

    qdrant_host: str = Field(default="localhost", description="Hôte Qdrant")
    qdrant_port: int = Field(default=6333, description="Port Qdrant")
    qdrant_collection: str = Field(
        default="hyperion_repos", description="Collection Qdrant par défaut"
    )

    # ============================================================================
    # Embeddings Configuration
    # ============================================================================

    embedding_model: str = Field(
        default="BAAI/bge-large-en-v1.5", description="Modèle d'embeddings"
    )
    embedding_device: str = Field(
        default="cuda", description="Device pour les embeddings (cuda/cpu)"
    )
    embedding_dim: int = Field(default=1024, description="Dimension des embeddings")

    # ============================================================================
    # LLM Configuration
    # ============================================================================

    ollama_base_url: str = Field(
        default="http://localhost:11434", description="URL de base d'Ollama"
    )
    ollama_model: str = Field(default="qwen2.5:32b", description="Modèle Ollama par défaut")
    llm_temperature: float = Field(default=0.1, description="Température du LLM", ge=0.0, le=2.0)
    llm_max_tokens: int = Field(default=2048, description="Nombre maximum de tokens", ge=1, le=8192)

    # ============================================================================
    # Performance Configuration
    # ============================================================================

    batch_size_commits: int = Field(
        default=500, description="Taille des batches pour les commits", ge=1, le=10000
    )
    batch_size_files: int = Field(
        default=2000, description="Taille des batches pour les fichiers", ge=1, le=50000
    )

    # ============================================================================
    # Security Configuration (v3.0)
    # ============================================================================

    jwt_secret_key: str | None = Field(default=None, description="Clé secrète JWT")
    jwt_algorithm: str = Field(default="HS256", description="Algorithme JWT")
    jwt_access_token_expire_minutes: int = Field(
        default=30, description="Expiration du token d'accès (minutes)"
    )
    jwt_refresh_token_expire_days: int = Field(
        default=7, description="Expiration du token de rafraîchissement (jours)"
    )

    # ============================================================================
    # Cache Configuration (v3.0)
    # ============================================================================

    redis_url: str = Field(default="redis://localhost:6379", description="URL Redis pour le cache")
    cache_default_ttl: int = Field(default=3600, description="TTL par défaut du cache (secondes)")
    cache_l1_size: int = Field(default=1000, description="Taille du cache L1")
    cache_l2_size: int = Field(default=10000, description="Taille du cache L2")

    # ============================================================================
    # Monitoring Configuration
    # ============================================================================

    log_level: str = Field(default="INFO", description="Niveau de logging")
    enable_metrics: bool = Field(default=True, description="Activer les métriques Prometheus")
    metrics_port: int = Field(default=8001, description="Port pour les métriques")

    # ============================================================================
    # API Configuration
    # ============================================================================

    api_host: str = Field(default="localhost", description="Hôte de l'API")
    api_port: int = Field(default=8000, description="Port de l'API")
    api_cors_origins: list[str] = Field(
        default=["http://localhost:3000", "http://localhost:3001"],
        description="Origines CORS autorisées",
    )

    @validator("log_level")
    def validate_log_level(cls, v):
        """Valide le niveau de logging."""
        valid_levels = ["DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"]
        if v.upper() not in valid_levels:
            raise ValueError(f"log_level doit être l'un de: {valid_levels}")
        return v.upper()

    @validator("embedding_device")
    def validate_device(cls, v):
        """Valide le device pour les embeddings."""
        valid_devices = ["cuda", "cpu", "mps"]
        if v.lower() not in valid_devices:
            raise ValueError(f"embedding_device doit être l'un de: {valid_devices}")
        return v.lower()

    def load_filters(self) -> dict:
        """Charge les filtres depuis config/filters.yaml."""
        filters_path = self.config_dir / "filters.yaml"
        if filters_path.exists():
            return yaml.safe_load(filters_path.read_text())

        # Filtres par défaut
        return {
            "ignore_extensions": [
                ".pem",
                ".crt",
                ".cer",
                ".der",
                ".ai",
                ".psd",
                ".png",
                ".jpg",
                ".jpeg",
                ".gif",
                ".svg",
                ".ico",
                ".pdf",
                ".lock",
                ".min.js",
                ".map",
                ".ttf",
                ".otf",
                ".woff",
                ".woff2",
                ".gz",
                ".zip",
                ".7z",
                ".tar",
                ".bz2",
                ".exe",
                ".dll",
                ".so",
                ".dylib",
            ],
            "ignore_prefixes": [
                "requests/packages/",
                "ext/",
                "docs/_build/",
                "docs/_static/",
                "docs/_themes/",
                ".git/",
                ".github/",
                ".gitlab/",
                "node_modules/",
                "vendor/",
                "site-packages/",
                "dist-packages/",
            ],
            "ignore_files": [
                "HISTORY.rst",
                "HISTORY.md",
                "CHANGELOG",
                "CHANGELOG.md",
                "README",
                "README.md",
            ],
        }

    def ensure_directories(self) -> None:
        """Crée les dossiers nécessaires s'ils n'existent pas."""
        for directory in [self.data_dir, self.output_dir, self.config_dir]:
            directory.mkdir(parents=True, exist_ok=True)

    class Config:
        """Configuration Pydantic."""

        env_file = ".env"
        env_file_encoding = "utf-8"
        case_sensitive = False
        extra = "allow"  # Permet les champs extra pour compatibilité


# ============================================================================
# Instance globale des paramètres
# ============================================================================

settings = Settings()

# Créer les dossiers au chargement
settings.ensure_directories()

# Charger les filtres
FILTERS = settings.load_filters()


# ============================================================================
# Compatibility layer pour l'ancien config.py
# ============================================================================

# Pour compatibilité avec l'ancien code
PROJECT_ROOT = settings.project_root
CONFIG_DIR = settings.config_dir
TEMPLATES_DIR = settings.templates_dir
DATA_DIR = settings.data_dir
OUTPUT_DIR = settings.output_dir

DEFAULT_MAIN_CANDIDATES = settings.git_main_candidates
DEFAULT_TAGS_REGEX = settings.git_tags_regex

NEO4J_URI = settings.neo4j_uri
NEO4J_USER = settings.neo4j_user
NEO4J_PASSWORD = settings.neo4j_password
NEO4J_DATABASE = settings.neo4j_database

BATCH_SIZE_COMMITS = settings.batch_size_commits
BATCH_SIZE_FILES = settings.batch_size_files
