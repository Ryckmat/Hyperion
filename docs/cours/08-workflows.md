# ⚡ Chapitre 08 - Workflows

**Workflows avancés et automatisation** - Intégrer Hyperion dans vos processus

*⏱️ Durée estimée : 60 minutes*

---

## 🎯 **Objectifs de ce Chapitre**

À la fin de ce chapitre, vous saurez :
- ✅ Créer des workflows automatisés complets
- ✅ Intégrer Hyperion dans vos pipelines CI/CD
- ✅ Configurer un monitoring continu
- ✅ Orchestrer des tâches complexes multi-repositories

---

## 🔄 **Types de Workflows**

### 1️⃣ **Workflow d'Analyse Continue**
- Analyse automatique à chaque push
- Quality gates et alertes
- Rapports périodiques

### 2️⃣ **Workflow de Monitoring**
- Surveillance proactive des métriques
- Détection d'anomalies en temps réel
- Alertes intelligentes

### 3️⃣ **Workflow de Documentation**
- Génération automatique de docs
- Mise à jour continue
- Synchronisation avec le code

### 4️⃣ **Workflow d'Onboarding**
- Analyse pour nouveaux développeurs
- Guide personnalisé
- Knowledge base automatique

---

## 🚀 **Workflow 1 : CI/CD Integration**

### 🏗️ **GitHub Actions Complet**

