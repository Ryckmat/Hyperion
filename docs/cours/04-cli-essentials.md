---
title: "Chapitre 04 - CLI Essentials"
toc: true
description: "Maîtriser l'interface ligne de commande : Les 5 commandes principales d'Hyperion"
weight: 5
---

**Maîtriser l'interface ligne de commande** - Les 5 commandes principales d'Hyperion

*⏱️ Durée estimée : 45 minutes*

---

## 🎯 **Objectifs de ce Chapitre**

À la fin de ce chapitre, vous maîtriserez :
- ✅ Les 5 commandes principales : `profile`, `generate`, `ingest`, `info`, `serve`
- ✅ Toutes les options et paramètres avancés
- ✅ Workflows pour différents cas d'usage
- ✅ Bonnes pratiques et optimisation

---

## 📋 **Vue d'ensemble du CLI Hyperion**

### 🔧 **Structure Générale**

```bash
hyperion [COMMANDE] [OPTIONS] [ARGUMENTS]

# Aide générale
hyperion --help

# Aide spécifique à une commande
hyperion profile --help
```

### 🎯 **Les 5 Commandes Essentielles**

| Commande | Usage Principal | Temps Typique |
|----------|----------------|---------------|
| `profile` | Analyser un repository | 10s - 5min |
| `generate` | Générer documentation | 5s - 30s |
| `ingest` | Indexer pour RAG/ML | 30s - 10min |
| `info` | Diagnostic système | <1s |
| `serve` | Démarrer API/Web | Continue |

---

## 🔍 **Commande 1 : `hyperion profile`**

### 🎯 **Usage Principal**

La commande `profile` analyse en profondeur un repository Git pour extraire métriques, insights et patterns.

### 📋 **Syntaxe de Base**

```bash
# Syntaxe générale
hyperion profile [REPOSITORY_PATH] [OPTIONS]

# Exemples simples
hyperion profile .                    # Repository actuel
hyperion profile ~/mon-projet        # Chemin spécifique
hyperion profile https://github.com/user/repo  # URL Git
```

### ⚙️ **Options Principales**

#### 📊 **Niveau d'Analyse**
```bash
# Analyse rapide (métriques de base seulement)
hyperion profile . --fast

# Analyse complète (incluant ML et prédictions)
hyperion profile . --detailed

# Analyse avec historique approfondi
hyperion profile . --deep-history --git-depth 1000
```

#### 📄 **Formats de Sortie**
```bash
# Sortie console (par défaut)
hyperion profile .

# Export JSON
hyperion profile . --format json --output results.json

# Export YAML
hyperion profile . --format yaml --output results.yaml

# Export CSV (métriques seulement)
hyperion profile . --format csv --output metrics.csv
```

#### 🔍 **Filtres et Exclusions**
```bash
# Exclure des dossiers
hyperion profile . --exclude "node_modules,venv,__pycache__,.git"

# Inclure seulement certains fichiers
hyperion profile . --include "*.py,*.js,*.md"

# Filtrer par taille de fichier
hyperion profile . --max-file-size 1MB

# Filtrer par date de modification
hyperion profile . --since "2024-01-01"
```

#### 🎯 **Analyses Spécialisées**
```bash
# Focus sur la qualité de code
hyperion profile . --focus quality

# Focus sur l'équipe et collaboration
hyperion profile . --focus team

# Focus sur l'architecture
hyperion profile . --focus architecture

# Focus sur la sécurité
hyperion profile . --focus security
```

### 💡 **Exemples Pratiques**

#### 🚀 **Analyse Rapide Quotidienne**
```bash
# Analyse rapide pour standup meeting
hyperion profile . --fast --format json | jq '.summary'
```

#### 📊 **Rapport Hebdomadaire**
```bash
# Analyse détaillée pour rapport équipe
hyperion profile . --detailed --since "7 days ago" --output weekly_report.json
```

#### 🔍 **Audit Code Legacy**
```bash
# Analyse approfondie projet legacy
hyperion profile ~/legacy-project \
  --deep-history \
  --focus quality \
  --include "*.py,*.java,*.cs" \
  --output legacy_audit.yaml
```

