"""Configuration RAG Hyperion."""

import os
from pathlib import Path

# ============================================================================
# Qdrant Configuration
# ============================================================================

QDRANT_HOST = os.getenv("QDRANT_HOST", "localhost")
QDRANT_PORT = int(os.getenv("QDRANT_PORT", "6333"))
QDRANT_COLLECTION = os.getenv("QDRANT_COLLECTION", "hyperion_repos")

# ============================================================================
# Embeddings Configuration
# ============================================================================

# Modèle d'embeddings local (GPU)
EMBEDDING_MODEL = os.getenv("EMBEDDING_MODEL", "BAAI/bge-large-en-v1.5")
EMBEDDING_DEVICE = os.getenv("EMBEDDING_DEVICE", "cuda")  # cuda ou cpu
EMBEDDING_DIM = 1024  # Dimension BGE-large

# Chunk configuration
CHUNK_SIZE = int(os.getenv("CHUNK_SIZE", "512"))
CHUNK_OVERLAP = int(os.getenv("CHUNK_OVERLAP", "50"))

# ============================================================================
# LLM Configuration (Ollama local)
# ============================================================================

OLLAMA_BASE_URL = os.getenv("OLLAMA_BASE_URL", "http://localhost:11434")
OLLAMA_MODEL = os.getenv("OLLAMA_MODEL", "qwen2.5:32b")

# LLM Parameters
LLM_TEMPERATURE = float(os.getenv("LLM_TEMPERATURE", "0.1"))
LLM_MAX_TOKENS = int(os.getenv("LLM_MAX_TOKENS", "2048"))
LLM_TOP_K = int(os.getenv("LLM_TOP_K", "5"))  # Nombre de chunks à récupérer

# ============================================================================
# Prompt Templates
# ============================================================================

SYSTEM_PROMPT = """Tu es un assistant expert en analyse de dépôts Git.
Tu réponds aux questions sur les repositories analysés par Hyperion.

Règles :
- Réponds de manière concise et précise
- Cite les sources (fichiers, métriques)
- Si tu ne sais pas, dis-le clairement
- Utilise les nombres exacts du contexte
- Formate les réponses de manière lisible
"""

QUERY_PROMPT_TEMPLATE = """Contexte sur le repository :
{context}

Question : {question}

Réponds de manière précise en te basant UNIQUEMENT sur le contexte ci-dessus.
Si l'information n'est pas dans le contexte, dis "Je ne trouve pas cette information dans les données analysées."
"""

# ============================================================================
# Paths
# ============================================================================

from hyperion.config import DATA_DIR

REPOS_DIR = DATA_DIR / "repositories"
