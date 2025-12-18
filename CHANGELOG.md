# Changelog

Tous les changements notables du projet Hyperion seront documentés ici.

Le format est basé sur [Keep a Changelog](https://keepachangelog.com/fr/1.0.0/),
et ce projet adhère au [Semantic Versioning](https://semver.org/lang/fr/).

## [1.0.0] - 2024-12-18

### 🎉 Refactoring majeur - Architecture professionnelle

#### Ajouté
- ✅ **Package Python structuré** (`hyperion/`)
  - `cli/` : Interface ligne de commande avec Click
  - `core/` : Logique métier (analyseurs, calculateurs)
  - `generators/` : Générateurs de documentation
  - `integrations/` : Neo4j, GitLab, GitHub (futurs)
  - `models/` : Modèles de données
  - `utils/` : Utilitaires
- ✅ **CLI unifié** : `hyperion profile|generate|export|ingest|info`
- ✅ **Configuration externalisée** : `config/filters.yaml`
- ✅ **Documentation complète** :
  - README.md avec exemples
  - CHANGELOG.md
  - CONTRIBUTING.md
  - LICENSE Apache-2.0
  - docs/getting_started.md
  - docs/architecture.md
- ✅ **Tests unitaires** : structure pytest + conftest
- ✅ **Setup.py** : Installation package (`pip install -e .`)
- ✅ **Templates Jinja2** : Extension `.j2` (templates/markdown/)
- ✅ **Organisation data** : `data/repositories/{repo}/profile.yaml`

#### Modifié
- 🔄 **Restructuration complète** du projet
- 🔄 **Nomenclature cohérente** : PascalCase classes, snake_case modules
- 🔄 **Séparation legacy** : Scripts originaux supprimés après refactoring

#### Supprimé
- ❌ `code/` : Scripts standalone (refactorés en package)
- ❌ `scripts/legacy/` : Code original (migré vers `hyperion/`)

#### Architecture

```
Hyperion/
├── hyperion/              # 📦 Package Python principal
│   ├── __init__.py
│   ├── __version__.py
│   ├── config.py          # Configuration centralisée
│   ├── cli/               # Interface CLI
│   ├── core/              # Analyseurs Git
│   ├── generators/        # Générateurs documentation
│   ├── integrations/      # Neo4j, APIs
│   ├── models/            # Modèles de données
│   └── utils/             # Utilitaires
├── config/                # ⚙️ Configuration
│   └── filters.yaml       # Filtres hotspots
├── templates/             # 📄 Templates Jinja2
│   └── markdown/
│       ├── index.md.j2
│       └── registre.md.j2
├── data/                  # 📁 Données générées
│   └── repositories/
├── output/                # 📤 Documentation générée
├── tests/                 # 🧪 Tests unitaires
├── docs/                  # 📚 Documentation
├── scripts/               # 🔧 Scripts utilitaires
│   └── migrate_old_data.py
├── README.md
├── CHANGELOG.md
├── CONTRIBUTING.md
├── LICENSE
├── setup.py
└── requirements.txt
```

---

## [0.x.x] - Pré-refactoring (historique)

### Fonctionnalités originales

Scripts Python standalone :
- `hyperion_git_profil.py` : Profiling Git complet avec déduplication contributeurs
- `generate_markdown_from_yaml.py` : Génération documentation Markdown
- `export_prod_history.py` : Export historique releases production
- `ingest_prod_history_to_neo4j.py` : Ingestion Neo4j
- `mini_git_summary.py` : Résumé Git rapide
- `json_to_hyperion_yaml.py` : Migration JSON → YAML

### Données
- Analyse complète du projet `requests` (Python)
- Templates Markdown simples
- Exports TSV/JSON/JSONL

---

## À venir

### [1.1.0] - Implémentation modules core
- [ ] `hyperion.core.git_analyzer` : Analyseur Git refactoré
- [ ] `hyperion.core.prod_exporter` : Export releases
- [ ] `hyperion.generators.markdown_generator` : Génération docs
- [ ] `hyperion.integrations.neo4j_ingester` : Ingestion Neo4j
- [ ] `hyperion.utils.git_utils` : Wrappers Git
- [ ] Tests end-to-end

### [1.2.0] - CLI fonctionnel
- [ ] Commandes `profile`, `generate`, `export`, `ingest` opérationnelles
- [ ] Mode interactif
- [ ] Gestion erreurs avancée
- [ ] Progress bars

### [1.3.0] - Fonctionnalités avancées
- [ ] Support multi-repos (batch)
- [ ] Export HTML
- [ ] Dashboard Streamlit
- [ ] Webhooks

### [2.0.0] - Hyperion Platform
- [ ] API REST FastAPI
- [ ] Client GitLab/GitHub APIs
- [ ] RAG sur documentation
- [ ] Graphe de dépendances inter-repos
- [ ] ML : prédiction risques

---

## Notes de migration

### Migration depuis 0.x.x

Les scripts originaux ont été **supprimés** après refactoring complet en package Python.

**Structure avant (0.x.x)** :
```
code/
├── hyperion_git_profil.py
├── generate_markdown_from_yaml.py
├── export_prod_history.py
└── ...
```

**Structure après (1.0.0)** :
```
hyperion/
├── core/
├── generators/
└── integrations/
```

**Installation** :
```bash
pip install -e .
hyperion --help
```

---

## Contributeurs

- **Matthieu Ryckembusch** (@Ryckmat) - Créateur & Lead Developer
