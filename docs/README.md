# HYPERION - DOCUMENTATION TECHNIQUE COMPLÈTE

**Version** : 1.1.0  
**Date** : 20 décembre 2025  
**Auteur** : Matthieu Ryckman  
**Type** : Documentation Architecture & Exploitation

---

## 📋 TABLE DES MATIÈRES

1. [Introduction / Contexte](#1-introduction--contexte)
2. [Architecture Fonctionnelle](#2-architecture-fonctionnelle)
3. [Architecture Technique](#3-architecture-technique)
4. [Workflow Détaillé](#4-workflow-détaillé)
5. [Administration & Monitoring](#5-administration--monitoring)
6. [Procédures d'Exploitation](#6-procédures-dexploitation)
7. [Problèmes Connus](#7-problèmes-connus)
8. [Annexes](#8-annexes)

---

## 1. INTRODUCTION / CONTEXTE

### 1.1 Présentation

**Hyperion** est une plateforme locale d'analyse et d'exploration de dépôts Git combinant analyse statistique avancée, indexation sémantique (RAG), graphe de connaissance (Neo4j optionnel) et interface conversationnelle via Open WebUI.

**Objectif** : Créer un socle de connaissance technique local pour comprendre, auditer et explorer du code source à grande échelle, sans dépendance cloud et avec inférence IA 100% locale.

### 1.2 Origine du nom

> **Hyperion (Ὑπερίων)**, Titan primordial de la lumière céleste dans la mythologie grecque.  
> Symbolise la **vision claire**, la **connaissance illuminée** et la **compréhension universelle**.

Dans le contexte du projet : **Hyperion révèle le sens caché des données de code**.

### 1.3 Cas d'usage

| Cas d'usage                | Description                                                  |
| -------------------------- | ------------------------------------------------------------ |
| **Audit de code**          | Identifier hotspots, contributeurs principaux, zones de dette technique |
| **Documentation auto**     | Génération automatique de documentation technique depuis profils Git |
| **Recherche sémantique**   | Questions en langage naturel sur les repositories ("Qui a créé ce projet?") |
| **Analyse comparative**    | Comparer qualité code/tests entre repos                      |
| **Exploration historique** | Comprendre l'évolution d'un projet dans le temps             |

### 1.4 Périmètre

**Inclus** :
- Analyse Git complète (commits, contributeurs, hotspots, métriques)
- Génération de profils YAML structurés
- Indexation sémantique RAG (Qdrant)
- Interface chat conversationnelle (Open WebUI)
- API REST compatible OpenAI
- Dashboard React de visualisation
- Graphe de connaissance Neo4j (optionnel)

**Exclus** :
- Analyse de code statique (AST, linting)
- Exécution de tests
- CI/CD orchestration
- Authentification multi-utilisateurs (single-user local)

### 1.5 Dépendances

#### Matérielles

| Composant | Requis    | Recommandé                  |
| --------- | --------- | --------------------------- |
| CPU       | 8 cores   | 16+ cores                   |
| RAM       | 16 GB     | 32+ GB                      |
| GPU       | Optionnel | NVIDIA 24GB VRAM (RTX 4090) |
| Disque    | 50 GB     | 200+ GB SSD NVMe            |

#### Logicielles

| Dépendance | Version    | Rôle                      |
| ---------- | ---------- | ------------------------- |
| Python     | ≥ 3.10     | Runtime principal         |
| Docker     | ≥ 24.0     | Conteneurisation services |
| Qdrant     | Latest     | Vector store RAG          |
| Ollama     | Latest     | Inférence LLM locale      |
| Neo4j      | 5.x (opt.) | Graphe de connaissance    |
| Fish Shell | 3.x        | Shell recommandé          |

---

## 2. ARCHITECTURE FONCTIONNELLE

### 2.1 Vue d'ensemble

```
┌─────────────────────────────────────────────────────────────┐
│                    UTILISATEUR FINAL                         │
│  (Terminal CLI, Dashboard Web, Open WebUI Chat)             │
└────────────────┬─────────────────────────────────┬──────────┘
                 │                                 │
                 ▼                                 ▼
┌─────────────────────────────┐   ┌──────────────────────────┐
│   HYPERION CLI              │   │   HYPERION API REST      │
│  (Click commands)           │   │   (FastAPI 8 endpoints)  │
│  • profile                  │   │   • /api/repos           │
│  • generate                 │   │   • /api/chat (RAG)      │
│  • ingest                   │   │   • /v1/chat/completions │
│  • info                     │   │   • /v1/models           │
└────────┬────────────────────┘   └───────┬──────────────────┘
         │                                │
         │         ┌──────────────────────┘
         │         │
         ▼         ▼
┌─────────────────────────────────────────────────────────────┐
│                   HYPERION CORE ENGINE                       │
│  ┌─────────────┐  ┌──────────────┐  ┌──────────────────┐   │
│  │ GitAnalyzer │  │ RAGQueryEngine│  │ Neo4jIngester   │   │
│  │  (analyse)  │  │  (recherche)  │  │  (graphe opt.)  │   │
│  └─────────────┘  └──────────────┘  └──────────────────┘   │
└────┬────────────────────┬─────────────────────┬────────────┘
     │                    │                     │
     ▼                    ▼                     ▼
┌──────────┐   ┌─────────────────┐   ┌──────────────────┐
│  Git     │   │  Qdrant         │   │  Neo4j (opt.)   │
│  Repos   │   │  Vector Store   │   │  Graph DB       │
│  Local   │   │  Port: 6333     │   │  Port: 7474     │
└──────────┘   └─────────────────┘   └──────────────────┘
                      │
                      ▼
              ┌────────────────┐
              │  Ollama LLM    │
              │  Qwen 2.5 32B  │
              │  Port: 11434   │
              └────────────────┘
```

### 2.2 Comportement fonctionnel

#### Workflow standard utilisateur

1. **Analyse d'un repository**
   ```bash
   hyperion profile /path/to/repo
   ```
   → Génère `data/repositories/{repo}/profile.yaml`

2. **Génération documentation**
   ```bash
   hyperion generate data/repositories/{repo}/profile.yaml
   ```
   → Génère `docs/generated/{repo}/index.md` + `registre.md`

3. **Ingestion RAG** (optionnel)
   ```bash
   python scripts/ingest_rag.py
   ```
   → Indexe chunks sémantiques dans Qdrant

4. **Interaction conversationnelle**
   - Via Open WebUI : http://localhost:3001
   - Via API REST : `POST /api/chat`
   - Via Dashboard : http://localhost:3000

### 2.3 Schémas fonctionnels

#### Pipeline d'analyse Git

```
Dépôt Git Local
      ↓
[GitAnalyzer]
  • Détection métadonnées (nom, remote, branche)
  • Extraction commits (git log --date=iso --pretty)
  • Parsing numstat (git log --numstat)
  • Déduplication contributeurs
  • Calcul hotspots filtrés
  • Stats par extension/répertoire
  • Détection CI/CD et licence
  • Calcul KPIs (ratios, densité)
      ↓
  profile.yaml
  (structure YAML normalisée)
```

#### Pipeline RAG (Retrieval-Augmented Generation)

```
profile.yaml
      ↓
[RAGIngester]
  • Découpage en chunks sémantiques
    - Overview (métadonnées)
    - Métriques qualité
    - Contributeurs (batch 5)
    - Hotspots (batch 5)
    - Extensions
  • Génération embeddings (BGE-large GPU)
  • Upload Qdrant avec métadonnées
      ↓
  Qdrant Collection
  (hyperion_repos)
      ↓
[RAGQueryEngine]
  • Question → embedding
  • Recherche top-k similaires
  • Assembly contexte
  • Prompt LLM Ollama
  • Réponse + sources citées
```

---

## 3. ARCHITECTURE TECHNIQUE

### 3.1 Composants

#### Hyperion Core (Python)

| Module                   | Fichiers                                | Responsabilité                           |
| ------------------------ | --------------------------------------- | ---------------------------------------- |
| **core**                 | `git_analyzer.py`                       | Analyse Git complète, génération profils |
| **api**                  | `main.py`, `openai_compat.py`           | API REST FastAPI, compatibilité OpenAI   |
| **cli**                  | `main.py`                               | Interface ligne de commande Click        |
| **modules.rag**          | `ingestion.py`, `query.py`, `config.py` | Système RAG complet                      |
| **modules.integrations** | `neo4j_ingester.py`                     | Ingestion graphe Neo4j                   |
| **modules.generators**   | `markdown_generator.py`                 | Génération docs Markdown                 |
| **utils**                | `git_utils.py`                          | Wrappers Git, parsing                    |

#### Stack externe

| Service        | Image/Version                      | Port      | Rôle                               |
| -------------- | ---------------------------------- | --------- | ---------------------------------- |
| **Qdrant**     | qdrant/qdrant:latest               | 6333      | Vector store, recherche sémantique |
| **Ollama**     | ollama/ollama:latest               | 11434     | Inférence LLM locale               |
| **Neo4j**      | neo4j:5.x                          | 7474/7687 | Graphe de connaissance (optionnel) |
| **Open WebUI** | ghcr.io/open-webui/open-webui:main | 3001      | Interface chat                     |

### 3.2 Flux de données

#### Format de données : profile.yaml

```yaml
service: requests
owner:
  team: "À remplir"
  contacts: ["https://github.com/psf/requests"]
repositories:
  - name: requests
    url: https://github.com/psf/requests
    main_language: python
    default_branch: main
    license: Apache-2.0
tech:
  runtime: python3
  framework: none
  ci: GitHub Actions
git_summary:
  commits: 6379
  first_commit: "2011-02-13"
  last_commit: "2024-12-18"
  contributors: 805
  recent_commits_90d: 42
  hotspots_top10:
    - path: requests/models.py
      changes: 11079
  contributors_top10:
    - name: Kenneth Reitz
      email: me@kennethreitz.org
      commits: 3148
  by_extension:
    - ext: .py
      files: 99
      changes: 63769
  directories_top:
    - dir: requests
      changes: 38075
metrics:
  evolution_years: 13
  avg_commits_per_year: 490.7
  avg_changes_per_hotspot: 4707.9
  changes_ratio:
    code_py: 44.3
    tests: 18.2
    docs: 19.0
  py_changes_per_file_avg: 644.1
```

### 3.3 Protocoles et ports

| Service               | Protocole | Port  | Endpoint         | Authentification |
| --------------------- | --------- | ----- | ---------------- | ---------------- |
| Hyperion API          | HTTP REST | 8000  | /api/*           | Aucune (local)   |
| Hyperion API (OpenAI) | HTTP REST | 8000  | /v1/*            | Aucune           |
| Qdrant                | HTTP REST | 6333  | /                | Aucune           |
| Ollama                | HTTP REST | 11434 | /api/*           | Aucune           |
| Neo4j Browser         | HTTP      | 7474  | /                | neo4j/password   |
| Neo4j Bolt            | Bolt      | 7687  | bolt://localhost | neo4j/password   |
| Open WebUI            | HTTP      | 3001  | /                | Créer compte     |
| Dashboard React       | HTTP      | 3000  | /                | Aucune           |

### 3.4 Configuration

#### Variables d'environnement (.env)

```bash
# === Neo4j ===
NEO4J_URI=bolt://localhost:7687
NEO4J_USER=neo4j
NEO4J_PASSWORD=your_password
NEO4J_DATABASE=hyperion

# === RAG Configuration ===
QDRANT_HOST=localhost
QDRANT_PORT=6333
QDRANT_COLLECTION=hyperion_repos

# Embeddings
EMBEDDING_MODEL=BAAI/bge-large-en-v1.5
EMBEDDING_DEVICE=cuda  # ou cpu
EMBEDDING_DIM=1024

# LLM Ollama
OLLAMA_BASE_URL=http://localhost:11434
OLLAMA_MODEL=qwen2.5:32b
LLM_TEMPERATURE=0.1
LLM_MAX_TOKENS=2048
LLM_TOP_K=5

# Chunk configuration
CHUNK_SIZE=512
CHUNK_OVERLAP=50

# === Batch sizes ===
BATCH_SIZE_COMMITS=500
BATCH_SIZE_FILES=2000
```

### 3.5 Arborescence détaillée des fichiers

```
Hyperion/
├── .env                          # Configuration locale
├── .env.example                  # Template configuration
├── .gitignore
├── README.md
├── CHANGELOG.md
├── CONTRIBUTING.md
├── LICENSE
├── requirements.txt              # Dépendances Python
├── setup.py                      # Installation package
│
├── config/
│   └── filters.yaml              # Filtres hotspots (extensions, prefixes)
│
├── data/
│   └── repositories/             # Profils Git analysés
│       └── {repo_name}/
│           ├── profile.yaml      # Profil structuré
│           └── profile.json      # Debug JSON
│
├── docs/
│   ├── generated/                # Documentation auto-générée
│   │   └── {repo_name}/
│   │       ├── index.md
│   │       └── registre.md
│   ├── status/                   # Fichiers status projet
│   │   ├── ALL_DONE.md
│   │   ├── API_DONE.md
│   │   ├── DASHBOARD_DONE.md
│   │   └── RAG_DONE.md
│   ├── architecture/
│   │   └── architecture.md
│   ├── guides/
│   └── api/
│
├── frontend/
│   ├── index.html                # Dashboard React (standalone)
│   └── README.md
│
├── src/hyperion/                 # Code source (structure moderne)
│   ├── __init__.py
│   ├── __version__.py
│   ├── config.py                 # Configuration centralisée
│   │
│   ├── api/                      # API REST
│   │   ├── main.py               # FastAPI app
│   │   ├── openai_compat.py      # Endpoints OpenAI-compatible
│   │   └── README.md
│   │
│   ├── cli/                      # Interface CLI
│   │   └── main.py               # Commandes Click
│   │
│   ├── core/                     # Logique métier
│   │   ├── git_analyzer.py       # Analyseur Git principal
│   │   └── README.md
│   │
│   ├── modules/
│   │   ├── rag/                  # Module RAG
│   │   │   ├── config.py         # Config RAG
│   │   │   ├── ingestion.py      # RAGIngester
│   │   │   └── query.py          # RAGQueryEngine
│   │   ├── generators/
│   │   │   └── markdown_generator.py
│   │   ├── integrations/
│   │   │   └── neo4j_ingester.py
│   │   └── models/
│   │
│   └── utils/
│       ├── git_utils.py          # Wrappers Git
│       └── README.md
│
├── scripts/                      # Scripts utilitaires
│   ├── deploy/
│   │   └── hyperion_master.sh    # Orchestrateur principal
│   ├── dev/
│   │   ├── run_api.py
│   │   └── run_dashboard.py
│   ├── setup/
│   │   └── setup_hyperion.sh     # Installation complète
│   ├── maintenance/
│   ├── ingest_rag.py             # Ingestion RAG
│   ├── test_rag.py               # Test RAG interactif
│   ├── MASTER_SCRIPT.md
│   └── SETUP_ULTIMATE.md
│
├── templates/
│   └── markdown/
│       ├── index.md.j2
│       └── registre.md.j2
│
├── tests/
│   ├── unit/
│   ├── integration/
│   └── e2e/
│
├── logs/                         # Logs services
└── venv/                         # Environnement virtuel Python
```

---

## 4. WORKFLOW DÉTAILLÉ

### 4.1 Installation initiale

#### Étape 1 : Prérequis système

```bash
# Vérifier versions
python --version          # ≥ 3.10
docker --version          # ≥ 24.0
nvidia-smi                # GPU optionnel

# Installer Fish shell (recommandé)
sudo pacman -S fish       # Manjaro/Arch
```

#### Étape 2 : Clonage et setup

```bash
# Cloner le projet
git clone https://github.com/Ryckmat/Hyperion.git
cd Hyperion

# Copier configuration
cp .env.example .env
# Éditer .env avec vos valeurs (mot de passe Neo4j, etc.)

# Installation Python
pip install -e . --break-system-packages

# Vérifier installation
hyperion --version
hyperion info
```

#### Étape 3 : Lancement services (mode automatique)

```bash
# Script d'installation complète
./scripts/setup/setup_hyperion.sh

# Ou lancement orchestré
./scripts/deploy/hyperion_master.sh
```

Le script `hyperion_master.sh` propose un menu interactif :
- Vérifier services (Docker, Qdrant, Ollama, Neo4j)
- Lancer dashboard React
- Lancer Open WebUI
- Ingestion RAG
- Génération documentation

#### Étape 4 : Vérification santé

```bash
# Health check API
curl http://localhost:8000/api/health

# Health check Qdrant
curl http://localhost:6333/

# Health check Ollama
curl http://localhost:11434/api/tags

# Dashboard
firefox http://localhost:3000

# Open WebUI
firefox http://localhost:3001
```

### 4.2 Workflow d'analyse d'un repository

#### Scénario : Analyser le repo "requests"

```bash
# 1. Profiler le repository
hyperion profile /home/kortazo/Documents/requests

# Output attendu :
# ================================================================================
# 🚀 HYPERION FULL WORKFLOW
# ================================================================================
# 
# 📁 Repository : /home/kortazo/Documents/requests
# 
# ⏳ Analyse en cours de requests...
# ✅ Analyse terminée !
#    • Repo          : requests
#    • Commits       : 6,377
#    • Contributeurs : 805
#    • Hotspots      : 10
# 
# 💾 Profil YAML : data/repositories/requests/profile.yaml

# 2. Générer documentation
hyperion generate data/repositories/requests/profile.yaml

# Output :
# ✅ Documentation générée :
#    • docs/generated/requests/index.md
#    • docs/generated/requests/registre.md

# 3. Ingérer dans Qdrant (RAG)
python scripts/ingest_rag.py

# Sélectionner "requests" dans le menu
# ✅ 7 chunks ingérés

# 4. Tester via API
curl -X POST http://localhost:8000/api/chat \
  -H "Content-Type: application/json" \
  -d '{
    "question": "Combien de commits dans requests ?",
    "repo": "requests"
  }'

# 5. Tester via Open WebUI
# → Ouvrir http://localhost:3001
# → Sélectionner modèle "hyperion-rag"
# → Poser question : "Qui est le contributeur principal ?"
```

### 4.3 Gestion des erreurs

#### Erreur : Port déjà utilisé

**Symptôme** : `Error: bind: address already in use`

**Solution** :
```bash
# Identifier processus
sudo lsof -i :8000

# Tuer processus
kill -9 <PID>

# Ou changer port dans .env
HYPERION_API_PORT=8001
```

#### Erreur : Qdrant non accessible

**Symptôme** : `Connection refused 6333`

**Solution** :
```bash
# Redémarrer container Qdrant
docker restart qdrant

# Vérifier logs
docker logs qdrant

# Health check
curl http://localhost:6333/
```

#### Erreur : Ollama modèle introuvable

**Symptôme** : `model 'qwen2.5:32b' not found`

**Solution** :
```bash
# Lister modèles installés
ollama list

# Télécharger modèle manquant
ollama pull qwen2.5:32b

# Vérifier
ollama list | grep qwen2.5
```

### 4.4 Règles métier

#### Déduplication contributeurs

**Algorithme** :

1. **Normalisation emails** :
   - Gmail : suppression `.` dans local part (`john.smith@gmail.com` → `johnsmith@gmail.com`)
   - GitHub noreply : suppression `+tag` (`user+tag@users.noreply.github.com` → `user@users.noreply.github.com`)

2. **Normalisation noms** :
   - Titre case (`JOHN SMITH` → `John Smith`)
   - Suppression `[bot]` suffix
   - Trim espaces multiples

3. **Fusion par nom canonique** :
   - Clé unique : nom normalisé lowercase
   - Agrégation commits
   - Conservation premier email valide

**Exemple** :
```
Input:
  - "John Smith <john.smith@gmail.com>" (50 commits)
  - "john smith <johnsmith@gmail.com>" (30 commits)
  - "John Smith [bot] <john.smith+bot@users.noreply.github.com>" (20 commits)

Output:
  - "John Smith <johnsmith@gmail.com>" (100 commits)
```

#### Filtrage hotspots

**Critères d'exclusion** :

1. **Extensions binaires** : `.png`, `.jpg`, `.pdf`, `.exe`, `.dll`, `.so`, etc.
2. **Préfixes vendored** : `node_modules/`, `vendor/`, `ext/`, `site-packages/`, etc.
3. **Fichiers bruits** : `README.md`, `CHANGELOG`, `HISTORY.rst`, etc.
4. **Build artifacts** : `.min.js`, `.map`, `dist/`, `.lock`, etc.

**Configuration** : `config/filters.yaml`

```yaml
ignore_extensions:
  - .png
  - .jpg
  - .pdf
  - .exe
ignore_prefixes:
  - node_modules/
  - vendor/
  - ext/
ignore_files:
  - README.md
  - CHANGELOG
```

#### Calcul métriques qualité

**Ratios code/tests/docs** :

```python
# Code Python
code_changes = sum(
    changes for path, changes in numstat
    if path.startswith(('src/', 'lib/', f'{service}/'))
    and path.endswith('.py')
)

# Tests
tests_changes = sum(
    changes for path, changes in numstat
    if path.startswith(('tests/', 'test/'))
)

# Docs
docs_changes = sum(
    changes for path, changes in numstat
    if path.startswith('docs/')
    or path.endswith(('.md', '.rst', '.adoc'))
)

ratio_code = 100 * code_changes / total_changes
ratio_tests = 100 * tests_changes / total_changes
ratio_docs = 100 * docs_changes / total_changes
```

---

## 5. ADMINISTRATION & MONITORING

### 5.1 Logs

#### Localisation logs

| Service      | Chemin                   | Format                |
| ------------ | ------------------------ | --------------------- |
| Hyperion API | `logs/api.log`           | Texte structuré       |
| Installation | `install.log`            | Texte avec timestamps |
| Qdrant       | `docker logs qdrant`     | JSON structuré        |
| Ollama       | `docker logs ollama`     | Texte                 |
| Neo4j        | `docker logs neo4j`      | Texte                 |
| Open WebUI   | `docker logs open-webui` | JSON                  |

#### Consultation logs temps réel

```bash
# Logs API
tail -f logs/api.log

# Logs Qdrant
docker logs -f qdrant

# Logs Ollama
docker logs -f ollama --tail 100

# Logs installation
tail -f install.log
```

### 5.2 Dashboards et sondes

#### Qdrant Dashboard

**URL** : http://localhost:6333/dashboard

**Métriques disponibles** :

- Collections count
- Points count par collection
- Vectors dimension
- Disk usage
- Memory usage

#### Neo4j Browser (si activé)

**URL** : http://localhost:7474

**Requêtes utiles** :

```cypher
// Compter nœuds par type
MATCH (n)
RETURN labels(n) AS type, count(n) AS count
ORDER BY count DESC

// Repos indexés
MATCH (r:Repo)
RETURN r.name, r.commits, r.contributors

// Top contributeurs global
MATCH (c:Contributor)
RETURN c.name, c.commits
ORDER BY c.commits DESC
LIMIT 20
```

#### Hyperion API Metrics

**Endpoint** : `GET /api/health`

**Réponse** :
```json
{
  "status": "healthy",
  "api": "ok",
  "neo4j": "ok",
  "rag": "ok"
}
```

### 5.3 Commandes administration

#### Gestion services Docker

```bash
# Lister containers actifs
docker ps

# Arrêter tous services Hyperion
docker stop qdrant ollama neo4j open-webui

# Redémarrer service spécifique
docker restart qdrant

# Supprimer container (garde données)
docker rm -f qdrant

# Supprimer container + volumes (⚠️ perte données)
docker rm -f -v qdrant
```

#### Gestion Python venv

```bash
# Activer venv
source venv/bin/activate

# Désactiver
deactivate

# Réinstaller Hyperion
pip install -e . --break-system-packages --force-reinstall

# Mettre à jour dépendances
pip install -r requirements.txt --upgrade
```

#### Nettoyage données

```bash
# Supprimer profils analysés
rm -rf data/repositories/*

# Supprimer docs générées
rm -rf docs/generated/*

# Supprimer logs
rm -f logs/*.log install.log api.log

# Supprimer collection Qdrant
curl -X DELETE http://localhost:6333/collections/hyperion_repos
```

---

## 6. PROCÉDURES D'EXPLOITATION

### 6.1 Démarrage

#### Mode manuel (services indépendants)

```bash
# Terminal 1 : Qdrant
docker run -d --name qdrant \
  -p 6333:6333 \
  -v qdrant_storage:/qdrant/storage \
  qdrant/qdrant:latest

# Terminal 2 : Ollama
docker run -d --name ollama \
  -p 11434:11434 \
  -v ollama:/root/.ollama \
  --gpus all \
  ollama/ollama:latest

# Télécharger modèle
docker exec -it ollama ollama pull qwen2.5:32b

# Terminal 3 : API Hyperion
cd /home/kortazo/Documents/Hyperion
source venv/bin/activate
python scripts/dev/run_api.py

# Terminal 4 : Dashboard
python scripts/dev/run_dashboard.py

# Terminal 5 : Open WebUI
docker run -d --name open-webui \
  -p 3001:8080 \
  -v open-webui:/app/backend/data \
  --add-host=host.docker.internal:host-gateway \
  ghcr.io/open-webui/open-webui:main
```

#### Mode orchestré (recommandé)

```bash
cd /home/kortazo/Documents/Hyperion
./scripts/deploy/hyperion_master.sh
```

**Menu interactif** :
```
============================================================
🚀 HYPERION MASTER - Orchestration complète
============================================================

Options disponibles :

[1] Vérifier services (Docker, Qdrant, Ollama, Neo4j)
[2] Lancer dashboard React
[3] Lancer Open WebUI
[4] Ingestion RAG
[5] Génération documentation
[6] Tout arrêter (Ctrl+C)

Choix :
```

### 6.2 Arrêt

#### Arrêt propre via script

```bash
# Ctrl+C dans terminal hyperion_master.sh
# → Arrête automatiquement API + Frontend

# Arrêt containers Docker
docker stop qdrant ollama neo4j open-webui
```

#### Arrêt forcé

```bash
# Tuer tous processus Python Hyperion
pkill -f hyperion

# Arrêter tous containers
docker stop $(docker ps -q)
```

### 6.3 Purge complète

⚠️ **ATTENTION : Perte de toutes les données**

```bash
# 1. Arrêter services
docker stop qdrant ollama neo4j open-webui

# 2. Supprimer containers + volumes
docker rm -f -v qdrant ollama neo4j open-webui

# 3. Supprimer volumes Docker
docker volume rm qdrant_storage ollama neo4j_data open-webui

# 4. Supprimer données locales
cd /home/kortazo/Documents/Hyperion
rm -rf data/repositories/*
rm -rf docs/generated/*
rm -rf logs/*
rm -f *.log

# 5. Réinstaller
./scripts/setup/setup_hyperion.sh
```

### 6.4 Tests

#### Test analyse Git

```bash
# Test profil requests
hyperion profile /home/kortazo/Documents/requests

# Vérifier output
cat data/repositories/requests/profile.yaml
```

#### Test génération docs

```bash
hyperion generate data/repositories/requests/profile.yaml

# Vérifier output
ls -lh docs/generated/requests/
```

#### Test RAG ingestion

```bash
python scripts/ingest_rag.py

# Sélectionner repo
# Vérifier output : "✅ 7 chunks ingérés"
```

#### Test RAG query

```bash
# Terminal interactif
python scripts/test_rag.py

# Ou API
curl -X POST http://localhost:8000/api/chat \
  -H "Content-Type: application/json" \
  -d '{"question": "Qui est le contributeur principal ?"}'
```

#### Test santé API

```bash
# Health check
curl http://localhost:8000/api/health | jq

# Liste repos
curl http://localhost:8000/api/repos | jq

# Détails repo
curl http://localhost:8000/api/repos/requests | jq
```

### 6.5 Escalade

#### Problème : API ne démarre pas

**Diagnostic** :
```bash
# Vérifier logs
tail -50 logs/api.log

# Vérifier processus
ps aux | grep hyperion

# Vérifier port
sudo lsof -i :8000
```

**Solution** :
1. Tuer processus existant : `kill -9 <PID>`
2. Vérifier .env : `cat .env`
3. Réinstaller : `pip install -e . --force-reinstall`
4. Relancer : `python scripts/dev/run_api.py`

#### Problème : RAG ne répond pas

**Diagnostic** :
```bash
# Vérifier Qdrant
curl http://localhost:6333/

# Vérifier Ollama
curl http://localhost:11434/api/tags

# Vérifier collection
curl http://localhost:6333/collections/hyperion_repos
```

**Solution** :
1. Redémarrer Qdrant : `docker restart qdrant`
2. Vérifier modèle Ollama : `docker exec ollama ollama list`
3. Réingérer données : `python scripts/ingest_rag.py`

#### Problème : GPU non détecté

**Diagnostic** :
```bash
# Vérifier NVIDIA
nvidia-smi

# Vérifier PyTorch CUDA
python -c "import torch; print(torch.cuda.is_available())"
```

**Solution** :
1. Réinstaller PyTorch CUDA : `pip install torch --index-url https://download.pytorch.org/whl/cu121`
2. Modifier .env : `EMBEDDING_DEVICE=cpu`

---

## 7. PROBLÈMES CONNUS

### 7.1 Docker networking (Manjaro Linux)

**Symptôme** : Open WebUI ne peut pas accéder à `http://localhost:8000`

**Cause** : Isolation réseau Docker sur Manjaro

**Solution** :
```bash
# Utiliser host.docker.internal au lieu de localhost
# Dans config Open WebUI (admin panel)
OPENAI_API_BASE_URL=http://host.docker.internal:8000/v1

# Ou ajouter au docker run
--add-host=host.docker.internal:host-gateway
```

**Workaround permanent** : Script `hyperion_master.sh` détecte automatiquement l'IP hôte

### 7.2 Qdrant API v1.7+ breaking changes

**Symptôme** : `AttributeError: 'QdrantClient' object has no attribute 'search'`

**Cause** : API Qdrant changée en v1.7 (`search()` → `query_points()`)

**Solution** : Code corrigé dans `hyperion/modules/rag/query.py`

```python
# ❌ Ancien (< v1.7)
results = client.search(
    collection_name="hyperion_repos",
    query_vector=embedding,
    limit=5
)

# ✅ Nouveau (≥ v1.7)
results = client.query_points(
    collection_name="hyperion_repos",
    query=embedding.tolist(),
    limit=5
).points
```

### 7.3 Embeddings BGE-large téléchargement

**Symptôme** : Première ingestion très lente (~10 min)

**Cause** : Téléchargement modèle BGE-large (1.34 GB)

**Solution** : Normal, téléchargement une seule fois. Cache dans `~/.cache/huggingface/`

**Accélération** :
```bash
# Pré-télécharger
python -c "from sentence_transformers import SentenceTransformer; SentenceTransformer('BAAI/bge-large-en-v1.5')"
```

### 7.4 Ollama modèle 32B mémoire

**Symptôme** : OOM (Out of Memory) avec Qwen 2.5 32B

**Cause** : Modèle 32B requiert ~20GB RAM + ~20GB VRAM

**Solution** :
```bash
# Option 1 : Utiliser modèle plus petit
ollama pull qwen2.5:14b  # ~10GB

# Modifier .env
OLLAMA_MODEL=qwen2.5:14b

# Option 2 : Augmenter swap (RAM insuffisante)
sudo fallocate -l 32G /swapfile
sudo chmod 600 /swapfile
sudo mkswap /swapfile
sudo swapon /swapfile

# Option 3 : CPU-only (lent mais fonctionne)
# Pas de --gpus all dans docker run
```

### 7.5 Neo4j mot de passe par défaut

**Symptôme** : Connexion Neo4j refusée

**Cause** : Mot de passe par défaut non défini

**Solution** :
```bash
# Premier démarrage Neo4j
docker run -d --name neo4j \
  -p 7474:7474 -p 7687:7687 \
  -e NEO4J_AUTH=neo4j/your_password \
  neo4j:latest

# Ou modifier .env
NEO4J_PASSWORD=your_password

# Puis dans Neo4j Browser (http://localhost:7474)
# Username: neo4j
# Password: your_password
```

---

## 8. ANNEXES

### 8.1 Glossaire

| Terme            | Définition                                                   |
| ---------------- | ------------------------------------------------------------ |
| **RAG**          | Retrieval-Augmented Generation - Technique combinant recherche documentaire et génération LLM |
| **Embedding**    | Représentation vectorielle dense d'un texte dans un espace sémantique |
| **Chunk**        | Fragment de texte découpé pour indexation sémantique         |
| **Hotspot**      | Fichier fréquemment modifié, indicateur de zone critique     |
| **Numstat**      | Statistiques Git (additions/suppressions par fichier)        |
| **LLM**          | Large Language Model - Modèle de langage de grande taille    |
| **Vector Store** | Base de données optimisée pour recherche de similarité vectorielle |
| **Graph DB**     | Base de données orientée graphe (nœuds et relations)         |

### 8.2 Tableaux de référence

#### Endpoints API REST

| Méthode | Endpoint                         | Description                 | Réponse                              |
| ------- | -------------------------------- | --------------------------- | ------------------------------------ |
| GET     | `/`                              | Info API                    | `{name, version, status, endpoints}` |
| GET     | `/api/health`                    | Health check                | `{status, api, neo4j, rag}`          |
| GET     | `/api/repos`                     | Liste repos                 | `{repos: [...], count}`              |
| GET     | `/api/repos/{name}`              | Détails repo                | `{profile YAML complet}`             |
| GET     | `/api/repos/{name}/contributors` | Top contributeurs           | `{repo, contributors, count}`        |
| GET     | `/api/repos/{name}/hotspots`     | Top hotspots                | `{repo, hotspots, count}`            |
| GET     | `/api/repos/{name}/metrics`      | Métriques                   | `{repo, metrics}`                    |
| POST    | `/api/chat`                      | Chat RAG                    | `{answer, sources, question}`        |
| GET     | `/v1/models`                     | Liste modèles OpenAI-compat | `{data: [{id: "hyperion-rag"}]}`     |
| POST    | `/v1/chat/completions`           | Chat OpenAI-compat          | `{choices: [{message}]}`             |

#### Commandes CLI

| Commande             | Arguments        | Description                   |
| -------------------- | ---------------- | ----------------------------- |
| `hyperion --version` | -                | Affiche version               |
| `hyperion info`      | -                | Affiche configuration         |
| `hyperion profile`   | `<repo_path>`    | Analyse repository Git        |
| `hyperion generate`  | `<profile.yaml>` | Génère documentation Markdown |
| `hyperion ingest`    | `<profile.yaml>` | Ingère dans Neo4j             |

#### Configuration RAG

| Paramètre           | Valeur par défaut      | Description             |
| ------------------- | ---------------------- | ----------------------- |
| `QDRANT_HOST`       | localhost              | Hôte Qdrant             |
| `QDRANT_PORT`       | 6333                   | Port Qdrant             |
| `QDRANT_COLLECTION` | hyperion_repos         | Nom collection          |
| `EMBEDDING_MODEL`   | BAAI/bge-large-en-v1.5 | Modèle embeddings       |
| `EMBEDDING_DEVICE`  | cuda                   | Device (cuda/cpu)       |
| `EMBEDDING_DIM`     | 1024                   | Dimension vecteurs      |
| `OLLAMA_MODEL`      | qwen2.5:32b            | Modèle LLM              |
| `LLM_TEMPERATURE`   | 0.1                    | Température génération  |
| `LLM_MAX_TOKENS`    | 2048                   | Tokens max réponse      |
| `LLM_TOP_K`         | 5                      | Nombre chunks récupérés |
| `CHUNK_SIZE`        | 512                    | Taille chunks           |
| `CHUNK_OVERLAP`     | 50                     | Overlap chunks          |

### 8.3 Exemples de requêtes RAG

#### Via API REST

```bash
# Question factuelle
curl -X POST http://localhost:8000/api/chat \
  -H "Content-Type: application/json" \
  -d '{
    "question": "Combien de commits dans requests ?",
    "repo": "requests"
  }' | jq

# Réponse :
# {
#   "answer": "Le repository requests contient 6 379 commits...",
#   "sources": [
#     {
#       "repo": "requests",
#       "section": "overview",
#       "score": 0.89,
#       "text": "Repository: requests\nTotal commits: 6379..."
#     }
#   ],
#   "question": "Combien de commits dans requests ?"
# }

# Analyse comparative
curl -X POST http://localhost:8000/api/chat \
  -H "Content-Type: application/json" \
  -d '{
    "question": "Compare la qualité code/tests de requests",
    "repo": "requests"
  }' | jq

# Question ouverte
curl -X POST http://localhost:8000/api/chat \
  -H "Content-Type: application/json" \
  -d '{
    "question": "Quels fichiers devraient être refactorés ?"
  }' | jq
```

#### Via Open WebUI

```
User: Qui est le contributeur principal de requests ?

Hyperion: D'après les données analysées, le contributeur principal 
du repository requests est Kenneth Reitz avec 3 148 commits, 
représentant environ 49% de l'activité totale du projet.

Sources :
- requests/contributors (score: 0.92)
- requests/overview (score: 0.87)
```

### 8.4 Diagrammes ASCII

#### Flux d'analyse complète

```
┌─────────────────────────────────────────────────────────────┐
│                    ANALYSE COMPLÈTE REPO                     │
└─────────────────────┬───────────────────────────────────────┘
                      │
                      ▼
        ┌─────────────────────────┐
        │  1. Git Clone/Local     │
        │  /path/to/repo          │
        └────────┬────────────────┘
                 │
                 ▼
        ┌─────────────────────────┐
        │  2. GitAnalyzer         │
        │  • Commits extraction   │
        │  • Contributors dedup   │
        │  • Hotspots calc        │
        │  • Metrics compute      │
        └────────┬────────────────┘
                 │
                 ▼
        ┌─────────────────────────┐
        │  3. profile.yaml        │
        │  data/repositories/     │
        │  {repo}/profile.yaml    │
        └────┬────────────┬───────┘
             │            │
     ┌───────┘            └───────┐
     ▼                            ▼
┌──────────────┐         ┌──────────────────┐
│ 4a. Markdown │         │ 4b. RAG Ingest   │
│ Generator    │         │ • Chunking       │
│              │         │ • Embeddings     │
│ → index.md   │         │ • Qdrant upload  │
│ → registre.md│         └────────┬─────────┘
└──────────────┘                  │
                                  ▼
                         ┌──────────────────┐
                         │ 5. Query Ready   │
                         │ • Open WebUI     │
                         │ • API /api/chat  │
                         │ • Dashboard      │
                         └──────────────────┘
```

#### Architecture systèmes

```
┌────────────────────────────────────────────────────────────────┐
│                        USER LAYER                               │
│  ┌──────────┐  ┌──────────┐  ┌──────────┐  ┌──────────┐      │
│  │  CLI     │  │Dashboard │  │Open WebUI│  │  API     │      │
│  │  Fish    │  │  React   │  │  Chat    │  │  REST    │      │
│  └────┬─────┘  └────┬─────┘  └────┬─────┘  └────┬─────┘      │
└───────┼─────────────┼─────────────┼─────────────┼─────────────┘
        │             │             │             │
        └─────────────┴─────────────┴─────────────┘
                            │
┌───────────────────────────┼────────────────────────────────────┐
│                    APPLICATION LAYER                            │
│                           │                                     │
│  ┌────────────────────────▼──────────────────────────┐         │
│  │         Hyperion Core (Python)                     │         │
│  │  ┌──────────┐ ┌───────────┐ ┌──────────────────┐ │         │
│  │  │   Git    │ │    RAG    │ │   Neo4j (opt.)  │ │         │
│  │  │ Analyzer │ │  Engine   │ │    Ingester     │ │         │
│  │  └──────────┘ └───────────┘ └──────────────────┘ │         │
│  └────────────────────────────────────────────────────┘         │
└───────────────────────────┼────────────────────────────────────┘
                            │
┌───────────────────────────┼────────────────────────────────────┐
│                      DATA LAYER                                 │
│                           │                                     │
│  ┌─────────┐  ┌──────────▼─────┐  ┌─────────────┐            │
│  │  Local  │  │    Qdrant      │  │   Neo4j     │            │
│  │   Git   │  │ Vector Store   │  │  Graph DB   │            │
│  │  Repos  │  │ :6333          │  │ :7474/:7687 │            │
│  └─────────┘  └────────┬───────┘  └─────────────┘            │
│                        │                                        │
│                ┌───────▼─────────┐                             │
│                │     Ollama      │                             │
│                │  LLM Inference  │                             │
│                │     :11434      │                             │
│                └─────────────────┘                             │
└────────────────────────────────────────────────────────────────┘
```

### 8.5 Exemples de données

#### Profile YAML (extrait)

```yaml
service: requests
owner:
  team: "À remplir"
  contacts: ["https://github.com/psf/requests"]
repositories:
  - name: requests
    url: https://github.com/psf/requests
    main_language: python
    default_branch: main
    stars: null
    license: Apache-2.0
tech:
  runtime: python3
  framework: none
  ci: GitHub Actions
git_summary:
  commits: 6379
  first_commit: "2011-02-13"
  last_commit: "2024-12-18"
  contributors: 805
  recent_commits_90d: 42
  hotspots_top10:
    - path: requests/models.py
      changes: 11079
    - path: requests/sessions.py
      changes: 7856
  contributors_top10:
    - name: Kenneth Reitz
      email: me@kennethreitz.org
      commits: 3148
    - name: Cory Benfield
      email: cory@lukasa.co.uk
      commits: 726
  by_extension:
    - ext: .py
      files: 99
      changes: 63769
    - ext: .rst
      files: 46
      changes: 20844
  directories_top:
    - dir: requests
      changes: 38075
    - dir: docs
      changes: 20995
metrics:
  evolution_years: 13
  avg_commits_per_year: 490.7
  avg_changes_per_hotspot: 4707.9
  changes_ratio:
    code_py: 44.3
    tests: 18.2
    docs: 19.0
  py_changes_per_file_avg: 644.1
notes:
  - "Hotspots calculés après filtrage vendored/artefacts"
  - "Contributeurs dédupliqués (noreply, Gmail)"
  - "Licence et CI détectés localement"
```

#### RAG Response JSON

```json
{
  "answer": "Le repository requests a été créé par Kenneth Reitz en février 2011. Kenneth Reitz est le contributeur principal avec 3 148 commits, soit environ 49% de l'activité totale. Le projet est écrit en Python et utilise la licence Apache-2.0.",
  "sources": [
    {
      "repo": "requests",
      "section": "contributors",
      "score": 0.92,
      "text": "Repository: requests\nTop Contributors:\n- Kenneth Reitz (me@kennethreitz.org): 3148 commits..."
    },
    {
      "repo": "requests",
      "section": "overview",
      "score": 0.87,
      "text": "Repository: requests\nLanguage: python\nLicense: Apache-2.0..."
    }
  ],
  "question": "Qui a créé le projet requests ?",
  "repo_filter": "requests"
}
```

---

## 📚 RÉFÉRENCES & LIENS

### Documentation externe

- **FastAPI** : https://fastapi.tiangolo.com/
- **Qdrant** : https://qdrant.tech/documentation/
- **Ollama** : https://github.com/ollama/ollama
- **Neo4j** : https://neo4j.com/docs/
- **LangChain** : https://python.langchain.com/
- **Sentence Transformers** : https://www.sbert.net/

### Repositories

- **Hyperion** : https://github.com/Ryckmat/Hyperion
- **Open WebUI** : https://github.com/open-webui/open-webui

### Support

- **Issues GitHub** : https://github.com/Ryckmat/Hyperion/issues
- **Discussions** : https://github.com/Ryckmat/Hyperion/discussions

---

**FIN DU DOCUMENT**

*Document généré le 20 décembre 2025  
*Projet Hyperion v1.1.0*  
*Auteur : Matthieu Ryckman*