```yaml
# .github/workflows/hyperion-analysis.yml
name: Hyperion Code Analysis

on:
  push:
    branches: [main, develop]
  pull_request:
    branches: [main]
  schedule:
    - cron: '0 2 * * *'  # Daily at 2 AM

env:
  HYPERION_VERSION: "2.7.0"

jobs:
  hyperion-analysis:
    runs-on: ubuntu-latest
    timeout-minutes: 30

    services:
      redis:
        image: redis:alpine
        options: >-
          --health-cmd "redis-cli ping"
          --health-interval 10s
          --health-timeout 5s
          --health-retries 5

      neo4j:
        image: neo4j:4.4-community
        env:
          NEO4J_AUTH: none
        options: >-
          --health-cmd "cypher-shell 'RETURN 1'"
          --health-interval 10s
          --health-timeout 5s
          --health-retries 5

    steps:
    - name: Checkout Code
      uses: actions/checkout@v4
      with:
        fetch-depth: 0  # Full history for better analysis

    - name: Setup Python
      uses: actions/setup-python@v4
      with:
        python-version: '3.10'

    - name: Cache Hyperion Installation
      uses: actions/cache@v3
      with:
        path: ~/.cache/pip
        key: ${{ runner.os }}-pip-hyperion-${{ env.HYPERION_VERSION }}

    - name: Install Hyperion
      run: |
        pip install hyperion==${{ env.HYPERION_VERSION }}
        hyperion --version

    - name: Setup Ollama
      run: |
        curl -fsSL https://ollama.ai/install.sh | sh
        ollama serve &
        sleep 10
        ollama pull llama3.2:1b

    - name: Configure Hyperion
      run: |
        mkdir -p ~/.hyperion
        cat > ~/.hyperion/config.yaml << EOF
        services:
          neo4j:
            url: "bolt://localhost:7687"
            user: "neo4j"
            password: ""
          redis:
            url: "redis://localhost:6379"
          ollama:
            url: "http://localhost:11434"
            default_model: "llama3.2:1b"
        EOF

    - name: Health Check
      run: |
        hyperion health
        if [ $? -ne 0 ]; then
          echo "❌ Hyperion services not ready"
          exit 1
        fi

    - name: Repository Analysis
      id: analysis
      run: |
        # Analyse complète
        hyperion profile . \
          --detailed \
          --format json \
          --output analysis.json

        # Extraire métriques clés
        COMPLEXITY=$(cat analysis.json | jq -r '.architecture.complexity_score')
        MAINTAINABILITY=$(cat analysis.json | jq -r '.architecture.maintainability_index')
        TECH_DEBT=$(cat analysis.json | jq -r '.architecture.technical_debt_ratio')

        echo "complexity=$COMPLEXITY" >> $GITHUB_OUTPUT
        echo "maintainability=$MAINTAINABILITY" >> $GITHUB_OUTPUT
        echo "tech_debt=$TECH_DEBT" >> $GITHUB_OUTPUT

    - name: ML Predictions
      run: |
        # Indexation pour ML
        hyperion ingest . --extract-features

        # Prédictions de risques
        hyperion predict . --type risk --output risks.json

        # Détection d'anomalies
        hyperion predict . --type anomaly --output anomalies.json

    - name: Quality Gates
      run: |
        # Quality gates
        COMPLEXITY=${{ steps.analysis.outputs.complexity }}
        MAINTAINABILITY=${{ steps.analysis.outputs.maintainability }}

        echo "📊 Quality Metrics:"
        echo "Complexity: $COMPLEXITY"
        echo "Maintainability: $MAINTAINABILITY"

        # Vérifications
        if (( $(echo "$COMPLEXITY > 7.0" | bc -l) )); then
          echo "❌ Complexity too high: $COMPLEXITY (limit: 7.0)"
          echo "::error::Code complexity exceeds threshold"
          exit 1
        fi

        if (( $(echo "$MAINTAINABILITY < 60" | bc -l) )); then
          echo "❌ Maintainability too low: $MAINTAINABILITY (minimum: 60)"
          echo "::error::Code maintainability below threshold"
          exit 1
        fi

        # Vérifier risques élevés
        HIGH_RISK_COUNT=$(cat risks.json | jq '[.risk_predictions[] | select(.risk_score > 0.8)] | length')
        if [ "$HIGH_RISK_COUNT" -gt 3 ]; then
          echo "⚠️ Too many high-risk files: $HIGH_RISK_COUNT"
          echo "::warning::Consider refactoring high-risk components"
        fi

        echo "✅ All quality gates passed"

    - name: Generate Documentation
      run: |
        # Documentation automatique
        hyperion generate . \
          --type docs \
          --include-metrics \
          --include-charts \
          --output docs/generated/

        # README mis à jour
        hyperion generate . \
          --type readme \
          --include-badges \
          --output README_updated.md

    - name: Comment PR with Analysis
      if: github.event_name == 'pull_request'
      uses: actions/github-script@v7
      with:
        script: |
          const fs = require('fs');
          const analysis = JSON.parse(fs.readFileSync('analysis.json', 'utf8'));
          const risks = JSON.parse(fs.readFileSync('risks.json', 'utf8'));

          // Créer le commentaire
          let comment = `## 🤖 Hyperion Analysis Report\n\n`;
          comment += `### 📊 Quality Metrics\n`;
          comment += `- **Complexity**: ${analysis.architecture.complexity_score}/10\n`;
          comment += `- **Maintainability**: ${analysis.architecture.maintainability_index}/100\n`;
          comment += `- **Technical Debt**: ${(analysis.architecture.technical_debt_ratio * 100).toFixed(1)}%\n\n`;

          // Risques élevés
          const highRiskFiles = risks.risk_predictions.filter(r => r.risk_score > 0.7);
          if (highRiskFiles.length > 0) {
            comment += `### ⚠️ High Risk Files\n`;
            highRiskFiles.forEach(file => {
              comment += `- \`${file.file}\` (risk: ${(file.risk_score * 100).toFixed(0)}%)\n`;
            });
            comment += `\n`;
          }

          comment += `### ✅ Recommendations\n`;
          comment += `- Review high-risk files before merging\n`;
          comment += `- Consider adding tests for complex modules\n`;
          comment += `- Check the generated documentation\n\n`;
          comment += `*Analysis generated by Hyperion v2.7.0*`;

          // Poster le commentaire
          github.rest.issues.createComment({
            issue_number: context.issue.number,
            owner: context.repo.owner,
            repo: context.repo.repo,
            body: comment
          });

    - name: Upload Analysis Artifacts
      uses: actions/upload-artifact@v3
      with:
        name: hyperion-analysis
        path: |
          analysis.json
          risks.json
          anomalies.json
          docs/generated/

    - name: Slack Notification
      if: failure()
      uses: 8398a7/action-slack@v3
      with:
        status: ${{ job.status }}
        text: |
          🔴 Hyperion Analysis Failed
          Repository: ${{ github.repository }}
          Branch: ${{ github.ref }}
          Commit: ${{ github.sha }}
        webhook_url: ${{ secrets.SLACK_WEBHOOK }}
