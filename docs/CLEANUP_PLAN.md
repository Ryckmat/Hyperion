# Plan de Nettoyage et Réorganisation - Hyperion v2.5.0

## 🎯 Objectif général

Améliorer la structure du projet Hyperion en :
1. Centralisant les logs dispersés
2. Supprimant les fichiers/dossiers legacy
3. Nettoyant les dossiers vides
4. Renforçant la documentation
5. Structurant correctement les modèles ML

---

## PHASE 1 : Nettoyage immédiat (Faire d'abord)

### 1.1 Centraliser les logs dispersés

**Fichiers concernés** :
- `/api.log` (racine) → à déplacer/supprimer
- `/install.log` (racine) → à supprimer (obsolète)
- `scripts/deploy/output/dashboard.log` → à déplacer dans `logs/`

**Actions** :
```bash
# Vérifier les logs existants
ls -la /home/kortazo/Documents/Hyperion/*.log
ls -la /home/kortazo/Documents/Hyperion/logs/
ls -la /home/kortazo/Documents/Hyperion/scripts/deploy/output/

# Créer la structure logs/ (si nécessaire)
mkdir -p /home/kortazo/Documents/Hyperion/logs/{api,dashboard,ml,ingestion}

# Déplacer les logs
mv /home/kortazo/Documents/Hyperion/api.log /home/kortazo/Documents/Hyperion/logs/api/ 2>/dev/null || echo "api.log doesn't exist at root"
mv /home/kortazo/Documents/Hyperion/scripts/deploy/output/dashboard.log /home/kortazo/Documents/Hyperion/logs/dashboard/ 2>/dev/null || echo "No dashboard.log in scripts/deploy/output"

# Supprimer install.log (obsolète)
rm /home/kortazo/Documents/Hyperion/install.log 2>/dev/null || echo "install.log not found"

# Mettre à jour .gitignore pour logs/
# Vérifier que .gitignore contient: /logs/*.log
```

**Vérification** :
```bash
find /home/kortazo/Documents/Hyperion -name "*.log" -type f
# Devrait retourner uniquement les logs dans /home/kortazo/Documents/Hyperion/logs/
```

**Impact sur les scripts** :
- Mettre à jour `scripts/deploy/hyperion_master.sh` pour utiliser `logs/dashboard/dashboard.log`
- Mettre à jour `scripts/dev/run_api.py` pour utiliser `logs/api/api.log`
- Mettre à jour `scripts/maintenance/*.py` pour utiliser les chemins corrects

---

### 1.2 Supprimer le dossier legacy output/

**Fichiers concernés** :
- `output/` (dossier entier, contient des docs générées legacy)

**Vérification du contenu** :
```bash
ls -la /home/kortazo/Documents/Hyperion/output/
find /home/kortazo/Documents/Hyperion/output -type f
```

**Actions** :
```bash
# Sauvegarder si nécessaire (backup)
# tar czf output.backup.tar.gz /home/kortazo/Documents/Hyperion/output/

# Supprimer le dossier
rm -rf /home/kortazo/Documents/Hyperion/output/
```

**Vérification** :
```bash
ls /home/kortazo/Documents/Hyperion/output/
# Devrait retourner "No such file or directory"
```

**Note** : Cette suppression n'affecte rien car les docs générées sont maintenant dans `docs/generated/`

---

### 1.3 Supprimer dossiers vides dans src/

**Dossiers concernés** :
```
src/config/      # Vide, config ailleurs (/config/, pyproject.toml)
src/data/        # Vide, data ailleurs (/data/)
src/docs/        # Vide, docs ailleurs (/docs/)
```

**Vérification** :
```bash
ls -la /home/kortazo/Documents/Hyperion/src/
ls -la /home/kortazo/Documents/Hyperion/src/config/
ls -la /home/kortazo/Documents/Hyperion/src/data/
ls -la /home/kortazo/Documents/Hyperion/src/docs/
```

