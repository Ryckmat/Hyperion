# 📚 Documentation Hyperion v2.7
<<<<<<< HEAD

![Hyperion](https://img.shields.io/badge/Hyperion-v2.7-blue.svg)
![Docker](https://img.shields.io/badge/Docker-Ready-green.svg)
![Python](https://img.shields.io/badge/Python-3.11+-blue.svg)
=======
>>>>>>> 559cf74 ( doc: Ajout d'une documentation)

**Hyperion v2.7.0 Enterprise Ready** - Plateforme d'intelligence locale pour repositories Git avec infrastructure ML complète

---

<<<<<<< HEAD
**Version actuelle : Hyperion v2.7 - Enterprise Ready with Docker Orchestration**
=======
## 🚀 Navigation Rapide
>>>>>>> 559cf74 ( doc: Ajout d'une documentation)

### 📚 **Pour Apprendre et Utiliser** → [Documentation Cours](cours/)
- Formation complète à Hyperion
- Guides pas-à-pas en français
- Exemples pratiques et workflows
- **Idéal pour** : nouveaux utilisateurs, formation, usage quotidien

<<<<<<< HEAD
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
=======
### 🔧 **Pour Développer et Administrer** → [Documentation Technique](technique/)
- Documentation technique complète
- Référence API et CLI
- Architecture et déploiement
- **Idéal pour** : développeurs, administrateurs, contributeurs
>>>>>>> 559cf74 ( doc: Ajout d'une documentation)

---

## 📖 **DOCUMENTATION COURS** - *Apprendre Hyperion*

La section **cours/** contient tout ce qu'il faut savoir pour maîtriser Hyperion :

### 📋 **Programme Complet (10 Chapitres)**

| Chapitre | Titre | Description | Niveau |
|----------|-------|-------------|--------|
| **01** | [Introduction](cours/01-introduction.md) | Qu'est-ce que Hyperion et ses capacités | 🟢 Débutant |
| **02** | [Installation](cours/02-installation.md) | Setup complet et vérification | 🟢 Débutant |
| **03** | [Premier Usage](cours/03-premier-usage.md) | Premier profiling et résultats | 🟢 Débutant |
| **04** | [CLI Essentials](cours/04-cli-essentials.md) | Maîtriser les commandes de base | 🟡 Intermédiaire |
| **05** | [API Basics](cours/05-api-basics.md) | Utiliser l'API REST et OpenAI | 🟡 Intermédiaire |
| **06** | [RAG et Chat](cours/06-rag-chat.md) | Interroger ses repos avec l'IA | 🟡 Intermédiaire |
| **07** | [Infrastructure ML](cours/07-infrastructure-ml.md) | Comprendre les modèles et prédictions | 🟡 Intermédiaire |
| **08** | [Workflows](cours/08-workflows.md) | Workflows avancés et automatisation | 🔴 Avancé |
| **09** | [Troubleshooting](cours/09-troubleshooting.md) | Résoudre les problèmes courants | 🔴 Avancé |
| **10** | [Usage Avancé](cours/10-advanced-usage.md) | Fonctionnalités expertes | 🔴 Avancé |

### 🎯 **Parcours Recommandés**

**🚀 Utilisateur Rapide** : Chapitres 01 → 02 → 03 → 06
**💼 Utilisateur Professionnel** : Chapitres 01 → 02 → 03 → 04 → 05 → 08
**🎓 Formation Complète** : Tous les chapitres dans l'ordre

---

## 🔧 **DOCUMENTATION TECHNIQUE** - *Développer avec Hyperion*

La section **technique/** contient la documentation technique complète :

### 🗂️ **Structure Technique**

```
technique/
├── 🚀 getting-started/          # Démarrage technique
├── 👥 user-guide/               # Guides utilisateur détaillés
│   ├── cli/                     # Interface ligne de commande
│   └── api/                     # API REST complète
├── 🏗️ architecture/             # Architecture système
├── 🤖 ml-platform/              # Plateforme Machine Learning
├── 🔬 advanced/                 # Fonctionnalités avancées
├── 🛠️ development/              # Développement et contribution
├── 📊 reference/                # Référence complète
└── 📋 legacy/                   # Documents historiques
```

### 📚 **Sections Principales**

#### 🚀 [Getting Started](technique/getting-started/)
- Installation technique
- Configuration avancée
- Premiers pas développeur

#### 👥 [User Guide](technique/user-guide/)
- **[CLI](technique/user-guide/cli/)** : Commandes complètes (profile, generate, ingest, export, info)
- **[API](technique/user-guide/api/)** : API Core + OpenAI Compatible + Code Intelligence v2
- **[Configuration](technique/user-guide/configuration.md)** : Variables d'environnement et YAML

#### 🏗️ [Architecture](technique/architecture/)
- Vue d'ensemble système
- Infrastructure ML
- Flux de données
- Déploiement

#### 🤖 [ML Platform](technique/ml-platform/)
- Feature Store (35+ features)
- Training Pipeline (4 modèles + ensemble)
- Model Registry (MLflow)
- Data Validation

#### 🔬 [Advanced](technique/advanced/)
- Code Intelligence v2
- Impact Analysis
- Anomaly Detection
- Neo4j Integration

#### 🛠️ [Development](technique/development/)
- Guide de contribution
- Structure du projet
- Tests et qualité
- Feuille de route

#### 📊 [Reference](technique/reference/)
- Référence API complète
- Référence CLI complète
- Configuration complète
- Troubleshooting technique

---

## 🎯 **Choisir sa Documentation**

### 🆕 **Vous découvrez Hyperion ?**
👉 **Commencez par** : [Documentation Cours](cours/) - Chapitre 01

### 💼 **Vous voulez utiliser Hyperion au quotidien ?**
👉 **Suivez** : [Parcours Professionnel](cours/) - Chapitres 01-05 + 08

### 🔧 **Vous développez ou administrez Hyperion ?**
👉 **Consultez** : [Documentation Technique](technique/)

### 🤖 **Vous travaillez avec l'infrastructure ML ?**
👉 **Explorez** : [ML Platform](technique/ml-platform/)

### 🚀 **Vous voulez contribuer au projet ?**
👉 **Lisez** : [Development Guide](technique/development/)

---

## 📊 **État de la Documentation v2.7**

### ✅ **Documentation Complète**
- **📚 Cours** : 10 chapitres en français pour tous niveaux
- **🔧 Technique** : 7 sections pour développeurs/administrateurs
- **📝 Référence** : API, CLI, configuration complète
- **🗃️ Organisation** : Structure claire et navigation intuitive

### 🎯 **Métriques v2.7.0**
- **Guides** : 10 chapitres cours + 7 sections techniques
- **Coverage** : 100% des fonctionnalités documentées
- **Langues** : Documentation en français
- **Formats** : Markdown avec navigation GitHub
- **Maintenance** : Documentation synchronisée avec le code

### 🔗 **Liens Rapides**

| Service | URL | Description |
|---------|-----|-------------|
| **API Hyperion** | http://localhost:8000 | API REST + Swagger docs |
| **Dashboard** | http://localhost:3000 | Interface visualisation |
| **Open WebUI** | http://localhost:3001 | Chat conversationnel |
| **Neo4j Browser** | http://localhost:7474 | Graphe de code |
| **MLflow UI** | http://localhost:5000 | ML tracking |

---

## 🆘 **Support et Aide**

### 💬 **Questions ?**
1. **Utilisateurs** → Consultez [Cours - Troubleshooting](cours/09-troubleshooting.md)
2. **Développeurs** → Consultez [Technique - Reference](technique/reference/troubleshooting.md)
3. **Contributors** → Lisez [Development Guide](technique/development/contributing.md)

### 🐛 **Bugs ou Problèmes ?**
- Vérifiez les logs dans `logs/`
- Utilisez `hyperion info` pour diagnostic
- Consultez le troubleshooting approprié

### 📧 **Feedback Documentation**
Pour améliorer cette documentation, n'hésitez pas à :
- Signaler les sections peu claires
- Proposer des exemples supplémentaires
- Suggérer de nouveaux chapitres

---

## 🏷️ **Historique et Versions**

- **v2.7.0** - Documentation complète restructurée (Cours + Technique)
- **v2.6.x** - Ajout Code Intelligence et Impact Analysis
- **v2.5.0** - Infrastructure ML Enterprise Ready

**Voir** : [CHANGELOG.md](CHANGELOG.md) pour l'historique détaillé

---

*Documentation mise à jour le 26 décembre 2024 pour Hyperion v2.7.0*