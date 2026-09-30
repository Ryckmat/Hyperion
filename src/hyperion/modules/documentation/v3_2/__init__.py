"""Module de génération de documentation v3.2.

Génère automatiquement:
- Docstrings via LLM
- README.md
- Diagrammes Mermaid (classes, dépendances)
"""

from .config import DiagramType, DocstringStyle, DocumentationConfig
from .doc_generator import DocumentationOrchestrator, GenerationResult

__all__ = [
    "DocumentationConfig",
    "DocstringStyle",
    "DiagramType",
    "DocumentationOrchestrator",
    "GenerationResult",
]
