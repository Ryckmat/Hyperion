"""
Indexeur de code pour compréhension sémantique.

Auteur: Ryckman Matthieu
Projet: Hyperion (projet personnel)
Version: 2.0.0
"""

import ast
from pathlib import Path
from typing import Any


class CodeIndexer:
    """
    Indexe le code source avec métadonnées sémantiques.

    Extrait: docstrings, commentaires, signatures, tests.
    """

    def __init__(self, repo_path: Path):
        """
        Initialise l'indexeur.

        Args:
            repo_path: Chemin du repository
        """
        self.repo_path = Path(repo_path)
        self.index: dict[str, dict[str, Any]] = {}

    def index_repository(self) -> dict[str, dict[str, Any]]:
        """
        Indexe tous les fichiers Python du repository.

        Returns:
            Index complet {file_path: metadata}
        """
        python_files = list(self.repo_path.rglob("*.py"))

        # Filtres pour éviter les problèmes
        excluded_patterns = [
            "__pycache__",
            ".git",
            ".pytest_cache",
            "venv",
            "env",
            ".tox",
            "dist",
            "build",
            ".egg-info",
            "node_modules",
        ]

        filtered_files = []
        for file_path in python_files:
            # Skip si dans un répertoire exclu
            if any(pattern in str(file_path) for pattern in excluded_patterns):
                continue
            # Skip si trop gros (>1MB)
            try:
                if file_path.stat().st_size > 1_000_000:
                    continue
            except OSError:
                continue

            filtered_files.append(file_path)

        print(f"📁 Indexation de {len(filtered_files)} fichiers Python...")

        for i, file_path in enumerate(filtered_files):
            if i % 10 == 0:
                print(f"   Progression: {i}/{len(filtered_files)}")

            metadata = self.index_file(file_path)
            if "error" not in metadata:  # Seulement si pas d'erreur
                self.index[str(file_path)] = metadata

        print(f"✅ Indexation terminée: {len(self.index)} fichiers")
        return self.index

    def index_file(self, file_path: Path) -> dict[str, Any]:
        """
        Indexe un fichier Python.

        Args:
            file_path: Chemin du fichier

        Returns:
            Métadonnées extraites
        """
        # TODO: Implémenter extraction complète
        try:
            with open(file_path, encoding="utf-8", errors="ignore") as f:
                content = f.read()
                tree = ast.parse(content, filename=str(file_path))
        except (UnicodeDecodeError, SyntaxError) as e:
            # Skip non-Python or binary files
            return {
                "path": str(file_path),
                "error": str(e),
                "docstrings": [],
                "imports": [],
                "functions": [],
                "classes": [],
            }

        return {
            "path": str(file_path),
            "docstrings": self._extract_docstrings(tree),
            "functions": self._extract_function_signatures(tree),
            "classes": self._extract_class_info(tree),
            "comments": self._extract_comments(content),
            "imports": self._extract_imports(tree),
        }

    def _extract_docstrings(self, tree: ast.AST) -> dict[str, str]:
        """Extrait toutes les docstrings (module, classes, fonctions)."""
        # TODO: Implémenter extraction docstrings
        docstrings = {}

        # Module docstring
        if isinstance(tree, ast.Module) and ast.get_docstring(tree):
            docstrings["module"] = ast.get_docstring(tree) or ""

        # Classes et fonctions
        for node in ast.walk(tree):
            if isinstance(node, (ast.FunctionDef, ast.ClassDef)):
                docstring = ast.get_docstring(node)
                if docstring:
                    docstrings[node.name] = docstring

        return docstrings

    def _extract_function_signatures(self, tree: ast.AST) -> list[dict[str, Any]]:
        """Extrait les signatures de toutes les fonctions."""
        # TODO: Implémenter extraction signatures
        signatures = []

        for node in ast.walk(tree):
            if isinstance(node, ast.FunctionDef):
                args = [arg.arg for arg in node.args.args]
                signatures.append(
                    {
                        "name": node.name,
                        "args": args,
                        "returns": ast.unparse(node.returns) if node.returns else None,
                        "is_async": isinstance(node, ast.AsyncFunctionDef),
                    }
                )

        return signatures

    def _extract_class_info(self, tree: ast.AST) -> list[dict[str, Any]]:
        """Extrait informations sur les classes."""
        # TODO: Implémenter extraction classes
        classes = []

        for node in ast.walk(tree):
            if isinstance(node, ast.ClassDef):
                methods = [n.name for n in node.body if isinstance(n, (ast.FunctionDef, ast.AsyncFunctionDef))]
                classes.append(
                    {
                        "name": node.name,
                        "bases": [ast.unparse(base) for base in node.bases],
                        "methods": methods,
                    }
                )

        return classes

    def _extract_comments(self, content: str) -> list[str]:
        """Extrait tous les commentaires inline."""
        # TODO: Implémenter extraction commentaires
        comments = []
        for line in content.split("\n"):
            stripped = line.strip()
            if stripped.startswith("#"):
                comments.append(stripped[1:].strip())
        return comments

    def _extract_imports(self, tree: ast.AST) -> list[str]:
        """Extrait tous les imports."""
        imports = []
        for node in ast.walk(tree):
            if isinstance(node, ast.Import):
                imports.extend(alias.name for alias in node.names)
            elif isinstance(node, ast.ImportFrom) and node.module:
                imports.append(node.module)
        return imports
