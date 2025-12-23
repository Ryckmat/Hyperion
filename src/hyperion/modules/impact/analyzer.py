"""
Analyseur d'impact basé sur AST et dépendances statiques.

Auteur: Ryckman Matthieu
Projet: Hyperion (projet personnel)
Version: 2.0.0
"""

import ast
from pathlib import Path
from typing import Any


class ImpactAnalyzer:
    """
    Analyse l'impact d'une modification de fichier.

    Détecte les dépendances statiques via parsing AST Python.
    """

    def __init__(self, repo_path: Path):
        """
        Initialise l'analyseur.

        Args:
            repo_path: Chemin du repository à analyser
        """
        self.repo_path = Path(repo_path)
        self.dependency_graph: dict[str, set[str]] = {}

    def analyze_file(self, file_path: Path) -> dict[str, Any]:
        """
        Analyse un fichier Python et extrait ses dépendances.

        Args:
            file_path: Chemin du fichier à analyser

        Returns:
            Dictionnaire avec imports, fonctions, classes
        """
        # TODO: Implémenter parsing AST
        with open(file_path) as f:
            tree = ast.parse(f.read(), filename=str(file_path))

        imports = self._extract_imports(tree)
        functions = self._extract_functions(tree)
        classes = self._extract_classes(tree)

        return {
            "file": str(file_path),
            "imports": imports,
            "functions": functions,
            "classes": classes,
        }

    def _extract_imports(self, tree: ast.AST) -> list[str]:
        """Extrait les imports d'un AST."""
        # TODO: Implémenter extraction imports
        imports = []
        for node in ast.walk(tree):
            if isinstance(node, ast.Import):
                imports.extend(alias.name for alias in node.names)
            elif isinstance(node, ast.ImportFrom):
                if node.module:
                    imports.append(node.module)
        return imports

    def _extract_functions(self, tree: ast.AST) -> list[str]:
        """Extrait les noms de fonctions d'un AST."""
        # TODO: Implémenter extraction fonctions
        return [node.name for node in ast.walk(tree) if isinstance(node, ast.FunctionDef)]

    def _extract_classes(self, tree: ast.AST) -> list[str]:
        """Extrait les noms de classes d'un AST."""
        # TODO: Implémenter extraction classes
        return [node.name for node in ast.walk(tree) if isinstance(node, ast.ClassDef)]

    def build_dependency_graph(self) -> dict[str, set[str]]:
        """
        Construit le graphe de dépendances du repository.

        Returns:
            Graphe {fichier: {dépendances}}
        """
        # TODO: Implémenter construction graphe complet
        python_files = self.repo_path.rglob("*.py")

        for file_path in python_files:
            analysis = self.analyze_file(file_path)
            self.dependency_graph[str(file_path)] = set(analysis["imports"])

        return self.dependency_graph

    def get_impacted_files(self, modified_file: Path) -> set[str]:
        """
        Retourne les fichiers impactés par une modification.

        Args:
            modified_file: Fichier modifié

        Returns:
            Set de fichiers impactés
        """
        # TODO: Implémenter algorithme traversal
        if not self.dependency_graph:
            self.build_dependency_graph()

        impacted = set()
        # Logique de traversal à implémenter
        return impacted
