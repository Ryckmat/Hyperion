"""Configuration RAG Hyperion."""

import os

from hyperion.settings import DATA_DIR

# ============================================================================
# Qdrant Configuration
# ============================================================================

QDRANT_HOST = os.getenv("QDRANT_HOST", "localhost")
QDRANT_PORT = int(os.getenv("QDRANT_PORT", "6333"))
QDRANT_COLLECTION = os.getenv("QDRANT_COLLECTION", "hyperion_repos")

# ============================================================================
# Embeddings Configuration
# ============================================================================

# Modèle d'embeddings local avec fallback automatique
EMBEDDING_MODEL = os.getenv("EMBEDDING_MODEL", "BAAI/bge-large-en-v1.5")


def get_optimal_device():
    """Détection automatique GPU/CPU avec fallback intelligent."""
    try:
        import torch

        # Vérifier si CUDA est disponible
        if not torch.cuda.is_available():
            return "cpu"

        try:
            import nvidia_ml_py3 as nvml

            # Vérifier mémoire GPU disponible
            nvml.nvmlInit()
            device_count = nvml.nvmlDeviceGetCount()

            for i in range(device_count):
                handle = nvml.nvmlDeviceGetHandleByIndex(i)
                mem_info = nvml.nvmlDeviceGetMemoryInfo(handle)

                # Si moins de 2GB libre, utiliser CPU
                free_gb = mem_info.free / (1024**3)
                if free_gb < 2.0:
                    print(f"🚨 GPU {i}: Seulement {free_gb:.1f}GB libre, fallback CPU")
                    return "cpu"

            return "cuda"

        except ImportError:
            # nvidia-ml-py3 non disponible, utiliser simple détection
            print("⚠️ nvidia-ml-py3 non disponible, détection simple GPU")
            return "cuda" if torch.cuda.device_count() > 0 else "cpu"

    except Exception as e:
        print(f"⚠️ Erreur détection GPU: {e}, fallback CPU")
        return "cpu"


EMBEDDING_DEVICE = os.getenv("EMBEDDING_DEVICE", get_optimal_device())
EMBEDDING_DIM = 1024  # Dimension BGE-large

# Chunk configuration
CHUNK_SIZE = int(os.getenv("CHUNK_SIZE", "512"))
CHUNK_OVERLAP = int(os.getenv("CHUNK_OVERLAP", "50"))

# ============================================================================
# LLM Configuration (Ollama local)
# ============================================================================

OLLAMA_BASE_URL = os.getenv("OLLAMA_BASE_URL", "http://localhost:11434")
OLLAMA_MODEL = os.getenv("OLLAMA_MODEL", "llama3.2:1b")

# LLM Parameters (ultra-optimisé <3s garanties absolues)
LLM_TEMPERATURE = float(os.getenv("LLM_TEMPERATURE", "0.0"))
LLM_MAX_TOKENS = int(os.getenv("LLM_MAX_TOKENS", "128"))
LLM_TOP_K = int(os.getenv("LLM_TOP_K", "1"))  # Un seul chunk pour vitesse ultime 2→1
LLM_TIMEOUT = int(os.getenv("LLM_TIMEOUT", "2"))

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

QUERY_PROMPT_TEMPLATE = """{context}

Q: {question}
A:"""

# ============================================================================
# Paths
# ============================================================================

REPOS_DIR = DATA_DIR / "repositories"