```

### 🛠️ **GitLab CI Equivalent**

```yaml
# .gitlab-ci.yml
stages:
  - setup
  - analysis
  - quality-gates
  - reporting

variables:
  HYPERION_VERSION: "2.7.0"

.setup-services: &setup-services
  services:
    - redis:alpine
    - neo4j:4.4-community

.install-hyperion: &install-hyperion
  before_script:
    - pip install hyperion==$HYPERION_VERSION
    - hyperion health

hyperion-analysis:
  stage: analysis
  image: python:3.10
  <<: *setup-services
  <<: *install-hyperion
  script:
    - hyperion profile . --detailed --output analysis.json
    - hyperion ingest . --extract-features
    - hyperion predict . --type risk --output risks.json
  artifacts:
    reports:
      junit: analysis.json
    paths:
      - analysis.json
      - risks.json
    expire_in: 1 week

quality-gates:
  stage: quality-gates
  dependencies:
    - hyperion-analysis
  script:
    - |
      COMPLEXITY=$(cat analysis.json | jq -r '.architecture.complexity_score')
      if (( $(echo "$COMPLEXITY > 7.0" | bc -l) )); then
        echo "Complexity too high: $COMPLEXITY"
        exit 1
      fi
  only:
    - merge_requests
    - main

generate-docs:
  stage: reporting
  dependencies:
    - hyperion-analysis
  script:
    - hyperion generate . --type docs --output public/
  artifacts:
    paths:
      - public/
  only:
    - main
```

---

## 📊 **Workflow 2 : Monitoring Continu**

### 🔍 **Surveillance Multi-Repository**

```python
#!/usr/bin/env python3
# continuous_monitoring.py

import asyncio
import aiohttp
import json
import time
from datetime import datetime, timedelta
from dataclasses import dataclass
from typing import List, Dict
import smtplib
from email.mime.text import MimeText

@dataclass
class Repository:
    name: str
    path: str
    critical: bool = False
    team: str = "default"

@dataclass
class Alert:
    repo: str
    type: str
    severity: str  # "low", "medium", "high", "critical"
    message: str
    timestamp: datetime