**Actions** :
```bash
# Supprimer dossiers vides
rmdir /home/kortazo/Documents/Hyperion/src/config/ 2>/dev/null || echo "src/config not empty or doesn't exist"
rmdir /home/kortazo/Documents/Hyperion/src/data/ 2>/dev/null || echo "src/data not empty or doesn't exist"
rmdir /home/kortazo/Documents/Hyperion/src/docs/ 2>/dev/null || echo "src/docs not empty or doesn't exist"
```

**Vérification** :
```bash
find /home/kortazo/Documents/Hyperion/src -maxdepth 1 -type d
# Ne devrait pas contenir config/, data/, docs/
```

---

### 1.4 Vérifier et nettoyer les caches

**Fichiers concernés** :
```
.ruff_cache/         # 160 KB
.pytest_cache/       # 40 KB
.benchmarks/         # 0 B
htmlcov/             # 764 KB
```

**Actions** :
```bash
# Ces fichiers sont regénérés automatiquement par les outils
# Peut les supprimer et laisser les outils les régénérer

# Option 1 : Supprimer
rm -rf /home/kortazo/Documents/Hyperion/.ruff_cache/
rm -rf /home/kortazo/Documents/Hyperion/.pytest_cache/
rm -rf /home/kortazo/Documents/Hyperion/.benchmarks/
# htmlcov/ peut être gardé si utile pour visualiser la coverage

# Option 2 : Vérifier .gitignore (devraient être ignorés)
grep -E "\.ruff_cache|\.pytest_cache|htmlcov" /home/kortazo/Documents/Hyperion/.gitignore
```

**Note** :
- Ces dossiers devraient être dans `.gitignore` (à vérifier)
- Peuvent être supprimés sans danger (regénérés lors du prochain test/lint)

---

### 1.5 Vérifier ML cache gitignore

**Fichiers concernés** :
```
data/ml/feature_store/cache/*.pkl
data/ml/feature_store/metadata/*.json
```

**Vérification** :
```bash
# Vérifier si ces fichiers sont dans .gitignore
grep -E "data/ml|feature_store" /home/kortazo/Documents/Hyperion/.gitignore

# Lister les fichiers
ls -la /home/kortazo/Documents/Hyperion/data/ml/feature_store/cache/
ls -la /home/kortazo/Documents/Hyperion/data/ml/feature_store/metadata/
```

**Actions** :
```bash
# S'assurer que .gitignore contient:
# data/ml/feature_store/cache/
# data/ml/feature_store/metadata/

# Si pas présent, ajouter à .gitignore (dans la section data/)
```

**Note** : Ces fichiers sont regénérables donc à ignorer dans git

---

## PHASE 2 : Documentation et organisation (Avant release)

### 2.1 Créer DEVELOPMENT.md

**Localisation** : `/home/kortazo/Documents/Hyperion/DEVELOPMENT.md`

**Contenu suggéré** :
```markdown
# Development Guide

## Quick Start

### Prerequisites
- Python 3.10+
- Git
- Virtual environment (recommended)

### Setup
```bash
# Clone repo
git clone https://github.com/Ryckmat/Hyperion.git
cd Hyperion

# Create virtual environment
python -m venv venv
source venv/bin/activate  # Linux/Mac
# ou: venv\Scripts\activate (Windows)

# Install in dev mode
pip install -e ".[dev]"

# Verify installation
hyperion --version
hyperion info
```

## Development Workflow

### Running Tests
```bash
# All tests
pytest tests/ -v

# Specific test file
pytest tests/unit/test_ml_config.py -v

# With coverage
pytest tests/ --cov=hyperion --cov-report=html

