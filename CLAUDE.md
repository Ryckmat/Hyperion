# CLAUDE.md

model: claude-sonnet-4-20250514

# 🚀 CONTEXTE HYPERION V2 - ANALYSE PROJET `requests`

## 📅 Date : Décembre 2024
## 🎯 Mission : Valider Hyperion v2 sur un projet Python réel

---

## 🎪 OBJECTIF PRINCIPAL

Tester **Hyperion v2** en analysant le projet Python **`requests`** (situé dans `/home/kortazo/Documents/requests/`) pour valider les 8 moteurs d'intelligence de code.

**Workflow de test :**
```bash
# 1. Orchestrateur unique - Profile complet
hyperion profile /home/kortazo/Documents/requests/ --output data/repositories/

# 2. Orchestrateur unique - Ingestion complète v2
hyperion ingest data/repositories/requests/profile.yaml --clear

# 3. Validation via API + RAG + Neo4j
```

---

## 🎯 LES 8 MOTEURS À VALIDER SUR `requests`

### 1. 🎯 Impact Analysis Engine
**Test cible :** Modifier `requests/sessions.py` → impact sur quels fichiers ?

**Questions de validation :**
- "Modification de `Session.request()` impacte-t-elle `api.py`, `models.py` ?"
- "L'orchestrateur calcule-t-il l'impact en <3 secondes ?"
- "Risk level CRITICAL/HIGH/MEDIUM/LOW est-il cohérent ?"

### 2. 🧭 Code Understanding Engine
**Test cible :** "Où est gérée l'authentification dans requests ?"

**Questions de validation :**
- "RAG peut-il localiser `requests/auth.py` avec sources précises ?"
- "L'orchestrateur extrait-il tous les docstrings de requests ?"
- "Mapping business → code fonctionne-t-il (auth, sessions, SSL) ?"

### 3. 🔍 Anomaly Detection
**Test cible :** Identifier code smells dans le projet requests

**Questions de validation :**
- "Détection fonctions >15 complexité cyclomatique dans requests ?"
- "Files >500 LOC flaggés comme anomalies ?"
- "Patterns suspects (hardcoded URLs, secrets) détectés ?"

### 4-8. Autres Moteurs
- **Onboarding Intelligent** : Parcours apprentissage requests
- **Refactoring Assistant** : Suggestions refacto
- **Documentation Auto** : README et diagrammes
- **Capacity Planning** : Estimation effort
- **Security & Compliance** : Scan sécurité

---

## 📋 QUESTIONS DE TEST PRIORITAIRES

### P0 - Validation Orchestrateur
1. **"L'orchestrateur profile-t-il requests (52k stars, ~100 files) sans crash ?"**
2. **"Neo4j v2 : nœuds `:Function`, `:Class` créés pour tout requests ?"**
3. **"RAG répond-il 'Comment marche requests.get()?' avec sources ?"**
4. **"Impact analysis : modif `sessions.py` → liste fichiers impactés ?"**

### P1 - Performance & Qualité
5. **"Profiling complet requests en <5 minutes ?"**
6. **"RAM <2GB pendant analyse complète ?"**
7. **"Code respecte-t-il Black + Ruff sans warnings ?"**
8. **"API responses <2s (p95) ?"**

---

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

Hyperion is a local Git repository analysis and exploration platform combining:
- Git analysis (commits, hotspots, contributors, metrics)
- RAG (Retrieval Augmented Generation) based on Qdrant
- Optional knowledge graph via Neo4j
- OpenAI-compatible API (Chat Completions / Models)
- Conversational interface via Open WebUI

## Common Commands

### Development

```bash
# Install in development mode
pip install -e ".[dev]"

# Run API server
python scripts/dev/run_api.py
# or directly:
uvicorn hyperion.api.main:app --reload --host 0.0.0.0 --port 8000

# Run dashboard (separate terminal)
cd frontend && python -m http.server 3000
```

### Testing

```bash
# Run all tests with coverage
pytest

# Run specific test file
pytest tests/unit/test_impact_analyzer.py

# Run tests by marker
pytest -m unit          # Unit tests only
pytest -m integration   # Integration tests only
pytest -m "not slow"    # Skip slow tests

# Run single test function
pytest tests/unit/test_impact_analyzer.py::test_analyze_file -v
```

### Linting & Formatting

```bash
# Format code
black src/ tests/

# Lint with ruff
ruff check src/ tests/

# Lint and auto-fix
ruff check src/ tests/ --fix

# Type checking
mypy src/
```

