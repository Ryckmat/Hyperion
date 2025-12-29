# Analyse Complète de la Structure Hyperion v2.5.0

## 1. Organisation actuelle des dossiers et fichiers

### Hiérarchie générale
```
Hyperion/
├── src/hyperion/                    # Code source principal (structure moderne)
│   ├── __init__.py
│   ├── __version__.py               # Versioning
│   ├── config.py                    # Configuration centralisée
│   ├── api/                         # FastAPI + OpenAI-compatible
│   │   ├── main.py
│   │   ├── openai_compat.py
│   │   ├── v2_endpoints.py
│   │   └── __init__.py
│   ├── cli/                         # Interface CLI (Click)
│   │   ├── main.py
│   │   └── __init__.py
│   ├── core/                        # Analyseur Git
│   │   ├── git_analyzer.py
│   │   └── __init__.py
│   ├── modules/                     # Modules métier (bien structurés)
│   │   ├── anomaly/                 # Détection d'anomalies
│   │   ├── capacity/                # Estimation capacité
│   │   ├── documentation/           # Génération docs
│   │   ├── generators/              # Générateurs (Markdown)
│   │   ├── impact/                  # Analyse d'impact (6 fichiers)
│   │   ├── integrations/            # Neo4j, Git, sources externes
│   │   ├── ml/                      # Infrastructure ML complète
│   │   │   ├── infrastructure/      # MLflow, Feature Store, Model Registry
│   │   │   ├── training/            # Training Pipeline
│   │   │   └── tests/               # Tests ML (6 fichiers)
│   │   ├── onboarding/              # Recommandations parcours
│   │   ├── rag/                     # Qdrant + Retrieval
│   │   ├── refactoring/             # Suggestions refactoring
│   │   ├── security/                # Scanning sécurité
│   │   └── understanding/           # Code understanding (indexing, mapping)
│   ├── utils/                       # Utilitaires (git_utils.py)
│   └── modules/models/              # Modèles de données
│
├── scripts/                         # Scripts d'orchestration
│   ├── deploy/                      # Déploiement (master scripts)
│   │   ├── hyperion_master_final.sh
│   │   ├── hyperion_master.sh
│   │   ├── hyperion_full_workflow.py
│   │   └── output/                  # Artefacts (dashboard.log)
│   ├── dev/                         # Développement
│   │   ├── run_api.py
│   │   ├── run_dashboard.py
│   │   ├── test_*.py                # 6 scripts de test
│   ├── maintenance/                 # Maintenance
│   │   ├── check_specs.py
│   │   ├── ingest_*.py              # Ingestion scripts
│   │   ├── migrate_old_data.py
│   │   └── __pycache__/             # Bytecode (à ignorer)
│   ├── setup/                       # Installation système
│   │   ├── setup_hyperion.sh
│   │   └── setup_rag.sh
│   ├── .gitignore                   # Scripts gitignore
│   ├── MASTER_SCRIPT.md
│   └── SETUP_ULTIMATE.md
│
├── tests/                           # Tests (21 fichiers .py)
│   ├── __init__.py
│   ├── conftest.py                  # Configuration pytest
│   ├── api/                         # Tests API (3 fichiers)
│   ├── benchmarks/                  # Benchmarks
│   │   ├── __init__.py
│   │   └── test_bench_impact.py
│   ├── integration/                 # Tests intégration (2 fichiers)
│   ├── unit/                        # Tests unitaires (9 fichiers)
│   ├── e2e/                         # Tests E2E (vide pour l'instant)
│   ├── test_cli.py
│   ├── test_git_analyzer.py
│   ├── test_git_utils.py
│   ├── test_structure.py
│   └── __pycache__/                 # Bytecode (à ignorer)
│
├── frontend/                        # Dashboard React (standalone)
│   ├── README.md
│   └── index.html                   # Single-file app (React + Tailwind)
│
├── data/                            # Données générées
│   ├── README.md                    # Documentation data/
│   ├── ml/                          # ML data
│   │   └── feature_store/           # Cache features + metadata
│   │       ├── cache/               # Fichiers .pkl (cached)
│   │       └── metadata/            # Metadata JSON
│   ├── repositories/                # Profils générés par repo (GITIGNORE)
│   │   ├── Hyperion/
│   │   └── requests/
│   └── (legacy files: requests.yaml, etc.)
│
├── docs/                            # Documentation
│   ├── README.md
│   ├── ARCHITECTURE.md              # Design document
│   ├── CHANGELOG.md
│   ├── CONTRIBUTING.md
│   ├── GUIDE_UTILISATION_COMPLETE.md
│   ├── v3.0-enterprise-plan.md
│   ├── architecture/
│   │   └── architecture.md
│   ├── guides/
│   │   ├── FOLDERS.md               # Guide des dossiers
│   │   ├── getting_started.md
│   │   ├── ingestion_generalized.md
│   │   └── RAG_SETUP.md
│   ├── v2/
│   │   ├── code_understanding.md
│   │   └── impact_analysis.md
│   ├── api/                         # (vide pour l'instant)
│   ├── generated/                   # Docs auto-générées (GITIGNORE)
│   └── analysis/                    # (vide pour l'instant)
│
├── logs/                            # Fichiers logs
│   ├── api.log
│   ├── dashboard.log
│   ├── api_test.log
│   └── ml/                          # ML logs (empty)
│
├── templates/                       # Templates pour exports
│   └── markdown/                    # Templates Markdown (vide)
│
├── config/                          # Configuration applicative
│   ├── filters.yaml                 # Filtres pour ingestion
│   ├── openwebui_hyperion_function.py
│   ├── dev/                         # Dev config (vide)
│   └── prod/                        # Prod config (vide)
│
├── modeles/                         # Modèles ML sauvegardés
│   ├── *.pkl                        # Modèles sérialisés (8 fichiers)
│   └── metadata/                    # Métadonnées modèles (8 fichiers JSON)
│
├── mlruns/                          # Tracking MLflow
│   ├── 0/                           # Experiment 0 (Default)
│   │   ├── meta.yaml
│   │   ├── {run_id}/
│   │   │   ├── metrics/             # Accuracy, precision, recall, f1
│   │   │   ├── params/              # Hyperparamètres
│   │   │   ├── tags/                # Métadonnées
│   │   │   ├── artifacts/           # Modèles sauvegardés
│   │   │   └── outputs/             # Sorties
│   │   ├── models/                  # Modèles MLflow
│   │   └── outputs/
│   ├── 560553070072455507/          # Autre experiment
│   ├── .trash/
│   └── (artefacts MLflow ~6.8MB)
│
├── output/                          # Docs générées (LEGACY, à supprimer)
│   └── Hyperion/
│
├── htmlcov/                         # Coverage reports (HTML)
│   ├── index.html
│   ├── status.json
│   └── ~764KB d'assets
│
├── venv/                            # Virtual env (à ignorer)
│   └── (92 MB, ne pas committer)
│
├── .ruff_cache/                     # Cache Ruff (160 KB)
├── .pytest_cache/                   # Cache pytest (40 KB)
├── .benchmarks/                     # Benchmarks (vide)
├── .claude/                         # Claude Code settings
│   └── settings.local.json
├── .github/                         # CI/CD GitHub Actions
│   └── workflows/
│
├── Configuration & root files
├── .env                             # Variables d'environnement
├── .env.example                     # Template .env
├── .gitignore                       # Git ignore rules (bien configuré)
├── .gitattributes
├── .pre-commit-config.yaml          # Pre-commit hooks
├── .commit-message.txt              # Message commit type
├── pyproject.toml                   # Configuration projet (moderne)
├── setup.py                         # Fallback setup
├── pytest.ini                       # Configuration pytest
├── requirements.txt                 # Dépendances prod
├── requirements-dev.txt             # Dépendances dev
├── LICENSE                          # Apache 2.0
├── README.md                        # Documentation principale
├── CHANGELOG.md                     # Historique versions
├── install.log                      # Log installation
├── api.log                          # Log API
├── .coverage                        # Données coverage
└── coverage.xml                     # Rapport coverage XML
```

