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

### Installation
```bash
git clone <repository>
cd Hyperion
pip install -e .
```

### Lancement
```bash
# Option 1: Orchestrateur master
./scripts/deploy/hyperion_master.sh --profile enterprise

# Option 2: Docker (8 services)
./scripts/docker/hyperion-docker.sh --action up --profile enterprise
```

### Services
Une fois lancé, les services sont disponibles :
* **API Gateway** : http://localhost:8000
* **Dashboard** : http://localhost:3000
* **Chat Interface** : http://localhost:3001
* **Monitoring** : http://localhost:9090
* **Neo4j Browser** : http://localhost:7474

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

## 🏗️ Architecture

```
Hyperion/
├── src/hyperion/              # Code source principal
│   ├── api/                   # API Gateway v3.0
│   ├── cli/                   # Interface ligne de commande
│   ├── core/                  # Analyseur Git
│   ├── modules/               # Modules métier v3.0
│   │   ├── analytics/         # Moteur d'intelligence v2.9
│   │   ├── cache/             # Cache distribué v3.0
│   │   ├── gateway/           # API Gateway v3.0
│   │   ├── ml/                # Infrastructure ML v2.9
│   │   ├── monitoring/        # Monitoring v3.0
│   │   ├── rag/               # Pipeline RAG v2.9
│   │   └── security/          # Sécurité v3.0
│   └── utils/                 # Utilitaires
├── docs/                      # Documentation complète
├── scripts/                   # Scripts déploiement
├── tests/                     # Tests (189/189 passing)
└── frontend/                  # Dashboard React
```

## 📊 Qualité & Fonctionnalités v2.9 + v3.0

### Code Quality Enterprise
* **Tests** : 189/189 passing (100%) - de 75+ erreurs Ruff à 0 erreurs
* **Linting** : 0 erreurs Ruff (100% compliance)
* **Formatage** : 148 fichiers Black compliant
* **Type safety** : 95%+ annotations
* **Exception chaining** : enterprise-grade error handling

### Quality System v2.8
* **Détection d'hallucinations** : patterns suspects, contenu inventé, cohérence sémantique
* **Confidence scoring** : scoring global pondéré (hallucination 40%, sources 25%, pertinence 20%, complétude 15%)
* **Validation automatique** : actions accept/flag/reject selon seuils configurables
* **Monitoring qualité** : métriques temps réel, alertes, recommandations

### Architecture v3.0 Validée
* **8 microservices** : tous validés et documentés
* **API Gateway v3.0** : auth, rate limiting, cache, routage intelligent
* **Enhanced RAG v2.9** : pipeline optimisé avec quality validation
* **Monitoring complet** : Prometheus, structured logging, performance tracking

## 📚 Documentation

Documentation complète disponible dans `docs/` :
* **Cours** : guides utilisateur complets (français)
* **Technique** : architecture, déploiement, API, qualité code
* **Référence** : CLI, API endpoints, exemples

Points d'entrée :
* [Guide utilisateur](docs/cours/) - formation complète
* [Architecture v3.0](docs/technique/architecture/v3-enterprise-architecture.md)
* [Déploiement](docs/technique/architecture/deployment.md)
* [API Reference](docs/technique/reference/api-reference.md)

## 🔧 Prérequis

* Python 3.11+
* Docker (pour services)
* 8GB RAM minimum, 16GB recommandé
* Neo4j, Redis, Ollama (gérés par scripts)

## 🌟 Statut Actuel v2.9 + v3.0

### ✅ Fonctionnalités Majeures Implémentées
* **Quality System v2.8** - détection d'hallucinations, confidence scoring, validation automatique
* **Enhanced RAG v2.9** - pipeline optimisé avec response optimization
* **Architecture v3.0 Enterprise** - 8 microservices avec API Gateway intelligent
* **Sécurité v3.0** - JWT, TOTP, RBAC, API authentication complète
* **Monitoring v3.0** - Prometheus, structured logging, performance tracking
* **Cache distribué v3.0** - L1/L2 avec invalidation par tags

### ✅ Qualité Enterprise Atteinte
* **Code qualité** - 0 erreurs Ruff (était 75+ erreurs), 148 fichiers Black compliant
* **Tests** - 189/189 passing (100% success rate)
* **Type safety** - 95%+ annotations avec exception chaining
* **Documentation** - guides complets, architecture v3.0, API référence
* **Déploiement** - orchestrateur master + Docker enterprise (8 services)

### 🎯 Production Ready
* **Architecture scalable** - microservices avec monitoring complet
* **Quality validation** - système de validation qualité temps réel
* **Enterprise security** - authentification et autorisation complètes
* **Deployment automation** - scripts orchestrés pour mise en production
