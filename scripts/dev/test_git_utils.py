#!/usr/bin/env python3
"""Test rapide du module git_utils."""

import sys
from pathlib import Path

# Ajouter le dossier parent au PYTHONPATH
sys.path.insert(0, str(Path(__file__).parent.parent))

from hyperion.utils.git_utils import GitRepo


def main():
    """Test du wrapper GitRepo sur le repo Hyperion."""

    repo_path = Path(__file__).parent.parent
    print(f"📁 Analyse du repo : {repo_path}\n")

    repo = GitRepo(str(repo_path))

    # Métadonnées
    print("=== MÉTADONNÉES ===")
    print(f"✅ Nom du repo    : {repo.get_name()}")
    print(f"✅ URL remote     : {repo.get_remote_url() or 'N/A'}")
    print(f"✅ Branche        : {repo.detect_main_branch()}")
    print(f"✅ Langage        : {repo.detect_language()}")
    print(f"✅ CI détecté     : {repo.detect_ci()}")
    print(f"✅ Licence        : {repo.detect_license() or 'N/A'}")

    # Stats
    print("\n=== STATISTIQUES ===")
    commits = repo.get_commits()
    contributors = repo.get_contributors()
    recent = repo.count_recent_commits(90)
    first, last = repo.get_date_range()

    print(f"✅ Commits totaux : {len(commits)}")
    print(f"✅ Contributeurs  : {len(contributors)}")
    print(f"✅ Commits (90j)  : {recent}")
    print(f"✅ Période        : {first[:10] if first else 'N/A'} → {last[:10] if last else 'N/A'}")

    # Top contributeurs
    if contributors:
        print("\n=== TOP 3 CONTRIBUTEURS ===")
        top_3 = sorted(contributors, key=lambda x: x["commits"], reverse=True)[:3]
        for i, c in enumerate(top_3, 1):
            print(f"{i}. {c['name']}: {c['commits']} commits")

    # Numstat sample
    print("\n=== NUMSTAT (sample) ===")
    numstat = repo.get_numstat()
    print(f"✅ Total entrées numstat: {len(numstat)}")
    if numstat:
        print("Sample (5 premiers):")
        for add, delete, path in numstat[:5]:
            print(f"  +{add}/-{delete}\t{path}")

    print("\n🎉 Test réussi !")


if __name__ == "__main__":
    main()
