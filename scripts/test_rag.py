#!/usr/bin/env python3
"""Test du RAG en ligne de commande."""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

from hyperion.rag.query import RAGQueryEngine


def main():
    """Test interactif du RAG."""
    print("=" * 70)
    print("🤖 HYPERION RAG - TEST INTERACTIF")
    print("=" * 70)
    print()
    print("Initialisation...")
    print()
    
    # Créer query engine
    engine = RAGQueryEngine()
    
    print("=" * 70)
    print("✅ RAG PRÊT ! Pose tes questions (Ctrl+C pour quitter)")
    print("=" * 70)
    print()
    print("💡 Exemples de questions :")
    print("   • Combien de commits dans requests ?")
    print("   • Qui est le contributeur principal ?")
    print("   • Quel fichier a le plus changé ?")
    print("   • Quelle est la qualité du code ?")
    print()
    
    # Boucle interactive
    repo = input("🎯 Filtrer sur un repo ? (vide = tous) : ").strip() or None
    print()
    
    while True:
        try:
            question = input("❓ Question : ").strip()
            
            if not question:
                continue
            
            print("\n⏳ Recherche...")
            
            result = engine.query(question, repo_filter=repo)
            
            print("\n" + "=" * 70)
            print("💬 RÉPONSE")
            print("=" * 70)
            print()
            print(result["answer"])
            print()
            
            if result["sources"]:
                print("📚 Sources :")
                for i, source in enumerate(result["sources"][:3], 1):
                    print(f"   {i}. {source['repo']} ({source['section']}) - score: {source['score']:.3f}")
                print()
            
        except KeyboardInterrupt:
            print("\n\n👋 Au revoir !")
            break
        except Exception as e:
            print(f"\n❌ Erreur : {e}")
            import traceback
            traceback.print_exc()


if __name__ == "__main__":
    try:
        main()
    except Exception as e:
        print(f"\n❌ ERREUR FATALE : {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