---

## 2. Fichiers temporaires, logs et artefacts à nettoyer

### Artefacts de cache et build
| Dossier | Taille | Type | Action |
|---------|--------|------|--------|
| `.ruff_cache/` | 160 KB | Cache linter | ✅ Peut être supprimé (regénéré auto) |
| `.pytest_cache/` | 40 KB | Cache tests | ✅ Peut être supprimé (regénéré auto) |
| `.benchmarks/` | 0 B | Benchmarks | ✅ Peut être supprimé (vide) |
| `htmlcov/` | 764 KB | Rapports coverage | ⚠️ À nettoyer (généré par pytest) |
| `venv/` | 92 MB | Virtual env | ⚠️ Ne pas committer (en .gitignore) |

### Logs non structurés
| Fichier | Emplacement | Action |
|---------|------------|--------|
| `api.log` | `/home/kortazo/Documents/Hyperion/` | À déplacer dans `logs/` |
| `install.log` | `/home/kortazo/Documents/Hyperion/` | À supprimer (obsolète) |
| `dashboard.log` | `scripts/deploy/output/` | À déplacer dans `logs/` |

### Fichiers d'ingestion ML (cache)
| Dossier | Taille | Contenu |
|---------|--------|---------|
| `data/ml/feature_store/cache/` | - | Fichiers `.pkl` (cache) |
| `data/ml/feature_store/metadata/` | - | Metadata JSON |

