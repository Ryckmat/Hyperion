#!/usr/bin/env python3
"""Test du GitAnalyzer sur le repo requests."""

import json
import sys
from pathlib import Path

import yaml

# Ajouter Hyperion au PYTHONPATH
sys.path.insert(0, str(Path(__file__).parent.parent))

from hyperion.core.git_analyzer import GitAnalyzer


def main():
    """Analyse complète du repo requests."""

    requests_path = "/home/kortazo/Documents/requests"

    print("=" * 70)
    print("🔍 ANALYSE DU REPO REQUESTS")
    print("=" * 70)
    print(f"\n📁 Chemin : {requests_path}\n")

    # Créer l'analyseur
    analyzer = GitAnalyzer(requests_path)

    print("⏳ Analyse en cours (peut prendre 30-60 secondes)...\n")

    # Analyser
    profile = analyzer.analyze()

    # Afficher les résultats
    print("=" * 70)
    print("✅ RÉSULTATS")
    print("=" * 70)

    print(f"\n🏷️  SERVICE: {profile['service']}")
    print(f"🌐 URL: {profile['repositories'][0]['url']}")
    print(f"🔧 Langage: {profile['repositories'][0]['main_language']}")
    print(f"📜 Licence: {profile['repositories'][0]['license']}")
    print(f"🚀 CI: {profile['tech']['ci']}")

    print("\n📊 STATISTIQUES:")
    print(f"   • Commits totaux     : {profile['git_summary']['commits']}")
    print(f"   • Contributeurs      : {profile['git_summary']['contributors']}")
    print(f"   • Première date      : {profile['git_summary']['first_commit']}")
    print(f"   • Dernière date      : {profile['git_summary']['last_commit']}")
    print(f"   • Activité récente   : {profile['git_summary']['recent_commits_90d']} commits (90j)")

    print("\n📈 MÉTRIQUES:")
    print(f"   • Années évolution            : {profile['metrics']['evolution_years']}")
    print(f"   • Commits/an (moyenne)        : {profile['metrics']['avg_commits_per_year']}")
    print(f"   • Changements/hotspot (moy)   : {profile['metrics']['avg_changes_per_hotspot']}")
    print(f"   • Ratio code Python           : {profile['metrics']['changes_ratio']['code_py']}%")
    print(f"   • Ratio tests                 : {profile['metrics']['changes_ratio']['tests']}%")
    print(f"   • Ratio docs                  : {profile['metrics']['changes_ratio']['docs']}%")
    print(
        f"   • Densité fichiers .py (moy)  : {profile['metrics']['py_changes_per_file_avg']} changements/fichier"
    )

    print("\n🔥 TOP 5 HOTSPOTS:")
    for i, hotspot in enumerate(profile["git_summary"]["hotspots_top10"][:5], 1):
        print(f"   {i}. {hotspot['path']}: {hotspot['changes']:,} changements")

    print("\n👥 TOP 5 CONTRIBUTEURS:")
    for i, contrib in enumerate(profile["git_summary"]["contributors_top10"][:5], 1):
        print(f"   {i}. {contrib['name']}: {contrib['commits']} commits")

    print("\n📦 TOP 5 EXTENSIONS:")
    for i, ext in enumerate(profile["git_summary"]["by_extension"][:5], 1):
        print(f"   {i}. {ext['ext']}: {ext['files']} fichiers, {ext['changes']:,} changements")

    print("\n📂 TOP 5 RÉPERTOIRES:")
    for i, dir_info in enumerate(profile["git_summary"]["directories_top"][:5], 1):
        print(f"   {i}. {dir_info['dir']}: {dir_info['changes']:,} changements")

    # Sauvegarder le profil
    output_dir = Path(__file__).parent.parent / "data" / "repositories" / "requests"
    output_dir.mkdir(parents=True, exist_ok=True)

    output_file = output_dir / "profile.yaml"

    with open(output_file, "w", encoding="utf-8") as f:
        yaml.safe_dump(profile, f, allow_unicode=True, sort_keys=False)

    print(f"\n💾 Profil sauvegardé : {output_file}")

    # Aussi en JSON pour debug
    json_file = output_dir / "profile.json"
    with open(json_file, "w", encoding="utf-8") as f:
        json.dump(profile, f, indent=2, ensure_ascii=False)

    print(f"💾 Version JSON      : {json_file}")

    print("\n" + "=" * 70)
    print("🎉 ANALYSE TERMINÉE AVEC SUCCÈS !")
    print("=" * 70)


if __name__ == "__main__":
    try:
        main()
    except Exception as e:
        print(f"\n❌ ERREUR: {e}")
        import traceback

        traceback.print_exc()
        sys.exit(1)
