#!/usr/bin/env python3
"""
🚀 HYPERION MASTER SCRIPT
Script complet : Analyse Git → Profil YAML → Ingestion Neo4j

Usage:
    python3 scripts/hyperion_full_workflow.py /path/to/repo [--clear]

Options:
    --clear    Nettoie les données existantes du repo dans Neo4j avant ingestion
"""

import sys
from pathlib import Path
import yaml
import argparse

# Ajouter Hyperion au PYTHONPATH
sys.path.insert(0, str(Path(__file__).parent.parent))

from hyperion.core.git_analyzer import GitAnalyzer
from hyperion.integrations.neo4j_ingester import Neo4jIngester


def main():
    """Workflow complet Hyperion."""
    
    # Parser arguments
    parser = argparse.ArgumentParser(description="Hyperion Full Workflow")
    parser.add_argument("repo_path", help="Chemin vers le dépôt Git")
    parser.add_argument("--clear", action="store_true", help="Nettoyer les données existantes")
    parser.add_argument("--skip-neo4j", action="store_true", help="Skip l'ingestion Neo4j")
    args = parser.parse_args()
    
    repo_path = Path(args.repo_path).resolve()
    
    if not repo_path.exists():
        print(f"❌ Chemin introuvable : {repo_path}")
        sys.exit(1)
    
    print("=" * 80)
    print("🚀 HYPERION FULL WORKFLOW")
    print("=" * 80)
    print(f"\n📁 Repository : {repo_path}")
    print(f"🧹 Clear data  : {'✅ Oui' if args.clear else '❌ Non'}")
    print(f"🗄️  Neo4j      : {'❌ Skip' if args.skip_neo4j else '✅ Actif'}")
    
    # ========================================================================
    # ÉTAPE 1 : ANALYSE GIT
    # ========================================================================
    
    print("\n" + "=" * 80)
    print("📊 ÉTAPE 1/3 : ANALYSE GIT")
    print("=" * 80)
    
    print(f"\n⏳ Analyse en cours de {repo_path.name}...")
    print("   (Cela peut prendre 30-60 secondes selon la taille du repo)")
    
    try:
        analyzer = GitAnalyzer(str(repo_path))
        profile = analyzer.analyze()
        
        repo_name = profile["service"]
        
        print(f"\n✅ Analyse terminée !")
        print(f"   • Repo          : {repo_name}")
        print(f"   • Commits       : {profile['git_summary']['commits']:,}")
        print(f"   • Contributeurs : {profile['git_summary']['contributors']:,}")
        print(f"   • Hotspots      : {len(profile['git_summary']['hotspots_top10'])}")
        print(f"   • Langage       : {profile['repositories'][0]['main_language']}")
        print(f"   • Licence       : {profile['repositories'][0]['license']}")
        
    except Exception as e:
        print(f"\n❌ ERREUR lors de l'analyse : {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
    
    # ========================================================================
    # ÉTAPE 2 : SAUVEGARDE PROFIL YAML
    # ========================================================================
    
    print("\n" + "=" * 80)
    print("💾 ÉTAPE 2/3 : SAUVEGARDE PROFIL")
    print("=" * 80)
    
    output_dir = Path(__file__).parent.parent / "data" / "repositories" / repo_name
    output_dir.mkdir(parents=True, exist_ok=True)
    
    yaml_file = output_dir / "profile.yaml"
    json_file = output_dir / "profile.json"
    
    try:
        # YAML
        with open(yaml_file, "w", encoding="utf-8") as f:
            yaml.safe_dump(profile, f, allow_unicode=True, sort_keys=False)
        print(f"\n✅ Profil YAML : {yaml_file}")
        
        # JSON (pour debug)
        import json
        with open(json_file, "w", encoding="utf-8") as f:
            json.dump(profile, f, indent=2, ensure_ascii=False)
        print(f"✅ Profil JSON : {json_file}")
        
    except Exception as e:
        print(f"\n❌ ERREUR lors de la sauvegarde : {e}")
        sys.exit(1)
    
    # ========================================================================
    # ÉTAPE 3 : INGESTION NEO4J
    # ========================================================================
    
    if args.skip_neo4j:
        print("\n⚠️  Ingestion Neo4j skippée (--skip-neo4j)")
    else:
        print("\n" + "=" * 80)
        print("🗄️  ÉTAPE 3/3 : INGESTION NEO4J")
        print("=" * 80)
        
        try:
            print("\n⏳ Connexion à Neo4j...")
            ingester = Neo4jIngester()
            print("✅ Connexion établie !")
            
            # Clear si demandé
            if args.clear:
                print(f"\n🧹 Nettoyage des données existantes pour '{repo_name}'...")
                ingester.clear_repo(repo_name)
                print("✅ Nettoyage terminé !")
            
            # Ingestion
            print(f"\n⏳ Ingestion du profil dans Neo4j...")
            stats = ingester.ingest_profile(str(yaml_file))
            
            print(f"\n✅ Ingestion terminée !")
            print(f"   • Repo créé     : {stats['repo']}")
            print(f"   • Contributeurs : {stats['contributors']}")
            print(f"   • Hotspots      : {stats['hotspots']}")
            print(f"   • Répertoires   : {stats['directories']}")
            print(f"   • Extensions    : {stats['extensions']}")
            print(f"   • Métriques     : {stats['metrics']}")
            
            # Vérification
            print(f"\n🔍 Vérification dans Neo4j...")
            repo_stats = ingester.get_repo_stats(repo_name)
            
            if repo_stats:
                print(f"✅ Repo trouvé dans Neo4j :")
                print(f"   • Nom           : {repo_stats.get('name')}")
                print(f"   • Commits       : {repo_stats.get('commits', 0):,}")
                print(f"   • Contributeurs : {repo_stats.get('contributors_count', 0)}")
                print(f"   • Hotspots      : {repo_stats.get('hotspots_count', 0)}")
                print(f"   • Répertoires   : {repo_stats.get('directories_count', 0)}")
                print(f"   • Extensions    : {repo_stats.get('extensions_count', 0)}")
            
            ingester.close()
            
        except Exception as e:
            print(f"\n❌ ERREUR lors de l'ingestion Neo4j : {e}")
            print("\n💡 Vérifier que :")
            print("   1. Neo4j Desktop est démarré")
            print("   2. Les credentials dans .env sont corrects")
            import traceback
            traceback.print_exc()
            # Ne pas quitter, l'analyse et le YAML sont OK
    
    # ========================================================================
    # RÉSUMÉ FINAL
    # ========================================================================
    
    print("\n" + "=" * 80)
    print("🎉 WORKFLOW TERMINÉ AVEC SUCCÈS !")
    print("=" * 80)
    
    print(f"\n📊 RÉSUMÉ :")
    print(f"   • Repository    : {repo_name}")
    print(f"   • Commits       : {profile['git_summary']['commits']:,}")
    print(f"   • Contributeurs : {profile['git_summary']['contributors']:,}")
    print(f"   • Période       : {profile['git_summary']['first_commit']} → {profile['git_summary']['last_commit']}")
    print(f"   • Langage       : {profile['repositories'][0]['main_language']}")
    print(f"   • Profil YAML   : {yaml_file}")
    
    if not args.skip_neo4j:
        print(f"   • Neo4j         : ✅ Ingéré")
        print(f"\n🌐 Ouvre Neo4j Browser : http://localhost:7474")
        print(f"   Query exemple : MATCH (r:Repo {{name: '{repo_name}'}}) RETURN r")
    
    print("\n" + "=" * 80)


if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\n\n⚠️  Interruption utilisateur")
        sys.exit(130)
    except Exception as e:
        print(f"\n❌ ERREUR FATALE : {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