Ces fichiers sont regénérables et devraient être dans `.gitignore` si non déjà fait.

### Artefacts MLflow
| Dossier | Taille | Contenu |
|---------|--------|---------|
| `mlruns/` | 6.8 MB | Tracking experiments ML |
| `mlruns/0/` | - | Experiment 0 (Default) |
| `mlruns/560553070072455507/` | - | Autres experiments |

**Action** : Ces fichiers sont importants pour MLflow tracking. À conserver mais considérer un cleanup des anciennes runs.

### Modèles sérialisés
| Dossier | Taille | Contenu |
|---------|--------|---------|
| `modeles/` | 1.9 MB | 8 modèles `.pkl` + metadata |
| `modeles/metadata/` | - | 8 fichiers JSON metadata |

**Action** : À conserver (importants pour inference). Considérer une arborescence `modeles/v1/`, `modeles/v2/` pour versioning.

### Output legacy
| Dossier | Action |
|---------|--------|
| `output/` | **À SUPPRIMER** (legacy, docs générées) |

---

## 3. Incohérences dans la structure

### ✅ Points positifs
1. **Structure `src/hyperion/` moderne** - Suit best practices Python
2. **Séparation claire** entre code, tests, scripts, docs
3. **Modules bien organisés** par domaine (ml, rag, impact, etc.)
4. **Configuration centralisée** (`pyproject.toml`, `.env`)
5. **Documentation documentée** (README pour data/, frontend/, docs/)
6. **Tests structurés** (unit, integration, benchmarks)

### ⚠️ Incohérences détectées

#### 3.1 Localisation des logs
**Problème** : Logs dispersés à plusieurs endroits
```
✗ /home/kortazo/Documents/Hyperion/api.log          (racine)
✗ /home/kortazo/Documents/Hyperion/install.log      (racine)
✓ /home/kortazo/Documents/Hyperion/logs/api.log     (correct)
✓ /home/kortazo/Documents/Hyperion/logs/dashboard.log (correct)
✗ scripts/deploy/output/dashboard.log               (scripts subdirectory)
```
**Impact** : Difficulté à localiser et nettoyer les logs  
**Suggestion** : Centraliser tous les logs dans `logs/` avec une convention de nommage

#### 3.2 Dossier output/ legacy
**Problème** : `output/` existe mais est ignoré par gitignore  
**Contenu** : `output/Hyperion/` (docs générées historiquement)  
**Suggestion** : Supprimer ce dossier (remplacé par `docs/generated/`)

#### 3.3 src/ contient des dossiers vides
**Détail** :
```
src/config/  (vide, config réelle dans root)
src/data/    (vide, data réelle dans root)
src/docs/    (vide, docs réelle dans root)
```
**Suggestion** : Nettoyer ces dossiers vides dans `src/`

#### 3.4 config/ et config dans src/
**Problème** : Confusion entre `/config/` (racine) et `src/config/`
```
✓ /config/filters.yaml         (config applicative)
✗ /config/dev/ et /config/prod/ (vides)
✗ /src/config/                 (vide)
```
**Suggestion** : Clarifier la structure config (centraliser ou supprimer les dossiers vides)

#### 3.5 Templates/ non utilisés
**Contenu** : `templates/markdown/` (vide)  
**Suggestion** : Utiliser ou documenter, ou supprimer

#### 3.6 Dossiers vides
```
docs/api/                       (vide)
docs/analysis/                  (vide)
config/dev/ et config/prod/     (vides)
.benchmarks/                    (vide)
tests/e2e/                      (vide, à créer)
```