#### 👥 **Analyse Post-Sprint**
```bash
# Analyse des changements récents
hyperion profile . \
  --since "2024-12-01" \
  --focus team \
  --detailed \
  --format json
```

### 📊 **Comprendre les Résultats**

#### 🏗️ **Section Architecture**
```json
{
  "architecture": {
    "complexity_score": 6.2,
    "maintainability_index": 78,
    "technical_debt_ratio": 0.12,
    "modularity_score": 0.85,
    "coupling": {
      "afferent": 23,
      "efferent": 45,
      "instability": 0.66
    }
  }
}
```

#### 👥 **Section Team Analytics**
```json
{
  "team": {
    "active_contributors": 15,
    "collaboration_score": 8.1,
    "knowledge_distribution": 0.73,
    "commit_patterns": {
      "avg_commit_size": 45,
      "commits_per_day": 12.5,
      "peak_hours": [9, 14, 16]
    }
  }
}
```

---

## 📚 **Commande 2 : `hyperion generate`**

### 🎯 **Usage Principal**

Génère automatiquement de la documentation, des rapports et des artefacts basés sur l'analyse du code.

### 📋 **Syntaxe de Base**

```bash
# Syntaxe générale
hyperion generate [REPOSITORY_PATH] [OPTIONS]

# Exemples
hyperion generate . --type readme
hyperion generate ~/projet --type docs --output ./documentation/
```

### 🎨 **Types de Documentation**

#### 📖 **README Automatique**
```bash
# README intelligent
hyperion generate . --type readme

# Avec badges et métriques
hyperion generate . --type readme --include-badges --include-metrics

# README personnalisé pour l'équipe
hyperion generate . --type readme --template team --lang fr
```

#### 🏗️ **Documentation Architecture**
```bash
# Documentation complète architecture
hyperion generate . --type architecture

# Diagrammes inclus
hyperion generate . --type architecture --include-diagrams

# Focus sur les patterns
hyperion generate . --type architecture --focus-patterns
```

#### 👥 **Guide Développeur**
```bash
# Guide de contribution
hyperion generate . --type contributing

# Guide d'onboarding
hyperion generate . --type onboarding

# Standards de l'équipe
hyperion generate . --type team-standards
```

#### 📊 **Rapports Business**
```bash
# Rapport exécutif
hyperion generate . --type executive-summary

# Métriques qualité
hyperion generate . --type quality-report

# Analyse des risques
hyperion generate . --type risk-assessment
```

### ⚙️ **Options Avancées**

#### 🎨 **Personnalisation**
```bash
# Templates personnalisés
hyperion generate . --template ./templates/custom.md

# Langues
hyperion generate . --lang fr  # français
hyperion generate . --lang en  # anglais (défaut)

# Thème visuel
hyperion generate . --theme corporate
hyperion generate . --theme minimal
hyperion generate . --theme developer
```

#### 📊 **Contenu Dynamique**
```bash
# Inclure métriques en temps réel
hyperion generate . --include-metrics

# Inclure graphiques
hyperion generate . --include-charts

# Inclure code samples
hyperion generate . --include-examples

# Inclure roadmap automatique
hyperion generate . --include-roadmap
```

### 💡 **Workflows de Génération**

#### 📅 **Documentation Continue**
```bash
# Script pour CI/CD
#!/bin/bash
hyperion generate . --type docs --output docs/ --format markdown
git add docs/
git commit -m "docs: update auto-generated documentation"
```

#### 🎯 **Rapport Mensuel**
```bash
# Génération rapport mensuel
hyperion generate . \
  --type monthly-report \
  --since "30 days ago" \
  --include-metrics \
  --include-charts \
  --output reports/$(date +%Y-%m).md
```

---

## 🗄️ **Commande 3 : `hyperion ingest`**

### 🎯 **Usage Principal**

Indexe le repository dans Neo4j pour permettre les requêtes RAG, ML et recherche sémantique.

### 📋 **Syntaxe de Base**

```bash
# Syntaxe générale
hyperion ingest [REPOSITORY_PATH] [OPTIONS]

# Exemples
hyperion ingest .                    # Indexation complète
hyperion ingest . --update          # Mise à jour incrémentale
hyperion ingest . --force           # Re-indexation complète
```