class HyperionMonitor:
    def __init__(self, config_path="monitor_config.yaml"):
        self.config = self.load_config(config_path)
        self.repositories = self.load_repositories()
        self.alert_history = []

    async def monitor_repository(self, repo: Repository):
        """Monitoring d'un repository"""
        try:
            # Analyse rapide
            analysis = await self.quick_analysis(repo)

            # Vérifications qualité
            alerts = self.check_quality_alerts(repo, analysis)

            # Prédictions ML
            ml_alerts = await self.check_ml_alerts(repo)

            # Anomalies
            anomaly_alerts = await self.check_anomalies(repo)

            all_alerts = alerts + ml_alerts + anomaly_alerts

            # Traitement des alertes
            for alert in all_alerts:
                await self.handle_alert(alert)

            return {
                "repo": repo.name,
                "status": "healthy" if not all_alerts else "issues_detected",
                "alerts_count": len(all_alerts),
                "last_check": datetime.now().isoformat()
            }

        except Exception as e:
            error_alert = Alert(
                repo=repo.name,
                type="monitoring_error",
                severity="high",
                message=f"Monitoring failed: {str(e)}",
                timestamp=datetime.now()
            )
            await self.handle_alert(error_alert)
            return {"repo": repo.name, "status": "error", "error": str(e)}

    async def quick_analysis(self, repo: Repository):
        """Analyse rapide du repository"""
        cmd = f"hyperion profile {repo.path} --fast --format json"
        process = await asyncio.create_subprocess_shell(
            cmd,
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE
        )

        stdout, stderr = await process.communicate()

        if process.returncode == 0:
            return json.loads(stdout.decode())
        else:
            raise Exception(f"Analysis failed: {stderr.decode()}")

    def check_quality_alerts(self, repo: Repository, analysis: dict) -> List[Alert]:
        """Vérifier les alertes qualité"""
        alerts = []
        arch = analysis.get("architecture", {})

        # Complexité élevée
        complexity = arch.get("complexity_score", 0)
        if complexity > 8.0:
            alerts.append(Alert(
                repo=repo.name,
                type="high_complexity",
                severity="high" if complexity > 9.0 else "medium",
                message=f"Complexity score: {complexity:.1f} (threshold: 8.0)",
                timestamp=datetime.now()
            ))

        # Maintenabilité faible
        maintainability = arch.get("maintainability_index", 100)
        if maintainability < 50:
            alerts.append(Alert(
                repo=repo.name,
                type="low_maintainability",
                severity="high" if maintainability < 30 else "medium",
                message=f"Maintainability: {maintainability:.1f} (minimum: 50)",
                timestamp=datetime.now()
            ))

        # Dette technique élevée
        tech_debt = arch.get("technical_debt_ratio", 0)
        if tech_debt > 0.25:
            alerts.append(Alert(
                repo=repo.name,
                type="high_tech_debt",
                severity="medium",
                message=f"Technical debt: {tech_debt*100:.1f}% (threshold: 25%)",
                timestamp=datetime.now()
            ))

        return alerts

    async def check_ml_alerts(self, repo: Repository) -> List[Alert]:
        """Vérifier les alertes ML"""
        alerts = []

        try:
            # Prédictions de risques
            cmd = f"hyperion predict {repo.path} --type risk --format json"
            result = await self.run_command(cmd)
            risk_data = json.loads(result)

            # Fichiers à haut risque
            high_risk_files = [
                f for f in risk_data.get("risk_predictions", [])
                if f.get("risk_score", 0) > 0.8
            ]

            if len(high_risk_files) > 5:
                alerts.append(Alert(
                    repo=repo.name,
                    type="high_risk_files",
                    severity="high",
                    message=f"{len(high_risk_files)} files with high risk score",
                    timestamp=datetime.now()
                ))

            # Prédiction de bugs
            cmd = f"hyperion predict {repo.path} --type bugs --format json"
            result = await self.run_command(cmd)
            bug_data = json.loads(result)

            bug_probability = bug_data.get("bug_predictions", {}).get("overall_probability_30_days", 0)
            if bug_probability > 0.4:
                alerts.append(Alert(
                    repo=repo.name,
                    type="high_bug_probability",
                    severity="medium",
                    message=f"Bug probability (30d): {bug_probability*100:.1f}%",
                    timestamp=datetime.now()
                ))

        except Exception as e:
            print(f"ML alerts check failed for {repo.name}: {e}")

        return alerts

    async def check_anomalies(self, repo: Repository) -> List[Alert]:
        """Détection d'anomalies"""
        alerts = []

        try:
            cmd = f"hyperion predict {repo.path} --type anomaly --format json"
            result = await self.run_command(cmd)
            anomaly_data = json.loads(result)

            anomalies = anomaly_data.get("anomalies_detected", [])

            for anomaly in anomalies:
                if anomaly.get("confidence", 0) > 0.8:
                    severity = "high" if anomaly.get("impact_assessment") == "High" else "medium"
                    alerts.append(Alert(
                        repo=repo.name,
                        type="anomaly_detected",
                        severity=severity,
                        message=f"Anomaly: {anomaly.get('description', 'Unknown')}",
                        timestamp=datetime.now()
                    ))

        except Exception as e:
            print(f"Anomaly check failed for {repo.name}: {e}")

        return alerts

    async def handle_alert(self, alert: Alert):
        """Traiter une alerte"""
        self.alert_history.append(alert)

        # Déduplication
        if self.is_duplicate_alert(alert):
            return

        # Notification selon la sévérité
        if alert.severity in ["high", "critical"]:
            await self.send_immediate_notification(alert)
        elif alert.severity == "medium":
            await self.send_aggregated_notification(alert)

        # Log
        print(f"[{alert.timestamp}] {alert.severity.upper()}: {alert.repo} - {alert.message}")

    def is_duplicate_alert(self, alert: Alert) -> bool:
        """Vérifier si l'alerte est dupliquée"""
        # Chercher alertes similaires dans les 2 dernières heures
        cutoff = datetime.now() - timedelta(hours=2)
        recent_alerts = [a for a in self.alert_history if a.timestamp > cutoff]

        for existing_alert in recent_alerts:
            if (existing_alert.repo == alert.repo and
                existing_alert.type == alert.type and
                existing_alert.severity == alert.severity):
                return True

        return False

    async def send_immediate_notification(self, alert: Alert):
        """Notification immédiate pour alertes critiques"""
        # Slack
        await self.notify_slack(alert)

        # Email si critique
        if alert.severity == "critical":
            await self.notify_email(alert)

    async def notify_slack(self, alert: Alert):
        """Notification Slack"""
        webhook_url = self.config.get("slack_webhook")
        if not webhook_url:
            return

        severity_emoji = {
            "low": "🟡",
            "medium": "🟠",
            "high": "🔴",
            "critical": "🚨"
        }

        message = {
            "text": f"{severity_emoji.get(alert.severity, '❓')} Hyperion Alert",
            "attachments": [{
                "color": "danger" if alert.severity in ["high", "critical"] else "warning",
                "fields": [
                    {"title": "Repository", "value": alert.repo, "short": True},
                    {"title": "Type", "value": alert.type, "short": True},
                    {"title": "Severity", "value": alert.severity.upper(), "short": True},
                    {"title": "Message", "value": alert.message, "short": False}
                ],
                "ts": alert.timestamp.timestamp()
            }]
        }

        async with aiohttp.ClientSession() as session:
            await session.post(webhook_url, json=message)

    async def run_monitoring_cycle(self):
        """Cycle de monitoring complet"""
        print(f"🔍 Starting monitoring cycle at {datetime.now()}")

        # Monitoring en parallèle
        tasks = [self.monitor_repository(repo) for repo in self.repositories]
        results = await asyncio.gather(*tasks, return_exceptions=True)

        # Rapport de cycle
        healthy_count = sum(1 for r in results if isinstance(r, dict) and r.get("status") == "healthy")
        total_alerts = sum(r.get("alerts_count", 0) for r in results if isinstance(r, dict))

        print(f"✅ Monitoring cycle complete:")
        print(f"   - {healthy_count}/{len(self.repositories)} repositories healthy")
        print(f"   - {total_alerts} total alerts generated")

        return results

    async def run_continuous_monitoring(self, interval_minutes=30):
        """Monitoring continu"""
        while True:
            try:
                await self.run_monitoring_cycle()
            except Exception as e:
                print(f"❌ Monitoring cycle failed: {e}")

            # Attendre le prochain cycle
            await asyncio.sleep(interval_minutes * 60)

