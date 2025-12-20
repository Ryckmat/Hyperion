# 🧠 Hyperion

**Hyperion** est une plateforme locale d'analyse et d'exploration de dépôts Git, combinant :

* 📊 **Analyse Git avancée** (commits, hotspots, contributeurs, métriques)
* 🧠 **RAG (Retrieval Augmented Generation)** basé sur **Qdrant**
* 🕸️ **Graphe de connaissance** optionnel via **Neo4j**
* 🤖 **API OpenAI-compatible** (Chat Completions / Models)
* 💬 **Interface conversationnelle** via **Open WebUI**
* 🚀 **Script d'orchestration unifié** pour tout lancer / arrêter

Hyperion est conçu comme un **socle de connaissance technique local**, orienté compréhension, audit et exploration de code à grande échelle.

---

## ✨ Fonctionnalités clés

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

### 🤖 API OpenAI-compatible

Hyperion expose une API compatible OpenAI :

* `/v1/models`
* `/v1/chat/completions`

👉 utilisable par :

* Open WebUI
* outils RAG
* scripts internes
* clients OpenAI existants

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
│       ├── rag/           # Qdrant, embeddings, query engine
│       ├── generators/    # Générateurs de documentation
│       ├── integrations/  # Neo4j, Git, autres sources
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

### 3️⃣ Lancer Hyperion

```bash
./scripts/deploy/hyperion_master.sh
```

Le script te guide pour :

* vérifier les services
* lancer le dashboard
* lancer Open WebUI
* choisir ce que tu veux activer

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

* `GET /` - Info API
* `GET /api/health` - Health check
* `GET /api/repos` - Liste des repos analysés
* `GET /api/repos/{repo_name}` - Détails d'un repo
* `POST /api/chat` - Chat RAG
* `GET /v1/models` - Liste modèles OpenAI-compatible
* `POST /v1/chat/completions` - Chat OpenAI-compatible

Documentation complète : [http://localhost:8000/docs](http://localhost:8000/docs)

---

## 🧪 État du projet

* ✔️ **v1.1.0** - Structure moderne (`src/` layout)
* ✔️ Fonctionnel et stable en local
* ✔️ RAG opérationnel avec sources
* ✔️ API OpenAI-compatible testée
* ✔️ Open WebUI intégré
* 🚧 En évolution continue
* ❌ Pas encore industrialisé (K8s, CI/CD, auth)

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
