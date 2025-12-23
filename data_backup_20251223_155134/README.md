# Data Directory

Ce dossier contient les données générées par Hyperion.

## Structure

```
data/
├── repositories/          # Profils par repository (gitignore)
│   └── {repo_name}/
│       ├── profile.yaml   # Profil Hyperion complet
│       ├── prod_deploys.json
│       ├── prod_commits.jsonl
│       └── prod_files.jsonl
├── cache/                 # Cache analyses (gitignore)
└── requests.yaml          # Exemple (projet requests)
```

## Fichiers racine (legacy)

Les fichiers à la racine de `data/` sont conservés pour référence historique :
- `requests.yaml` : Profil du projet Python `requests` (exemple complet)
- `*.tsv`, `*.json`, `*.jsonl` : Exports bruts historiques

## Nouveaux projets

Pour de nouveaux projets analysés, les données sont organisées dans `data/repositories/{repo_name}/`.

Exemple :
```bash
hyperion profile /path/to/mon-repo --output data/repositories/
# → Génère data/repositories/mon-repo/profile.yaml
```

## Gitignore

Les sous-dossiers `data/repositories/*/` et `data/cache/` sont ignorés par Git car ils peuvent être volumineux et sont regénérables.

Seuls les exemples à la racine (`requests.yaml`) sont versionnés.