### 🔄 **Modes d'Indexation**

#### 🆕 **Indexation Initiale**
```bash
# Première indexation (complète)
hyperion ingest ~/mon-projet --initial

# Avec nettoyage préalable
hyperion ingest ~/mon-projet --clean --initial
```

#### ⚡ **Mise à jour Incrémentale**
```bash
# Indexer seulement les changements
hyperion ingest . --update

# Depuis une date spécifique
hyperion ingest . --update --since "2024-12-20"

# Auto-détection des changements
hyperion ingest . --smart-update
```

#### 🔄 **Re-indexation**
```bash
# Forcer une re-indexation complète
hyperion ingest . --force

# Re-indexer avec nouvelle configuration
hyperion ingest . --force --config new-config.yaml
```

### 🎯 **Options Spécialisées**

#### 📚 **Types de Contenu**
```bash
# Indexer seulement le code
hyperion ingest . --content code

# Indexer seulement la documentation
hyperion ingest . --content docs

# Indexer l'historique Git
hyperion ingest . --content history

# Tout indexer
hyperion ingest . --content all  # (défaut)
```

#### 🔍 **Configuration Vectorielle**
```bash
# Modèle d'embedding spécifique
hyperion ingest . --embedding-model all-MiniLM-L6-v2

# Taille des chunks
hyperion ingest . --chunk-size 512 --chunk-overlap 50

# Filtres pour vectorisation
hyperion ingest . --vector-filter "*.py,*.md,*.txt"
```

#### 📊 **Features ML**
```bash
# Extraction des features ML
hyperion ingest . --extract-features

# Features spécialisées
hyperion ingest . --features quality,team,security

# Cache des features
hyperion ingest . --cache-features --cache-ttl 3600
```

### 📈 **Monitoring de l'Indexation**

```bash
# Indexation avec progress bar
hyperion ingest . --progress

# Mode verbose
hyperion ingest . --verbose

# Logs détaillés
hyperion ingest . --debug --log-file indexation.log
```

### 🎯 **Workflows d'Indexation**

#### 🔄 **Indexation Continue (CI/CD)**
```bash
# Dans votre pipeline CI/CD
# .github/workflows/hyperion.yml
- name: Update Hyperion Index
  run: |
    hyperion ingest . --update --smart
    hyperion health --check-index
```

#### 📅 **Indexation Programmée**
```bash
# Cron job pour indexation nocturne
# crontab -e
# 0 2 * * * cd /path/to/repo && hyperion ingest . --update
```

---

## ℹ️ **Commande 4 : `hyperion info`**

### 🎯 **Usage Principal**

Diagnostic complet du système Hyperion et des services connectés.

### 📋 **Informations Système**

```bash
# Informations de base
hyperion info

# Sortie détaillée
hyperion info --detailed

# Format JSON pour scripts
hyperion info --format json
```

### 🔍 **Diagnostics Spécialisés**

#### 🏥 **Santé des Services**
```bash
# Check complet des services
hyperion info --health

# Test de connectivité
hyperion info --connectivity

# Performance des services
hyperion info --performance
```

#### 📊 **Métriques Système**
```bash
# Utilisation des ressources
hyperion info --resources

# Statistiques des databases
hyperion info --database-stats

# Métriques ML
hyperion info --ml-metrics
```

#### 🔧 **Configuration Active**
```bash
# Configuration actuelle
hyperion info --config

# Variables d'environnement
hyperion info --env

# Chemins et fichiers
hyperion info --paths
```

### 💡 **Exemples d'Usage**

#### 🐛 **Debug d'un Problème**
```bash
# Diagnostic complet pour troubleshooting
hyperion info --detailed --health --resources > debug_report.txt
```

#### 📊 **Monitoring de Production**
```bash
# Script de monitoring
#!/bin/bash
STATUS=$(hyperion info --health --format json | jq -r '.status')
if [ "$STATUS" != "healthy" ]; then
  echo "ALERT: Hyperion unhealthy" | mail admin@company.com
fi
```

---

## 🌐 **Commande 5 : `hyperion serve`**

