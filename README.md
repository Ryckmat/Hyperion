# 🧠 Hyperion

[![Python 3.11+](https://img.shields.io/badge/python-3.11+-blue.svg)](https://www.python.org/downloads/)
[![Code style: black](https://img.shields.io/badge/code%20style-black-000000.svg)](https://github.com/psf/black)
[![Ruff](https://img.shields.io/endpoint?url=https://raw.githubusercontent.com/astral-sh/ruff/main/assets/badge/v2.json)](https://github.com/astral-sh/ruff)
[![Tests](https://img.shields.io/badge/tests-189%2F189-green.svg)](#)

**Hyperion v2.9 + v3.0** - Plateforme d'intelligence locale pour repositories Git avec architecture microservices.

## 🎯 Fonctionnalités

### Core
* **Analyse Git** : commits, contributeurs, hotspots, métriques
* **RAG Pipeline v2.9** : recherche sémantique avec validation qualité et optimisation réponses
* **Détection d'hallucinations** : patterns suspects, cohérence sémantique, scoring confiance
* **Quality System v2.8** : validation automatique, confidence scoring, actions programmables
* **API REST** : endpoints complets + compatibilité OpenAI + sécurité enterprise
* **CLI** : interface ligne de commande complète avec qualité intégrée
* **Dashboard** : interface web avec métriques qualité temps réel

### Architecture v3.0 Enterprise
* **API Gateway v3.0** : routage intelligent, auth JWT/TOTP, rate limiting, cache distribué
* **Enhanced RAG v2.9** : pipeline optimisé avec response optimization et quality validation
* **Analytics Engine v2.9** : intelligence comportementale et pattern analysis
* **8 Microservices** : Gateway, RAG, Analytics, Dashboard, Chat, Monitoring, Neo4j, MLflow
* **Cache distribué v3.0** : L1/L2 avec invalidation par tags et TTL intelligent
* **Monitoring v3.0** : Prometheus, structured logging, performance tracking
* **Sécurité v3.0** : JWT, TOTP, RBAC, session management, API authentication

## 🚀 Démarrage rapide

### 1. Installation
```bash
git clone <repository>
cd Hyperion
pip install -e .
```

### 2. Vérification
```bash
# Vérifier l'installation
hyperion --version
hyperion info
```

### 3. Lancement des services
```bash
# Option 1: Orchestrateur master (recommandé)
./scripts/deploy/hyperion_master.sh --profile enterprise

# Option 2: Docker enterprise (8 services)
./scripts/docker/hyperion-docker.sh --action up --profile enterprise

# Option 3: Développement rapide
./scripts/deploy/hyperion_master.sh --auto
```

### 4. Accès aux interfaces
Une fois les services démarrés :
* **API Gateway + docs** : http://localhost:8000
* **Dashboard enterprise** : http://localhost:3000
* **Chat interface** : http://localhost:3001
* **Monitoring Prometheus** : http://localhost:9090
* **Neo4j Browser** : http://localhost:7474
* **MLflow Platform** : http://localhost:5000

### 5. Premier usage
```bash
# Analyser un repository
hyperion profile /path/to/your/repo

# Utiliser le chat via API
curl -X POST http://localhost:8000/api/chat \
  -H "Content-Type: application/json" \
  -d '{"question": "Analyse ce repository", "repo": "your-repo"}'
```

## 📋 Utilisation

### CLI
```bash
# Analyser un repository
hyperion profile /path/to/repo

# Générer documentation
hyperion generate data/repositories/mon-repo/profile.yaml

# Ingérer dans Neo4j
hyperion ingest data/repositories/mon-repo/profile.yaml

# Informations système
hyperion info
```

### API REST
```bash
# Health check
curl http://localhost:8000/api/health

# Liste repositories
curl http://localhost:8000/api/repos

# Chat RAG
curl -X POST http://localhost:8000/api/chat \
  -H "Content-Type: application/json" \
  -d '{"question": "Combien de commits ?", "repo": "requests"}'

# OpenAI compatible
curl -X POST http://localhost:8000/v1/chat/completions \
  -H "Content-Type: application/json" \
  -d '{
    "model": "hyperion-rag",
    "messages": [{"role": "user", "content": "Analyse ce repository"}]
  }'

# Quality validation metrics
curl http://localhost:8000/api/quality/metrics

# Anomaly detection
curl -X POST http://localhost:8000/api/v2/anomaly/scan \
  -H "Content-Type: application/json" \
  -d '{"repo": "requests", "types": ["complexity", "size"]}'
```

## 🏗️ Architecture du Repository

```
Hyperion/
├── src/hyperion/              # Code source principal
│   ├── api/                   # API Gateway v3.0 + endpoints REST
│   ├── cli/                   # Interface ligne de commande
│   ├── core/                  # Analyseur Git principal
│   ├── modules/               # Modules métier v3.0
│   │   ├── analytics/v2_9/    # Analytics Engine + intelligence comportementale
│   │   ├── cache/v3_0/        # Cache distribué L1/L2 + invalidation tags
│   │   ├── gateway/v3_0/      # API Gateway + routage + auth + rate limiting
│   │   ├── ml/v2_9/           # Infrastructure ML + ensemble models
│   │   ├── monitoring/        # Monitoring v3.0 + Prometheus + structured logs
│   │   ├── rag/               # Pipeline RAG classique
│   │   │   ├── v2_9/          # Enhanced RAG + response optimization
│   │   │   ├── monitoring/    # Quality metrics tracking
│   │   │   └── quality/       # Système validation qualité v2.8
│   │   └── security/v3_0/     # Sécurité JWT + TOTP + RBAC
│   └── utils/                 # Utilitaires + helpers
├── docs/                      # Documentation complète
│   ├── cours/                 # 📚 Formation complète (10 chapitres français)
│   └── technique/             # Documentation technique + architecture v3.0
├── scripts/                   # Scripts orchestration + déploiement
│   ├── deploy/                # hyperion_master.sh + orchestrateurs
│   ├── docker/                # Containerisation enterprise (8 services)
│   └── dev/                   # Outils développement
├── tests/                     # Tests complets (architecture + validation + intégration)
├── frontend/                  # Dashboard React enterprise
└── data/                      # Données + profils Git + index RAG
```

## 📊 Fonctionnalités Avancées v2.9 + v3.0

### Quality System v2.8
* **Détection d'hallucinations** : patterns suspects, contenu inventé, cohérence sémantique
* **Confidence scoring** : scoring global pondéré (hallucination 40%, sources 25%, pertinence 20%, complétude 15%)
* **Validation automatique** : actions accept/flag/reject selon seuils configurables
* **Monitoring qualité** : métriques temps réel, alertes, recommandations

### Enhanced RAG v2.9
* **Response optimization** : amélioration automatique clarté, concision, cohérence
* **Context compression** : compression intelligente des contextes longs
* **Quality validation** : intégration du système de validation dans le pipeline
* **Semantic reranking** : reclassement sémantique des résultats

### Architecture Enterprise v3.0
* **8 microservices** : Gateway, RAG, Analytics, Dashboard, Chat, Monitoring, Neo4j, MLflow
* **API Gateway v3.0** : auth JWT/TOTP, rate limiting, cache distribué, routage intelligent
* **Cache distribué** : L1/L2 avec invalidation par tags et TTL intelligent
* **Monitoring complet** : Prometheus, structured logging, performance tracking, alertes

## 📚 Documentation

Documentation complète disponible dans `docs/` :

### 🎓 Formation et Apprentissage
* **[Section Cours](docs/cours/)** : **Formation complète en 10 chapitres (français)**
  - Introduction, installation, premier usage
  - CLI essentials, API basics, RAG et chat
  - Infrastructure ML, workflows avancés
  - Troubleshooting et usage expert
  - **Idéal pour s'initier et maîtriser Hyperion**

### 🔧 Documentation Technique
* **[Architecture v3.0](docs/technique/architecture/v3-enterprise-architecture.md)** - architecture complète 8 microservices
* **[Déploiement](docs/technique/architecture/deployment.md)** - guides orchestrateur + Docker enterprise
* **[API Reference](docs/technique/reference/api-reference.md)** - endpoints complets + exemples
* **[Code Quality](docs/technique/development/code-quality.md)** - standards enterprise

### 📖 Parcours Recommandés
* **🚀 Débutant** : [Section Cours](docs/cours/) chapitres 1-3 puis usage via interfaces web
* **💼 Utilisateur** : Formation complète [Section Cours](docs/cours/) + guides API
* **🔧 Administrateur** : Documentation technique + déploiement + monitoring

## 🔧 Prérequis

* Python 3.11+
* Docker (pour services)
* 8GB RAM minimum, 16GB recommandé
* Neo4j, Redis, Ollama (gérés par scripts)

## 🌟 Statut Actuel v2.9 + v3.0

### ✅ Fonctionnalités Implémentées
* **Quality System v2.8** - détection d'hallucinations + confidence scoring + validation automatique
* **Enhanced RAG v2.9** - pipeline optimisé + response optimization + context compression
* **Architecture v3.0 Enterprise** - 8 microservices + API Gateway + monitoring complet
* **Sécurité v3.0** - JWT + TOTP + RBAC + API authentication
* **Cache distribué v3.0** - L1/L2 + invalidation par tags + TTL intelligent
* **Analytics Engine v2.9** - intelligence comportementale + pattern analysis

### 🎯 Production Ready
* **Architecture scalable** - microservices avec load balancing et health checks
* **Quality validation** - système de validation qualité temps réel intégré
* **Enterprise security** - authentification multi-facteur et gestion des rôles
* **Deployment automation** - orchestrateur master + Docker enterprise
* **Documentation complète** - formation 10 chapitres + guides techniques
* **Monitoring avancé** - Prometheus + structured logging + alertes
