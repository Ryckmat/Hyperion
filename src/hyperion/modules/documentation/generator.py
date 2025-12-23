"""
Générateur de documentation automatique.

Auteur: Ryckman Matthieu
Projet: Hyperion (projet personnel)
Version: 2.0.0
"""

from pathlib import Path


class AutoDocGenerator:
    """Génère de la documentation technique automatiquement."""

    def __init__(self, repo_path: Path):
        """Initialise le générateur."""
        self.repo_path = Path(repo_path)

    def generate_module_doc(self, module_path: Path) -> str:
        """
        Génère la documentation d'un module.

        Args:
            module_path: Chemin du module

        Returns:
            Documentation Markdown
        """
        # TODO: Implémenter génération via AST + LLM
        return ""
