"""
Parser AST pour analyse sémantique de code Python.

Module d'analyse statique pour extraire la structure, les dépendances et la complexité du code.
"""

from __future__ import annotations

import ast
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

from hyperion.modules.monitoring.logging.json_logger import get_logger

logger = get_logger("hyperion.ast_parser")


@dataclass
class FunctionInfo:
    """Information extraite sur une fonction."""

    name: str
    lineno: int
    col_offset: int
    args: list[str]
    defaults: list[Any]
    decorators: list[str]
    docstring: str | None
    return_annotation: str | None
    complexity: int = 0
    calls: list[str] = field(default_factory=list)
    is_async: bool = False
    is_method: bool = False
    visibility: str = "public"  # public, protected, private


@dataclass
class ClassInfo:
    """Information extraite sur une classe."""

    name: str
    lineno: int
    col_offset: int
    bases: list[str]
    decorators: list[str]
    docstring: str | None
    methods: list[FunctionInfo] = field(default_factory=list)
    attributes: list[str] = field(default_factory=list)
    is_abstract: bool = False
    visibility: str = "public"


@dataclass
class ImportInfo:
    """Information sur un import."""

    module: str
    name: str | None = None  # Pour les imports from X import Y
    alias: str | None = None
    lineno: int = 0
    is_relative: bool = False


@dataclass
class FileAnalysis:
    """Résultat complet d'analyse d'un fichier."""

    file_path: str
    encoding: str
    lines_of_code: int
    lines_of_comments: int
    lines_blank: int
    imports: list[ImportInfo]
    functions: list[FunctionInfo]
    classes: list[ClassInfo]
    variables: list[str]
    constants: list[str]
    complexity_total: int
    dependencies: set[str] = field(default_factory=set)
    exports: set[str] = field(default_factory=set)  # __all__
    errors: list[str] = field(default_factory=list)