#### 3.7 Fichiers non-Python dans scripts/
```
scripts/.gitignore              (redondant avec root .gitignore)
scripts/MASTER_SCRIPT.md        (documentation)
scripts/SETUP_ULTIMATE.md       (documentation)
```

#### 3.8 ML tests au mauvais endroit
**Problème** : Tests ML dans `src/hyperion/modules/ml/tests/` ET dans `tests/`
```
✓ src/hyperion/modules/ml/tests/    (6 fichiers)
✓ tests/integration/test_*           (tests d'intégration)
```
**Situation** : C'est acceptable si les tests en `src/` sont des tests unitaires du module ML et les tests en `tests/` sont d'intégration. À clarifier.

### 📊 Sommaire des incohérences
| Incohérence | Sévérité | Type |
|-------------|----------|------|
| Logs dispersés | Moyen | Organisation |
| `output/` legacy | Bas | Nettoyage |
| Dossiers vides dans src/ | Bas | Nettoyage |
| Confusion config/ | Moyen | Organisation |
| Templates non utilisés | Bas | Nettoyage |
| Multiple emplacements tests ML | Moyen | Clarification |

---

## 4. Améliorations d'organisation possibles

### 4.1 Restructuration des logs
```
logs/
├── api/
│   ├── api.log
│   └── api_test.log
├── dashboard/
│   └── dashboard.log
├── ml/                      (exist already)
│   └── training.log
├── ingestion/
│   └── ingestion.log
└── .gitignore              # ignorer *.log
```

**Action** :
- Centraliser tous les logs dans `logs/`
- Utiliser des subdossiers par composant
- Mettre à jour les scripts pour utiliser les nouveaux chemins

### 4.2 Nettoyage du dossier src/
```
Supprimer:
- src/config/               (vide, config ailleurs)
- src/data/                 (vide, data ailleurs)
- src/docs/                 (vide, docs ailleurs)
```

### 4.3 Clarification config/
```
Option A - Simplifier:
config/
├── filters.yaml            # Config métier
├── openwebui_hyperion_function.py
└── .gitignore

Supprimer: config/dev/ et config/prod/ (vides)

Option B - Structurer:
config/
├── default.yaml            # Config par défaut
├── dev.yaml                # Config dev
├── prod.yaml               # Config prod
└── schema.yaml             # Validation schema
```

### 4.4 Consolidation des données ML
```
data/ml/
├── feature_store/
│   ├── cache/              # .pkl files
│   └── metadata/           # .json files
└── .gitignore             # ignore cache/

Ou mieux: .gitignore au niveau data/:
data/ml/feature_store/cache/   (déjà ignoré?)
data/ml/feature_store/metadata/ (déjà ignoré?)
```

Vérifier: Les fichiers .pkl et JSON sont-ils dans .gitignore?

### 4.5 Versioning des modèles
```
modeles/
├── v1.0.0/
│   ├── risk_predictor_*.pkl
│   ├── metadata/
│   └── README.md
├── v1.1.0/
│   ├── ...
│   └── README.md
├── latest/ → symlink vers v1.1.0
└── archived/
    └── v0.9.0/
```

**Avantages** :
- Tracking clair des versions
- Rollback facile
- Documentation par version

### 4.6 Tests : Clarifier la séparation
```
Option A - Centralisé (recommandé):
tests/
├── unit/
│   ├── test_ml_*.py        # Tests ML units
│   ├── test_impact_*.py
│   └── ...
├── integration/
│   ├── test_ml_pipeline.py # Tests pipeline ML
│   └── ...
└── conftest.py

Supprimer: src/hyperion/modules/ml/tests/

Option B - Garder ml/tests/ pour tests isolés
Garder: src/hyperion/modules/ml/tests/ (pour tests unitaires du module)
Ajouter: tests/integration/ (pour tests pipeline complets)
```

### 4.7 Documentation organisée
```
docs/
├── README.md               # Index docs
├── getting_started.md      # Quick start
├── architecture.md         # Design
├── api/
│   ├── overview.md
│   ├── endpoints.md
│   └── examples.md
├── guides/
│   ├── installation.md
│   ├── usage.md
│   ├── rag_setup.md
│   └── ml_training.md
├── modules/
│   ├── ml.md
│   ├── impact.md
│   └── rag.md
├── contributing/
│   └── CONTRIBUTING.md
├── changelog.md
├── v2/
│   └── (legacy)
└── generated/              # (GITIGNORE)
```

