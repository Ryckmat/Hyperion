"""Extraction du contenu de code source pour ingestion RAG."""

import ast
from pathlib import Path


class CodeExtractor:
    """
    Extrait le contenu sémantique du code source.

    Process:
    1. Parse AST des fichiers Python
    2. Extrait fonctions, classes, docstrings
    3. Génère chunks textuels pour RAG
    """

    def __init__(self, repo_path: str):
        """Initialise l'extracteur."""
        self.repo_path = Path(repo_path)

    def extract_repo_code(self) -> dict:
        """
        Extrait tout le contenu de code du repository.

        Returns:
            Dict avec sections: files, functions, classes, imports
        """
        result = {
            "files": [],
            "functions": [],
            "classes": [],
            "imports": [],
            "docstrings": []
        }

        # Scanner tous les fichiers Python
        for py_file in self.repo_path.rglob("*.py"):
            if self._should_skip_file(py_file):
                continue

            try:
                file_content = self._extract_file_content(py_file)
                if file_content:
                    result["files"].append(file_content)

                    # Parser AST pour extraire fonctions/classes
                    ast_data = self._parse_ast(py_file)
                    result["functions"].extend(ast_data["functions"])
                    result["classes"].extend(ast_data["classes"])
                    result["imports"].extend(ast_data["imports"])
                    result["docstrings"].extend(ast_data["docstrings"])

            except Exception as e:
                print(f"⚠️  Erreur parsing {py_file}: {e}")
                continue

        return result

    def _extract_file_content(self, file_path: Path) -> dict:
        """Extrait métadonnées d'un fichier."""
        try:
            with open(file_path, encoding='utf-8') as f:
                content = f.read()

            rel_path = file_path.relative_to(self.repo_path)

            return {
                "path": str(rel_path),
                "size_lines": len(content.splitlines()),
                "size_bytes": len(content.encode()),
                "summary": self._extract_file_summary(content)
            }
        except Exception:
            return None

    def _extract_file_summary(self, content: str) -> str:
        """Génère résumé d'un fichier Python."""
        lines = content.splitlines()

        # Extraire docstring module si disponible
        try:
            tree = ast.parse(content)
            if tree.body and isinstance(tree.body[0], ast.Expr) and isinstance(tree.body[0].value, ast.Str):
                return tree.body[0].value.s[:200] + "..."
        except:
            pass

        # Sinon utiliser premiers commentaires
        for line in lines[:10]:
            line = line.strip()
            if line.startswith('"""') or line.startswith("'''"):
                return line[:200] + "..."
            if line.startswith("#") and not line.startswith("#!/"):
                return line[1:].strip()[:200] + "..."

        return f"Module Python avec {len(lines)} lignes"

    def _parse_ast(self, file_path: Path) -> dict:
        """Parse AST et extrait fonctions/classes."""
        result = {
            "functions": [],
            "classes": [],
            "imports": [],
            "docstrings": []
        }

        try:
            with open(file_path, encoding='utf-8') as f:
                content = f.read()

            tree = ast.parse(content)
            rel_path = str(file_path.relative_to(self.repo_path))

            for node in ast.walk(tree):
                # Fonctions
                if isinstance(node, ast.FunctionDef):
                    func_data = self._extract_function(node, rel_path, content)
                    if func_data:
                        result["functions"].append(func_data)

                # Classes
                elif isinstance(node, ast.ClassDef):
                    class_data = self._extract_class(node, rel_path, content)
                    if class_data:
                        result["classes"].append(class_data)

                # Imports
                elif isinstance(node, (ast.Import, ast.ImportFrom)):
                    import_data = self._extract_import(node, rel_path)
                    if import_data:
                        result["imports"].append(import_data)

        except Exception as e:
            print(f"⚠️  Erreur AST {file_path}: {e}")

        return result

    def _extract_function(self, node: ast.FunctionDef, file_path: str, content: str) -> dict:
        """Extrait info d'une fonction."""
        # Docstring
        docstring = ast.get_docstring(node) or "Aucune documentation"

        # Arguments
        args = [arg.arg for arg in node.args.args]

        # Lignes de code
        start_line = node.lineno
        end_line = node.end_lineno or start_line

        return {
            "name": node.name,
            "file": file_path,
            "line_start": start_line,
            "line_end": end_line,
            "args": args,
            "docstring": docstring[:500],  # Limiter taille
            "signature": f"def {node.name}({', '.join(args)})",
            "is_method": self._is_method(node),
            "is_private": node.name.startswith('_')
        }

    def _extract_class(self, node: ast.ClassDef, file_path: str, content: str) -> dict:
        """Extrait info d'une classe."""
        # Docstring
        docstring = ast.get_docstring(node) or "Aucune documentation"

        # Méthodes
        methods = []
        for item in node.body:
            if isinstance(item, ast.FunctionDef):
                methods.append(item.name)

        # Bases (héritage)
        bases = []
        for base in node.bases:
            if isinstance(base, ast.Name):
                bases.append(base.id)

        return {
            "name": node.name,
            "file": file_path,
            "line_start": node.lineno,
            "line_end": node.end_lineno or node.lineno,
            "docstring": docstring[:500],
            "methods": methods,
            "bases": bases,
            "is_private": node.name.startswith('_')
        }

    def _extract_import(self, node, file_path: str) -> dict:
        """Extrait info d'un import."""
        if isinstance(node, ast.Import):
            modules = [alias.name for alias in node.names]
            return {
                "type": "import",
                "modules": modules,
                "file": file_path,
                "line": node.lineno
            }
        elif isinstance(node, ast.ImportFrom):
            return {
                "type": "from_import",
                "module": node.module or "",
                "names": [alias.name for alias in node.names],
                "file": file_path,
                "line": node.lineno
            }

    def _is_method(self, node: ast.FunctionDef) -> bool:
        """Vérifie si une fonction est une méthode."""
        # Approximation : fonction avec 'self' en premier argument
        return (node.args.args and
                node.args.args[0].arg in ['self', 'cls'])

    def _should_skip_file(self, file_path: Path) -> bool:
        """Vérifie si un fichier doit être ignoré."""
        skip_patterns = [
            "__pycache__",
            ".git",
            "build",
            "dist",
            ".venv",
            "venv",
            "node_modules",
            ".pytest_cache",
            "tests/",  # On garde les tests mais séparément
            "test_"
        ]

        path_str = str(file_path)
        return any(pattern in path_str for pattern in skip_patterns)