# Configuration
config = {
    "repositories": [
        {"name": "frontend", "path": "/projects/frontend", "critical": True, "team": "ui"},
        {"name": "backend", "path": "/projects/backend", "critical": True, "team": "api"},
        {"name": "mobile", "path": "/projects/mobile", "critical": False, "team": "mobile"}
    ],
    "slack_webhook": "https://hooks.slack.com/services/...",
    "email_smtp": {
        "host": "smtp.company.com",
        "port": 587,
        "username": "monitoring@company.com",
        "password": "password"
    }
}

# Lancement
if __name__ == "__main__":
    monitor = HyperionMonitor()
    asyncio.run(monitor.run_continuous_monitoring(interval_minutes=15))
```

---

## 📚 **Workflow 3 : Documentation Continue**

### 📄 **Auto-Documentation Pipeline**

```bash
#!/bin/bash
# docs_pipeline.sh

set -euo pipefail

PROJECT_ROOT=${1:-.}
DOCS_OUTPUT="docs/generated"
BRANCH_NAME=$(git branch --show-current)

echo "📚 Starting documentation pipeline for $PROJECT_ROOT"

# 1. Nettoyage
echo "🧹 Cleaning previous documentation..."
rm -rf "$DOCS_OUTPUT"
mkdir -p "$DOCS_OUTPUT"

# 2. Analyse du projet
echo "🔍 Analyzing project structure..."
hyperion profile "$PROJECT_ROOT" \
    --detailed \
    --format json \
    --output "$DOCS_OUTPUT/analysis.json"

# 3. Génération documentation architecture
echo "🏗️ Generating architecture documentation..."
hyperion generate "$PROJECT_ROOT" \
    --type architecture \
    --include-diagrams \
    --output "$DOCS_OUTPUT/architecture/"

# 4. Génération API docs (si applicable)
if [ -f "openapi.yaml" ] || [ -f "swagger.yaml" ]; then
    echo "📋 Generating API documentation..."
    hyperion generate "$PROJECT_ROOT" \
        --type api-docs \
        --include-examples \
        --output "$DOCS_OUTPUT/api/"
fi

