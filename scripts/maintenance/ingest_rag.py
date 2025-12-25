#!/usr/bin/env python3
"""Script d'ingestion RAG."""

import argparse
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

from hyperion.rag.ingestion import RAGIngester


def main():
    """Ingestion des repos dans Qdrant."""
    parser = argparse.ArgumentParser(description="Ingestion RAG Hyperion")
    parser.add_argument("--repo", help="Repo spécifique à ingérer")
    parser.add_argument("--clear", action="store_true", help="Clear avant ingestion")
    args = parser.parse_args()

    print("=" * 70)
    print("📥 HYPERION RAG INGESTION")
    print("=" * 70)
    print()

    try:
        # Créer ingester
        ingester = RAGIngester()

        if args.repo:
            # Ingérer un seul repo
            if args.clear:
                print(f"🧹 Nettoyage repo {args.repo}...")
                ingester.clear_repo(args.repo)

            count = ingester.ingest_repo(args.repo)
            print(f"\n✅ Total : {count} chunks ingérés")
        else:
            # Ingérer tous les repos
            results = ingester.ingest_all_repos()

            print("\n" + "=" * 70)
            print("📊 RÉSULTATS")
            print("=" * 70)

            total = 0
            for repo, count in results.items():
                print(f"   • {repo}: {count} chunks")
                total += count

            print(f"\n✅ Total : {total} chunks ingérés pour {len(results)} repos")

        # Stats collection
        stats = ingester.get_stats()
        print("\n📊 Stats Qdrant :")
        print(f"   • Points totaux : {stats['total_points']}")

        print("\n" + "=" * 70)
        print("🎉 INGESTION TERMINÉE !")
        print("=" * 70)

    except Exception as e:
        print(f"\n❌ ERREUR : {e}")
        import traceback

        traceback.print_exc()
        sys.exit(1)


if __name__ == "__main__":
    main()
