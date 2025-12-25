"""Ingestion Neo4j v2 - Code Source avec Functions, Classes, Imports."""

from pathlib import Path

from neo4j import GraphDatabase

from hyperion.modules.understanding.code_extractor import CodeExtractor


class Neo4jCodeIngester:
    """
    Ingère le code source dans Neo4j v2.

    Crée le modèle de graphe manquant pour le code :
    - (:File)-[:CONTAINS]->(:Function)
    - (:File)-[:CONTAINS]->(:Class)
    - (:Class)-[:HAS_METHOD]->(:Function)
    - (:Function)-[:CALLS]->(:Function) [TODO]
    - (:File)-[:IMPORTS]->(:Module)

    Example:
        >>> ingester = Neo4jCodeIngester()
        >>> ingester.ingest_repo_code("/path/to/repo")
    """

    def __init__(
        self,
        uri: str = "bolt://localhost:7687",
        user: str = "neo4j",
        password: str = "hyperion123",
        database: str = "neo4j",
    ):
        """Initialise la connexion Neo4j."""
        self.uri = uri
        self.user = user
        self.password = password
        self.database = database

        self.driver = GraphDatabase.driver(self.uri, auth=(self.user, self.password))
        self.driver.verify_connectivity()

    def close(self):
        """Ferme la connexion Neo4j."""
        self.driver.close()

    def ingest_repo_code(self, repo_path: str | Path, repo_name: str = None) -> dict[str, int]:
        """
        Ingère tout le code source dans Neo4j v2.

        Args:
            repo_path: Chemin vers le repository
            repo_name: Nom du repo (déduit du path si None)

        Returns:
            Statistiques d'ingestion
        """
        repo_path = Path(repo_path)
        if repo_name is None:
            repo_name = repo_path.name

        stats = {
            "functions": 0,
            "classes": 0,
            "files": 0,
            "imports": 0,
            "methods": 0,
            "function_relations": 0,
            "class_relations": 0,
        }

        # Extraire le code source
        print(f"📊 Extraction code source : {repo_name}")
        extractor = CodeExtractor(str(repo_path))
        code_data = extractor.extract_repo_code()

        print(f"   • {len(code_data['files'])} fichiers")
        print(f"   • {len(code_data['functions'])} fonctions")
        print(f"   • {len(code_data['classes'])} classes")

        with self.driver.session(database=self.database) as session:
            # 1. Setup contraintes et index
            session.execute_write(self._setup_code_constraints)

            # 2. Ingérer fichiers
            session.execute_write(self._ingest_files, repo_name, code_data["files"])
            stats["files"] = len(code_data["files"])

            # 3. Ingérer fonctions
            session.execute_write(self._ingest_functions, repo_name, code_data["functions"])
            stats["functions"] = len(code_data["functions"])

            # 4. Ingérer classes
            session.execute_write(self._ingest_classes, repo_name, code_data["classes"])
            stats["classes"] = len(code_data["classes"])

            # 5. Créer relations File->Function/Class
            session.execute_write(
                self._create_file_relations,
                repo_name,
                code_data["functions"],
                code_data["classes"],
            )

            # 6. Créer relations Class->Method
            stats["methods"] = session.execute_write(
                self._create_class_method_relations, repo_name, code_data["functions"]
            )

            # 7. Ingérer imports
            session.execute_write(self._ingest_imports, repo_name, code_data["imports"])
            stats["imports"] = len(code_data["imports"])

        print(f"✅ Neo4j Code Ingestion: {stats}")
        return stats

    def _setup_code_constraints(self, tx) -> None:
        """Crée les contraintes Neo4j pour le code."""
        constraints = [
            "CREATE CONSTRAINT IF NOT EXISTS FOR (f:Function) REQUIRE f.id IS UNIQUE",
            "CREATE CONSTRAINT IF NOT EXISTS FOR (c:Class) REQUIRE c.id IS UNIQUE",
            "CREATE CONSTRAINT IF NOT EXISTS FOR (f:File) REQUIRE f.path IS UNIQUE",
            "CREATE CONSTRAINT IF NOT EXISTS FOR (m:Module) REQUIRE m.name IS UNIQUE",
        ]

        for constraint in constraints:
            try:
                tx.run(constraint)
            except Exception:
                print(f"⚠️  Constraint exists: {constraint[:50]}...")

    def _ingest_files(self, tx, repo_name: str, files: list[dict]) -> None:
        """Ingère les fichiers de code."""
        query = """
        UNWIND $files AS file
        MERGE (f:File {path: file.path, repo: $repo})
        SET
            f.size_lines = file.size_lines,
            f.size_bytes = file.size_bytes,
            f.summary = file.summary,
            f.updated_at = datetime()
        """

        tx.run(query, files=files, repo=repo_name)

    def _ingest_functions(self, tx, repo_name: str, functions: list[dict]) -> None:
        """Ingère les fonctions."""
        # Préparer les données avec ID unique
        for func in functions:
            func["id"] = f"{repo_name}:{func['file']}:{func['name']}:{func['line_start']}"

        query = """
        UNWIND $functions AS func
        MERGE (f:Function {id: func.id})
        SET
            f.name = func.name,
            f.repo = $repo,
            f.file = func.file,
            f.line_start = func.line_start,
            f.line_end = func.line_end,
            f.signature = func.signature,
            f.docstring = func.docstring,
            f.is_method = func.is_method,
            f.is_private = func.is_private,
            f.args = func.args,
            f.updated_at = datetime()
        """

        tx.run(query, functions=functions, repo=repo_name)

    def _ingest_classes(self, tx, repo_name: str, classes: list[dict]) -> None:
        """Ingère les classes."""
        # Préparer les données avec ID unique
        for cls in classes:
            cls["id"] = f"{repo_name}:{cls['file']}:{cls['name']}:{cls['line_start']}"

        query = """
        UNWIND $classes AS cls
        MERGE (c:Class {id: cls.id})
        SET
            c.name = cls.name,
            c.repo = $repo,
            c.file = cls.file,
            c.line_start = cls.line_start,
            c.line_end = cls.line_end,
            c.docstring = cls.docstring,
            c.methods = cls.methods,
            c.bases = cls.bases,
            c.is_private = cls.is_private,
            c.updated_at = datetime()
        """

        tx.run(query, classes=classes, repo=repo_name)

    def _create_file_relations(
        self, tx, repo_name: str, functions: list[dict], classes: list[dict]
    ) -> None:
        """Crée les relations File->Function et File->Class."""

        # File->Function
        query_func = """
        UNWIND $functions AS func
        MATCH (file:File {path: func.file, repo: $repo})
        MATCH (f:Function {id: $repo + ':' + func.file + ':' + func.name + ':' + toString(func.line_start)})
        MERGE (file)-[:CONTAINS]->(f)
        """
        tx.run(query_func, functions=functions, repo=repo_name)

        # File->Class
        query_class = """
        UNWIND $classes AS cls
        MATCH (file:File {path: cls.file, repo: $repo})
        MATCH (c:Class {id: $repo + ':' + cls.file + ':' + cls.name + ':' + toString(cls.line_start)})
        MERGE (file)-[:CONTAINS]->(c)
        """
        tx.run(query_class, classes=classes, repo=repo_name)

    def _create_class_method_relations(self, tx, repo_name: str, functions: list[dict]) -> int:
        """Crée les relations Class->Method."""
        query = """
        UNWIND $methods AS method
        MATCH (c:Class {repo: $repo})
        WHERE c.file = method.file AND method.name IN c.methods
        MATCH (f:Function {id: $repo + ':' + method.file + ':' + method.name + ':' + toString(method.line_start)})
        MERGE (c)-[:HAS_METHOD]->(f)
        SET f:Method
        """

        # Filtrer seulement les méthodes
        methods = [f for f in functions if f.get("is_method", False)]
        tx.run(query, methods=methods, repo=repo_name)

        return len(methods)

    def _ingest_imports(self, tx, repo_name: str, imports: list[dict]) -> None:
        """Ingère les imports."""
        query = """
        UNWIND $imports AS imp
        MERGE (file:File {path: imp.file, repo: $repo})
        WITH file, imp
        UNWIND (CASE
            WHEN imp.type = 'import' THEN imp.modules
            WHEN imp.type = 'from_import' THEN [imp.module]
            ELSE []
        END) AS module_name
        MERGE (m:Module {name: module_name})
        MERGE (file)-[:IMPORTS]->(m)
        """

        tx.run(query, imports=imports, repo=repo_name)

    def get_repo_stats(self, repo_name: str) -> dict:
        """Obtient les statistiques d'un repo."""
        with self.driver.session(database=self.database) as session:
            result = session.run(
                """
                MATCH (f:Function {repo: $repo})
                WITH count(f) as functions
                MATCH (c:Class {repo: $repo})
                WITH functions, count(c) as classes
                MATCH (file:File {repo: $repo})
                WITH functions, classes, count(file) as files
                MATCH (m:Method {repo: $repo})
                RETURN functions, classes, files, count(m) as methods
            """,
                repo=repo_name,
            ).single()

            if result:
                return {
                    "functions": result["functions"],
                    "classes": result["classes"],
                    "files": result["files"],
                    "methods": result["methods"],
                }
            return {"functions": 0, "classes": 0, "files": 0, "methods": 0}

    def clear_repo(self, repo_name: str) -> None:
        """Supprime toutes les données d'un repo."""
        with self.driver.session(database=self.database) as session:
            session.run(
                """
                MATCH (n {repo: $repo})
                DETACH DELETE n
            """,
                repo=repo_name,
            )
        print(f"🧹 Repo {repo_name} supprimé de Neo4j")
