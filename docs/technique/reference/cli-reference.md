# 💻 CLI Hyperion v2.7

**Version**: 2.7.0
**Date**: Décembre 2024
**Auteur**: Matthieu Ryckman

---

## 📋 Table des Matières

- [Vue d'ensemble](#vue-densemble)
- [Installation](#installation)
- [Configuration](#configuration)
- [Commandes disponibles](#commandes-disponibles)
- [Workflows](#workflows)
- [Variables d'environnement](#variables-denvironnement)
- [Exemples avancés](#exemples-avancés)
- [Troubleshooting](#troubleshooting)

---

## 🎯 Vue d'ensemble

Le CLI Hyperion fournit une interface en ligne de commande complète pour :

- **Profiler** des repositories Git (analyse commits, contributeurs, hotspots)
- **Générer** de la documentation technique automatiquement
- **Ingérer** les données dans Neo4j pour analyse avancée
- **Exporter** l'historique de production (releases, déploiements)
- **Inspecter** la configuration système

### Framework et Architecture

```python
Framework: Click 8.1+                 # CLI framework Python
Entry Point: hyperion                 # Console script
Structure: Groupe de commandes        # Commandes modulaires
Configuration: Environment + YAML     # .env + config/
```

### Philosophie de Design

- **Simplicité** : Commandes intuitives et cohérentes
- **Feedback** : Progress indicators et messages clairs
- **Robustesse** : Gestion d'erreurs et validation input
- **Flexibilité** : Options configurables et environnement
- **Standards** : Conventions Unix et exit codes

---

## 📦 Installation

### Prérequis

```bash
# Système
Python >= 3.10
Git (installé et configuré)
Docker (pour Neo4j et Qdrant)

# Optionnel
Neo4j (pour graphe de connaissance)
Ollama (pour LLM local)
```

### Installation du package

```bash
# Clone du projet
git clone https://github.com/Ryckmat/Hyperion.git
cd Hyperion

# Installation en mode développement
pip install -e . --break-system-packages

# Vérification
hyperion --version
# Output: 2.7.0

hyperion --help
# Output: Usage guide complet
```

### Vérification installation

```bash
# Test complet de l'installation
hyperion info

# Output attendu:
# ============================================================
# 🚀 Hyperion v2.7.0
# ============================================================
#
# 📁 Chemins :
#    PROJECT_ROOT    : /home/user/Hyperion
#    CONFIG_DIR      : /home/user/Hyperion/config
#    [...]
```

---

## ⚙️ Configuration

### Structure de Configuration

```
config/
├── filters.yaml             # Filtres d'analyse
└── profiles/               # Profils de configuration
    ├── default.yaml
    └── enterprise.yaml

.env                        # Variables d'environnement
```

### Variables d'Environnement

```bash
# Copier et adapter le fichier exemple
cp .env.example .env
vim .env
```

**Configuration minimale** :
```bash
# Neo4j (optionnel)
NEO4J_URI=bolt://localhost:7687
NEO4J_USER=neo4j
NEO4J_PASSWORD=your_password
NEO4J_DATABASE=neo4j

# Hyperion paths
HYPERION_DATA_DIR=data/
HYPERION_OUTPUT_DIR=output/

# Processing
BATCH_SIZE_COMMITS=1000
BATCH_SIZE_FILES=500
```

### Filtres d'Analyse

Le fichier `config/filters.yaml` contrôle quels fichiers sont analysés :

```yaml
# Extensions ignorées
ignore_extensions:
  - .pyc
  - .pyo
  - .jpg
  - .png
  - .gif
  - .ico
  - .svg
  - .pdf
  - .zip
  - .tar.gz
  - .log

# Préfixes de dossiers ignorés
ignore_prefixes:
  - __pycache__
  - .git
  - .pytest_cache
  - node_modules
  - .venv
  - venv
  - .tox
  - dist

# Fichiers spécifiques ignorés
ignore_files:
  - README.md
  - LICENSE
  - CHANGELOG.md
  - .gitignore
  - requirements.txt
```

---

## 🚀 Commandes disponibles

### Arbre des Commandes

```
hyperion                    # Groupe principal
├── profile <repo_path>     # Analyse repository
├── generate <profile>      # Génère documentation
├── ingest <profile>        # Ingestion Neo4j
├── export <repo_path>      # Export historique prod (stub)
├── info                    # Informations système
├── --version               # Version actuelle
└── --help                  # Aide générale
```

---

## 1️⃣ hyperion profile

**Usage** : `hyperion profile <repo_path> [OPTIONS]`

**Description** : Analyse complète d'un repository Git

### Syntaxe Complète

```bash
hyperion profile /path/to/repository \
    --output data/repositories/ \
    --name custom-name
```

### Arguments

| Argument | Type | Description | Obligatoire |
|----------|------|-------------|-------------|
| `repo_path` | Path | Chemin vers le repository Git | ✅ |

### Options

| Option | Alias | Défaut | Description |
|--------|-------|--------|-------------|
| `--output` | `-o` | `data/repositories/` | Dossier de sortie |
| `--name` | `-n` | Auto-détecté | Nom du repository |
| `--help` | `-h` | N/A | Afficher l'aide |

### Analyse Effectuée

Le profiling analyse et extrait :

```
📊 Analyse Git :
├── Commits et historique temporel
├── Contributeurs (déduplication par email)
├── Top 10 contributeurs (par nombre de commits)
├── Hotspots (top 10 fichiers les plus modifiés)
├── Première et dernière contribution
└── Branches principales et tags

🗂️ Analyse Structure :
├── Fichiers par extension (.py, .js, .md, etc.)
├── Répertoires analysés
├── Ratio code/tests/documentation
└── Détection architecture (src/, tests/, docs/)

🔍 Détection Automatique :
├── CI/CD (GitHub Actions, GitLab CI, Jenkins)
├── Licence (SPDX format)
├── Langage principal
├── Framework détecté
└── Pattern d'organisation

📈 Métriques Qualité :
├── Code quality score
├── Test coverage estimation
├── Documentation ratio
└── Maintenance indicators
```

### Exemples d'Usage

```bash
# Analyse simple
hyperion profile /home/user/requests

# Analyse avec nom personnalisé
hyperion profile /home/user/my-project --name "MyProject"

# Sortie dans dossier spécifique
hyperion profile ./local-repo -o /tmp/analysis/

# Analyse repository distant (après clone local)
git clone https://github.com/psf/requests.git /tmp/requests
hyperion profile /tmp/requests --name requests-analysis
```

### Output Généré

```
✅ Analyse terminée !
   • Repository    : requests
   • Commits       : 1,250
   • Contributeurs : 45
   • Hotspots      : 10 fichiers
   • Profil YAML   : data/repositories/requests/profile.yaml
   • Temps analyse : 3.2s
```

**Fichier généré** : `profile.yaml` structuré
```yaml
service: requests
repositories:
  - main_language: Python
    license: Apache-2.0
    ci_cd: [GitHub Actions]
git_summary:
  commits: 1250
  contributors: 45
  contributors_top10: [...]
  hotspots_top10: [...]
  first_commit: "2011-02-13"
  last_commit: "2024-12-26"
metrics:
  code_quality: {...}
  test_coverage: {...}
  documentation: {...}
```

---

## 2️⃣ hyperion generate

**Usage** : `hyperion generate <profile_yaml> [OPTIONS]`

**Description** : Génère de la documentation à partir d'un profil analysé

### Syntaxe Complète

```bash
hyperion generate data/repositories/requests/profile.yaml \
    --format markdown \
    --output output/documentation/
```

### Arguments

| Argument | Type | Description | Obligatoire |
|----------|------|-------------|-------------|
| `profile_yaml` | Path | Chemin vers le fichier profile.yaml | ✅ |

### Options

| Option | Alias | Défaut | Choix | Description |
|--------|-------|--------|-------|-------------|
| `--format` | `-f` | `markdown` | `markdown`, `html` | Format de sortie |
| `--output` | `-o` | `output/` | Path | Dossier de destination |
| `--help` | `-h` | N/A | N/A | Afficher l'aide |

### Formats Supportés

#### Markdown (✅ Implémenté)
Génère une documentation Markdown complète :

- **`index.md`** : Vue d'ensemble du repository
- **`registre.md`** : Registre technique détaillé

#### HTML (⏳ En développement)
Génèrera un dashboard HTML statique :

- **`dashboard.html`** : Dashboard interactif
- **`assets/`** : CSS, JS, images

### Templates Utilisés

Les templates Jinja2 se trouvent dans `src/hyperion/templates/` :

```
templates/
├── markdown/
│   ├── index.md.j2          # Template vue d'ensemble
│   └── registre.md.j2       # Template registre technique
└── html/                    # Templates HTML (à venir)
    ├── dashboard.html.j2
    └── components/
```

### Exemples d'Usage

```bash
# Génération standard
hyperion generate data/repositories/requests/profile.yaml

# Format et destination spécifiques
hyperion generate data/repositories/myproject/profile.yaml \
    -f markdown \
    -o docs/generated/

# Génération pour documentation projet
hyperion generate ./analysis/profile.yaml -o ./website/content/
```

### Output Généré

```
✅ Documentation générée !
   • Format        : Markdown
   • Fichiers      : 2 générés
   • Destination   : output/requests/
   • Files créés   :
     - output/requests/index.md (vue d'ensemble)
     - output/requests/registre.md (registre technique)
```

### Contenu Documentation

**index.md** contient :
- Informations générales du repository
- Statistiques clés (commits, contributeurs)
- Top contributeurs et hotspots
- Métriques qualité
- Détection CI/CD et licence

**registre.md** contient :
- Historique détaillé des contributions
- Analyse temporelle des commits
- Répartition par extensions de fichiers
- Structure des répertoires
- Métriques techniques avancées

---

## 3️⃣ hyperion ingest

**Usage** : `hyperion ingest <profile_yaml> [OPTIONS]`

**Description** : Ingestion du profil dans Neo4j pour analyse graphe

### Syntaxe Complète

```bash
hyperion ingest data/repositories/requests/profile.yaml \
    --uri bolt://localhost:7687 \
    --user neo4j \
    --password secret \
    --database neo4j \
    --clear
```

### Arguments

| Argument | Type | Description | Obligatoire |
|----------|------|-------------|-------------|
| `profile_yaml` | Path | Chemin vers le fichier profile.yaml | ✅ |

### Options

| Option | Alias | Var Env | Défaut | Description |
|--------|-------|---------|--------|-------------|
| `--uri` | N/A | `NEO4J_URI` | None | URI de connexion Neo4j |
| `--user` | N/A | `NEO4J_USER` | None | Nom d'utilisateur |
| `--password` | N/A | `NEO4J_PASSWORD` | None | Mot de passe |
| `--database` | N/A | `NEO4J_DATABASE` | None | Nom de la base |
| `--clear` | N/A | N/A | False | Nettoyer avant ingestion |
| `--help` | `-h` | N/A | N/A | Afficher l'aide |

### Configuration Neo4j

**Option 1** : Variables d'environnement (recommandé)
```bash
export NEO4J_URI=bolt://localhost:7687
export NEO4J_USER=neo4j
export NEO4J_PASSWORD=your_password
export NEO4J_DATABASE=neo4j

# Commande simplifiée
hyperion ingest data/repositories/requests/profile.yaml --clear
```

**Option 2** : Arguments explicites
```bash
hyperion ingest profile.yaml \
    --uri bolt://localhost:7687 \
    --user neo4j \
    --password secret \
    --database neo4j
```

### Modèle de Données Neo4j

L'ingestion crée la structure suivante dans Neo4j :

```cypher
// Nodes créés
(:Repository {name, commits, contributors})
(:Author {name, email, commits})
(:File {path, changes, last_modified})
(:Directory {path})
(:Extension {name, count})
(:Branch {name})
(:Tag {name, date})

// Relationships
(:Author)-[:CONTRIBUTED_TO]->(:Repository)
(:Author)-[:MODIFIED]->(:File)
(:File)-[:IN_DIRECTORY]->(:Directory)
(:File)-[:HAS_EXTENSION]->(:Extension)
(:Repository)-[:HAS_BRANCH]->(:Branch)
(:Repository)-[:HAS_TAG]->(:Tag)
```

### Exemples d'Usage

```bash
# Ingestion simple (avec env vars)
hyperion ingest data/repositories/requests/profile.yaml

# Ingestion avec nettoyage
hyperion ingest profile.yaml --clear

# Ingestion avec connexion explicite
hyperion ingest profile.yaml \
    --uri bolt://neo4j.company.com:7687 \
    --user reader \
    --password readonly
```

### Output Généré

```
✅ Ingestion terminée !
   • Repository     : requests
   • Contributeurs  : 45 nodes créés
   • Fichiers       : 125 nodes créés
   • Hotspots       : 10 relationships créées
   • Extensions     : 8 nodes créées
   • Répertoires    : 28 nodes créés
   • Temps total    : 2.1s
```

### Requêtes Neo4j Utiles

```cypher
-- Top contributeurs
MATCH (a:Author)-[r:CONTRIBUTED_TO]->(repo:Repository {name: 'requests'})
RETURN a.name, r.commits
ORDER BY r.commits DESC LIMIT 10;

-- Fichiers les plus modifiés
MATCH (f:File)<-[:MODIFIED]-(a:Author)
RETURN f.path, count(a) as modifications
ORDER BY modifications DESC LIMIT 10;

-- Analyse des extensions
MATCH (f:File)-[:HAS_EXTENSION]->(e:Extension)
RETURN e.name, count(f) as files
ORDER BY files DESC;
```

---

## 4️⃣ hyperion export

**Usage** : `hyperion export <repo_path> [OPTIONS]`

**Description** : Export de l'historique de production (releases, déploiements)

⚠️ **Status** : Commande en développement (stub implémenté)

### Syntaxe Complète

```bash
hyperion export /path/to/repository \
    --tags-pattern "^v\d+\.\d+\.\d+$" \
    --output data/production/
```

### Arguments

| Argument | Type | Description | Obligatoire |
|----------|------|-------------|-------------|
| `repo_path` | Path | Chemin vers le repository | ✅ |

### Options

| Option | Alias | Défaut | Description |
|--------|-------|--------|-------------|
| `--tags-pattern` | N/A | `^v?\d+\.\d+\.\d+$` | Regex pattern releases |
| `--output` | `-o` | `data/repositories/` | Dossier de sortie |
| `--help` | `-h` | N/A | Afficher l'aide |

### Fonctionnalité Prévue

L'export générera :

```
data/production/{repo}/
├── prod_deploys.json       # Index des releases
├── prod_commits.jsonl      # Commits par release (1/ligne)
├── prod_files.jsonl        # Fichiers modifiés (1/ligne)
└── prod_stats.json         # Statistiques globales
```

### Status Actuel

```bash
hyperion export /path/to/repo

# Output:
# ⏳ Commande 'export' en cours de développement
# 📋 Fonctionnalité prévue :
#    • Export historique releases
#    • Analyse déploiements production
#    • Génération métriques DORA
```

---

## 5️⃣ hyperion info

**Usage** : `hyperion info`

**Description** : Affiche les informations de configuration système

### Syntaxe

```bash
hyperion info
```

**Pas d'arguments ni d'options**

### Informations Affichées

```
============================================================
🚀 Hyperion v2.7.0
============================================================

📁 Chemins :
   PROJECT_ROOT    : /home/user/Hyperion
   CONFIG_DIR      : /home/user/Hyperion/config
   TEMPLATES_DIR   : /home/user/Hyperion/src/hyperion/templates
   DATA_DIR        : /home/user/Hyperion/data
   OUTPUT_DIR      : /home/user/Hyperion/output

🔧 Configuration Neo4j :
   URI             : bolt://localhost:7687
   USER            : neo4j
   DATABASE        : neo4j

⚙️  Batch sizes :
   COMMITS         : 1000
   FILES           : 500

🔍 Filtres actifs :
   Extensions      : 12 ignorées (.pyc, .jpg, .log, ...)
   Préfixes        : 8 ignorés (__pycache__, node_modules, ...)
   Fichiers        : 5 ignorés (README.md, LICENSE, ...)

📊 Repositories analysés :
   Disponibles     : 2 (requests, hyperion)
   Dernier profil  : requests (2024-12-26 10:30)

🛠️  Services :
   Neo4j           : ✅ Accessible
   Qdrant          : ✅ Opérationnel
   MLflow          : ✅ Tracking activé
```

### Diagnostic Automatique

La commande `info` effectue des vérifications :

- ✅ **Chemins** : Existence des dossiers de configuration
- ✅ **Neo4j** : Test de connexion (si configuré)
- ✅ **Qdrant** : Vérification service vectoriel
- ✅ **Profils** : Scan des repositories analysés
- ⚠️ **Config** : Détection problèmes configuration

---

## 🔄 Workflows

### Workflow Complet - Analyse d'un Repository

```bash
# 1. Analyser le repository
hyperion profile /home/user/requests \
    --output data/repositories/ \
    --name requests

# 2. Générer la documentation
hyperion generate data/repositories/requests/profile.yaml \
    --format markdown \
    --output docs/requests/

# 3. Ingérer dans Neo4j (optionnel)
hyperion ingest data/repositories/requests/profile.yaml \
    --clear

# 4. Vérifier la configuration
hyperion info
```

### Workflow - Analyse Multiple

```bash
#!/bin/bash
# Analyser plusieurs repositories

REPOS=(
    "/home/user/project1"
    "/home/user/project2"
    "/home/user/project3"
)

for repo in "${REPOS[@]}"; do
    echo "🔍 Analyzing: $repo"

    # Profile
    hyperion profile "$repo" -o data/repositories/

    # Generate docs
    repo_name=$(basename "$repo")
    hyperion generate "data/repositories/$repo_name/profile.yaml" \
        -o "docs/$repo_name/"

    # Ingest to Neo4j
    hyperion ingest "data/repositories/$repo_name/profile.yaml"

    echo "✅ Completed: $repo_name"
done

echo "🎉 All repositories analyzed!"
```

### Workflow - Documentation Continue

```bash
#!/bin/bash
# Script de documentation continue

# Variables
REPO_PATH="/path/to/monitored/repo"
REPO_NAME="myproject"
OUTPUT_BASE="output/continuous"

# Function to check if repo changed
check_repo_changes() {
    local last_commit=$(git -C "$REPO_PATH" rev-parse HEAD)
    local stored_commit=""

    if [ -f ".last_commit" ]; then
        stored_commit=$(cat .last_commit)
    fi

    if [ "$last_commit" != "$stored_commit" ]; then
        echo "$last_commit" > .last_commit
        return 0  # Changed
    fi

    return 1  # No change
}

# Main monitoring loop
while true; do
    if check_repo_changes; then
        echo "🔄 Repository changed, updating documentation..."

        # Re-profile
        hyperion profile "$REPO_PATH" \
            --name "$REPO_NAME" \
            -o data/repositories/

        # Re-generate docs
        hyperion generate "data/repositories/$REPO_NAME/profile.yaml" \
            -o "$OUTPUT_BASE/docs/"

        # Update Neo4j
        hyperion ingest "data/repositories/$REPO_NAME/profile.yaml" \
            --clear

        echo "✅ Documentation updated"
    fi

    # Wait 5 minutes
    sleep 300
done
```

---

## 🌍 Variables d'environnement

### Configuration Complète

```bash
# ============================================================
# HYPERION CONFIGURATION
# ============================================================

# Version et info
HYPERION_VERSION=2.7.0
HYPERION_ENV=development

# Chemins principaux
HYPERION_PROJECT_ROOT=/home/user/Hyperion
HYPERION_CONFIG_DIR=/home/user/Hyperion/config
HYPERION_DATA_DIR=/home/user/Hyperion/data
HYPERION_OUTPUT_DIR=/home/user/Hyperion/output
HYPERION_TEMPLATES_DIR=/home/user/Hyperion/src/hyperion/templates

# ============================================================
# NEO4J CONFIGURATION
# ============================================================

# Connexion principale
NEO4J_URI=bolt://localhost:7687
NEO4J_USER=neo4j
NEO4J_PASSWORD=your_secure_password
NEO4J_DATABASE=neo4j

# Connexion alternative (optionnel)
NEO4J_URI_READONLY=bolt://readonly.neo4j.com:7687
NEO4J_USER_READONLY=reader
NEO4J_PASSWORD_READONLY=readonly_password

# ============================================================
# PROCESSING CONFIGURATION
# ============================================================

# Batch sizes pour performance
BATCH_SIZE_COMMITS=1000
BATCH_SIZE_FILES=500
BATCH_SIZE_CONTRIBUTORS=100

# Timeouts
GIT_OPERATION_TIMEOUT=300
NEO4J_CONNECTION_TIMEOUT=30

# Memory limits
MAX_MEMORY_USAGE_MB=1024
MAX_FILE_SIZE_MB=10

# ============================================================
# ANALYSIS CONFIGURATION
# ============================================================

# Git analysis
GIT_MAIN_BRANCH_CANDIDATES=main,master,develop,trunk
GIT_IGNORE_MERGE_COMMITS=true
GIT_ANALYZE_BRANCHES=main,develop,release/*

# Quality thresholds
MIN_COMMITS_FOR_ANALYSIS=10
MIN_CONTRIBUTORS_FOR_STATS=2
HOTSPOT_THRESHOLD=5

# ============================================================
# OUTPUT CONFIGURATION
# ============================================================

# Documentation generation
DOC_TEMPLATE_ENGINE=jinja2
DOC_DEFAULT_FORMAT=markdown
DOC_INCLUDE_TIMESTAMPS=true

# Export formats
EXPORT_JSON_INDENT=2
EXPORT_YAML_FLOW=false

# ============================================================
# LOGGING CONFIGURATION
# ============================================================

# Log level
LOG_LEVEL=INFO
LOG_FORMAT=standard
LOG_FILE=logs/hyperion.log
LOG_ROTATION=daily
LOG_RETENTION_DAYS=30

# Debug options
DEBUG_MODE=false
VERBOSE_OUTPUT=false
PROFILE_PERFORMANCE=false
```

### Variables par Commande

#### hyperion profile
```bash
# Analysis behavior
GIT_MAIN_BRANCH_CANDIDATES=main,master,develop
BATCH_SIZE_COMMITS=1000
BATCH_SIZE_FILES=500
MIN_COMMITS_FOR_ANALYSIS=10

# Output paths
HYPERION_DATA_DIR=data/repositories/
DEFAULT_PROFILE_NAME=auto_detected
```

#### hyperion generate
```bash
# Template configuration
HYPERION_TEMPLATES_DIR=src/hyperion/templates/
DOC_DEFAULT_FORMAT=markdown
HYPERION_OUTPUT_DIR=output/

# Template engine
DOC_TEMPLATE_ENGINE=jinja2
DOC_INCLUDE_TIMESTAMPS=true
```

#### hyperion ingest
```bash
# Neo4j connection
NEO4J_URI=bolt://localhost:7687
NEO4J_USER=neo4j
NEO4J_PASSWORD=password
NEO4J_DATABASE=neo4j

# Ingestion behavior
BATCH_SIZE_NODES=100
NEO4J_CONNECTION_TIMEOUT=30
CLEAR_BEFORE_INGEST=false
```

#### hyperion export
```bash
# Export configuration
EXPORT_DEFAULT_PATTERN="^v?\d+\.\d+\.\d+$"
EXPORT_JSON_INDENT=2
EXPORT_INCLUDE_METADATA=true

# Output formats
HYPERION_OUTPUT_DIR=data/production/
```

### Validation des Variables

```bash
#!/bin/bash
# Script de validation de la configuration

# Function to check required vars
check_required_vars() {
    local required_vars=(
        "HYPERION_PROJECT_ROOT"
        "HYPERION_CONFIG_DIR"
        "HYPERION_DATA_DIR"
    )

    for var in "${required_vars[@]}"; do
        if [ -z "${!var}" ]; then
            echo "❌ Missing required variable: $var"
            return 1
        fi
    done

    echo "✅ All required variables set"
    return 0
}

# Function to check optional vars with defaults
check_optional_vars() {
    # Set defaults if not set
    export BATCH_SIZE_COMMITS=${BATCH_SIZE_COMMITS:-1000}
    export BATCH_SIZE_FILES=${BATCH_SIZE_FILES:-500}
    export LOG_LEVEL=${LOG_LEVEL:-INFO}
    export DOC_DEFAULT_FORMAT=${DOC_DEFAULT_FORMAT:-markdown}

    echo "✅ Optional variables configured with defaults"
}

# Function to test connections
test_connections() {
    # Test Neo4j if configured
    if [ -n "$NEO4J_URI" ]; then
        echo "🔍 Testing Neo4j connection..."
        # Add actual Neo4j test here
        echo "  Neo4j: ${NEO4J_URI}"
    fi

    # Test file system permissions
    echo "🔍 Testing file system permissions..."
    if [ -w "$HYPERION_DATA_DIR" ]; then
        echo "  ✅ Data directory writable"
    else
        echo "  ❌ Data directory not writable: $HYPERION_DATA_DIR"
    fi
}

# Run validation
echo "🚀 Validating Hyperion Configuration..."
check_required_vars && check_optional_vars && test_connections
echo "✅ Configuration validation complete"
```

---

## 💡 Exemples avancés

### 1. Analyse de Repository Distant

```bash
#!/bin/bash
# Analyser un repository GitHub sans le cloner manuellement

REPO_URL="https://github.com/psf/requests.git"
REPO_NAME="requests"
TEMP_DIR="/tmp/hyperion_analysis"

# Clone temporaire
echo "📥 Cloning repository..."
git clone "$REPO_URL" "$TEMP_DIR/$REPO_NAME"

# Analyse
echo "🔍 Analyzing repository..."
hyperion profile "$TEMP_DIR/$REPO_NAME" \
    --name "$REPO_NAME" \
    --output data/repositories/

# Documentation
echo "📝 Generating documentation..."
hyperion generate "data/repositories/$REPO_NAME/profile.yaml" \
    --output "docs/$REPO_NAME/"

# Cleanup
echo "🧹 Cleaning up..."
rm -rf "$TEMP_DIR"

echo "✅ Analysis complete for $REPO_NAME"
```

### 2. Comparaison de Repositories

```bash
#!/bin/bash
# Comparer plusieurs repositories

REPOS=(
    "https://github.com/psf/requests.git:requests"
    "https://github.com/pallets/flask.git:flask"
    "https://github.com/django/django.git:django"
)

echo "📊 Multi-Repository Analysis"

for repo_info in "${REPOS[@]}"; do
    IFS=':' read -r repo_url repo_name <<< "$repo_info"

    echo "🔍 Processing: $repo_name"

    # Clone
    git clone "$repo_url" "/tmp/$repo_name"

    # Profile
    hyperion profile "/tmp/$repo_name" --name "$repo_name"

    # Extract key metrics
    commits=$(grep "commits:" "data/repositories/$repo_name/profile.yaml" | cut -d' ' -f4)
    contributors=$(grep "contributors:" "data/repositories/$repo_name/profile.yaml" | cut -d' ' -f4)

    echo "  📈 Metrics: $commits commits, $contributors contributors"

    # Cleanup
    rm -rf "/tmp/$repo_name"
done

echo "✅ Multi-repository analysis complete"
```

### 3. Monitoring Continu avec Slack

```bash
#!/bin/bash
# Monitoring avec notifications Slack

SLACK_WEBHOOK="https://hooks.slack.com/services/YOUR/SLACK/WEBHOOK"
REPO_PATH="/path/to/monitored/repo"
REPO_NAME="critical-project"

# Function to send Slack notification
send_slack_notification() {
    local message="$1"
    local emoji="$2"

    curl -X POST -H 'Content-type: application/json' \
        --data "{
            \"text\":\"$emoji Hyperion Analysis: $message\",
            \"username\":\"hyperion-bot\"
        }" \
        "$SLACK_WEBHOOK"
}

# Monitor function
monitor_repo() {
    local current_commit=$(git -C "$REPO_PATH" rev-parse HEAD)
    local stored_commit=""

    if [ -f ".monitoring_state" ]; then
        stored_commit=$(cat .monitoring_state)
    fi

    if [ "$current_commit" != "$stored_commit" ]; then
        echo "🔄 Repository changed, running analysis..."

        # Profile repository
        if hyperion profile "$REPO_PATH" --name "$REPO_NAME"; then
            # Generate documentation
            hyperion generate "data/repositories/$REPO_NAME/profile.yaml"

            # Extract metrics
            commits=$(grep "commits:" "data/repositories/$REPO_NAME/profile.yaml" | cut -d' ' -f4)
            contributors=$(grep "contributors:" "data/repositories/$REPO_NAME/profile.yaml" | cut -d' ' -f4)

            # Save state
            echo "$current_commit" > .monitoring_state

            # Notify success
            send_slack_notification \
                "Analysis updated for $REPO_NAME: $commits commits, $contributors contributors" \
                ":white_check_mark:"
        else
            # Notify error
            send_slack_notification \
                "Failed to analyze $REPO_NAME" \
                ":x:"
        fi
    fi
}

# Main monitoring loop
while true; do
    monitor_repo
    sleep 3600  # Check every hour
done
```

### 4. Pipeline CI/CD Integration

```yaml
# .github/workflows/hyperion-analysis.yml
name: Hyperion Code Analysis

on:
  push:
    branches: [main, develop]
  pull_request:
    branches: [main]

jobs:
  analyze:
    runs-on: ubuntu-latest

    steps:
    - name: Checkout code
      uses: actions/checkout@v3

    - name: Setup Python
      uses: actions/setup-python@v4
      with:
        python-version: '3.11'

    - name: Install Hyperion
      run: |
        git clone https://github.com/Ryckmat/Hyperion.git
        cd Hyperion
        pip install -e .

    - name: Run Hyperion Analysis
      run: |
        hyperion profile . --name "${{ github.event.repository.name }}"
        hyperion generate "data/repositories/${{ github.event.repository.name }}/profile.yaml" \
          --output analysis-report/

    - name: Upload Analysis Report
      uses: actions/upload-artifact@v3
      with:
        name: hyperion-analysis
        path: analysis-report/

    - name: Comment PR with Analysis
      if: github.event_name == 'pull_request'
      uses: actions/github-script@v6
      with:
        script: |
          const fs = require('fs');
          const path = 'analysis-report/index.md';
          if (fs.existsSync(path)) {
            const analysis = fs.readFileSync(path, 'utf8');
            const comment = `## 📊 Hyperion Code Analysis\n\n${analysis}`;

            github.rest.issues.createComment({
              issue_number: context.issue.number,
              owner: context.repo.owner,
              repo: context.repo.repo,
              body: comment
            });
          }
```

---

## 🔧 Troubleshooting

### Problèmes Courants et Solutions

#### 1. Erreur : "Repository not found"

```bash
# Problème
hyperion profile /path/to/repo
# ❌ Error: Repository not found or not a Git repository

# Solutions
# 1. Vérifier que le chemin existe
ls -la /path/to/repo

# 2. Vérifier que c'est un repository Git
ls -la /path/to/repo/.git

# 3. Initialiser Git si nécessaire
cd /path/to/repo && git init

# 4. Vérifier les permissions
stat /path/to/repo
```

#### 2. Erreur : "Permission denied"

```bash
# Problème
hyperion profile /root/secure-repo
# ❌ Error: Permission denied

# Solutions
# 1. Changer les permissions
sudo chown -R $USER:$USER /path/to/repo

# 2. Utiliser sudo (non recommandé)
sudo hyperion profile /root/secure-repo

# 3. Copier vers un répertoire accessible
cp -r /root/secure-repo /tmp/my-repo
hyperion profile /tmp/my-repo
```

#### 3. Erreur : Neo4j connection failed

```bash
# Problème
hyperion ingest profile.yaml
# ❌ Error: Failed to connect to Neo4j

# Diagnostic
hyperion info
# Vérifier la section "🔧 Configuration Neo4j"

# Solutions
# 1. Vérifier que Neo4j fonctionne
docker ps | grep neo4j
# ou
systemctl status neo4j

# 2. Tester la connexion
telnet localhost 7687

# 3. Vérifier les credentials
export NEO4J_PASSWORD=correct_password
hyperion ingest profile.yaml

# 4. Utiliser une connexion explicite
hyperion ingest profile.yaml \
    --uri bolt://localhost:7687 \
    --user neo4j \
    --password your_password
```

#### 4. Erreur : "Template not found"

```bash
# Problème
hyperion generate profile.yaml
# ❌ Error: Template not found

# Diagnostic
hyperion info
# Vérifier "TEMPLATES_DIR"

# Solutions
# 1. Vérifier l'existence des templates
ls -la src/hyperion/templates/markdown/

# 2. Réinstaller Hyperion
pip install -e . --force-reinstall

# 3. Définir le chemin manuellement
export HYPERION_TEMPLATES_DIR=/full/path/to/templates
```

#### 5. Performance Issues

```bash
# Problème : Analyse très lente

# Solutions de performance
# 1. Réduire les batch sizes
export BATCH_SIZE_COMMITS=100
export BATCH_SIZE_FILES=50

# 2. Augmenter les timeouts
export GIT_OPERATION_TIMEOUT=600

# 3. Exclure des gros fichiers
# Modifier config/filters.yaml :
ignore_extensions:
  - .zip
  - .tar.gz
  - .iso

# 4. Analyser par branches spécifiques
export GIT_ANALYZE_BRANCHES=main
```

#### 6. Memory Issues

```bash
# Problème : Out of memory

# Solutions
# 1. Limiter la mémoire utilisée
export MAX_MEMORY_USAGE_MB=512
export MAX_FILE_SIZE_MB=5

# 2. Traitement par chunks
export BATCH_SIZE_COMMITS=100

# 3. Nettoyer les caches
rm -rf data/cache/
rm -rf __pycache__/

# 4. Augmenter la mémoire disponible
ulimit -m 2097152  # 2GB
```

### Logs et Debug

#### Activation des logs détaillés

```bash
# Mode debug complet
export LOG_LEVEL=DEBUG
export VERBOSE_OUTPUT=true
export DEBUG_MODE=true

# Exécution avec logs
hyperion profile /path/to/repo 2>&1 | tee analysis.log

# Logs spécifiques par composant
export LOG_LEVEL=DEBUG
hyperion info  # Vérifier config
```

#### Fichiers de log

```bash
# Localisation des logs
ls -la logs/
# - hyperion.log (log principal)
# - git_analysis.log (logs Git)
# - neo4j_operations.log (logs Neo4j)

# Consultation des logs
tail -f logs/hyperion.log

# Recherche d'erreurs
grep -i error logs/hyperion.log
grep -i warning logs/hyperion.log
```

### Diagnostic Système

#### Script de diagnostic complet

```bash
#!/bin/bash
# diagnostic.sh - Diagnostic complet Hyperion

echo "🔍 HYPERION DIAGNOSTIC REPORT"
echo "================================"

# 1. Version et installation
echo "📦 Installation:"
which hyperion
hyperion --version
pip show hyperion 2>/dev/null || echo "  ❌ Package not found"

# 2. Configuration
echo ""
echo "⚙️ Configuration:"
hyperion info

# 3. Dependencies
echo ""
echo "🔗 Dependencies:"
python -c "import click; print(f'  ✅ Click: {click.__version__}')" 2>/dev/null || echo "  ❌ Click not found"
python -c "import yaml; print(f'  ✅ PyYAML: {yaml.__version__}')" 2>/dev/null || echo "  ❌ PyYAML not found"
python -c "import jinja2; print(f'  ✅ Jinja2: {jinja2.__version__}')" 2>/dev/null || echo "  ❌ Jinja2 not found"

# 4. File system
echo ""
echo "📁 File System:"
echo "  Data dir: $(ls -ld data/ 2>/dev/null || echo 'Not found')"
echo "  Output dir: $(ls -ld output/ 2>/dev/null || echo 'Not found')"
echo "  Config dir: $(ls -ld config/ 2>/dev/null || echo 'Not found')"

# 5. Services
echo ""
echo "🌐 Services:"
# Test Neo4j
if command -v docker &> /dev/null; then
    docker ps | grep neo4j >/dev/null && echo "  ✅ Neo4j (Docker)" || echo "  ❌ Neo4j not running"
fi

# Test Git
git --version >/dev/null 2>&1 && echo "  ✅ Git available" || echo "  ❌ Git not found"

# 6. Recent activity
echo ""
echo "📊 Recent Analysis:"
if [ -d "data/repositories" ]; then
    find data/repositories -name "profile.yaml" -exec echo "  - {}" \; | head -5
else
    echo "  No repositories analyzed yet"
fi

echo ""
echo "✅ Diagnostic complete"
```

### Recovery Procedures

#### Reset complet

```bash
#!/bin/bash
# reset.sh - Reset complet de Hyperion

echo "🔄 HYPERION COMPLETE RESET"
read -p "Are you sure? This will delete all data. [y/N] " -n 1 -r
echo
if [[ ! $REPLY =~ ^[Yy]$ ]]; then
    exit 1
fi

# 1. Stop services
docker stop neo4j qdrant 2>/dev/null || true

# 2. Clean data
rm -rf data/repositories/
rm -rf output/
rm -rf logs/
rm -rf mlruns/
rm -rf .monitoring_state

# 3. Recreate directories
mkdir -p data/repositories
mkdir -p output
mkdir -p logs

# 4. Reset configuration
cp .env.example .env

echo "✅ Reset complete. Please reconfigure your .env file."
```

---

Cette documentation CLI complète couvre tous les aspects d'utilisation d'Hyperion v2.7. Pour des questions spécifiques ou des problèmes non couverts, consultez les logs détaillés ou utilisez le script de diagnostic fourni.