### CLI Usage

```bash
# Profile a Git repository
hyperion profile /path/to/repo --output data/repositories/

# Generate documentation from profile
hyperion generate data/repositories/mon-repo/profile.yaml

# Ingest profile into Neo4j
hyperion ingest data/repositories/mon-repo/profile.yaml --clear

# Show configuration
hyperion info
```

## Architecture

### Source Layout (`src/hyperion/`)

- **core/**: Git analysis engine
  - `git_analyzer.py`: Main analyzer generating Hyperion profiles (commits, contributors, hotspots, metrics)
  - Uses `GitRepo` wrapper from `utils/git_utils.py`

- **api/**: FastAPI REST backend
  - `main.py`: FastAPI app with CORS, health checks, repos endpoints, RAG chat
  - `openai_compat.py`: OpenAI-compatible endpoints (`/v1/models`, `/v1/chat/completions`)

- **cli/**: Click-based command line interface
  - `main.py`: Commands: `profile`, `generate`, `ingest`, `info`

- **modules/**: Business modules
  - `rag/`: Qdrant integration, embeddings (BGE-large), query engine with Ollama LLM
  - `generators/`: Markdown documentation generation from profiles
  - `integrations/`: Neo4j ingester for knowledge graph
  - `impact/`: AST-based impact analysis and dependency detection
  - `understanding/`: Semantic code indexer
  - `anomaly/`: ML-based anomaly detection (Isolation Forest)
  - `onboarding/`: Learning path generator
  - `capacity/`, `documentation/`, `refactoring/`, `security/`: Additional modules

### Configuration

- `config.py`: Centralized config (paths, Neo4j, batch sizes, filters)
- `modules/rag/config.py`: RAG-specific config (Qdrant, embeddings, Ollama, prompts)
- Environment variables loaded from `.env` at project root

### Key Environment Variables

```bash
# Neo4j
NEO4J_URI=bolt://localhost:7687
NEO4J_USER=neo4j
NEO4J_PASSWORD=

# Qdrant
QDRANT_HOST=localhost
QDRANT_PORT=6333

# Ollama LLM
OLLAMA_BASE_URL=http://localhost:11434
OLLAMA_MODEL=qwen2.5:32b

# Embeddings
EMBEDDING_MODEL=BAAI/bge-large-en-v1.5
EMBEDDING_DEVICE=cuda
```

### Test Structure

- `tests/unit/`: Unit tests (mocked dependencies)
- `tests/integration/`: Integration tests (require services)
- `tests/api/`: API smoke tests and endpoint tests
- `tests/benchmarks/`: Performance benchmarks
- `tests/conftest.py`: Fixtures for sample repos, Qdrant/Neo4j clients

### Code Style

- Line length: 88 characters (Black standard pour v2)
- Formatter: Black
- Linter: Ruff (E, W, F, B, I, UP, SIM rules)
- Imports sorted with isort via ruff, `hyperion` as first-party
- Python 3.10+ required

### Import Convention

```python
# Core imports
from hyperion.core import GitAnalyzer
from hyperion.api.main import app

# Module imports
from hyperion.modules.rag.query import RAGQueryEngine
from hyperion.modules.generators.markdown_generator import MarkdownGenerator
from hyperion.modules.integrations.neo4j_ingester import Neo4jIngester
```

---

## 🛠️ COMMANDES SPÉCIFIQUES TEST V2

### Setup & Profiling requests
```bash
# Vérif code style avant test
black --check src/ tests/ --line-length=88
ruff check src/ tests/ --select=E,W,F,B,I,UP,SIM

# Profile orchestrateur unique sur requests
hyperion profile /home/kortazo/Documents/requests/ --output data/repositories/

# Ingestion v2 complète
hyperion ingest data/repositories/requests/profile.yaml --clear --neo4j-v2
```

### Tests API V2
```bash
# Test Neo4j v2 nodes
curl http://localhost:8000/api/repos/requests/functions

# Test RAG enhanced sur requests
curl -X POST http://localhost:8000/api/chat \
  -H "Content-Type: application/json" \
  -d '{
    "message": "Explique architecture auth dans requests",
    "repo_filter": ["requests"]
  }'

# Test impact analysis
curl -X POST http://localhost:8000/api/impact/analyze \
  -H "Content-Type: application/json" \
  -d '{
    "repo": "requests",
    "file": "requests/sessions.py",
    "changes": ["Session.request"]
  }'
```

### Tests Unitaires V2
```bash
# Tests spécifiques v2 modules
pytest tests/unit/test_impact_analyzer.py -v
pytest tests/unit/test_understanding_indexer.py -v
pytest tests/unit/test_anomaly_detector.py -v

# Benchmarks performance sur requests
pytest tests/benchmarks/ -m benchmark
```

---

## 📊 MÉTRIQUES DE SUCCÈS V2

### ✅ V2 Validée si :
- **Profiling requests** : <5min, 0 crash, format correct
- **Neo4j v2** : >500 `:Function` nodes, relations correctes
- **RAG enhanced** : réponses précises avec sources requests
- **Impact analysis** : dependencies session→api détectées
- **Code quality** : Black + Ruff compliance 100%
- **Performance** : <2GB RAM, <5s queries

### ❌ V2 Échoue si :
- Crash pendant orchestration
- Neo4j nodes v2 vides/incorrects
- RAG hors-sujet sur questions requests
- Impact analysis rate dependencies
- Style violations Black/Ruff
- OOM ou timeouts fréquents

---

## 🚦 ACTIONS PRIORITAIRES TEST V2

### Immediate
1. **Vérifier code style** : `black src/ && ruff check src/`
2. **Test orchestrateur** : `hyperion profile requests/`
3. **Validate Neo4j v2** : vérif nodes `:Function`, `:Class`

### Validation Complète
4. **Test 8 moteurs** individuellement sur requests
5. **Performance benchmarks** sur codebase réelle
6. **Documentation** des résultats d'analyse requests

---

## 🚀 DÉPLOIEMENT HYPERION MASTER

### Script de Déploiement Automatique
```bash
# Lancement complet automatique (v1 + v2 + RAG + API + Dashboard + Open WebUI)
./scripts/deploy/hyperion_master.sh --auto
```

### ✅ Services Lancés Automatiquement
- **API Hyperion** : http://localhost:8000
- **Dashboard React** : http://localhost:3000
- **Open WebUI** : http://localhost:3001
- **Neo4j Browser** : http://localhost:7474
- **Qdrant** : http://localhost:6333

### 📊 Ingestion Automatique Complète
1. **Git Stats (v1)** : 35 commits, 1 contributeur, 10 hotspots
2. **Code Analysis (v2)** : 81 fichiers Python, 467 nodes Neo4j, 387 relations
3. **RAG Embeddings** : 6 chunks ingérés dans Qdrant

### ⚠️ PROBLÈME IDENTIFIÉ - À CORRIGER

**Issue** : Le script `hyperion_master.sh --auto` se termine automatiquement au lieu d'attendre Ctrl+C pour stopper les services.

**Comportement actuel :**
```bash
🎯 Tout est opérationnel !
   Ctrl+C pour arrêter tous les services
# Script se termine immédiatement → services restent en arrière-plan
```

**Comportement attendu :**
```bash
🎯 Tout est opérationnel !
   Ctrl+C pour arrêter tous les services
# Script reste actif, écoute Ctrl+C, puis tue tous les services proprement
```

**Correction nécessaire dans `scripts/deploy/hyperion_master.sh` :**
```bash
# À la fin du script, ajouter :
echo "🎯 Tout est opérationnel !"
echo "   Ctrl+C pour arrêter tous les services"

# Fonction cleanup pour tuer tous les services
cleanup() {
    echo "🛑 Arrêt des services..."
    kill $API_PID $DASHBOARD_PID 2>/dev/null
    docker stop open-webui 2>/dev/null
    echo "✅ Services arrêtés"
    exit 0
}

# Trap pour capturer Ctrl+C
trap cleanup SIGINT

# Boucle infinie pour maintenir le script actif
while true; do
    sleep 1
done
```

**Test de validation :**
1. `./scripts/deploy/hyperion_master.sh --auto`
2. Vérifier que le script reste actif
3. Ctrl+C → doit arrêter tous les services proprement

Coté ingestion  

![graph](/home/kortazo/Documents/Hyperion/graph.png)

Deux soucis à souligner : 
1 il n'y pas plus la notion de commit selon le contributeur donc donc on perd le tracage 

2 il y a aucun lien entre les directory et les files ce qui est dommage pour une arborecence de projet 

faudra aussi arranger le ingestion de noe4j V1 et V2 pour que ça soit pertinant