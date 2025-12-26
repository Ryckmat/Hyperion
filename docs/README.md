# 📚 Documentation Hyperion v2.7

![Hyperion](https://img.shields.io/badge/Hyperion-v2.7-blue.svg)
![Docker](https://img.shields.io/badge/Docker-Ready-green.svg)
![Python](https://img.shields.io/badge/Python-3.11+-blue.svg)

## 🚀 Vue d'ensemble

Hyperion est une plateforme d'intelligence locale pour repositories Git qui utilise l'IA pour analyser, comprendre et interagir avec votre code.

**Version actuelle : Hyperion v2.7 - Enterprise Ready with Docker Orchestration**

## 📖 Guides principaux

### 🚀 Démarrage rapide

#### Option 1: Docker (Recommandé)
```bash
# Lancer avec Docker
./scripts/docker/hyperion-docker.sh --action up --profile core

# Accéder à l'interface
open http://localhost:8000
```

#### Option 2: Orchestrateur Master
```bash
# Mode automatique
./scripts/deploy/hyperion_master.sh --auto

# Configuration interactive
./scripts/deploy/hyperion_master.sh --setup-model
```

#### Option 3: Installation Locale
```bash
pip install -e .
hyperion --help
```

- **[Getting Started](guides/getting_started.md)** - Installation et premier usage
- **[Configuration RAG](guides/RAG_SETUP.md)** - Configuration du système de recherche
- **[Déploiement Docker](deployment/README.md)** - Guide complet Docker/Compose

### 🎯 Sélection de modèles
- **[Guide de sélection des modèles](MODEL_SELECTION_GUIDE.md)** - Choisir le bon modèle LLM selon vos besoins

### 🏗️ Architecture
- **[Architecture générale](ARCHITECTURE.md)** - Vue d'ensemble du système
- **[Architecture détaillée](architecture/architecture.md)** - Composants techniques

### 📊 Analyses et rapports
- **[Analyse de structure](STRUCTURE_ANALYSIS.md)** - Analyse complète du projet
- **[Santé du projet](PROJECT_HEALTH_SUMMARY.md)** - État de santé et métriques
- **[Plan de nettoyage](CLEANUP_PLAN.md)** - Optimisations et améliorations

### 🔧 Développement
- **[Contributing](CONTRIBUTING.md)** - Guide de contribution
- **[Changelog](../CHANGELOG.md)** - Historique des versions

### ⚙️ API v2
- **[Code Understanding](v2/code_understanding.md)** - API d'analyse de code
- **[Impact Analysis](v2/impact_analysis.md)** - Analyse d'impact des changements

## 🎮 Usage rapide

```bash
# Démarrage complet avec sélection de modèle
./scripts/deploy/hyperion_master.sh --setup-model

# Mode automatique
./scripts/deploy/hyperion_master.sh --auto

# Aide complète
./scripts/deploy/hyperion_master.sh --help
```

## 🌟 Nouveautés v2.5

### Sélection intelligente de modèles
- **4 profils d'usage** adaptés à vos besoins :
  - 🏃‍♂️ **Performance Ultra-Rapide** (<3s) : llama3.2:1b
  - ⚖️ **Équilibre Performance/Qualité** (5-10s) : llama3.1:8b
  - 🧠 **Qualité Premium** (10-30s) : qwen2.5:14b
  - 🚀 **Expert/Recherche** (30s+) : qwen2.5:32b

### Infrastructure ML complète
- Training Pipeline avec ensemble de modèles
- Model Registry avec versioning MLflow
- Feature Store intelligent avec cache
- Data Validation avec détection de drift

### Architecture données robuste
- 35 Features ML configurées et validées
- 4 Modèles prêts pour production
- Neo4j intégré et stable (72 nœuds)
- Pipeline bout-en-bout fonctionnel

## 📊 Métriques de qualité

- **Tests Core** : 138/138 passés (100%)
- **Tests ML** : 114/123 passés (92.7%)
- **Lancement master** : 7/7 fonctionnels
- **Code formaté** : Black/Ruff

## 🎯 Profils d'usage recommandés

### 🏢 Entreprise/Production
- **Standard** : llama3.1:8b (équilibre optimal)
- **Mission critique** : qwen2.5:14b (qualité premium)

### 👨‍💻 Développement/Debug
- **Exploration rapide** : llama3.2:1b
- **Analyse approfondie** : llama3.1:8b

### 🎓 Recherche/Formation
- **Études de cas** : qwen2.5:14b
- **Publications scientifiques** : qwen2.5:32b

## 🛠️ Configuration dynamique

```bash
# Configuration interactive du modèle
./scripts/deploy/hyperion_master.sh --setup-model

# Configuration automatique
echo "1" | ./scripts/deploy/hyperion_master.sh --setup-model --auto
```

## 📱 Services disponibles

- **API Hyperion v2** : http://localhost:8000
- **Dashboard React** : http://localhost:3000
- **Open WebUI** : http://localhost:3001
- **Neo4j Browser** : http://localhost:7474
- **Qdrant** : http://localhost:6333

## 🧪 Tests disponibles

```bash
# Health check API
curl http://localhost:8000/api/v2/health

# Functions endpoint
curl http://localhost:8000/api/v2/repos/{repo}/functions

# Chat RAG
curl -X POST http://localhost:8000/api/chat \
  -d '{"question":"test","repo":"repo_name"}'
```

## 🚨 Support

Pour toute question ou problème :
1. Consultez la documentation appropriée
2. Vérifiez les logs dans `logs/`
3. Utilisez les scripts de diagnostic dans `scripts/`

## 🏷️ Historique des versions

- **v2.5.0** - Enterprise Ready : Infrastructure ML, sélection intelligente de modèles
- **v2.4.x** - Optimisations RAG et performance
- **v2.3.x** - API v2 et analyse de code avancée
- **v2.2.x** - Intégration Neo4j et graphe de connaissance
- **v2.1.x** - Dashboard React et interface utilisateur
- **v2.0.x** - Refactoring majeur et architecture moderne