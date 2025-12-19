Parfait 👍
Je te refais un **README.md complet, propre et “projet sérieux”**, aligné avec **ce que fait réellement Hyperion aujourd’hui** (RAG, graphe, OpenAI-compatible, Open WebUI, orchestration), sans survendre ni simplifier à l’excès.

Tu peux **copier-coller tel quel** pour remplacer ton README actuel.

---

# 🧠 Hyperion

**Hyperion** est une plateforme locale d’analyse et d’exploration de dépôts Git, combinant :

* 📊 **Analyse Git avancée** (commits, hotspots, contributeurs, métriques)
* 🧠 **RAG (Retrieval Augmented Generation)** basé sur **Qdrant**
* 🕸️ **Graphe de connaissance** optionnel via **Neo4j**
* 🤖 **API OpenAI-compatible** (Chat Completions / Models)
* 💬 **Interface conversationnelle** via **Open WebUI**
* 🚀 **Script d’orchestration unifié** pour tout lancer / arrêter

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
* lancer l’API Hyperion
* lancer Open WebUI
* lancer le dashboard React
* arrêter proprement tous les services (Ctrl+C)

---

## 🗂️ Architecture du projet

```
Hyperion/
├── hyperion/              # Cœur Python (API, RAG, intégrations)
│   ├── api/               # FastAPI + OpenAI-compatible
│   ├── rag/               # Qdrant, embeddings, query engine
│   ├── integrations/      # Neo4j, Git, autres sources
│   └── config.py
│
├── scripts/               # Scripts d’orchestration
│   └── run_dashboard.py
│
├── frontend/              # Dashboard React
├── data/                  # Profils Git, index RAG
├── templates/             # Templates docs / exports
├── docs/                  # Documentation
├── tests/                 # Tests
│
├── hyperion_master.sh     # 🚀 Script maître
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

### 2️⃣ Lancer Hyperion

```bash
./hyperion_master.sh
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

---

## 🧪 État du projet

* ✔️ Fonctionnel
* ✔️ Stable en local
* 🚧 En évolution continue
* ❌ Pas encore industrialisé (K8s, CI/CD, auth)

Hyperion est un **socle expérimental sérieux**, pensé pour évoluer vers :

* un moteur de connaissance technique
* un outil d’audit de code
* une base RAG multi-sources (Git, docs, tickets, graphes)

---

## 🧭 Roadmap (indicative)

* [ ] Séparation API / Dashboard
* [ ] Mode `start|stop|status`
* [ ] RAG multi-sources (Git + Neo4j + Docs)
* [ ] Tests automatiques RAG
* [ ] Packaging Docker complet
* [ ] Documentation approfondie

---

## 📜 Licence

Projet personnel — usage libre pour expérimentation.
Voir le fichier `LICENSE` si présent.

---

## 🙌 Auteur

**Matthieu Ryckman**
Projet personnel — exploration RAG, graphes et IA locale.
