#!/usr/bin/env python3
"""
Test d'ingestion v2 sur un petit repo.

Auteur: Ryckman Matthieu
Projet: Hyperion (projet personnel)
Version: 2.0.0
"""

import sys
from pathlib import Path

# Ajouter src au path
sys.path.insert(0, str(Path(__file__).parent.parent.parent / "src"))

from scripts.maintenance.ingest_generalized import GeneralizedIngestion


def test_ingestion_small_repo():
    """Test ingestion sur un petit repo."""
    # Créer un mini repo de test
    test_repo = Path("/tmp/test_hyperion_v2")
    test_repo.mkdir(exist_ok=True)

    # Fichier 1: main.py
    (test_repo / "main.py").write_text(
        '''
"""Module principal."""
from utils import helper

def main():
    """Point d'entrée."""
    result = helper("test")
    return result

if __name__ == "__main__":
    main()
'''
    )

    # Fichier 2: utils.py
    (test_repo / "utils.py").write_text(
        '''
"""Utilities."""

def helper(data: str) -> str:
    """Helper function."""
    return data.upper()

class DataProcessor:
    """Process data."""
    
    def process(self, data):
        """Process method."""
        return helper(data)
'''
    )

    # Lancer ingestion
    print("🧪 Test ingestion v2 sur mini repo\n")

    ingestion = GeneralizedIngestion(
        neo4j_uri="bolt://localhost:7687",
        neo4j_user="neo4j",
        neo4j_password="password",
    )

    try:
        stats = ingestion.run(repo_path=test_repo)

        print("\n✅ Test réussi !")
        print(f"   Fichiers analysés: {stats['code']}")
        print(f"   Nodes Neo4j: {stats['neo4j_nodes']}")
        print(f"   Relations Neo4j: {stats['neo4j_relations']}")

        # Vérifications
        assert stats["code"] == 2, "Devrait avoir 2 fichiers"
        assert stats["neo4j_nodes"] > 0, "Devrait avoir des nodes"
        assert stats["neo4j_relations"] > 0, "Devrait avoir des relations"

        print("\n🎉 Tous les tests passent !")

    except Exception as e:
        print(f"\n❌ Erreur: {e}")
        import traceback

        traceback.print_exc()
        sys.exit(1)
    finally:
        ingestion.close()


if __name__ == "__main__":
    test_ingestion_small_repo()