# Watch for specific marker
pytest tests/ -m "unit"
```

### Code Quality

#### Format Code
```bash
black src/ tests/
```

#### Lint Code
```bash
ruff check src/ tests/
ruff check --fix src/ tests/  # Auto-fix
```

#### Type Checking
```bash
mypy src/hyperion
```

#### Run All Checks
```bash
black src/ tests/
ruff check --fix src/ tests/
mypy src/hyperion
pytest tests/
```

## Project Structure

### src/hyperion/
- `api/` : FastAPI endpoints
- `cli/` : Command-line interface
- `core/` : Git analysis engine
- `modules/` : Feature modules
  - `ml/` : Machine learning infrastructure
  - `rag/` : RAG/retrieval system
  - `impact/` : Impact analysis
  - `integrations/` : Neo4j, external services
  - ... (other modules)
- `utils/` : Utilities

### tests/
- `unit/` : Unit tests
- `integration/` : Integration tests
- `api/` : API tests
- `benchmarks/` : Performance tests

### docs/
- Getting started guides
- Architecture documentation
- API reference

## Common Tasks

### Adding a New Feature
1. Create branch: `git checkout -b feature/feature-name`
2. Implement feature in appropriate module
3. Add tests in `tests/unit/` or `tests/integration/`
4. Run: `pytest tests/`
5. Format: `black src/ && ruff check --fix src/`
6. Commit and push
7. Create pull request

### Adding Tests
- Unit tests in `tests/unit/`
- Integration tests in `tests/integration/`
- Test file naming: `test_*.py` or `*_test.py`
- Fixtures in `tests/conftest.py`

### Debugging
```bash
# Run with debug output
pytest tests/unit/test_ml_config.py -v -s

# Drop into debugger
pytest tests/unit/test_ml_config.py --pdb
```

## Pre-commit Hooks

This project uses pre-commit hooks for code quality.

### Setup Hooks
```bash
pre-commit install
```

### Run Manually
```bash
pre-commit run --all-files
```

## Documentation

Generate HTML coverage report:
```bash
pytest tests/ --cov=hyperion --cov-report=html
open htmlcov/index.html
```

## Troubleshooting

### Import errors
- Ensure virtual environment is activated
- Run: `pip install -e ".[dev]"`

### Tests failing
- Check Python version: `python --version` (should be 3.10+)
- Run: `pip install --upgrade -e ".[dev]"`

### Linting errors
- Format: `black src/ tests/`
- Check: `ruff check --fix src/ tests/`

## Resources
- README.md - Project overview
- ARCHITECTURE.md - System design
- docs/ - Complete documentation
```

---

### 2.2 Créer MAINTAINERS.md

**Localisation** : `/home/kortazo/Documents/Hyperion/MAINTAINERS.md`

**Contenu suggéré** :
```markdown
# Maintainers & Contributors Guide

## Current Maintainers

### Lead
- **Matthieu Ryckman** (contact@ryckmat.dev)
  - Project lead, architecture decisions
  - Code reviews for all PRs
  - Release management

### Modules (To be assigned)
- **ML Pipeline** : [TBD]
  - Feature Store
  - Training Pipeline
  - Model Registry
- **RAG/Vector Store** : [TBD]
  - Qdrant integration
  - Embeddings
  - Query engine
- **API/Integrations** : [TBD]
  - FastAPI endpoints
  - Neo4j integration
  - External services

## Contribution Guidelines

### Code Standards
- **Python Version** : 3.10+
- **Code Style** : Black formatter
- **Linting** : Ruff
- **Type Hints** : MyPy (when applicable)
- **Tests** : Minimum 80% coverage
- **Docstrings** : Google style

### Pull Request Process
1. Create feature branch from `main`
2. Implement changes
3. Add/update tests
4. Run code quality checks:
   ```bash
   black src/ tests/
   ruff check --fix src/ tests/
   pytest tests/ --cov
   ```
5. Update documentation as needed
6. Submit PR with clear description
7. Wait for code review and CI/CD to pass
8. Address review comments
9. Merge once approved

### Commit Messages
- Use descriptive, actionable titles
- Reference issues if applicable
- Format: `<type>: <description>`
  - `feat:` New feature
  - `fix:` Bug fix
  - `docs:` Documentation
  - `test:` Tests
  - `refactor:` Code refactoring
  - `perf:` Performance improvement

### Issue Labels
- `bug` : Something is broken
- `enhancement` : New feature or improvement
- `documentation` : Docs improvement
- `good-first-issue` : Good for new contributors
- `help-wanted` : Help needed
- `question` : Questions or discussions
- `blocked` : Blocked by another issue

## Release Process

### Version Numbering
- Follow semantic versioning: `MAJOR.MINOR.PATCH`
- v2.5.0 format

### Release Steps
1. Update version in `src/hyperion/__version__.py`
2. Update `CHANGELOG.md` with changes
3. Create release branch: `release/v2.x.x`
4. Tag commit: `git tag v2.x.x`
5. Push to GitHub
6. Create GitHub release
7. Update version to next dev: `v2.x.x+dev`

## Code Review Guidelines

### What to Review
- Functionality : Does it work correctly?
- Tests : Are tests adequate and passing?
- Documentation : Is it clear and complete?
- Performance : Any obvious bottlenecks?
- Security : Any security concerns?

### Comment Style
- Be respectful and constructive
- Ask questions rather than demand changes
- Suggest improvements with examples
- Acknowledge good work

## Contact
- Issues : GitHub Issues
- Discussions : GitHub Discussions
- Email : contact@ryckmat.dev

## Code of Conduct

We're committed to a welcoming and inclusive community. Please see our CODE_OF_CONDUCT.md (when created).
```

