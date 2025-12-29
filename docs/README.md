# 📚 Documentation Hyperion v2.9 + v3.0 Enterprise

![Hyperion](https://img.shields.io/badge/Hyperion-v2.9+v3.0-blue.svg)
![Docker](https://img.shields.io/badge/Docker-Ready-green.svg)
![Python](https://img.shields.io/badge/Python-3.11+-blue.svg)
![Quality](https://img.shields.io/badge/Code_Quality-100%25-green.svg)

**Hyperion v2.9 + v3.0 Enterprise Ready** - Plateforme d'intelligence locale pour repositories Git avec infrastructure ML complète et architecture v3.0

---

**Version actuelle : Hyperion v2.9 + v3.0 - Advanced RAG + Enterprise Architecture**

## 🚀 Navigation Rapide

### 📚 **Pour Apprendre et Utiliser** → [Documentation Cours](cours/)
- Formation complète à Hyperion
- Guides pas-à-pas en français
- Exemples pratiques et workflows
- **Idéal pour** : nouveaux utilisateurs, formation, usage quotidien

### 🔧 **Pour Développer et Administrer** → [Documentation Technique](technique/)
- Documentation technique complète
- Référence API et CLI
- Architecture et déploiement
- **Idéal pour** : développeurs, administrateurs, contributeurs

---

## 🆕 **Nouveautés v2.9 + v3.0**

### 🎯 **RAG Pipeline v2.9 - Enhanced Intelligence**
- **Enhanced Pipeline** : Système RAG avancé avec compression contextuelle
- **Response Optimizer** : Optimisation automatique des réponses (clarté, concision, cohérence)
- **Context Manager** : Gestion intelligente des conversations et profils utilisateur
- **Quality Validation v2.8** : Validation qualité avec métriques de confiance

### 🏗️ **Architecture v3.0 - Enterprise Ready**
- **API Gateway v3.0** : Routage intelligent, rate limiting, cache distribué
- **Monitoring v3.0** : StructuredLogger, PerformanceTracker, PrometheusExporter
- **Cache Distribué v3.0** : Cache L1/L2 avec invalidation par tags
- **Sécurité v3.0** : AuthManager, JWT, TOTP, gestion des rôles
- **Load Balancer** : Répartition de charge avec health checks

### 📊 **Analytics v2.9 - Intelligence Engine**
- **Pattern Analysis** : Détection automatique de patterns comportementaux
- **Behavioral Analysis** : Analyse des comportements utilisateur
- **Intelligence Engine** : Insights temps réel et recommandations
- **Real-time Dashboard** : Métriques live et alertes

### 🔧 **Code Quality Enterprise**
- **100% Linting Compliance** : Ruff, Black, Pytest - 0 erreurs
- **189 Tests Passing** : Couverture complète avec tests d'architecture
- **Type Safety** : Annotations de type complètes
- **Exception Chaining** : Gestion d'erreurs enterprise-grade

---

## 🚀 **Démarrage Rapide v3.0**

### Option 1: Docker (Recommandé)
```bash
# Lancer l'architecture complète v3.0
./scripts/docker/hyperion-docker.sh --action up --profile enterprise

# Accéder aux services
open http://localhost:8000  # API Gateway v3.0
open http://localhost:3000  # Dashboard Analytics
open http://localhost:9090  # Prometheus Monitoring
```

### Option 2: Orchestrateur Master v3.0
```bash
# Déploiement automatique avec architecture v3.0
./scripts/deploy/hyperion_master.sh --profile enterprise

# Configuration interactive avancée
./scripts/deploy/hyperion_master.sh --setup-v3 --enable-monitoring
```

### Option 3: Installation Développeur
```bash
# Installation avec environnement qualité
pip install -e .

# Vérification qualité (tout doit passer)
ruff check src/ tests/     # ✅ 0 erreurs
black --check src/ tests/  # ✅ 148 files compliant
pytest tests/ -v          # ✅ 189/189 passing

# Lancer Hyperion
hyperion --help
```

---

## 📖 **DOCUMENTATION COURS** - *Apprendre Hyperion*

La section **cours/** contient tout ce qu'il faut savoir pour maîtriser Hyperion v2.9 + v3.0 :

### 📋 **Programme Complet (10 Chapitres + Nouveautés)**

| Chapitre | Titre | Description | Niveau | Nouveautés v3.0 |
|----------|-------|-------------|--------|-----------------|
| **01** | [Introduction](cours/01-introduction.md) | Hyperion v3.0 et ses capacités | 🟢 Débutant | Architecture v3.0 |
| **02** | [Installation](cours/02-installation.md) | Setup v3.0 et vérification | 🟢 Débutant | Docker Enterprise |
| **03** | [Premier Usage](cours/03-premier-usage.md) | RAG v2.9 et résultats optimisés | 🟢 Débutant | Response Optimizer |
| **04** | [CLI Essentials](cours/04-cli-essentials.md) | Commandes v3.0 avancées | 🟡 Intermédiaire | Quality metrics |
| **05** | [API Basics](cours/05-api-basics.md) | API Gateway v3.0 | 🟡 Intermédiaire | Rate limiting |
| **06** | [RAG et Chat](cours/06-rag-chat.md) | Enhanced Pipeline v2.9 | 🟡 Intermédiaire | Context Manager |
| **07** | [Infrastructure ML](cours/07-infrastructure-ml.md) | Analytics v2.9 + ML | 🟡 Intermédiaire | Intelligence Engine |
| **08** | [Workflows](cours/08-workflows.md) | Workflows v3.0 enterprise | 🔴 Avancé | Monitoring v3.0 |
| **09** | [Troubleshooting](cours/09-troubleshooting.md) | Debug avec v3.0 tools | 🔴 Avancé | Structured Logging |
| **10** | [Usage Avancé](cours/10-advanced-usage.md) | Architecture distribuée | 🔴 Avancé | Cache distribué |

### 🎯 **Parcours Recommandés v3.0**

**🚀 Utilisateur Rapide** : Chapitres 01 → 02 → 03 → 06
**💼 Utilisateur Enterprise** : Chapitres 01 → 02 → 03 → 04 → 05 → 07 → 08
**🏗️ Administrateur Système** : Tous + focus Chapitres 08 → 09 → 10
**🎓 Formation Complète v3.0** : Tous les chapitres dans l'ordre

---

## 🔧 **DOCUMENTATION TECHNIQUE** - *Architecture v2.9 + v3.0*

### 🗂️ **Structure Technique Mise à Jour**

```
technique/
├── 🚀 getting-started/          # Démarrage technique v3.0
├── 👥 user-guide/               # Guides utilisateur v2.9+
│   ├── cli/                     # CLI avec quality metrics
│   ├── api/                     # API Gateway v3.0
│   └── rag/                     # Enhanced RAG v2.9
├── 🏗️ architecture/             # Architecture v3.0
│   ├── system-overview.md       # Vue d'ensemble v3.0
│   ├── api-gateway.md          # Gateway architecture
│   ├── monitoring.md           # Monitoring v3.0
│   └── security.md             # Sécurité enterprise
├── 🤖 ml-platform/              # ML + Analytics v2.9
│   ├── intelligence-engine.md   # Moteur d'intelligence
│   ├── pattern-analysis.md      # Analyse de patterns
│   └── behavioral-analysis.md   # Analyse comportementale
├── 🔬 advanced/                 # Fonctionnalités v3.0
│   ├── distributed-cache.md     # Cache distribué
│   ├── quality-system.md        # Système qualité v2.8
│   └── response-optimization.md # Optimisation réponses
├── 🛠️ development/              # Développement v3.0
│   ├── code-quality.md          # Standards qualité
│   ├── testing.md               # Tests enterprise
│   └── contributing-v3.md       # Contribution v3.0
├── 📊 reference/                # Référence complète v3.0
└── 📋 legacy/                   # Documents historiques
```

---

## 🎯 **Fonctionnalités Clés v2.9 + v3.0**

### 🔍 **Enhanced RAG Pipeline v2.9**
- **Context Compression** : Compression intelligente des contextes longs
- **Semantic Reranking** : Reclassement sémantique des résultats
- **Response Optimization** : Amélioration automatique clarté/concision
- **Quality Validation v2.8** : Validation qualité avec scoring

### 🏗️ **Enterprise Architecture v3.0**
- **API Gateway** : Routage, auth, rate limiting, cache
- **Monitoring Stack** : Prometheus, structured logging, metrics
- **Distributed Cache** : L1/L2 cache avec tags et TTL
- **Security Layer** : JWT, TOTP, RBAC, session management

### 📊 **Intelligence Analytics v2.9**
- **Pattern Detection** : Détection automatique patterns
- **Behavioral Insights** : Analyse comportements utilisateur
- **Real-time Dashboard** : Métriques temps réel
- **Predictive Analytics** : Prédictions basées ML

### 🔧 **Code Quality Enterprise**
- **Zero Linting Errors** : Ruff + Black compliance
- **100% Test Coverage** : 189 tests passing
- **Type Safety** : Annotations complètes
- **Documentation** : Mise à jour complète

---

## 📊 **Métriques v2.9 + v3.0**

### ✅ **Qualité Code**
- **Ruff Errors** : ✅ 0/0 (100% compliance)
- **Black Formatting** : ✅ 148/148 files compliant
- **Tests** : ✅ 189/189 passing (100% success)
- **Type Coverage** : ✅ 95%+ annotations

### 🚀 **Performance**
- **API Response** : <100ms (P95)
- **RAG Pipeline** : <2s query processing
- **Cache Hit Rate** : >85% efficiency
- **Memory Usage** : <512MB baseline

### 🏗️ **Architecture**
- **Microservices** : 8 services v3.0
- **Load Balancing** : Auto-scaling ready
- **Monitoring** : Real-time metrics
- **Security** : Enterprise-grade auth

---

## 🔗 **Services v3.0**

| Service | Port | URL | Description |
|---------|------|-----|-------------|
| **API Gateway v3.0** | 8000 | http://localhost:8000 | Gateway principal + docs |
| **RAG Pipeline v2.9** | 8001 | http://localhost:8001 | Enhanced RAG service |
| **Analytics Engine** | 8002 | http://localhost:8002 | Intelligence + insights |
| **Dashboard v3.0** | 3000 | http://localhost:3000 | Interface admin v3.0 |
| **Open WebUI** | 3001 | http://localhost:3001 | Chat conversationnel |
| **Prometheus** | 9090 | http://localhost:9090 | Monitoring metrics |
| **Neo4j Browser** | 7474 | http://localhost:7474 | Graphe de code |
| **MLflow UI** | 5000 | http://localhost:5000 | ML tracking + models |

---

## 🆘 **Support et Troubleshooting v3.0**

### 💬 **Questions ?**
1. **Utilisateurs** → [Cours - Troubleshooting v3.0](cours/09-troubleshooting.md)
2. **Développeurs** → [Technique - Debugging v3.0](technique/development/troubleshooting-v3.md)
3. **Administrateurs** → [Architecture - Monitoring](technique/architecture/monitoring.md)

### 🐛 **Debug Tools v3.0**
```bash
# Health check complet
hyperion health --detailed --services-v3

# Monitoring status
hyperion monitoring --prometheus --check-all

# Quality verification
hyperion quality --run-full-check --ruff --black --pytest

# Cache status
hyperion cache --status --l1 --l2 --redis
```

### 📧 **Feedback v3.0**
- Architecture feedback → technique/development/
- Quality issues → Code review process
- Documentation → docs/ improvements

---

## 🏷️ **Historique Versions**

- **v2.9 + v3.0** - Enhanced RAG + Enterprise Architecture + 100% Code Quality
- **v2.8.0** - Quality Validation System + Response Optimization
- **v2.7.0** - Documentation complète restructurée (Cours + Technique)
- **v2.6.x** - Code Intelligence et Impact Analysis
- **v2.5.0** - Infrastructure ML Enterprise Ready

**Voir** : [CHANGELOG.md](CHANGELOG.md) pour l'historique détaillé

---

*Documentation Hyperion v2.9 + v3.0 Enterprise Architecture*