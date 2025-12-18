#!/usr/bin/env python3
"""
Script de migration des anciennes données Hyperion vers la nouvelle structure.

Usage:
    python scripts/migrate_old_data.py
"""
from pathlib import Path
import shutil
import yaml

def migrate():
    """Migre les anciennes données vers data/repositories/."""
    
    print("🔄 Migration des données Hyperion...")
    
    # Chemins
    project_root = Path(__file__).parent.parent
    old_data = project_root / "data"
    new_base = project_root / "data" / "repositories"
    
    new_base.mkdir(parents=True, exist_ok=True)
    
    # Migration fichiers YAML versionnés (requests_V1.yaml, etc.)
    migrated = []
    for yaml_file in old_data.glob("*.yaml"):
        if yaml_file.name.startswith("requests"):
            # Extraire version si présente
            if "_V" in yaml_file.name:
                version = yaml_file.name.replace("requests_", "").replace(".yaml", "")
                print(f"   📄 Trouvé : {yaml_file.name} ({version})")
            else:
                version = "base"
                print(f"   📄 Trouvé : {yaml_file.name}")
            
            # Copier vers repositories/requests/
            target_dir = new_base / "requests"
            target_dir.mkdir(parents=True, exist_ok=True)
            
            # Le dernier (VX) devient profile.yaml, les autres sont archivés
            if "_V4" in yaml_file.name or "_V" not in yaml_file.name:
                target = target_dir / "profile.yaml"
                print(f"   ✅ Migration vers : {target}")
            else:
                target = target_dir / f"profile_{version}.yaml.old"
                print(f"   📦 Archivage vers : {target}")
            
            shutil.copy2(yaml_file, target)
            migrated.append(yaml_file.name)
    
    # Migration fichiers exports production (prod_*.json, prod_*.jsonl)
    for export_file in old_data.glob("prod_*"):
        if export_file.suffix in [".json", ".jsonl"]:
            print(f"   📄 Trouvé : {export_file.name}")
            target_dir = new_base / "requests"
            target_dir.mkdir(parents=True, exist_ok=True)
            target = target_dir / export_file.name
            shutil.copy2(export_file, target)
            print(f"   ✅ Migration vers : {target}")
            migrated.append(export_file.name)
    
    # Migration autres fichiers TSV/TXT
    for data_file in old_data.glob("*"):
        if data_file.suffix in [".tsv", ".txt", ".json"] and data_file.name not in migrated:
            print(f"   📄 Trouvé : {data_file.name}")
            target_dir = new_base / "requests"
            target_dir.mkdir(parents=True, exist_ok=True)
            target = target_dir / data_file.name
            shutil.copy2(data_file, target)
            print(f"   ✅ Migration vers : {target}")
            migrated.append(data_file.name)
    
    print(f"\n✅ Migration terminée : {len(migrated)} fichiers migrés")
    print(f"📁 Nouvelle structure : {new_base / 'requests'}")
    
    # Afficher contenu final
    print("\n📂 Contenu data/repositories/requests/ :")
    for f in sorted((new_base / "requests").glob("*")):
        size = f.stat().st_size / 1024  # KB
        print(f"   - {f.name} ({size:.1f} KB)")

if __name__ == "__main__":
    migrate()
