# 🧠 Hyperion

[![CI](https://github.com/Ryckmat/Hyperion/actions/workflows/ci.yml/badge.svg)](https://github.com/Ryckmat/Hyperion/actions/workflows/ci.yml)
[![Python 3.12+](https://img.shields.io/badge/python-3.12+-blue.svg)](https://www.python.org/downloads/)
[![License](https://img.shields.io/badge/license-Apache%202.0-green.svg)](LICENSE)
[![Code style: black](https://img.shields.io/badge/code%20style-black-000000.svg)](https://github.com/psf/black)
[![Ruff](https://img.shields.io/endpoint?url=https://raw.githubusercontent.com/astral-sh/ruff/main/assets/badge/v2.json)](https://github.com/astral-sh/ruff)

**Hyperion v2.7.0 Enterprise Ready** est une plateforme locale d'intelligence pour repositories Git avec infrastructure ML complète, combinant :

* 📊 **Analyse Git avancée** (commits, hotspots, contributeurs, métriques)
* 🤖 **Infrastructure ML Enterprise** (MLflow, Feature Store, Training Pipeline)
* 🧠 **RAG (Retrieval Augmented Generation)** basé sur **Qdrant**
* 🕸️ **Graphe de connaissance** optionnel via **Neo4j**
* 🎯 **Sélection intelligente de modèles** selon vos besoins de performance
* 🔍 **Détection d'anomalies** et analyse d'impact intelligente
* 🤖 **API OpenAI-compatible** (Chat Completions / Models)
* 💬 **Interface conversationnelle** via **Open WebUI**
* 🚀 **Orchestration unifiée** avec configuration dynamique

Hyperion est conçu comme un **socle de connaissance technique local**, orienté compréhension, audit et exploration de code à grande échelle, **prêt pour la production**.

---

## ✨ Fonctionnalités clés

### 🎯 Sélection intelligente de modèles (v2.7.0)

* **4 profils d'usage** adaptés à vos besoins :
  - 🏃‍♂️ **Performance Ultra-Rapide** (<3s) : llama3.2:1b
  - ⚖️ **Équilibre Performance/Qualité** (5-10s) : llama3.1:8b
  - 🧠 **Qualité Premium** (10-30s) : qwen2.5:14b
  - 🚀 **Expert/Recherche** (30s+) : qwen2.5:32b
* **Configuration dynamique** via l'orchestrateur
* **Téléchargement automatique** des modèles
* **Test de performance** intégré

### 🤖 Infrastructure ML Enterprise

* **MLflow Integration** : Tracking automatique et registry de modèles avec versioning sémantique
* **Feature Store** : 35+ features ingénieurées (code quality, team dynamics, business impact, temporal) avec cache intelligent TTL
* **Training Pipeline** : Entraînement automatisé de 4 modèles (RandomForest, XGBoost, IsolationForest, Meta-learner)
* **Data Validator** : Validation structure, qualité, distributions avec détection de data drift
* **Model Registry** : Cycle de vie complet (trained → validated → production → deprecated)

### 🔮 Modèles ML opérationnels

* **RiskPredictor** : Prédiction de risques avec ensemble Random Forest + XGBoost
* **AnomalyDetector** : Détection d'anomalies avec Isolation Forest (contamination 10%)
* **BugPredictor** : Prédiction de bugs sur horizon 30 jours basée sur historique Git
* **ImpactAnalyzer** : Analyse de propagation des changements dans le graphe de code
* **Meta-learner** : Ensemble voting avec LogisticRegression pour agrégation

### 🔍 Analyse Git

* Nombre de commits
* Contributeurs principaux
* Fichiers les plus modifiés (hotspots)
* Historique temporel
* Métriques de qualité

### 🧠 RAG (Qdrant)

* Indexation sémantique des profils Git
* Recherche contextuelle multi-sections
* Réponses enrichies avec **sources**
* Filtrage par repository

### 🕸️ Graphe de connaissance (optionnel)

* Modélisation des repos, commits, fichiers
* Requêtes avancées Neo4j
* Complément du RAG (pas obligatoire)

### 🤖 API REST complète

Hyperion expose une API REST riche avec 3 couches :

**Core API (v1)** :
* `/api/health` - Health check complet (API, Neo4j, RAG)
* `/api/repos` - Gestion repositories analysés
* `/api/chat` - Chat RAG avec sources et métadonnées

**OpenAI-compatible** :
* `/v1/models` - Liste modèles disponibles
* `/v1/chat/completions` - Chat completions standard OpenAI

**API v2 (Code Intelligence)** :
* `/api/v2/repos/{repo}/functions` - Extraction fonctions Python (AST)
* `/api/v2/repos/{repo}/classes` - Extraction classes et méthodes
* `/api/v2/understanding/search` - Recherche sémantique dans le code
* `/api/v2/impact/analyze` - Analyse d'impact des changements
* `/api/v2/anomaly/scan` - Détection anomalies code (complexity, size, duplicates)

👉 Compatible avec Open WebUI, outils RAG et clients OpenAI existants

### 💬 Open WebUI

* Interface chat moderne
* Sélection de modèle (`hyperion-rag`)
* Historique de conversation
* Aucune clé OpenAI requise

### 🚀 Orchestration unifiée

Un seul script pour :

* vérifier les dépendances
* démarrer Qdrant / Ollama
* lancer l'API Hyperion
* lancer Open WebUI
* lancer le dashboard React
* arrêter proprement tous les services (Ctrl+C)

---

## 🗂️ Architecture du projet

```
Hyperion/
├── src/hyperion/          # Code source (structure moderne)
│   ├── core/              # Analyseur Git
│   ├── api/               # FastAPI + OpenAI-compatible
│   ├── cli/               # Interface ligne de commande
│   ├── utils/             # Utilitaires
│   └── modules/           # Modules métier
│       ├── ml/            # Infrastructure ML (MLflow, Feature Store, Training)
│       ├── rag/           # Qdrant, embeddings, query engine
│       ├── generators/    # Générateurs de documentation
│       ├── integrations/  # Neo4j, Git, autres sources
│       ├── impact/        # Analyse d'impact et prédiction de risques
│       ├── anomaly/       # Détection d'anomalies et code smells
│       └── models/        # Modèles de données
│
├── scripts/               # Scripts d'orchestration
│   ├── setup/             # Installation système
│   ├── dev/               # Développement (run_api, run_dashboard)
│   ├── deploy/            # Déploiement (hyperion_master)
│   └── maintenance/       # Maintenance
│
├── frontend/              # Dashboard React
├── data/                  # Profils Git, index RAG
├── templates/             # Templates docs / exports
├── docs/                  # Documentation
│   ├── architecture/      # Designs techniques
│   ├── guides/            # Guides utilisateur
│   └── api/               # Documentation API
├── tests/                 # Tests
│   ├── unit/              # Tests unitaires
│   ├── integration/       # Tests d'intégration
│   └── e2e/               # Tests end-to-end
│
├── requirements.txt
├── setup.py
├── .env.example
└── README.md
```

---

## ⚙️ Prérequis

### Système

* Linux (testé sur Manjaro / Arch)
* Docker
* Python ≥ 3.10
* GPU recommandé (optionnel)

### Services

* 🐳 Docker
* 🤖 Ollama
* 📦 Qdrant (Docker)
* 🕸️ Neo4j (optionnel)

---

## 🚀 Démarrage rapide

### 1️⃣ Cloner le projet

```bash
git clone https://github.com/Ryckmat/Hyperion.git
cd Hyperion
```

### 2️⃣ Installation

```bash
# Installer les dépendances Python
pip install -e . --break-system-packages

# Vérifier l'installation
hyperion --version
hyperion info
```

### 3️⃣ Lancer Hyperion avec sélection de modèle

```bash
# Démarrage avec configuration de modèle
./scripts/deploy/hyperion_master.sh --setup-model

# Ou démarrage automatique
./scripts/deploy/hyperion_master.sh --auto
```

Le script te guide pour :

* **configurer ton modèle LLM** selon tes besoins
* vérifier les services
* lancer le dashboard
* lancer Open WebUI
* choisir ce que tu veux activer

### 4️⃣ Profils de modèles disponibles

🏃‍♂️ **Ultra-Rapide** (option 1) : Réponses <3s - **llama3.2:1b**
⚖️ **Équilibre** (option 2) : Performance/Qualité - **llama3.1:8b** *(recommandé)*
🧠 **Premium** (option 3) : Analyses approfondies - **qwen2.5:14b**
🚀 **Expert** (option 4) : Recherche & audits - **qwen2.5:32b**

👉 **Ctrl+C** arrête proprement tous les services lancés.

---

## 💬 Utilisation via Open WebUI

Une fois lancé :

* Open WebUI : [http://localhost:3001](http://localhost:3001)
* Dashboard : [http://localhost:3000](http://localhost:3000)
* API Hyperion : [http://localhost:8000](http://localhost:8000)

Exemples de questions :

```
Combien de commits dans requests ?
Quels sont les fichiers les plus modifiés ?
Qui est le contributeur principal ?
Quels sont les hotspots du repo ?
```

Les réponses incluent :

* texte explicatif
* **sources**
* score de pertinence

---

## 🖥️ Interface CLI

Hyperion propose une interface en ligne de commande :

```bash
# Profiler un repository
hyperion profile /path/to/repo

# Générer la documentation
hyperion generate data/repositories/mon-repo/profile.yaml

# Ingérer dans Neo4j
hyperion ingest data/repositories/mon-repo/profile.yaml --clear

# Afficher la configuration
hyperion info
```

---

## 🤖 Utilisation via API (OpenAI-compatible)

### Liste des modèles

```bash
curl http://localhost:8000/v1/models
```

### Chat completion

```bash
curl http://localhost:8000/v1/chat/completions \
  -H "Content-Type: application/json" \
  -d '{
    "model": "hyperion-rag",
    "messages": [
      {"role": "user", "content": "combien de commit dans requests ?"}
    ]
  }'
```

### Endpoints disponibles

**Core API** :
* `GET /` - Info API générale
* `GET /api/health` - Health check (API, Neo4j, RAG, détails)
* `GET /api/repos` - Liste tous repos analysés + métadonnées
* `GET /api/repos/{repo}/contributors` - Top contributeurs avec stats
* `GET /api/repos/{repo}/hotspots` - Top fichiers modifiés (hotspots)
* `POST /api/chat` - Chat RAG avec sources et processing time

**OpenAI Compatible** :
* `GET /v1/models` - Liste modèles (hyperion-rag)
* `POST /v1/chat/completions` - Chat completions avec sources incluses

**API v2 (Neo4j Code Intelligence)** :
* `GET /api/v2/health` - Health check moteurs v2
* `GET /api/v2/repos/{repo}/functions` - Fonctions Python (limit=50)
* `GET /api/v2/repos/{repo}/classes` - Classes Python (limit=30)
* `POST /api/v2/understanding/search` - Recherche code (function/class/all)
* `POST /api/v2/impact/analyze` - Analyse impact changements (profondeur configurable)
* `POST /api/v2/anomaly/scan` - Scan anomalies (complexity, size, duplicates)

Documentation Swagger interactive : [http://localhost:8000/docs](http://localhost:8000/docs)

---

## 🧪 État du projet

* ✅ **v2.7.0 Enterprise Ready** - Infrastructure ML complète + API v2
* ✅ **138 tests passent** à 100% (Core + ML + API + Integration)
* ✅ **Infrastructure ML opérationnelle** :
  - MLflow tracking et model registry
  - Feature Store avec 35+ features ingénieurées
  - Training Pipeline automatisé (4 modèles + ensemble)
  - Data Validator avec drift detection
* ✅ **5 modèles ML prêts** : RiskPredictor (RF+XGBoost), AnomalyDetector, BugPredictor, ImpactAnalyzer, Meta-learner
* ✅ **API v2 Code Intelligence** : fonctions/classes extraction, impact analysis, anomaly detection
* ✅ **RAG opérationnel** avec sources, metadata et processing time
* ✅ **API OpenAI-compatible** testée avec Open WebUI
* ✅ **Neo4j integration** : 3 ingesteurs (Git, Code AST, v2 Git)
* ✅ **CLI complète** : profile, generate, ingest, export (stub), info
* ✅ **Code formaté Black/Ruff** - Standards entreprise (100% conformité)
* 🚧 En évolution continue vers industrialisation
* ⏳ **À venir** : Containerisation Docker complète, authentification, déploiement cloud

Hyperion est un **socle expérimental sérieux**, pensé pour évoluer vers :

* un moteur de connaissance technique
* un outil d'audit de code
* une base RAG multi-sources (Git, docs, tickets, graphes)

---

## 🧭 Roadmap (indicative)

* [x] Structure `src/` moderne (v1.1.0)
* [x] CLI fonctionnelle
* [x] API OpenAI-compatible
* [x] Dashboard React
* [ ] Tests automatiques complets
* [ ] RAG multi-sources (Git + Neo4j + Docs)
* [ ] Packaging Docker complet
* [ ] Mode `start|stop|status`
* [ ] Documentation approfondie

---

## 🛠️ Développement

### Structure des imports

Depuis la version 1.1.0, les imports utilisent la structure `src/` :

```python
# Imports core
from hyperion.core import GitAnalyzer
from hyperion.api.main import app

# Imports modules
from hyperion.modules.rag.query import RAGQueryEngine
from hyperion.modules.generators.markdown_generator import MarkdownGenerator
from hyperion.modules.integrations.neo4j_ingester import Neo4jIngester
```

### Lancer en mode développement

```bash
# API seule
python scripts/dev/run_api.py

# Dashboard seul (dans un autre terminal)
cd frontend
python -m http.server 3000

# Tests
pytest tests/
```

---

## 📜 Licence

Projet personnel — usage libre pour expérimentation.

---

## 🙌 Auteur

**Matthieu Ryckman**  
Projet personnel — exploration RAG, graphes et IA locale

---

## 🤝 Contribution

Ce projet est en développement actif. Les contributions, suggestions et retours sont les bienvenus via les issues GitHub.
