#!/usr/bin/env python3
"""
Script d'ingestion généralisé multi-sources.

Sources supportées:
- Git repositories (commits, diffs)
- Documentation (Markdown, HTML)
- Tickets (GitLab, Jira via API)
- Code source (AST parsing)

Auteur: Ryckman Matthieu
Projet: Hyperion (projet personnel)
Version: 2.0.0
"""

import argparse
import json
import sys
from pathlib import Path
from typing import Any

from neo4j import GraphDatabase

from hyperion.modules.understanding.indexer import CodeIndexer


class GeneralizedIngestion:
    """Pipeline d'ingestion multi-sources vers Qdrant + Neo4j."""

    def __init__(
        self,
        qdrant_host: str = "localhost",
        qdrant_port: int = 6333,
        neo4j_uri: str = "bolt://localhost:7687",
        neo4j_user: str = "neo4j",
        neo4j_password: str = "password",
    ):
        """
        Initialise le pipeline.

        Args:
            qdrant_host: Hôte Qdrant
            qdrant_port: Port Qdrant
            neo4j_uri: URI Neo4j
            neo4j_user: Username Neo4j
            neo4j_password: Password Neo4j
        """
        self.qdrant_host = qdrant_host
        self.qdrant_port = qdrant_port
        self.neo4j_uri = neo4j_uri
        self.neo4j_password = neo4j_password
        self.stats = {"git": 0, "docs": 0, "tickets": 0, "code": 0, "neo4j_nodes": 0, "neo4j_relations": 0}

        # Connexion Neo4j
        try:
            self.neo4j_driver = GraphDatabase.driver(neo4j_uri, auth=(neo4j_user, neo4j_password))
            self.neo4j_driver.verify_connectivity()
            print(f"✅ Neo4j connecté ({neo4j_uri})")
            self._setup_neo4j_constraints()
        except Exception as e:
            print(f"⚠️  Neo4j non disponible: {e}")
            self.neo4j_driver = None

    def _setup_neo4j_constraints(self):
        """Crée les contraintes et index Neo4j pour v2."""
        if not self.neo4j_driver:
            return

        constraints = [
            "CREATE CONSTRAINT file_path IF NOT EXISTS FOR (f:File) REQUIRE f.path IS UNIQUE",
            "CREATE CONSTRAINT function_id IF NOT EXISTS FOR (fn:Function) REQUIRE fn.id IS UNIQUE",
            "CREATE CONSTRAINT class_id IF NOT EXISTS FOR (c:Class) REQUIRE c.id IS UNIQUE",
            "CREATE INDEX file_repo IF NOT EXISTS FOR (f:File) ON (f.repo)",
            "CREATE INDEX function_name IF NOT EXISTS FOR (fn:Function) ON (fn.name)",
        ]

        with self.neo4j_driver.session() as session:
            for constraint in constraints:
                try:
                    session.run(constraint)
                except Exception:
                    pass  # Contrainte existe déjà

    def ingest_git_repository(self, repo_path: Path) -> int:
        """
        Ingère un repository Git avec tracking complet Commit->Contributor->File.

        Args:
            repo_path: Chemin du repository

        Returns:
            Nombre d'éléments ingérés
        """
        print(f"📦 Ingestion Git: {repo_path}")

        # Import ici pour éviter la dépendance circulaire
        from hyperion.modules.integrations.neo4j_v2_git_ingester import (
            Neo4jV2GitIngester,
        )

        if self.neo4j_driver:
            git_ingester = Neo4jV2GitIngester(
                uri=self.neo4j_uri,
                user="neo4j",
                password=self.neo4j_password,
            )

            try:
                git_stats = git_ingester.ingest_git_history(repo_path)
                git_ingester.close()

                print(f"   ✅ Git History: {git_stats}")

                # Mettre à jour les stats
                count = git_stats["commits"]
                self.stats["git"] = count
                self.stats["neo4j_nodes"] += (
                    git_stats["commits"]
                    + git_stats["contributors"]
                    + git_stats["directories"]
                )
                self.stats["neo4j_relations"] += (
                    git_stats["commit_relations"]
                    + git_stats["file_relations"]
                    + git_stats["directory_relations"]
                )

                return count

            except Exception as e:
                print(f"   ⚠️  Erreur ingestion Git: {e}")
                return 0

        print("   ⚠️  Neo4j non disponible - Git skip")
        return 0

    def ingest_documentation(self, docs_path: Path) -> int:
        """
        Ingère de la documentation.

        Args:
            docs_path: Chemin des docs

        Returns:
            Nombre de documents ingérés
        """
        print(f"📚 Ingestion Documentation: {docs_path}")
        # TODO: Parser Markdown/HTML
        # TODO: Chunking intelligent
        # TODO: Indexer Qdrant
        count = 0
        markdown_files = list(Path(docs_path).rglob("*.md"))
        count = len(markdown_files)
        self.stats["docs"] = count
        return count

    def ingest_tickets(self, api_url: str, api_token: str) -> int:
        """
        Ingère des tickets depuis API.

        Args:
            api_url: URL de l'API
            api_token: Token d'authentification

        Returns:
            Nombre de tickets ingérés
        """
        print(f"🎫 Ingestion Tickets: {api_url}")
        # TODO: Appels API GitLab/Jira
        # TODO: Parser issues/MR
        # TODO: Indexer Qdrant + Neo4j
        count = 0
        self.stats["tickets"] = count
        return count

    def ingest_code_analysis(self, repo_path: Path) -> int:
        """
        Ingère l'analyse de code (AST) dans Neo4j v2.

        Crée:
        - Nodes :File avec métadonnées
        - Nodes :Function, :Class
        - Relations :DEPENDS_ON, :CONTAINS, :IMPORTS

        Args:
            repo_path: Chemin du repository

        Returns:
            Nombre de fichiers analysés
        """
        print(f"💻 Ingestion Code Analysis: {repo_path}")

        # 1. Indexation AST
        indexer = CodeIndexer(repo_path)
        code_index = indexer.index_repository()

        if not code_index:
            print("   ⚠️  Aucun fichier Python trouvé")
            return 0

        # 2. Ingestion Neo4j v2
        if self.neo4j_driver:
            nodes_count, relations_count = self._ingest_to_neo4j(repo_path, code_index)
            self.stats["neo4j_nodes"] = nodes_count
            self.stats["neo4j_relations"] = relations_count
            print(f"   ✅ Neo4j: {nodes_count} nodes, {relations_count} relations")

        # 3. TODO: Indexer dans Qdrant
        count = len(code_index)
        self.stats["code"] = count
        return count

    def _ingest_to_neo4j(self, repo_path: Path, code_index: dict) -> tuple[int, int]:
        """
        Ingère le code_index dans Neo4j avec labels v2.

        Args:
            repo_path: Chemin du repo
            code_index: Index généré par CodeIndexer

        Returns:
            (nodes_count, relations_count)
        """
        repo_name = repo_path.name
        nodes_count = 0
        relations_count = 0

        with self.neo4j_driver.session() as session:
            for file_path, metadata in code_index.items():
                # Créer node :File
                session.run(
                    """
                    MERGE (f:File {path: $path})
                    SET f.repo = $repo,
                        f.num_functions = $num_functions,
                        f.num_classes = $num_classes,
                        f.has_docstring = $has_docstring
                    """,
                    path=file_path,
                    repo=repo_name,
                    num_functions=len(metadata.get("functions", [])),
                    num_classes=len(metadata.get("classes", [])),
                    has_docstring="module" in metadata.get("docstrings", {}),
                )
                nodes_count += 1

                # Créer nodes :Function
                for func in metadata.get("functions", []):
                    func_id = f"{file_path}::{func['name']}"
                    session.run(
                        """
                        MERGE (fn:Function {id: $id})
                        SET fn.name = $name,
                            fn.file = $file,
                            fn.args = $args,
                            fn.returns = $returns,
                            fn.is_async = $is_async
                        WITH fn
                        MATCH (f:File {path: $file})
                        MERGE (f)-[:CONTAINS]->(fn)
                        """,
                        id=func_id,
                        name=func["name"],
                        file=file_path,
                        args=func.get("args", []),
                        returns=func.get("returns"),
                        is_async=func.get("is_async", False),
                    )
                    nodes_count += 1
                    relations_count += 1

                # Créer nodes :Class
                for cls in metadata.get("classes", []):
                    cls_id = f"{file_path}::{cls['name']}"
                    session.run(
                        """
                        MERGE (c:Class {id: $id})
                        SET c.name = $name,
                            c.file = $file,
                            c.bases = $bases,
                            c.methods = $methods
                        WITH c
                        MATCH (f:File {path: $file})
                        MERGE (f)-[:CONTAINS]->(c)
                        """,
                        id=cls_id,
                        name=cls["name"],
                        file=file_path,
                        bases=cls.get("bases", []),
                        methods=cls.get("methods", []),
                    )
                    nodes_count += 1
                    relations_count += 1

                # Créer relations :IMPORTS (dépendances)
                for import_name in metadata.get("imports", []):
                    # Chercher si l'import correspond à un fichier du repo
                    potential_paths = [
                        str(repo_path / f"{import_name.replace('.', '/')}.py"),
                        str(repo_path / import_name.replace(".", "/") / "__init__.py"),
                    ]

                    for potential_path in potential_paths:
                        if potential_path in code_index:
                            session.run(
                                """
                                MATCH (source:File {path: $source})
                                MATCH (target:File {path: $target})
                                MERGE (source)-[:DEPENDS_ON {type: 'import'}]->(target)
                                """,
                                source=file_path,
                                target=potential_path,
                            )
                            relations_count += 1
                            break

        return nodes_count, relations_count

    def run(
        self,
        repo_path: Path | None = None,
        docs_path: Path | None = None,
        tickets_api: dict[str, str] | None = None,
    ) -> dict[str, Any]:
        """
        Execute le pipeline complet.

        Args:
            repo_path: Repository Git optionnel
            docs_path: Documentation optionnelle
            tickets_api: Config API tickets optionnelle

        Returns:
            Statistiques d'ingestion
        """
        print("🚀 Démarrage ingestion généralisée v2\n")

        if repo_path:
            self.ingest_git_repository(Path(repo_path))
            self.ingest_code_analysis(Path(repo_path))

        if docs_path:
            self.ingest_documentation(Path(docs_path))

        if tickets_api:
            self.ingest_tickets(tickets_api["url"], tickets_api["token"])

        print(f"\n✅ Ingestion terminée")
        print(f"📊 Stats: {json.dumps(self.stats, indent=2)}")

        return self.stats

    def close(self):
        """Ferme les connexions."""
        if self.neo4j_driver:
            self.neo4j_driver.close()