---

### 2.3 Créer .editorconfig

**Localisation** : `/home/kortazo/Documents/Hyperion/.editorconfig`

**Contenu** :
```ini
# EditorConfig helps maintain consistent coding styles for multiple developers
# working on the same project across various editors and IDEs.
# editorconfig.org

root = true

# All files
[*]
charset = utf-8
end_of_line = lf
insert_final_newline = true
trim_trailing_whitespace = true

# Python files
[*.py]
indent_style = space
indent_size = 4
max_line_length = 100

# YAML files
[*.{yaml,yml}]
indent_style = space
indent_size = 2

# JSON files
[*.json]
indent_style = space
indent_size = 2

# Markdown files
[*.md]
trim_trailing_whitespace = false
max_line_length = off

# Shell scripts
[*.sh]
indent_style = space
indent_size = 2

# Makefile
[Makefile]
indent_style = tab

# Ignore whitespace changes in certain files
[*.md]
end_of_line = lf
```

---

### 2.4 Améliorer ARCHITECTURE.md

**Actions** :
1. Ajouter diagramme architecture ASCII
2. Documenter flux de données
3. Expliciter intégrations (Neo4j, Qdrant, Ollama)
4. Ajouter Decision Records (ADRs)

**Exemple de diagramme à ajouter** :
```
User/System
    │
    ├──────────────────────────┬──────────────────────────┐
    │                          │                          │
    v                          v                          v
[Open WebUI]              [CLI Tools]            [API Clients]
(Chat Interface)         (hyperion cli)          (SDK/REST)
    │                          │                          │
    └──────────────────────────┼──────────────────────────┘
                               │
                               v
                        [FastAPI Server]
                        (src/hyperion/api/)
                               │
                ┌──────────────┼──────────────┐
                │              │              │
                v              v              v
          [RAG Engine]    [Git Analysis]  [ML Pipeline]
          (Qdrant)       (GitAnalyzer)    (MLflow)
                │              │              │
                v              v              v
          [Vector Store]   [Metrics]     [Models]
          (Embeddings)     (Analysis)    (Registry)
                │              │              │
                └──────────────┼──────────────┘
                               │
                               v
                        [Neo4j DB] (optional)
                        (Knowledge Graph)
```

---

## PHASE 3 : Structure des modèles ML (Next)

### 3.1 Restructurer modeles/ avec versioning

**Situation actuelle** :
```
modeles/
├── risk_predictor_isolation_forest_v1.0.0.pkl
├── risk_predictor_isolation_forest_v1.1.0.pkl
├── risk_predictor_random_forest_v1.0.0.pkl
├── risk_predictor_random_forest_v1.1.0.pkl
├── risk_predictor_xgboost_v1.0.0.pkl
├── risk_predictor_meta_learner_v1.0.0.pkl
├── risk_predictor_meta_learner_v1.1.0.pkl
└── metadata/
    └── (metadata JSON files)
```