### 🎯 **Usage Principal**

Démarre l'API REST et l'interface web d'Hyperion.

### 📋 **Démarrage Standard**

```bash
# Démarrage par défaut (port 8000)
hyperion serve

# Port personnalisé
hyperion serve --port 8080

# Host spécifique
hyperion serve --host 0.0.0.0 --port 8000
```

### ⚙️ **Modes de Démarrage**

#### 🔧 **Mode Développement**
```bash
# Mode dev avec auto-reload
hyperion serve --dev

# Debug activé
hyperion serve --debug --log-level DEBUG

# CORS permissif pour développement
hyperion serve --dev --cors-all
```

#### 🚀 **Mode Production**
```bash
# Production avec optimisations
hyperion serve --production

# Avec worker processes multiples
hyperion serve --workers 4

# Avec SSL
hyperion serve --ssl-cert cert.pem --ssl-key key.pem
```

#### 🎯 **Services Spécifiques**
```bash
# API seulement (pas d'interface web)
hyperion serve --api-only

# Interface web seulement
hyperion serve --web-only

# OpenAI compatible API seulement
hyperion serve --openai-api
```

### 📊 **Configuration Avancée**

```bash
# Configuration personnalisée
hyperion serve --config ~/hyperion-prod.yaml

# Limite de ressources
hyperion serve --max-memory 4GB --max-cpu 80%

# Cache configuration
hyperion serve --cache-size 2GB --cache-ttl 3600
```

---

## 🔄 **Workflows Avancés**

### 1️⃣ **Workflow Analyse Complète**

```bash
#!/bin/bash
# complete_analysis.sh

REPO_PATH=${1:-.}
OUTPUT_DIR="./hyperion-analysis"

echo "🚀 Starting complete Hyperion analysis..."

# 1. Profile the repository
echo "📊 Profiling repository..."
hyperion profile "$REPO_PATH" --detailed --output "$OUTPUT_DIR/profile.json"

# 2. Ingest for ML and RAG
echo "🗄️ Ingesting repository..."
hyperion ingest "$REPO_PATH" --extract-features

# 3. Generate documentation
echo "📚 Generating documentation..."
hyperion generate "$REPO_PATH" --type docs --output "$OUTPUT_DIR/docs/"

# 4. Health check
echo "🏥 Checking system health..."
hyperion info --health

echo "✅ Complete analysis finished!"
echo "📁 Results in: $OUTPUT_DIR"
```

### 2️⃣ **Workflow Monitoring Continu**

```bash
#!/bin/bash
# monitor_repositories.sh

REPOS_FILE="repositories.txt"

while IFS= read -r repo; do
  echo "📊 Analyzing $repo..."

  # Quick profile
  hyperion profile "$repo" --fast --format json > "reports/$(basename $repo).json"

  # Update index
  hyperion ingest "$repo" --update --smart

  # Check for anomalies
  ANOMALIES=$(hyperion predict "$repo" --type anomaly --format json | jq '.anomalies | length')

  if [ "$ANOMALIES" -gt 0 ]; then
    echo "⚠️ Anomalies detected in $repo"
    # Send notification
  fi

done < "$REPOS_FILE"
```

### 3️⃣ **Workflow CI/CD Integration**

```yaml
# .github/workflows/hyperion-analysis.yml
name: Hyperion Code Analysis

on:
  push:
    branches: [main, develop]
  pull_request:
    branches: [main]

jobs:
  hyperion-analysis:
    runs-on: ubuntu-latest

    steps:
    - uses: actions/checkout@v3
      with:
        fetch-depth: 0  # Full history for better analysis

    - name: Setup Python
      uses: actions/setup-python@v4
      with:
        python-version: '3.10'

    - name: Install Hyperion
      run: pip install hyperion==2.7.0

    - name: Start Services
      run: |
        # Setup minimal services for CI
        docker run -d --name redis redis:alpine
        docker run -d --name neo4j -e NEO4J_AUTH=none neo4j:4.4-community

    - name: Analyze Code
      run: |
        hyperion profile . --fast --format json --output analysis.json

    - name: Check Quality Gates
      run: |
        # Quality gates
        COMPLEXITY=$(cat analysis.json | jq '.architecture.complexity_score')
        MAINTAINABILITY=$(cat analysis.json | jq '.architecture.maintainability_index')

        if (( $(echo "$COMPLEXITY > 7.0" | bc -l) )); then
          echo "❌ Complexity too high: $COMPLEXITY"
          exit 1
        fi

        if (( $(echo "$MAINTAINABILITY < 60" | bc -l) )); then
          echo "❌ Maintainability too low: $MAINTAINABILITY"
          exit 1
        fi

    - name: Upload Results
      uses: actions/upload-artifact@v3
      with:
        name: hyperion-analysis
        path: analysis.json
```