class PythonASTParser:
    """
    Parser AST pour Python avec analyse sémantique avancée.

    Fonctionnalités :
    - Extraction structure (classes, fonctions, imports)
    - Calcul de complexité cyclomatique
    - Analyse des dépendances
    - Détection des patterns (singleton, factory, etc.)
    - Métriques de qualité code
    """

    def __init__(self):
        self.logger = get_logger("hyperion.ast_parser")

    def parse_file(self, file_path: str | Path) -> FileAnalysis | None:
        """
        Parse un fichier Python et extrait toutes les informations.

        Args:
            file_path: Chemin vers le fichier Python

        Returns:
            Analyse complète du fichier ou None si erreur
        """
        file_path = Path(file_path)

        if not file_path.exists():
            self.logger.error(f"Fichier non trouvé : {file_path}")
            return None

        if file_path.suffix != ".py":
            self.logger.warning(f"Fichier non Python ignoré : {file_path}")
            return None

        try:
            # Lecture du fichier avec détection encoding
            content, encoding = self._read_file_with_encoding(file_path)

            # Parse AST
            tree = ast.parse(content, filename=str(file_path))

            # Analyse complète
            analysis = self._analyze_ast(tree, str(file_path), content, encoding)

            self.logger.debug(
                f"Fichier analysé : {file_path}",
                functions=len(analysis.functions),
                classes=len(analysis.classes),
                imports=len(analysis.imports),
                complexity=analysis.complexity_total,
            )

            return analysis

        except SyntaxError as e:
            self.logger.error(f"Erreur syntaxe dans {file_path} : {e}")
            return FileAnalysis(
                file_path=str(file_path),
                encoding="utf-8",
                lines_of_code=0,
                lines_of_comments=0,
                lines_blank=0,
                imports=[],
                functions=[],
                classes=[],
                variables=[],
                constants=[],
                complexity_total=0,
                errors=[f"SyntaxError: {e}"],
            )
        except Exception as e:
            self.logger.error(f"Erreur parsing {file_path} : {e}", exc_info=True)
            return None

    def _read_file_with_encoding(self, file_path: Path) -> tuple[str, str]:
        """Lit un fichier avec détection automatique de l'encoding."""
        # Tentative avec encodings courants
        encodings = ["utf-8", "utf-8-sig", "latin1", "cp1252"]

        for encoding in encodings:
            try:
                with open(file_path, encoding=encoding) as f:
                    content = f.read()
                return content, encoding
            except UnicodeDecodeError:
                continue

        # Fallback avec erreurs ignorées
        with open(file_path, encoding="utf-8", errors="ignore") as f:
            content = f.read()
        return content, "utf-8"

    def _analyze_ast(
        self, tree: ast.AST, file_path: str, content: str, encoding: str
    ) -> FileAnalysis:
        """Analyse complète de l'AST."""
        # Comptage de lignes
        lines_stats = self._count_lines(content)

        # Extraction des éléments
        imports = self._extract_imports(tree)
        functions = self._extract_functions(tree)
        classes = self._extract_classes(tree)
        variables = self._extract_variables(tree)
        constants = self._extract_constants(tree)

        # Calcul complexité totale
        complexity_total = sum(f.complexity for f in functions)
        for cls in classes:
            complexity_total += sum(m.complexity for m in cls.methods)

        # Analyse des dépendances
        dependencies = self._extract_dependencies(imports, functions, classes)

        # Exports (__all__)
        exports = self._extract_exports(tree)

        return FileAnalysis(
            file_path=file_path,
            encoding=encoding,
            lines_of_code=lines_stats["code"],
            lines_of_comments=lines_stats["comments"],
            lines_blank=lines_stats["blank"],
            imports=imports,
            functions=functions,
            classes=classes,
            variables=variables,
            constants=constants,
            complexity_total=complexity_total,
            dependencies=dependencies,
            exports=exports,
        )

    def _count_lines(self, content: str) -> dict[str, int]:
        """Compte les lignes de code, commentaires et blanches."""
        lines = content.split("\n")
        stats = {"code": 0, "comments": 0, "blank": 0}

        in_multiline_string = False
        quote_char = None

        for line in lines:
            stripped = line.strip()

            if not stripped:
                stats["blank"] += 1
                continue

            # Gérer les chaînes multilignes (docstrings)
            if '"""' in stripped or "'''" in stripped:
                if not in_multiline_string:
                    quote_char = '"""' if '"""' in stripped else "'''"
                    in_multiline_string = True
                elif quote_char in stripped:
                    in_multiline_string = False
                    quote_char = None

            if in_multiline_string or stripped.startswith("#"):
                stats["comments"] += 1
            else:
                stats["code"] += 1

        return stats

    def _extract_imports(self, tree: ast.AST) -> list[ImportInfo]:
        """Extrait les imports du fichier."""
        imports = []

        for node in ast.walk(tree):
            if isinstance(node, ast.Import):
                for alias in node.names:
                    imports.append(
                        ImportInfo(
                            module=alias.name,
                            alias=alias.asname,
                            lineno=node.lineno,
                            is_relative=False,
                        )
                    )

            elif isinstance(node, ast.ImportFrom):
                module = node.module or ""
                level = getattr(node, "level", 0)

                for alias in node.names:
                    imports.append(
                        ImportInfo(
                            module=module,
                            name=alias.name,
                            alias=alias.asname,
                            lineno=node.lineno,
                            is_relative=level > 0,
                        )
                    )

        return imports

    def _extract_functions(self, tree: ast.AST) -> list[FunctionInfo]:
        """Extrait les fonctions du fichier."""
        functions = []

        for node in ast.walk(tree):
            if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
                func_info = self._analyze_function(node)
                functions.append(func_info)

        return functions

    def _analyze_function(self, node: ast.FunctionDef | ast.AsyncFunctionDef) -> FunctionInfo:
        """Analyse détaillée d'une fonction."""
        # Arguments
        args = []
        defaults = []

        if node.args:
            args = [arg.arg for arg in node.args.args]
            defaults = [
                ast.unparse(default) if hasattr(ast, "unparse") else str(default)
                for default in node.args.defaults
            ]

        # Décorateurs
        decorators = []
        for decorator in node.decorator_list:
            if hasattr(ast, "unparse"):
                decorators.append(ast.unparse(decorator))
            else:
                decorators.append(self._get_decorator_name(decorator))

        # Docstring
        docstring = ast.get_docstring(node)

        # Annotation de retour
        return_annotation = None
        if node.returns and hasattr(ast, "unparse"):
            return_annotation = ast.unparse(node.returns)

        # Appels de fonctions
        calls = self._extract_function_calls(node)

        # Complexité cyclomatique
        complexity = self._calculate_complexity(node)

        # Visibilité (convention Python)
        visibility = "public"
        if node.name.startswith("__") and node.name.endswith("__"):
            visibility = "magic"
        elif node.name.startswith("__"):
            visibility = "private"
        elif node.name.startswith("_"):
            visibility = "protected"

        return FunctionInfo(
            name=node.name,
            lineno=node.lineno,
            col_offset=node.col_offset,
            args=args,
            defaults=defaults,
            decorators=decorators,
            docstring=docstring,
            return_annotation=return_annotation,
            complexity=complexity,
            calls=calls,
            is_async=isinstance(node, ast.AsyncFunctionDef),
            is_method=False,  # Sera mis à jour si dans une classe
            visibility=visibility,
        )

    def _extract_classes(self, tree: ast.AST) -> list[ClassInfo]:
        """Extrait les classes du fichier."""
        classes = []

        for node in ast.walk(tree):
            if isinstance(node, ast.ClassDef):
                class_info = self._analyze_class(node)
                classes.append(class_info)

        return classes

    def _analyze_class(self, node: ast.ClassDef) -> ClassInfo:
        """Analyse détaillée d'une classe."""
        # Bases (héritage)
        bases = []
        for base in node.bases:
            if hasattr(ast, "unparse"):
                bases.append(ast.unparse(base))
            elif isinstance(base, ast.Name):
                bases.append(base.id)

        # Décorateurs
        decorators = []
        for decorator in node.decorator_list:
            if hasattr(ast, "unparse"):
                decorators.append(ast.unparse(decorator))
            else:
                decorators.append(self._get_decorator_name(decorator))

        # Docstring
        docstring = ast.get_docstring(node)

        # Méthodes
        methods = []
        for child in node.body:
            if isinstance(child, (ast.FunctionDef, ast.AsyncFunctionDef)):
                method_info = self._analyze_function(child)
                method_info.is_method = True
                methods.append(method_info)

        # Attributs de classe
        attributes = []
        for child in node.body:
            if isinstance(child, ast.Assign):
                for target in child.targets:
                    if isinstance(target, ast.Name):
                        attributes.append(target.id)

        # Détection classe abstraite
        is_abstract = (
            any("abstractmethod" in str(dec) for dec in decorators)
            or any("ABC" in base for base in bases)
            or "abc.ABC" in str(bases)
        )

        # Visibilité
        visibility = "public"
        if node.name.startswith("_"):
            visibility = (
                "protected"
                if node.name.startswith("_") and not node.name.startswith("__")
                else "private"
            )

        return ClassInfo(
            name=node.name,
            lineno=node.lineno,
            col_offset=node.col_offset,
            bases=bases,
            decorators=decorators,
            docstring=docstring,
            methods=methods,
            attributes=attributes,
            is_abstract=is_abstract,
            visibility=visibility,
        )

    def _extract_variables(self, tree: ast.AST) -> list[str]:
        """Extrait les variables globales."""
        variables = []

        for node in ast.walk(tree):
            if isinstance(node, ast.Assign):
                for target in node.targets:
                    if isinstance(target, ast.Name) and not target.id.isupper():
                        # Éviter les constantes (convention UPPER_CASE)
                        variables.append(target.id)

        return list(set(variables))

    def _extract_constants(self, tree: ast.AST) -> list[str]:
        """Extrait les constantes (variables en UPPER_CASE)."""
        constants = []

        for node in ast.walk(tree):
            if isinstance(node, ast.Assign):
                for target in node.targets:
                    if isinstance(target, ast.Name) and target.id.isupper():
                        constants.append(target.id)

        return list(set(constants))

    def _extract_function_calls(self, node: ast.AST) -> list[str]:
        """Extrait les appels de fonctions dans un nœud."""
        calls = []

        for child in ast.walk(node):
            if isinstance(child, ast.Call):
                if isinstance(child.func, ast.Name):
                    calls.append(child.func.id)
                elif isinstance(child.func, ast.Attribute):
                    calls.append(child.func.attr)

        return calls

    def _calculate_complexity(self, node: ast.AST) -> int:
        """
        Calcule la complexité cyclomatique d'une fonction.

        La complexité cyclomatique compte le nombre de chemins linéairement
        indépendants dans le code.
        """
        complexity = 1  # Base complexity

        for child in ast.walk(node):
            # Structures de contrôle qui augmentent la complexité
            if isinstance(
                child,
                (
                    ast.If,
                    ast.While,
                    ast.For,
                    ast.AsyncFor,
                    ast.ExceptHandler,
                    ast.And,
                    ast.Or,
                    ast.comprehension,
                ),
            ):
                complexity += 1

        return complexity

    def _extract_dependencies(
        self, imports: list[ImportInfo], functions: list[FunctionInfo], classes: list[ClassInfo]
    ) -> set[str]:
        """Extrait les dépendances du module."""
        dependencies = set()

        # Dépendances des imports
        for imp in imports:
            if imp.module:
                # Extraire le package principal
                base_module = imp.module.split(".")[0]
                dependencies.add(base_module)

        # Dépendances des appels de fonctions (heuristique)
        all_calls = []
        for func in functions:
            all_calls.extend(func.calls)

        for cls in classes:
            for method in cls.methods:
                all_calls.extend(method.calls)

        # Filtrer les dépendances externes connues
        external_packages = {
            "os",
            "sys",
            "json",
            "yaml",
            "requests",
            "numpy",
            "pandas",
            "torch",
            "tensorflow",
            "sklearn",
            "matplotlib",
            "seaborn",
        }

        for call in all_calls:
            if call in external_packages:
                dependencies.add(call)

        return dependencies

    def _extract_exports(self, tree: ast.AST) -> set[str]:
        """Extrait les exports (__all__) du module."""
        exports = set()

        for node in ast.walk(tree):
            if isinstance(node, ast.Assign):
                for target in node.targets:
                    if (
                        isinstance(target, ast.Name)
                        and target.id == "__all__"
                        and isinstance(node.value, ast.List)
                    ):
                        # Extraire la liste
                        for elt in node.value.elts:
                            if isinstance(elt, ast.Str):
                                exports.add(elt.s)
                            elif isinstance(elt, ast.Constant) and isinstance(elt.value, str):
                                exports.add(elt.value)

        return exports

    def _get_decorator_name(self, decorator: ast.AST) -> str:
        """Extrait le nom d'un décorateur."""
        if isinstance(decorator, ast.Name):
            return decorator.id
        elif isinstance(decorator, ast.Attribute):
            return decorator.attr
        elif isinstance(decorator, ast.Call):
            if isinstance(decorator.func, ast.Name):
                return decorator.func.id
            elif isinstance(decorator.func, ast.Attribute):
                return decorator.func.attr

        return str(decorator)

    def analyze_directory(
        self, directory: str | Path, recursive: bool = True
    ) -> dict[str, FileAnalysis]:
        """
        Analyse tous les fichiers Python d'un répertoire.

        Args:
            directory: Répertoire à analyser
            recursive: Analyse récursive des sous-dossiers

        Returns:
            Dictionnaire des analyses par fichier
        """
        directory = Path(directory)
        results = {}

        if not directory.exists():
            self.logger.error(f"Répertoire non trouvé : {directory}")
            return results

        # Trouver tous les fichiers Python
        pattern = "**/*.py" if recursive else "*.py"
        python_files = list(directory.glob(pattern))

        self.logger.info(
            f"Analyse du répertoire {directory}", files_found=len(python_files), recursive=recursive
        )

        for file_path in python_files:
            # Ignorer les fichiers dans __pycache__
            if "__pycache__" in str(file_path):
                continue

            analysis = self.parse_file(file_path)
            if analysis:
                relative_path = str(file_path.relative_to(directory))
                results[relative_path] = analysis

        self.logger.info(
            "Analyse terminée",
            files_analyzed=len(results),
            total_functions=sum(len(a.functions) for a in results.values()),
            total_classes=sum(len(a.classes) for a in results.values()),
        )

        return results

    def get_dependency_graph(self, analyses: dict[str, FileAnalysis]) -> dict[str, set[str]]:
        """
        Construit un graphe de dépendances entre fichiers.

        Args:
            analyses: Résultats d'analyse par fichier

        Returns:
            Graphe de dépendances (fichier -> set de dépendances)
        """
        graph = {}

        for file_path, analysis in analyses.items():
            dependencies = set()

            # Dépendances via imports relatifs
            for imp in analysis.imports:
                if imp.is_relative or imp.module.startswith("."):
                    # Convertir en chemin de fichier potentiel
                    module_path = imp.module.replace(".", "/") + ".py"
                    if module_path in analyses:
                        dependencies.add(module_path)

            graph[file_path] = dependencies

        return graph
