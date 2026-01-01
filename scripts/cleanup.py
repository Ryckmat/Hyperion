#!/usr/bin/env python3
"""
🧹 Hyperion Cleanup Script
Nettoie les fichiers temporaires et anciens scripts de déploiement
"""

import os
import shutil
from pathlib import Path

def cleanup_project():
    """Nettoie le projet"""
    project_root = Path(__file__).parent

    print("🧹 Nettoyage du projet Hyperion...")

    # Fichiers et dossiers à supprimer
    to_remove = [
        "test_*.py",  # Anciens tests à la racine (déjà déplacés)
        "deploy_*.py",  # Anciens scripts de déploiement (déjà déplacés)
        "deployment_*.py",  # Anciens scripts (déjà déplacés)
        "hyperion_deploy.log",  # Logs anciens
        "__pycache__",
        "*.pyc",
        ".pytest_cache",
        "mlruns/*/meta.yaml.tmp*",  # Fichiers temporaires MLflow
        "src/**/__pycache__",
        "src/**/*.pyc",
        "/tmp/hyperion_*.model",  # Modèles temporaires
    ]

    # Nettoyage
    cleaned_count = 0

    for pattern in to_remove:
        for file_path in project_root.glob(pattern):
            if file_path.exists():
                try:
                    if file_path.is_dir():
                        shutil.rmtree(file_path)
                        print(f"   🗑️  Dossier supprimé: {file_path.name}")
                    else:
                        file_path.unlink()
                        print(f"   🗑️  Fichier supprimé: {file_path.name}")
                    cleaned_count += 1
                except Exception as e:
                    print(f"   ⚠️  Impossible de supprimer {file_path}: {e}")

    # Nettoyage des fichiers temporaires système
    try:
        import tempfile
        temp_dir = Path(tempfile.gettempdir())
        for temp_file in temp_dir.glob("hyperion_*"):
            if temp_file.is_file():
                temp_file.unlink()
                print(f"   🗑️  Temp supprimé: {temp_file.name}")
                cleaned_count += 1
    except Exception:
        pass

    print(f"\n✅ Nettoyage terminé: {cleaned_count} éléments supprimés")
    print("\n📁 Structure organisée:")
    print("   ✅ deploy.py - Script unifié principal")
    print("   ✅ tests/ - Tests organisés par catégorie")
    print("   ✅ deployment/ - Scripts archivés")
    print("   ✅ DEPLOYMENT.md - Guide d'utilisation")

if __name__ == "__main__":
    cleanup_project()