def main():
    """Point d'entrée CLI."""
    parser = argparse.ArgumentParser(description="Ingestion généralisée multi-sources Hyperion v2")

    parser.add_argument("--repo", type=str, help="Chemin du repository Git")
    parser.add_argument("--docs", type=str, help="Chemin de la documentation")
    parser.add_argument("--tickets-url", type=str, help="URL API tickets")
    parser.add_argument("--tickets-token", type=str, help="Token API tickets")
    parser.add_argument("--qdrant-host", type=str, default="localhost", help="Hôte Qdrant")
    parser.add_argument("--qdrant-port", type=int, default=6333, help="Port Qdrant")
    parser.add_argument("--neo4j-uri", type=str, default="bolt://localhost:7687", help="URI Neo4j")
    parser.add_argument("--neo4j-user", type=str, default="neo4j", help="Username Neo4j")
    parser.add_argument("--neo4j-password", type=str, default="password", help="Password Neo4j")

    args = parser.parse_args()

    # Validation
    if not any([args.repo, args.docs, args.tickets_url]):
        print("❌ Erreur: Au moins une source doit être spécifiée (--repo, --docs, --tickets-url)")
        sys.exit(1)

    # Exécution
    ingestion = GeneralizedIngestion(
        qdrant_host=args.qdrant_host,
        qdrant_port=args.qdrant_port,
        neo4j_uri=args.neo4j_uri,
        neo4j_user=args.neo4j_user,
        neo4j_password=args.neo4j_password,
    )

    try:
        tickets_api = None
        if args.tickets_url and args.tickets_token:
            tickets_api = {"url": args.tickets_url, "token": args.tickets_token}

        stats = ingestion.run(repo_path=args.repo, docs_path=args.docs, tickets_api=tickets_api)

        print(f"\n📈 Total ingéré: {sum(stats.values())} éléments")
    finally:
        ingestion.close()


if __name__ == "__main__":
    main()