### 4.8 Scripts mieux organisés
```
scripts/
├── README.md               # Guide scripts
├── setup/
│   ├── setup_hyperion.sh
│   └── setup_rag.sh
├── run/                    # Scripts execution
│   ├── run_api.sh         (wrapper pour run_api.py)
│   ├── run_dashboard.sh   (wrapper pour run_dashboard.py)
│   └── run_master.sh      (master orchestration)
├── maintenance/
│   ├── cleanup.sh
│   ├── ingest_generalized.py
│   └── check_specs.py
├── dev/                    # Dev helpers
│   ├── test_*.py
│   └── debug_*.py
└── deploy/
    ├── hyperion_master.sh
    └── docker-compose.yml (future)
```

---

## 5. Fichiers manquants et à créer

### ✅ Présents (OK)
- ✅ `README.md` (complet et bien structuré)
- ✅ `requirements.txt` (production)
- ✅ `requirements-dev.txt` (développement)
- ✅ `pyproject.toml` (moderne, bien configuré)
- ✅ `LICENSE` (Apache 2.0)
- ✅ `.env.example` (template)
- ✅ `.gitignore` (complet)
- ✅ `.pre-commit-config.yaml` (hooks)
- ✅ `CHANGELOG.md` (historique)
- ✅ `pytest.ini` (config tests)
- ✅ `setup.py` (fallback)

### ⚠️ À créer ou améliorer

#### 5.1 MAINTAINERS.md
**Objectif** : Documenter qui maintient le projet  
**Contenu suggéré** :
```markdown
# Maintainers

## Roles
- **Lead**: Project Maintainer
- **ML Pipeline**: [À compléter]
- **RAG/Vector Store**: [À compléter]
- **API/Integration**: [À compléter]

## Guidelines
- Code review required for all PRs
- Minimum Python 3.10
- Black + Ruff formatting
- 80%+ test coverage
```

#### 5.2 DEVELOPMENT.md
**Objectif** : Guide pour développeurs  
**Contenu suggéré** :
```markdown
# Development Guide

## Setup
```bash
pip install -e ".[dev]"
```

## Testing
```bash
pytest tests/ -v --cov
```

## Code Quality
- Format: `black src/`
- Lint: `ruff check src/`
- Type check: `mypy src/`

## Modules

### ML Module
- Feature Store
- Training Pipeline
- Model Registry

### RAG Module
- Qdrant integration
- Embeddings
- Query engine

[...]
```

#### 5.3 ARCHITECTURE.md (compléter existant)
**Situation** : Existe mais à améliorer  
**À ajouter** :
- Diagramme architecture ASCII/Mermaid
- Flux de données
- Intégrations (Neo4j, Qdrant, Ollama)
- Decision Records (ADRs)

#### 5.4 API_REFERENCE.md
**Objectif** : Documenter l'API REST  
**Contenu** :
- Endpoints (GET, POST)
- Payloads (exemples)
- Réponses (schémas)
- Erreurs (status codes)
- Authentication (si applicable)

#### 5.5 scripts/README.md
**Objectif** : Guide des scripts  
**Contenu** :
- Quand utiliser quel script
- Prérequis pour chaque script
- Exemples d'utilisation
- Troubleshooting

#### 5.6 docs/DEPLOYMENT.md
**Objectif** : Guide déploiement en production  
**Contenu** :
- Docker setup
- Environment vars
- Service dependencies
- Monitoring
- Backup strategy

#### 5.7 docs/TROUBLESHOOTING.md
**Objectif** : Résoudre les problèmes courants  
**Contenu** :
- Neo4j connection issues
- Qdrant/vector store problems
- MLflow tracking issues
- API/Dashboard issues
- Common Python/dependency errors

#### 5.8 SECURITY.md
**Objectif** : Politiques de sécurité  
**Contenu** :
- Password/credential handling
- .env usage
- Pre-commit hooks
- Dependency scanning
- Responsible disclosure

#### 5.9 .editorconfig
**Objectif** : Standardiser configuration éditeur  
```ini
root = true

[*]
charset = utf-8
end_of_line = lf
trim_trailing_whitespace = true
insert_final_newline = true

[*.py]
indent_style = space
indent_size = 4

[*.{yaml,yml}]
indent_style = space
indent_size = 2

[*.md]
trim_trailing_whitespace = false
```