---

## 🛠️ **Configuration Avancée**

### 📄 **Fichier de Configuration Global**

`~/.hyperion/config.yaml` :

```yaml
# Configuration CLI globale
cli:
  default_format: "json"
  default_output_dir: "~/hyperion-results"
  auto_open_results: true
  progress_bar: true

# Profils prédéfinis
profiles:
  quick:
    profile:
      fast: true
      exclude: "node_modules,venv,__pycache__"
    generate:
      type: "readme"

  complete:
    profile:
      detailed: true
      deep_history: true
    ingest:
      extract_features: true
    generate:
      type: "docs"
      include_charts: true

# Aliases de commandes
aliases:
  analyze: "profile --detailed"
  docs: "generate --type docs"
  update: "ingest --update"
```

### 🎯 **Utilisation des Profils**

```bash
# Utiliser un profil prédéfini
hyperion --profile quick analyze ~/mon-projet

# Combiner avec des options
hyperion --profile complete analyze ~/mon-projet --output ./results/
```

---

## 📊 **Performance et Optimisation**

### ⚡ **Optimisations Communes**

#### 🚀 **Analyse Rapide**
```bash
# Pour repositories > 100k files
hyperion profile . \
  --fast \
  --exclude "node_modules,venv,dist,build" \
  --max-file-size 1MB \
  --git-depth 100
```

#### 🎯 **Focus Spécialisé**
```bash
# Focus seulement sur la qualité
hyperion profile . --focus quality --include "*.py,*.js"

# Focus équipe
hyperion profile . --focus team --since "30 days ago"
```

### 📈 **Mise en Cache**

```bash
# Utiliser le cache pour analyses répétées
hyperion profile . --use-cache --cache-ttl 3600

# Nettoyer le cache si nécessaire
hyperion clean-cache
```

---

## 🎉 **Maîtrise du CLI !**

### ✅ **Ce que Vous Maîtrisez Maintenant**

- 🔍 **`profile`** : Analyse complète avec toutes les options
- 📚 **`generate`** : Documentation automatique personnalisée
- 🗄️ **`ingest`** : Indexation pour RAG et ML
- ℹ️ **`info`** : Diagnostic système complet
- 🌐 **`serve`** : API et interface web

### 🚀 **Workflows Professionnels**

- Analyse complète automatisée
- Intégration CI/CD
- Monitoring continu
- Configuration avancée

### 📈 **Prochaines Étapes**

Vous êtes maintenant expert du CLI Hyperion !

👉 **Continuez avec** : [Chapitre 05 - API Basics](05-api-basics)

Au prochain chapitre :
- API REST complète
- Intégration OpenAI
- Code Intelligence v2
- Exemples pratiques

---

## 📖 **Récapitulatif du Chapitre**

### ✅ **Commandes Maîtrisées :**
- **profile** : Analyse repository (fast, detailed, focus)
- **generate** : Documentation automatique (readme, docs, reports)
- **ingest** : Indexation pour RAG/ML (update, force, features)
- **info** : Diagnostic système (health, config, performance)
- **serve** : API/Web server (dev, production, SSL)

### 🔧 **Compétences Acquises :**
- Workflows avancés et automation
- Configuration et optimisation
- Intégration CI/CD
- Troubleshooting et monitoring

---

*Excellent ! Vous maîtrisez maintenant complètement le CLI d'Hyperion. Rendez-vous au [Chapitre 05](05-api-basics) !* 💪

---

*Cours Hyperion - Chapitre 04*