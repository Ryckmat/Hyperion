# 🏗️ Architecture Hyperion v2.7

**Version**: 2.7.0
**Date**: 
**Auteur**: Matthieu Ryckman

---

## 📋 Table des Matières

- [Vue d'ensemble](#vue-densemble)
- [Principes de conception](#principes-de-conception)
- [Structure du projet](#structure-du-projet)
- [Composants principaux](#composants-principaux)
- [Flux de données](#flux-de-données)
- [Choix techniques](#choix-techniques)
- [Diagrammes](#diagrammes)

---

## 🎯 Vue d'ensemble

Hyperion v2.7 est une plateforme d'intelligence locale complète pour repositories Git avec infrastructure ML enterprise, conçue pour :

1. **Analyser en profondeur** les dépôts Git (commits, contributeurs, hotspots, métriques qualité)
2. **Indexer sémantiquement** les profils Git dans Qdrant avec RAG contextuel
3. **Entraîner et déployer** des modèles ML pour prédiction de risques et détection d'anomalies
4. **Extraire et analyser** le code source (Python AST) avec Neo4j pour compréhension structurelle
5. **Offrir une interface conversationnelle** via RAG pour explorer les données avec sources
6. **Exposer une API REST complète** (Core + OpenAI-compatible + v2 Code Intelligence)
7. **Fournir des outils CLI** complets pour profiling, génération docs et ingestion
8. **Analyser l'impact** des changements et détecter les anomalies code en temps réel

### Architecture Générale

```
┌───────────────────────────────────────────────────────────────────────────────────┐
│                                  HYPERION v2.7                                    │
│                          Enterprise ML Platform                                   │
├───────────────────────────────────────────────────────────────────────────────────┤
│                                                                                   │
│  ┌─────────────────────── PRESENTATION LAYER ──────────────────────────┐        │
│  │                                                                      │        │
│  │  ┌──────────┐  ┌────────────┐  ┌──────────────┐  ┌─────────────┐  │        │
│  │  │   CLI    │  │  REST API  │  │ Dashboard    │  │ Open WebUI  │  │        │
│  │  │ (Click)  │  │ (FastAPI)  │  │  (React)     │  │ (Chat UI)   │  │        │
│  │  │ 5 cmds   │  │ 30+ endpts │  │ Port 3000    │  │ Port 3001   │  │        │
│  │  └─────┬────┘  └──────┬─────┘  └──────┬───────┘  └──────┬──────┘  │        │
│  │        │              │               │                 │         │        │
│  └────────┼──────────────┼───────────────┼─────────────────┼─────────┘        │
│           │              │               │                 │                   │
│  ┌────────┼──────────────┼───────────────┼─────────────────┼─────────┐        │
│  │        │     BUSINESS LOGIC LAYER     │                 │         │        │
│  │        │                              │                 │         │        │
│  │  ┌─────▼─────────┐  ┌─────────────────▼─┐  ┌────────────▼────────┐ │        │
│  │  │  GitAnalyzer  │  │   RAG Engine     │  │   ML Infrastructure │ │        │
│  │  │  (Profile)    │  │   (Qdrant)       │  │                     │ │        │
│  │  └───────────────┘  └─────────────────┬─┘  │ ┌─────────────────┐ │ │        │
│  │                                       │    │ │  Feature Store  │ │ │        │
│  │  ┌─────────────────┐  ┌────────────────▼──┐ │ │   (35+ feat.)   │ │ │        │
│  │  │  CodeAnalyzer   │  │  Neo4j Code Graph │ │ └─────────────────┘ │ │        │
│  │  │  (AST Parser)   │  │ (Functions/Classes)│ │                     │ │        │
│  │  └─────────────────┘  └───────────────────┘ │ ┌─────────────────┐ │ │        │
│  │                                             │ │ Training Pipeline│ │ │        │
│  │  ┌─────────────────┐  ┌───────────────────┐ │ │ (4 models + ens.)│ │ │        │
│  │  │ ImpactAnalyzer  │  │ AnomalyDetector   │ │ └─────────────────┘ │ │        │
│  │  │ (Change Impact) │  │ (Code Smells)     │ │                     │ │        │
│  │  └─────────────────┘  └───────────────────┘ │ ┌─────────────────┐ │ │        │
│  │                                             │ │  Model Registry │ │ │        │
│  │                                             │ │   (MLflow)      │ │ │        │
│  │                                             │ └─────────────────┘ │ │        │
│  │                                             └─────────────────────┘ │        │
│  └─────────────────────────┬───────────────────────────┬───────────────┘        │
│                            │                           │                         │
│  ┌─────────────────────── DATA LAYER ────────────────────────────────┐          │
│  │                        │                           │               │          │
│  │ ┌──────────────────────▼─┐  ┌─────────────────────▼──┐  ┌─────────▼───────┐ │
│  │ │   Git Repository      │  │  Qdrant Vector DB     │  │ MLflow Tracking │ │ │
│  │ │   (Local FS)          │  │  (Embeddings+Chunks)  │  │ (Experiments)   │ │ │
│  │ └───────────────────────┘  └────────────────────────┘  └─────────────────┘ │ │
│  │                                                                            │ │
│  │ ┌─────────────────────┐   ┌─────────────────────────┐  ┌─────────────────┐ │ │
│  │ │   Neo4j Graph DB    │   │    Feature Store        │  │  Model Store    │ │ │
│  │ │   (Code Structure)  │   │    (Cache + TTL)        │  │   (Pickle)      │ │ │
│  │ └─────────────────────┘   └─────────────────────────┘  └─────────────────┘ │ │
│  └────────────────────────────────────────────────────────────────────────────┘ │
│                                                                                   │
│  ┌─────────────────────── INFRASTRUCTURE LAYER ───────────────────────┐        │
│  │                                                                      │        │
│  │ ┌─────────────────┐  ┌──────────────────┐  ┌─────────────────────┐  │        │
│  │ │   Ollama LLM    │  │  Docker Services │  │  Python Ecosystem   │  │        │
│  │ │ (4 model types) │  │  (Qdrant+Neo4j)  │  │ (FastAPI+MLflow+SK) │  │        │
│  │ └─────────────────┘  └──────────────────┘  └─────────────────────┘  │        │
│  └──────────────────────────────────────────────────────────────────────┘        │
│                                                                                   │
└───────────────────────────────────────────────────────────────────────────────────┘
```

---

## 🎨 Principes de Conception

### 1. **Separation of Concerns** (Séparation des responsabilités)
- **CLI** : Interface utilisateur ligne de commande
- **API** : Endpoints REST et OpenAI-compatible
- **Core** : Logique métier (analyse Git, RAG)
- **Modules** : Fonctionnalités isolées (rag, generators, integrations)

### 2. **Layered Architecture** (Architecture en couches)
```
┌─────────────────────────┐
│  Presentation Layer     │  ← CLI, API, Dashboard
├─────────────────────────┤
│  Business Logic Layer   │  ← Core, Modules
├─────────────────────────┤
│  Data Access Layer      │  ← Git, Qdrant, Neo4j
├─────────────────────────┤
│  Infrastructure Layer   │  ← Config, Utils
└─────────────────────────┘
```

### 3. **Modern Python Packaging** (src/ layout)
- Code source dans `src/hyperion/`
- Tests dans `tests/`
- Configuration centralisée dans `pyproject.toml`

### 4. **Lazy Loading**
- RAG engine chargé à la demande (réduction temps démarrage)
- Neo4j connection optional

### 5. **Dependency Injection**
- Configuration injectable via `.env`
- Paths configurables dans `config.py`

---

## 📁 Structure du Projet

```
Hyperion/
├── src/hyperion/              # Package principal (src/ layout)
│   ├── __init__.py
│   ├── __version__.py         # Version centralisée
│   ├── config.py              # Configuration globale
│   │
│   ├── cli/                   # Interface CLI (Click)
│   │   ├── __init__.py
│   │   └── main.py            # Commandes: profile, generate, ingest, info
│   │
│   ├── core/                  # Logique métier
│   │   ├── __init__.py
│   │   └── git_analyzer.py    # Analyseur Git principal
│   │
│   ├── api/                   # API REST (FastAPI)
│   │   ├── __init__.py
│   │   ├── main.py            # Endpoints REST
│   │   └── openai_compat.py   # Endpoints OpenAI-compatible
│   │
│   ├── modules/               # Modules métier
│   │   ├── rag/               # Retrieval Augmented Generation
│   │   │   ├── config.py      # Config RAG
│   │   │   ├── ingestion.py   # Indexation Qdrant
│   │   │   └── query.py       # Moteur de requêtes RAG
│   │   │
│   │   ├── generators/        # Générateurs de documentation
│   │   │   └── markdown_generator.py
│   │   │
│   │   ├── integrations/      # Intégrations externes
│   │   │   └── neo4j_ingester.py
│   │   │
│   │   └── models/            # Modèles de données
│   │       └── __init__.py
│   │
│   └── utils/                 # Utilitaires
│       ├── __init__.py
│       └── git_utils.py       # Wrappers Git
│
├── tests/                     # Tests unitaires & intégration
│   ├── conftest.py            # Fixtures pytest
│   ├── test_structure.py      # Tests structure
│   ├── unit/                  # Tests unitaires
│   ├── integration/           # Tests d'intégration
│   └── e2e/                   # Tests end-to-end
│
├── scripts/                   # Scripts d'automatisation
│   ├── setup/                 # Installation
│   ├── dev/                   # Développement
│   ├── deploy/                # Déploiement
│   │   └── hyperion_master.sh # Script d'orchestration
│   └── maintenance/           # Maintenance
│
├── frontend/                  # Dashboard React
│   └── index.html             # Single-page app
│
├── data/                      # Données générées
│   └── repositories/          # Profils Git analysés
│
├── templates/                 # Templates Jinja2
│   └── markdown/              # Templates docs Markdown
│
├── config/                    # Configuration
│   └── filters.yaml           # Filtres hotspots
│
├── docs/                      # Documentation
│   ├── architecture/          # Docs architecture
│   ├── guides/                # Guides utilisateur
│   └── api/                   # Docs API
│
├── .github/                   # GitHub Actions
│   └── workflows/
│       └── ci.yml             # CI/CD pipeline
│
├── pyproject.toml             # Configuration moderne Python
├── requirements.txt           # Dépendances production
├── requirements-dev.txt       # Dépendances développement
├── .pre-commit-config.yaml    # Pre-commit hooks
├── .gitignore                 # Git ignore rules
├── setup.py                   # Setup legacy (à migrer)
├── README.md                  # Documentation principale
├── CHANGELOG.md               # Historique des versions
├── CONTRIBUTING.md            # Guide de contribution
└── ARCHITECTURE.md            # Ce fichier

```

---

## 🧩 Composants Principaux

### 1. **CLI (Command Line Interface)**

**Fichier**: [src/hyperion/cli/main.py](src/hyperion/cli/main.py)

**Framework**: Click

**Commandes**:
```bash
hyperion profile <repo_path>     # Analyse un dépôt Git
hyperion generate <profile.yaml> # Génère la documentation
hyperion ingest <profile.yaml>   # Ingestion dans Neo4j
hyperion export <repo_path>      # Export historique prod
hyperion info                    # Affiche configuration
```

**Responsabilités**:
- Parsing des arguments CLI
- Validation des entrées
- Affichage des résultats
- Gestion des erreurs user-friendly

---

### 2. **GitAnalyzer (Core)**

**Fichier**: [src/hyperion/core/git_analyzer.py](src/hyperion/core/git_analyzer.py)

**Responsabilités**:
1. Analyser un dépôt Git local
2. Extraire métadonnées (commits, contributeurs, hotspots)
3. Calculer métriques qualité
4. Générer profil YAML Hyperion

**Fonctionnalités clés**:
- **Déduplication contributeurs** : Fusionne variantes emails (Gmail, GitHub noreply)
- **Filtrage hotspots** : Ignore binaries, vendored code, generated files
- **Détection automatique** : Langage, CI, license
- **Métriques** : Ratio code/tests/docs, complexité, évolution

**Exemple d'utilisation**:
```python
from hyperion.core import GitAnalyzer

analyzer = GitAnalyzer("/path/to/repo")
profile = analyzer.analyze()

print(profile["git_summary"]["commits"])
print(profile["git_summary"]["hotspots_top10"])
```

---

### 3. **API REST (FastAPI)**

**Fichier**: [src/hyperion/api/main.py](src/hyperion/api/main.py)

**Framework**: FastAPI

**Endpoints**:

| Endpoint | Méthode | Description |
|----------|---------|-------------|
| `/` | GET | Info API |
| `/api/health` | GET | Health check (API + Neo4j + RAG) |
| `/api/repos` | GET | Liste repos analysés |
| `/api/repos/{name}` | GET | Détails repo |
| `/api/repos/{name}/contributors` | GET | Top contributeurs |
| `/api/repos/{name}/hotspots` | GET | Top hotspots |
| `/api/chat` | POST | Chat RAG |
| `/v1/models` | GET | Liste modèles (OpenAI) |
| `/v1/chat/completions` | POST | Chat (OpenAI) |

**Fonctionnalités**:
- CORS pour React dashboard
- Lazy loading RAG engine
- Gestion erreurs HTTP
- Documentation auto (Swagger/ReDoc)

---

### 4. **RAG Engine**

**Fichiers**:
- [src/hyperion/modules/rag/query.py](src/hyperion/modules/rag/query.py) - Moteur de requêtes
- [src/hyperion/modules/rag/ingestion.py](src/hyperion/modules/rag/ingestion.py) - Indexation

**Stack technique**:
- **Vector DB** : Qdrant
- **Embeddings** : BAAI/bge-large-en-v1.5 (1024 dim)
- **LLM** : Ollama + Qwen 2.5 32B
- **Framework** : LangChain

**Workflow RAG**:
```
1. Question utilisateur
       ↓
2. Embedding question (BGE)
       ↓
3. Recherche similaire Qdrant (top-K=5)
       ↓
4. Récupération contexte (profils Git)
       ↓
5. Prompt LLM (Qwen) + contexte
       ↓
6. Génération réponse + sources
```

**Exemple**:
```python
from hyperion.modules.rag.query import RAGQueryEngine

engine = RAGQueryEngine()
result = engine.chat(
    question="Combien de commits dans requests ?",
    repo="requests"
)

print(result["answer"])
print(result["sources"])
```

---

### 5. **Configuration Centralisée**

**Fichier**: [src/hyperion/config.py](src/hyperion/config.py)

**Responsabilités**:
- Chemins projet (PROJECT_ROOT, DATA_DIR, etc.)
- Configuration Neo4j (URI, credentials)
- Configuration Qdrant (host, port, collection)
- Chargement filtres hotspots

**Variables d'environnement** (.env):
```bash
# Neo4j
NEO4J_URI=bolt://localhost:7687
NEO4J_USER=neo4j
NEO4J_PASSWORD=password
NEO4J_DATABASE=neo4j

# Qdrant
QDRANT_HOST=localhost
QDRANT_PORT=6333
QDRANT_COLLECTION=hyperion_profiles

# Embeddings
EMBEDDING_MODEL=BAAI/bge-large-en-v1.5
EMBEDDING_DEVICE=cuda

# LLM
OLLAMA_MODEL=qwen2.5:32b
OLLAMA_BASE_URL=http://localhost:11434
```

---

## 🔄 Flux de Données

### Workflow Complet

```
┌─────────────────────────────────────────────────────────────┐
│  1. ANALYSE GIT                                             │
└─────────────────────────────────────────────────────────────┘
   hyperion profile /path/to/repo
              ↓
   GitAnalyzer.analyze()
              ↓
   data/repositories/repo/profile.yaml

┌─────────────────────────────────────────────────────────────┐
│  2. INDEXATION RAG                                          │
└─────────────────────────────────────────────────────────────┘
   RAGIngester.ingest_profile(profile.yaml)
              ↓
   Chunking (sections YAML)
              ↓
   Embeddings BGE (1024 dim)
              ↓
   Qdrant.upsert(vectors)

┌─────────────────────────────────────────────────────────────┐
│  3. QUERY RAG                                               │
└─────────────────────────────────────────────────────────────┘
   POST /api/chat {"question": "..."}
              ↓
   RAGQueryEngine.chat()
              ↓
   Qdrant.search(query_embedding, top_k=5)
              ↓
   LLM (Ollama Qwen) + context
              ↓
   {answer, sources, score}
```

---

## 🛠️ Choix Techniques

### Langage & Framework

| Composant | Technologie | Justification |
|-----------|-------------|---------------|
| **Langage** | Python 3.10+ | Écosystème ML/AI, async support |
| **CLI** | Click | Simple, extensible, documentation auto |
| **API** | FastAPI | Async, validation Pydantic, OpenAPI auto |
| **RAG** | LangChain | Abstraction LLM, intégrations multiples |
| **Vector DB** | Qdrant | Performant, local, open source |
| **LLM** | Ollama + Qwen | Privacy, local, pas de coût cloud |
| **Embeddings** | BGE-large | SOTA quality, 1024 dim |
| **Graph DB** | Neo4j | Relations complexes, Cypher query |
| **Templates** | Jinja2 | Standard Python, flexible |

### Architecture Patterns

1. **Repository Pattern** : `GitRepo` encapsule les opérations Git
2. **Lazy Loading** : RAG engine chargé à la demande
3. **Facade Pattern** : CLI simplifie complexité interne
4. **Template Method** : Génération docs via Jinja2
5. **Dependency Injection** : Config injectable

---

## 📊 Diagrammes

### Séquence : Analyse Git

```
┌─────┐          ┌────────────┐          ┌─────────┐          ┌──────┐
│ CLI │          │ GitAnalyzer│          │ GitRepo │          │ YAML │
└──┬──┘          └─────┬──────┘          └────┬────┘          └──┬───┘
   │                   │                      │                  │
   │  profile(path)    │                      │                  │
   ├──────────────────>│                      │                  │
   │                   │  get_commits()       │                  │
   │                   ├─────────────────────>│                  │
   │                   │ <────────────────────┤                  │
   │                   │                      │                  │
   │                   │  get_contributors()  │                  │
   │                   ├─────────────────────>│                  │
   │                   │ <────────────────────┤                  │
   │                   │                      │                  │
   │                   │  _deduplicate()      │                  │
   │                   ├──────────┐           │                  │
   │                   │ <────────┘           │                  │
   │                   │                      │                  │
   │                   │  _calculate_hotspots()                  │
   │                   ├──────────┐           │                  │
   │                   │ <────────┘           │                  │
   │                   │                      │                  │
   │                   │  generate_profile()  │                  │
   │                   ├────────────────────────────────────────>│
   │ <─────────────────┤                      │                  │
   │  profile.yaml     │                      │                  │
```

### Séquence : RAG Query

```
┌────────┐   ┌──────┐   ┌──────────┐   ┌────────┐   ┌──────┐
│ Client │   │ API  │   │ RAGEngine│   │ Qdrant │   │ LLM  │
└───┬────┘   └──┬───┘   └────┬─────┘   └───┬────┘   └──┬───┘
    │           │            │              │           │
    │  POST     │            │              │           │
    │  /chat    │            │              │           │
    ├──────────>│            │              │           │
    │           │  chat()    │              │           │
    │           ├───────────>│              │           │
    │           │            │  embed(q)    │           │
    │           │            ├──────┐       │           │
    │           │            │<─────┘       │           │
    │           │            │  search()    │           │
    │           │            ├─────────────>│           │
    │           │            │ <────────────┤           │
    │           │            │  contexts    │           │
    │           │            │              │           │
    │           │            │  prompt+ctx  │           │
    │           │            ├─────────────────────────>│
    │           │            │ <────────────────────────┤
    │           │            │  answer      │           │
    │           │ <──────────┤              │           │
    │ <─────────┤            │              │           │
    │  {answer, │            │              │           │
    │  sources} │            │              │           │
```

---

## 🚀 Évolution v1.5 → v2.0

### Limitations v1.5

1. **Tests insuffisants** : Coverage ~10%
2. **Pas d'auth API** : Sécurité manquante
3. **RAG mono-source** : Uniquement profils Git
4. **Pas de domain models** : Dictionnaires partout
5. **Config hardcodée** : Ports, chemins

### Objectifs v2.0

1. ✅ **Impact Analysis Engine** : Prédire impacts modifications
2. ✅ **Code Understanding** : Mapper business → code
3. ✅ **Anomaly Detection** : Code smells, patterns bugs
4. ✅ **Multi-source RAG** : Git + Neo4j + Docs
5. ✅ **Domain models** : Classes métier explicites
6. ✅ **Auth & Security** : JWT, rate limiting
7. ✅ **AST parsing** : tree-sitter multi-langage

Voir la [Documentation Legacy](../legacy/) pour les détails des versions précédentes.

---

## 📝 Notes Importantes

### Performance

- **Lazy loading** : RAG engine chargé à la demande
- **Batch processing** : Neo4j ingestion par batches (500 commits, 2000 files)
- **GPU acceleration** : Embeddings sur CUDA si disponible
- **Cache Qdrant** : Collections persistées

### Sécurité

- **Secrets** : Jamais dans Git (.env.local, secrets.yaml ignorés)
- **CORS** : Restreint à localhost pour développement
- **SQL Injection** : Parameterized queries Neo4j
- **Path Traversal** : Validation chemins fichiers

### Scalabilité

- **Horizontal** : API stateless, scalable via load balancer
- **Vertical** : Qdrant supporte millions de vectors
- **Storage** : Profils YAML compressibles (gzip)

---

## 📚 Ressources

- [README.md](../../README.md) - Documentation utilisateur
- [CHANGELOG.md](../../../CHANGELOG.md) - Historique versions
- [CONTRIBUTING.md](../../../CONTRIBUTING.md) - Guide contribution
- [Legacy Documents](../legacy/) - Documents historiques

---

**Dernière mise à jour** : 22 
**Auteur** : Matthieu Ryckman
**Version** : 1.5.0