#### 5.10 .github/workflows
**Situation** : Dossier existe mais workflows à créer  
**À créer** :
- `ci.yml` (tests, linting)
- `codeql.yml` (security analysis)
- `release.yml` (versioning)

---

## 6. Analyse détaillée par répertoire clé

### 📦 src/hyperion/ (Code source)
**État** : ✅ Bien organisé  
**Statistiques** :
- 67 fichiers `.py`
- 5419 fichiers `__init__.py` (compté dans total)
- Modules bien séparés (ml, rag, impact, etc.)

**Issues** :
- Dossiers vides : `src/config/`, `src/data/`, `src/docs/`
- À clarifier : tests ML (localisés dans le module vs tests globaux)

### 🧪 tests/ (Tests)
**État** : ✅ Bien structuré  
**Statistiques** :
- 21 fichiers `.py`
- Unit, integration, benchmarks
- Coverage reports (htmlcov/)

**Issues** :
- E2E vide (à développer)
- Tests ML aussi dans `src/hyperion/modules/ml/tests/` (à clarifier)

### 📚 docs/ (Documentation)
**État** : ⚠️ À améliorer  
**Statistiques** :
- 13 fichiers `.md`
- Architecture, guides, changelog

**Issues** :
- Dossiers vides : `docs/api/`, `docs/analysis/`, `docs/generated/`
- Manque : DEVELOPMENT.md, TROUBLESHOOTING.md, API_REFERENCE.md

### 🗂️ data/ (Données)
**État** : ⚠️ À clarifier  
**Contenu** :
- `data/repositories/` (profils, gitignore)
- `data/ml/` (feature store cache)

**Issues** :
- Fichiers `.pkl` et `.json` en cache - vérifier gitignore
- Structure de versioning à clarifier

### ⚙️ scripts/ (Scripts)
**État** : ⚠️ À réorganiser  
**Contenu** :
- 18 fichiers scripts
- Setup, deploy, dev, maintenance

**Issues** :
- Mélange de `.sh` et `.py`
- Pas de centralisation des logs (scripts créent des logs à plusieurs endroits)
- Documentation manquante (MASTER_SCRIPT.md, SETUP_ULTIMATE.md sont documentations)

### 🎛️ config/ (Configuration)
**État** : ⚠️ À clarifier  
**Contenu** :
- `filters.yaml` (config métier)
- `openwebui_hyperion_function.py`
- Dossiers `dev/` et `prod/` vides

**Issues** :
- Structure à clarifier (dev/prod pas utilisés)
- Config réelle centralisée dans `pyproject.toml`, `.env`

### 🏃 modeles/ (Modèles ML)
**État** : ⚠️ À structurer  
**Contenu** :
- 8 modèles `.pkl` (v1.0.0, v1.1.0)
- 8 metadata `.json`

**Issues** :
- Pas de versioning clair (nommage uniquement)
- À migrer vers structure versionnée : `v1.0.0/`, `v1.1.0/`, `latest/`

### 📊 mlruns/ (MLflow tracking)
**État** : ✅ Bien utilisé  
**Contenu** :
- Experiment 0 (Default)
- Run 77e3e764725c4ecaa4e210740508a23b avec metrics
- ~6.8 MB

**Notes** :
- À conserver
- Cleanup des vieilles runs recommandé

### 📈 htmlcov/ (Coverage reports)
**État** : 📊 À maintenir  
**Contenu** :
- Rapports HTML pytest-cov
- ~764 KB

**Issues** :
- À régénérer après chaque run
- Peut être ignoré en git (généré automatiquement)

### 📝 logs/ (Logs)
**État** : ⚠️ À centraliser  
**Contenu** :
- `api.log`
- `dashboard.log`
- `api_test.log`
- `ml/` (vide)

**Issues** :
- Logs aussi à la racine : `api.log`, `install.log`
- Logs aussi dans `scripts/deploy/output/dashboard.log`
- Centraliser dans `logs/` avec structure par composant

### 🌐 frontend/
**État** : ✅ Simplifié et fonctionnel  
**Contenu** :
- `index.html` (React standalone)
- `README.md`

**Notes** :
- Pas de build nécessaire
- Pas de node_modules
- À améliorer : CSS, graphiques, dark mode

---

