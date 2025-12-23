# Changelog

Tous les changements notables du projet Hyperion seront documentés ici.

Le format est basé sur [Keep a Changelog](https://keepachangelog.com/fr/1.0.0/),
et ce projet adhère au [Semantic Versioning](https://semver.org/lang/fr/).

## [2.0.0] - 2024-12-23

### 🚀 Hyperion v2.0 - Intelligence Artificielle pour l'Analyse de Code

#### Nouvelles Capacités Majeures
- ✅ **8 Moteurs d'Intelligence** pour l'analyse de code
  - Impact Analysis Engine : Détection précise des impacts de modification
  - Anomaly Detection : Identification automatique des code smells
  - Code Understanding : Recherche sémantique dans le code source
  - Code Exploration : Navigation intelligente des codebases
  - RAG Enhanced : Réponses contextuelles avec sources précises
  - Neo4j v2 : Graphe de code complet (fonctions, classes, relations)
  - Performance Optimisée : <10s queries, multi-moteurs
  - Integration Workflow : RAG → Neo4j → Impact Analysis

#### Ajouté
- ✅ **RAG Enhanced** (13 → 121 points indexés)
  - Extraction code source via AST (240 fonctions, 45 classes)
  - Chunks sémantiques enrichis (Git + Code)
  - Sources précises avec fichier:ligne
- ✅ **Neo4j v2 Code Engine** (0 → 240 functions)
  - Graphe code complet (Functions, Classes, Files, Imports)
  - Relations File→Function, Class→Method
  - 6 nouveaux endpoints API v2
- ✅ **API v2 Endpoints**
  - `/api/v2/repos/{repo}/functions` - Liste fonctions
  - `/api/v2/repos/{repo}/classes` - Liste classes
  - `/api/v2/impact/analyze` - Analyse impact
  - `/api/v2/anomaly/scan` - Détection anomalies
  - `/api/v2/understanding/search` - Recherche sémantique
  - `/api/v2/health` - Health check v2
- ✅ **Modules Core v2**
  - `neo4j_code_ingester.py` - Ingestion code source
  - `code_extractor.py` - AST parsing Python
  - `v2_endpoints.py` - 6 endpoints moteurs v2
- ✅ **Deploy Script Master Unifié**
  - Modules sélectifs (v1, v2, rag, all)
  - Validation automatique 8 moteurs
  - Stats temps réel Neo4j v2 + RAG
  - Mode auto + interactif

#### Validation Réussie
- 🎯 **Score Final : 8.0/10** sur repository requests (52k stars)
- ✅ Neo4j v2: 5.0/5.0 (240 fonctions indexées)
- ✅ Impact Analysis: 5.0/5.0 (détection précise)
- ✅ Anomaly Detection: 5.0/5.0 (12 anomalies + suggestions)
- ✅ Code Search: 5.0/5.0 (recherche sémantique)
- ✅ Code Exploration: 5.0/5.0 (navigation intelligente)
- ✅ Performance: 4.0/5.0 (RAG <10s, Neo4j <1s)

#### Architecture Finale
```
Hyperion v2 Stack:
├── 📊 RAG (Qdrant + BGE-large): 121 chunks sémantiques
├── 🔍 Neo4j v2: 240 functions + 45 classes + relations
├── ⚡ Impact Analysis: Neo4j queries + risk scoring
├── 🔬 Anomaly Detection: Complexity + Size + Documentation
├── 🧭 Code Understanding: Semantic search + exploration
├── 🚀 API v2: 6 nouveaux endpoints opérationnels
├── ⚙️ Code Extraction: AST parsing Python complet
└── 🎯 Performance: <10s queries, multi-moteurs
```

## [1.5.0] - 2024-12-22

### 🎯 Préparation Hyperion v2 - Infrastructure RAG + Neo4j

#### Ajouté
- ✅ **Infrastructure v2 complète** pour 8 moteurs
- ✅ **RAG Pipeline** : Qdrant + BGE embeddings + Ollama LLM
- ✅ **Neo4j v2 preparation** : Structures pour code analysis
- ✅ **API endpoints foundation** pour moteurs intelligents

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

- **Matthieu Ryckman** (@Ryckmat) - Créateur & Lead Developer
