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

from hyperion.modules.understanding.indexer import CodeIndexer


class GeneralizedIngestion:
    """Pipeline d'ingestion multi-sources vers Qdrant + Neo4j."""

    def __init__(
        self,
        qdrant_host: str = "localhost",
        qdrant_port: int = 6333,
        neo4j_uri: str = "bolt://localhost:7687",
    ):
        """
        Initialise le pipeline.

        Args:
            qdrant_host: Hôte Qdrant
            qdrant_port: Port Qdrant
            neo4j_uri: URI Neo4j
        """
        self.qdrant_host = qdrant_host
        self.qdrant_port = qdrant_port
        self.neo4j_uri = neo4j_uri
        self.stats = {"git": 0, "docs": 0, "tickets": 0, "code": 0}

    def ingest_git_repository(self, repo_path: Path) -> int:
        """
        Ingère un repository Git.

        Args:
            repo_path: Chemin du repository

        Returns:
            Nombre d'éléments ingérés
        """
        print(f"📦 Ingestion Git: {repo_path}")
        # TODO: Utiliser existing hyperion.core.git_analyzer
        # TODO: Indexer dans Qdrant + Neo4j
        count = 0
        self.stats["git"] = count
        return count

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
        Ingère l'analyse de code (AST).

        Args:
            repo_path: Chemin du repository

        Returns:
            Nombre de fichiers analysés
        """
        print(f"💻 Ingestion Code Analysis: {repo_path}")
        indexer = CodeIndexer(repo_path)
        code_index = indexer.index_repository()

        # TODO: Indexer dans Qdrant
        # TODO: Créer relations Neo4j (DEPENDS_ON, CALLS, etc)
        count = len(code_index)
        self.stats["code"] = count
        return count

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
        print("🚀 Démarrage ingestion généralisée\n")

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
    )

    tickets_api = None
    if args.tickets_url and args.tickets_token:
        tickets_api = {"url": args.tickets_url, "token": args.tickets_token}

    stats = ingestion.run(repo_path=args.repo, docs_path=args.docs, tickets_api=tickets_api)

    print(f"\n📈 Total ingéré: {sum(stats.values())} éléments")


if __name__ == "__main__":
    main()
