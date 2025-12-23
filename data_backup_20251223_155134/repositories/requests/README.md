# Anciennes versions YAML (archive)

Ce dossier contient les anciennes versions du fichier `requests.yaml` à des fins d'historique.

## Versions

| Fichier | Description | Date | Notes |
|---------|-------------|------|-------|
| `profile.yaml` | **Version actuelle (V4)** | 2024-12 | Format final avec tous les KPIs |
| `profile_V3.yaml.old` | Version 3 | 2024-11 | Ajout métriques avancées |
| `profile_V2.yaml.old` | Version 2 | 2024-10 | Amélioration hotspots |
| `profile_V1.yaml.old` | Version 1 | 2024-09 | Format initial basique |

## Utilisation

**Utilisez toujours `profile.yaml` (version actuelle).**

Les anciennes versions sont conservées pour :
- Comparaison évolution format
- Debug migrations
- Historique décisions architecture

## Migration

Pour migrer d'anciennes données, utiliser :
```bash
python scripts/migrate_old_data.py
```
