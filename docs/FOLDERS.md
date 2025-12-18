# 📁 Organisation des dossiers Hyperion

## Structure

```
Hyperion/
├── data/                      # Données d'analyse
│   └── repositories/          # Profils par repo (gitignore *)
│       └── {repo}/
│           ├── profile.yaml   # Profil Hyperion
│           └── profile.json   # Debug
│
├── docs/                      # Documentation
│   ├── generated/             # Docs générées AUTO (gitignore)
│   │   └── {repo}/
│   │       ├── index.md
│   │       └── registre.md
│   ├── getting_started.md
│   └── architecture.md
│
├── output/                    # Legacy (gitignore, à supprimer)
│
└── scripts/                   # Scripts utilitaires
```

## 📝 Règles

### ✅ Committer (versionné)
- `data/requests.yaml` : Exemples
- `docs/*.md` : Documentation manuelle
- Templates, code source, config

### ❌ Ne PAS committer (gitignore)
- `data/repositories/*/` : Profils générés (volumineux)
- `docs/generated/` : Docs auto-générées (regénérables)
- `output/` : Legacy

## 🎯 Pourquoi cette organisation ?

### data/repositories/
Profils YAML générés par l'analyse Git.  
**Ignoré** car :
- Volumineux (6K+ commits = gros YAML)
- Regénérable avec `hyperion profile`
- Spécifique à chaque environnement

### docs/generated/
Documentation Markdown générée depuis les profils.  
**Ignoré** car :
- Regénérable avec `hyperion generate`
- Évite pollution du dépôt
- Toujours à jour si regénéré

## 📦 Workflow

```bash
# 1. Analyser (génère data/repositories/requests/profile.yaml)
hyperion profile /path/to/requests

# 2. Générer docs (génère docs/generated/requests/*.md)
hyperion generate data/repositories/requests/profile.yaml

# 3. Consulter
cat docs/generated/requests/index.md
```

## 💡 Note

Les docs générées sont dans `docs/generated/` par défaut (CONFIG.OUTPUT_DIR).  
Le dossier `output/` est legacy et sera supprimé.