## 7. Checklist de nettoyage recommandé

### Haute priorité (faire immédiatement)
- [ ] Centraliser les logs (api.log, install.log, dashboard.log dans logs/)
- [ ] Supprimer `output/` (legacy)
- [ ] Vérifier gitignore pour `data/ml/feature_store/cache/` et `data/ml/feature_store/metadata/`
- [ ] Créer/remplir dossiers vides ou les supprimer (src/config/, src/data/, src/docs/)

### Moyenne priorité (faire avant release)
- [ ] Créer DEVELOPMENT.md
- [ ] Créer MAINTAINERS.md
- [ ] Améliorer ARCHITECTURE.md (ajouter diagrammes)
- [ ] Créer API_REFERENCE.md
- [ ] Clarifier tests ML (src vs tests/)
- [ ] Créer `.editorconfig`

### Basse priorité (faire progressivement)
- [ ] Structurer modèles avec versioning (v1.0.0/, v1.1.0/, latest/)
- [ ] Créer scripts/README.md
- [ ] Créer docs/DEPLOYMENT.md
- [ ] Créer docs/TROUBLESHOOTING.md
- [ ] Créer SECURITY.md
- [ ] Organiser config/ (dev/prod ou supprimer)
- [ ] Nettoyer caches (.ruff_cache, .pytest_cache, htmlcov)

---

## 8. Résumé et recommandations

### État actuel : ✅ Solide

**Forces** :
1. Structure `src/` moderne et bien organisée
2. Séparation claire : src, tests, docs, scripts, data
3. Configuration centralisée (pyproject.toml)
4. Tests structurés avec coverage
5. Documentation complète (README, ARCHITECTURE, GUIDE_UTILISATION)
6. Infrastructure ML complète (MLflow, Feature Store, Training)
7. RAG opérationnel avec Qdrant

**Faiblesses** :
1. Logs dispersés à plusieurs endroits
2. Dossiers vides à nettoyer
3. Structure modèles/ pas versionnée
4. Documentation dev/deployment manquante
5. Output/ legacy à supprimer
6. Quelques incohérences (config/, templates/)

### Plan d'action (Phase 1 - Now)
1. **Nettoyage des logs** : Centraliser dans `logs/`
2. **Suppression output/** : Supprimer dossier legacy
3. **Nettoyage src/** : Supprimer dossiers vides
4. **Vérifier gitignore** : S'assurer ML cache est ignoré
5. **Documentation** : Créer DEVELOPMENT.md et MAINTAINERS.md

### Plan d'action (Phase 2 - Next)
1. **Versioning modèles** : Restructurer `modeles/`
2. **Clarifier config** : Nettoyer ou structurer `config/`
3. **Documenter API** : Créer API_REFERENCE.md
4. **Tests ML** : Clarifier séparation (src vs tests)
5. **Workflows CI/CD** : Créer `.github/workflows/`

### Plan d'action (Phase 3 - Later)
1. **Déploiement** : Créer docs/DEPLOYMENT.md
2. **Troubleshooting** : Créer TROUBLESHOOTING.md
3. **Sécurité** : Créer SECURITY.md
4. **Standardisation** : Créer .editorconfig

**Priorité générale** : La structure est bonne. Les améliorations sont surtout du nettoyage et de la documentation.

---

## 9. Annexe : Fichiers à ignorer ou nettoyer

### Candidats suppression (avec confirmation)
```
output/                         # Legacy (vide sauf subdirs)
scripts/.gitignore             # Redondant avec root
src/config/                    # Vide
src/data/                      # Vide
src/docs/                      # Vide
config/dev/                    # Vide
config/prod/                   # Vide
templates/markdown/            # Vide
docs/api/                      # Vide
docs/analysis/                 # Vide
.benchmarks/                   # Vide
```

### À centraliser dans logs/
```
api.log                        # → logs/api.log
install.log                    # → À supprimer (obsolète)
scripts/deploy/output/dashboard.log  # → logs/dashboard.log
```

### À ignorer (vérifier .gitignore)
```
data/ml/feature_store/cache/*.pkl
data/ml/feature_store/metadata/*.json
.ruff_cache/
.pytest_cache/
htmlcov/
venv/
.coverage
```

### À conserver (important)
```
modeles/                       # Modèles ML sauvegardés
mlruns/                        # MLflow tracking
logs/                          # Logs applicatifs
```