**Structure cible** :
```
modeles/
├── v1.0.0/
│   ├── risk_predictor_isolation_forest.pkl
│   ├── risk_predictor_random_forest.pkl
│   ├── risk_predictor_xgboost.pkl
│   ├── risk_predictor_meta_learner.pkl
│   ├── metadata/
│   │   └── (metadata JSON for v1.0.0)
│   └── README.md
│       # Changelog, performance metrics, notes
├── v1.1.0/
│   ├── risk_predictor_isolation_forest.pkl
│   ├── risk_predictor_random_forest.pkl
│   ├── risk_predictor_xgboost.pkl
│   ├── risk_predictor_meta_learner.pkl
│   ├── metadata/
│   │   └── (metadata JSON for v1.1.0)
│   └── README.md
├── latest -> v1.1.0  (symlink)
├── archived/
│   └── v0.9.0/
│       └── (old models)
└── README.md
    # Overview of all model versions
```

**Avantages** :
- Versioning clair
- Rollback facile
- Documentation par version
- Historique conservé
- Gestion des dépendances facile

---

## PHASE 4 : Documentation complémentaire (Later)

### 4.1 Créer API_REFERENCE.md
### 4.2 Créer docs/DEPLOYMENT.md
### 4.3 Créer docs/TROUBLESHOOTING.md
### 4.4 Créer SECURITY.md
### 4.5 Créer scripts/README.md
### 4.6 Clarifier config/ structure

---

## Checklist d'exécution

### Avant tout
- [ ] Créer branche de travail : `git checkout -b refactor/cleanup-structure`
- [ ] Vérifier git status : `git status`
- [ ] Faire sauvegarde : `git stash` (si modification en cours)

### Phase 1 - Immédiat
- [ ] 1.1 Centraliser les logs
  - [ ] Créer structure logs/
  - [ ] Déplacer fichiers
  - [ ] Mettre à jour scripts
- [ ] 1.2 Supprimer output/
  - [ ] Vérifier contenu
  - [ ] Supprimer dossier
- [ ] 1.3 Supprimer dossiers vides dans src/
  - [ ] src/config/
  - [ ] src/data/
  - [ ] src/docs/
- [ ] 1.4 Vérifier caches
  - [ ] .ruff_cache/
  - [ ] .pytest_cache/
  - [ ] .benchmarks/
- [ ] 1.5 Vérifier gitignore ML cache
  - [ ] data/ml/feature_store/cache/
  - [ ] data/ml/feature_store/metadata/

### Phase 2 - Before Release
- [ ] 2.1 Créer DEVELOPMENT.md
- [ ] 2.2 Créer MAINTAINERS.md
- [ ] 2.3 Créer .editorconfig
- [ ] 2.4 Améliorer ARCHITECTURE.md
- [ ] Tests : `pytest tests/`
- [ ] Format : `black src/ tests/`
- [ ] Lint : `ruff check --fix src/ tests/`

### Après tout
- [ ] Vérifier git status : `git status`
- [ ] Commit : `git add . && git commit -m "refactor: structure cleanup"`
- [ ] Push : `git push origin refactor/cleanup-structure`
- [ ] Créer PR et merger

---

## Notes importantes

1. **Backups** : Avant suppression majeure, sauvegarder
2. **Tests** : Toujours tester après refactoring
3. **Documentation** : Mettre à jour les chemins dans la doc
4. **Scripts** : Vérifier les chemins hardcodés dans les scripts
5. **CI/CD** : Vérifier que les workflows utilisent les bons chemins

---

## Questions/Décisions à confirmer

1. **Fichiers .log** : Garder uniquement les logs générés récemment ou tous les historiques?
2. **output/** : Y a-t-il du contenu important à conserver?
3. **modeles/** : Faut-il migrer les versions ou laisser tel quel pour l'instant?
4. **config/dev et config/prod** : À utiliser ou à supprimer?
5. **templates/markdown/** : À documenter ou à supprimer?