# 5. Guide développeur
echo "👨‍💻 Generating developer guide..."
hyperion generate "$PROJECT_ROOT" \
    --type developer-guide \
    --include-setup \
    --output "$DOCS_OUTPUT/dev-guide/"

# 6. Métriques et rapports
echo "📊 Generating metrics report..."
hyperion generate "$PROJECT_ROOT" \
    --type metrics-report \
    --include-trends \
    --output "$DOCS_OUTPUT/metrics/"

# 7. README intelligent
echo "📖 Updating README..."
hyperion generate "$PROJECT_ROOT" \
    --type readme \
    --include-badges \
    --include-metrics \
    --template smart \
    --output "README_generated.md"

# 8. Index de navigation
echo "🗂️ Creating navigation index..."
cat > "$DOCS_OUTPUT/index.md" << EOF
# 📚 Documentation Projet

Documentation générée automatiquement le $(date)

## 🗂️ Sections Disponibles

### 🏗️ Architecture
- [Vue d'ensemble](architecture/overview.md)
- [Diagrammes](architecture/diagrams/)
- [Patterns](architecture/patterns.md)

### 👨‍💻 Guide Développeur
- [Setup](dev-guide/setup.md)
- [Contribution](dev-guide/contributing.md)
- [Standards](dev-guide/standards.md)

### 📊 Métriques
- [Qualité](metrics/quality.md)
- [Performance](metrics/performance.md)
- [Équipe](metrics/team.md)

### 📋 API (si applicable)
- [Référence](api/reference.md)
- [Exemples](api/examples.md)

---

*Documentation générée par Hyperion v2.7.0*
*Branch: $BRANCH_NAME | Date: $(date)*
EOF

# 9. Validation des liens
echo "🔗 Validating documentation links..."
if command -v markdown-link-check &> /dev/null; then
    find "$DOCS_OUTPUT" -name "*.md" -exec markdown-link-check {} \;
else
    echo "⚠️ markdown-link-check not installed, skipping link validation"
fi

# 10. Génération site statique (optionnel)
if [ "$GENERATE_SITE" = "true" ]; then
    echo "🌐 Generating static site..."
    if command -v mkdocs &> /dev/null; then
        mkdocs build --config-file mkdocs.generated.yml
    elif command -v hugo &> /dev/null; then
        hugo --source "$DOCS_OUTPUT" --destination public/
    fi
fi

echo "✅ Documentation pipeline completed!"
echo "📁 Output directory: $DOCS_OUTPUT"
echo "📊 Files generated: $(find "$DOCS_OUTPUT" -type f | wc -l)"

# 11. Commit automatique (optionnel)
if [ "$AUTO_COMMIT" = "true" ]; then
    echo "📝 Committing documentation updates..."

    git add "$DOCS_OUTPUT/" README_generated.md

    if git diff --staged --quiet; then
        echo "ℹ️ No documentation changes to commit"
    else
        git commit -m "docs: update generated documentation

        🤖 Auto-generated documentation update:
        - Architecture diagrams refreshed
        - Metrics updated with latest analysis
        - Developer guides synchronized with code

        Generated by Hyperion v2.7.0 on $(date)"

        echo "✅ Documentation committed successfully"
    fi
fi
```

### 🔄 **Cron Job pour Documentation**

```bash
# Crontab entry
# Mise à jour documentation quotidienne à 3h du matin
0 3 * * * cd /projects/mon-projet && ./scripts/docs_pipeline.sh

# Mise à jour documentation après chaque release (webhook)
# Script appelé par webhook GitHub/GitLab
```

---

## 🎓 **Workflow 4 : Onboarding Automatique**

### 👨‍🎓 **Script d'Onboarding Personnalisé**

```python
#!/usr/bin/env python3
# onboarding_assistant.py

import os
import json
import subprocess
from pathlib import Path
from datetime import datetime
from typing import List, Dict

class OnboardingAssistant:
    def __init__(self, project_path: str, new_developer: str):
        self.project_path = Path(project_path)
        self.developer = new_developer
        self.output_dir = Path(f"onboarding/{new_developer}")
        self.output_dir.mkdir(parents=True, exist_ok=True)

    def analyze_project_for_onboarding(self):
        """Analyser le projet pour créer un guide d'onboarding personnalisé"""
        print(f"🔍 Analyzing project for {self.developer}...")

        # Analyse Hyperion complète
        analysis = self.run_hyperion_analysis()

        # Guide personnalisé
        guide = self.create_personalized_guide(analysis)

        # Knowledge base
        knowledge_base = self.create_knowledge_base(analysis)

        # Roadmap d'apprentissage
        roadmap = self.create_learning_roadmap(analysis)

        # FAQ automatique
        faq = self.generate_faq(analysis)

        return {
            "guide": guide,
            "knowledge_base": knowledge_base,
            "roadmap": roadmap,
            "faq": faq
        }

    def run_hyperion_analysis(self):
        """Analyse Hyperion pour onboarding"""
        # Analyse détaillée
        cmd = ["hyperion", "profile", str(self.project_path), "--detailed", "--format", "json"]
        result = subprocess.run(cmd, capture_output=True, text=True)
        analysis = json.loads(result.stdout)

        # Indexation pour le chat
        subprocess.run(["hyperion", "ingest", str(self.project_path), "--extract-features"])

        return analysis

    def create_personalized_guide(self, analysis: dict) -> str:
        """Créer un guide d'onboarding personnalisé"""
        arch = analysis.get("architecture", {})
        team = analysis.get("team", {})

        guide = f"""# 👋 Welcome {self.developer}!

## 🎯 Project Overview

This project is a **{self.detect_project_type(analysis)}** with:
- **Complexity Level**: {self.complexity_to_text(arch.get('complexity_score', 0))}
- **Team Size**: {team.get('active_contributors', 0)} active contributors
- **Main Technologies**: {', '.join(self.extract_technologies(analysis))}

## 🚀 Quick Start (Your First Day)

### 1. Setup Environment
```bash
# Clone the repository (if not done)
git clone <repository-url>
cd {self.project_path.name}

# Setup (detected automatically)
{self.generate_setup_commands(analysis)}
```

### 2. Understand the Architecture
{self.generate_architecture_explanation(analysis)}

### 3. Your First Code Exploration
{self.generate_exploration_tasks(analysis)}

## 🎓 Learning Path (Your First Week)

### Day 1: Environment & Overview
- [ ] Complete environment setup
- [ ] Run the project successfully
- [ ] Explore main directories
- [ ] Ask Hyperion: "Comment est structuré ce projet ?"

### Day 2-3: Core Modules
{self.generate_core_module_tasks(analysis)}

### Day 4-5: Practical Tasks
{self.generate_practical_tasks(analysis)}

## 🤖 Your AI Assistant

You have Hyperion to help you! Here are some questions to get started:

```bash
# Ask about architecture
hyperion chat "Explain the overall architecture of this project"

# Find specific functionality
hyperion chat "Where is the user authentication handled?"

# Understand testing
hyperion chat "How do I run tests and what testing patterns are used?"

# Get examples
hyperion chat "Show me examples of how to add a new feature"
```

## 👥 Team & Collaboration

- **Team Collaboration Score**: {team.get('collaboration_score', 0):.1f}/10
- **Knowledge Distribution**: {team.get('knowledge_distribution', 0):.2f}
- **Main Contributors**: Check git log or ask your team lead

## 🎯 Recommended Focus Areas

{self.generate_focus_recommendations(analysis)}

---

*Generated by Hyperion Onboarding Assistant on {datetime.now().strftime("%Y-%m-%d")}*
"""
        return guide

    def create_knowledge_base(self, analysis: dict) -> Dict[str, str]:
        """Créer une base de connaissances pour le nouveau développeur"""
        knowledge = {}

        # Questions/réponses automatiques via Hyperion
        common_questions = [
            "Comment démarrer le serveur de développement ?",
            "Où sont les tests et comment les lancer ?",
            "Comment ajouter une nouvelle dépendance ?",
            "Quelle est la structure des dossiers ?",
            "Comment configurer l'environnement de développement ?",
            "Où est la documentation technique ?",
            "Comment déboguer l'application ?",
            "Quels sont les standards de code ?",
            "Comment faire une pull request ?",
            "Où demander de l'aide ?"
        ]

        for question in common_questions:
            answer = self.ask_hyperion(question)
            knowledge[question] = answer

        return knowledge

    def ask_hyperion(self, question: str) -> str:
        """Poser une question à Hyperion"""
        try:
            cmd = ["hyperion", "chat", question, "--repository", self.project_path.name]
            result = subprocess.run(cmd, capture_output=True, text=True)

            if result.returncode == 0:
                response = json.loads(result.stdout)
                return response.get("answer", "No answer available")
            else:
                return f"Error getting answer: {result.stderr}"
        except Exception as e:
            return f"Error: {str(e)}"

    def generate_interactive_onboarding_session(self):
        """Session d'onboarding interactive"""
        print(f"🎓 Starting interactive onboarding session for {self.developer}")
        print("Ask questions about the codebase. Type 'exit' to finish.")

        session_log = []

        while True:
            try:
                question = input(f"\n{self.developer}: ")
                if question.lower() in ['exit', 'quit', 'done']:
                    break

                print("🤖 Hyperion: Thinking...")
                answer = self.ask_hyperion(question)
                print(f"🤖 Hyperion: {answer}")

                session_log.append({
                    "question": question,
                    "answer": answer,
                    "timestamp": datetime.now().isoformat()
                })

            except KeyboardInterrupt:
                break

        # Sauvegarder la session
        session_file = self.output_dir / "onboarding_session.json"
        with open(session_file, 'w') as f:
            json.dump(session_log, f, indent=2)

        print(f"\n✅ Onboarding session saved to {session_file}")

    def complexity_to_text(self, score: float) -> str:
        if score < 3: return "Simple"
        elif score < 6: return "Moderate"
        elif score < 8: return "Complex"
        else: return "Very Complex"

    def detect_project_type(self, analysis: dict) -> str:
        # Logic pour détecter le type de projet
        return "Web Application"  # Simplified

    def extract_technologies(self, analysis: dict) -> List[str]:
        # Logic pour extraire les technologies
        return ["Python", "JavaScript", "PostgreSQL"]  # Simplified

# Usage
if __name__ == "__main__":
    import sys

    if len(sys.argv) != 3:
        print("Usage: python onboarding_assistant.py <project_path> <developer_name>")
        sys.exit(1)

    project_path = sys.argv[1]
    developer_name = sys.argv[2]

    assistant = OnboardingAssistant(project_path, developer_name)

    # Analyse et génération
    print("📋 Generating onboarding materials...")
    materials = assistant.analyze_project_for_onboarding()

    # Sauvegarder les guides
    output_dir = assistant.output_dir
    with open(output_dir / "guide.md", 'w') as f:
        f.write(materials["guide"])

    with open(output_dir / "knowledge_base.json", 'w') as f:
        json.dump(materials["knowledge_base"], f, indent=2)

    print(f"✅ Onboarding materials generated in {output_dir}")
    print(f"📖 Start with: cat {output_dir}/guide.md")
    print(f"🎓 Interactive session: python onboarding_assistant.py --interactive")

    # Session interactive optionnelle
    if "--interactive" in sys.argv:
        assistant.generate_interactive_onboarding_session()
```

---

## 🎉 **Maîtrise des Workflows !**

### ✅ **Ce que Vous Maîtrisez Maintenant**

- 🔄 **CI/CD Integration** : GitHub Actions, GitLab CI avec quality gates
- 📊 **Monitoring Continu** : Surveillance multi-repo, alertes intelligentes
- 📚 **Documentation Continue** : Auto-génération, mise à jour synchronisée
- 🎓 **Onboarding Automatique** : Guides personnalisés, sessions interactives

### 🚀 **Workflows Avancés**

- Orchestration de tâches complexes
- Monitoring proactif avec ML
- Documentation toujours à jour
- Onboarding efficace et personnalisé

### 📚 **Prochaines Étapes**

👉 **Continuez avec** : [Chapitre 09 - Troubleshooting](09-troubleshooting.md)

Au prochain chapitre, vous apprendrez à :
- Diagnostiquer et résoudre les problèmes courants
- Optimiser les performances d'Hyperion
- Configurer des alertes et monitoring
- Recovery procedures et maintenance

---

*Excellent ! Vous maîtrisez maintenant l'automatisation complète avec Hyperion. Rendez-vous au [Chapitre 09](09-troubleshooting.md) !* ⚡

---

*Cours Hyperion v2.7.0 - Chapitre 08 - Décembre 2024*