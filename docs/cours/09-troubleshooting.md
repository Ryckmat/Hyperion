---
title: "Chapitre 09 - Troubleshooting"
toc: true
description: "Résoudre les problèmes courants : Diagnostic, optimisation et maintenance"
weight: 10
---

**Résoudre les problèmes courants** - Diagnostic, optimisation et maintenance

*⏱️ Durée estimée : 45 minutes*

---

## 🎯 **Objectifs de ce Chapitre**

À la fin de ce chapitre, vous saurez :
- ✅ Diagnostiquer et résoudre tous les problèmes courants d'Hyperion
- ✅ Optimiser les performances selon votre environnement
- ✅ Configurer un monitoring efficace pour éviter les problèmes
- ✅ Maintenir Hyperion en parfait état de fonctionnement

---

## 🩺 **Diagnostic Système**

### 🔍 **Commande de Diagnostic Complète**

```bash
# Diagnostic complet
hyperion diagnose

# Diagnostic avec détails de performance
hyperion diagnose --performance

# Export du diagnostic
hyperion diagnose --export diagnose_report.json

# Diagnostic avec tests de connectivité
hyperion diagnose --connectivity --verbose
```

### 📊 **Comprendre le Rapport de Diagnostic**

```json
{
  "hyperion_status": {
    "version": "2.7.0",
    "status": "healthy",
    "uptime_seconds": 3600,
    "last_restart": "2024-12-26T10:00:00Z"
  },
  "services": {
    "neo4j": {
      "status": "connected",
      "response_time_ms": 12.3,
      "version": "4.4.12",
      "database_size_mb": 245,
      "active_transactions": 2
    },
    "redis": {
      "status": "connected",
      "response_time_ms": 1.2,
      "memory_usage_mb": 156,
      "cache_hit_rate": 0.87
    },
    "ollama": {
      "status": "connected",
      "response_time_ms": 89.5,
      "models_loaded": ["llama3.2:1b"],
      "gpu_available": false,
      "memory_usage_mb": 2048
    }
  },
  "performance": {
    "cpu_usage_percent": 23.5,
    "memory_usage_mb": 1024,
    "disk_usage_percent": 45.2,
    "network_latency_ms": 5.1
  },
  "issues_detected": [
    {
      "level": "warning",
      "component": "ollama",
      "message": "Model loading time > 60s",
      "recommendation": "Consider using smaller model for faster responses"
    }
  ]
}
```

---

## ❌ **Problèmes de Services**

### 🗃️ **Neo4j - Problèmes Courants**

#### ❌ **Erreur : "Connection refused"**

```bash
# 1. Vérifier que Neo4j fonctionne
sudo systemctl status neo4j

# 2. Vérifier les ports
sudo netstat -tulpn | grep 7687  # Bolt protocol
sudo netstat -tulpn | grep 7474  # HTTP interface

# 3. Tester la connexion
curl http://localhost:7474
telnet localhost 7687

# 4. Vérifier les logs
sudo journalctl -u neo4j -f
tail -f /var/log/neo4j/neo4j.log
```

**Solutions :**

```bash
# Redémarrer Neo4j
sudo systemctl restart neo4j

# Vérifier la configuration
sudo cat /etc/neo4j/neo4j.conf | grep -E "(listen|connector)"

# Vérifier l'espace disque
df -h /var/lib/neo4j

# Reset password si nécessaire
sudo neo4j-admin set-initial-password hyperion_new_password
```

#### ❌ **Erreur : "Database is locked"**

```bash
# Arrêter Neo4j proprement
sudo systemctl stop neo4j

# Vérifier qu'aucun processus Neo4j ne tourne
sudo ps aux | grep neo4j

# Nettoyer les verrous
sudo rm -f /var/lib/neo4j/data/databases/*/neostore.transaction.db.lock

# Redémarrer
sudo systemctl start neo4j
```

#### ❌ **Performance Dégradée**

```bash
# Vérifier l'utilisation mémoire
sudo neo4j-admin memrec

# Optimiser la configuration
sudo nano /etc/neo4j/neo4j.conf

# Configuration recommandée pour développement
dbms.memory.heap.max_size=2G
dbms.memory.pagecache.size=1G

# Pour production
dbms.memory.heap.max_size=4G
dbms.memory.pagecache.size=2G
```

### 🔴 **Redis - Problèmes Courants**

#### ❌ **Erreur : "Connection refused"**

```bash
# Vérifier Redis
redis-cli ping

# Status du service
sudo systemctl status redis-server

# Logs Redis
sudo journalctl -u redis-server -f

# Redémarrer si nécessaire
sudo systemctl restart redis-server
```

#### ❌ **Mémoire Pleine**

```bash
# Vérifier l'utilisation mémoire
redis-cli info memory

# Nettoyer le cache
redis-cli flushall

# Configurer l'éviction
redis-cli config set maxmemory 256mb
redis-cli config set maxmemory-policy allkeys-lru
```

#### ❌ **Performance Cache**

```python
# Script de diagnostic Redis
import redis

def diagnose_redis():
    r = redis.Redis(host='localhost', port=6379, db=0)

    info = r.info()

    print("📊 Redis Diagnostics:")
    print(f"Memory Used: {info['used_memory_human']}")
    print(f"Cache Hit Rate: {info.get('cache_hits', 0) / (info.get('cache_hits', 0) + info.get('cache_misses', 1)):.2%}")
    print(f"Connected Clients: {info['connected_clients']}")
    print(f"Operations/sec: {info['instantaneous_ops_per_sec']}")

    # Analyser les clés
    keys = r.keys('*')
    print(f"Total Keys: {len(keys)}")

    # Top des clés par type
    key_types = {}
    for key in keys[:100]:  # Échantillon
        key_type = r.type(key).decode()
        key_types[key_type] = key_types.get(key_type, 0) + 1

    print("Key Types:", key_types)

if __name__ == "__main__":
    diagnose_redis()
```

### 🤖 **Ollama - Problèmes Courants**

#### ❌ **Erreur : "Model not found"**

```bash
# Lister les modèles installés
ollama list

# Installer le modèle manquant
ollama pull llama3.2:1b

# Vérifier l'espace disque
du -sh ~/.ollama/models

# Nettoyer anciens modèles
ollama rm unused-model
```

#### ❌ **Performance Lente**

```bash
# Vérifier les ressources système
htop  # Voir CPU/RAM
nvidia-smi  # Si GPU disponible

# Utiliser modèle plus léger
ollama pull llama3.2:1b  # Plus rapide que 8b

# Configuration Ollama
export OLLAMA_HOST=0.0.0.0
export OLLAMA_NUM_PARALLEL=2
export OLLAMA_MAX_LOADED_MODELS=1
```

#### ❌ **Timeout de Modèle**

```yaml
# Configuration Hyperion pour timeouts
services:
  ollama:
    url: "http://localhost:11434"
    timeout_seconds: 120  # Augmenter le timeout
    max_retries: 3
    default_model: "llama3.2:1b"  # Modèle plus rapide
```

---

## ⚡ **Problèmes de Performance**

### 🐌 **Analyse Lente**

#### 🔍 **Diagnostic Performance**

```bash
# Profiling d'une analyse
time hyperion profile mon-projet/ --detailed

# Analyse avec métriques
hyperion profile mon-projet/ --performance-metrics

# Analyse en mode debug
hyperion profile mon-projet/ --debug --log-level DEBUG
```

#### ⚡ **Optimisations**

```bash
# 1. Exclusions pour gros projets
hyperion profile . --exclude "node_modules,venv,__pycache__,dist,build"

# 2. Limite de fichiers
hyperion profile . --max-files 1000

# 3. Analyse rapide
hyperion profile . --fast

# 4. Cache activé
hyperion profile . --use-cache --cache-ttl 3600

# 5. Parallélisation
hyperion profile . --parallel --workers 4
```

### 💬 **Chat RAG Lent**

#### 🔍 **Diagnostic RAG**

```python
# Script de benchmark RAG
import time
import requests

def benchmark_rag():
    questions = [
        "Comment est structuré ce projet ?",
        "Où se trouve l'authentification ?",
        "Comment ajouter une nouvelle route ?",
        "Quels sont les tests disponibles ?"
    ]

    results = []

    for question in questions:
        start_time = time.time()

        response = requests.post('http://localhost:8000/api/chat', json={
            'message': question,
            'repository': 'mon-projet'
        })

        end_time = time.time()
        duration = end_time - start_time

        results.append({
            'question': question,
            'duration_seconds': duration,
            'status_code': response.status_code
        })

        print(f"❓ {question}")
        print(f"⏱️  {duration:.2f}s")
        print(f"📊 {response.status_code}")
        print("---")

    avg_duration = sum(r['duration_seconds'] for r in results) / len(results)
    print(f"📊 Average Response Time: {avg_duration:.2f}s")

if __name__ == "__main__":
    benchmark_rag()
```

#### ⚡ **Optimisations RAG**

```yaml
# Configuration optimisée
rag:
  # Modèle plus rapide
  embedding_model: "all-MiniLM-L6-v2"  # Au lieu de all-mpnet-base-v2

  # Moins de chunks pour plus de vitesse
  top_k_results: 3  # Au lieu de 5
  max_tokens: 500   # Au lieu de 1000

  # Cache agressif
  cache_embeddings: true
  cache_ttl: 7200   # 2 heures

  # Modèle LLM rapide
  llm_model: "llama3.2:1b"  # Ultra-rapide

# Mode vitesse dans la requête
speed_mode: "ultra_fast"  # ultra_fast, balanced, high_precision
```

### 🗄️ **Indexation Lente**

#### ⚡ **Optimisation Indexation**

```bash
# Indexation avec parallélisation
hyperion ingest . --parallel --workers 8

# Indexation incrémentale seulement
hyperion ingest . --update --smart

# Exclure fichiers non nécessaires
hyperion ingest . --exclude "*.log,*.tmp,node_modules/**"

# Limiter la taille des fichiers
hyperion ingest . --max-file-size 1MB

# Désactiver features ML temporairement
hyperion ingest . --no-ml-features
```

---

## 🔧 **Optimisation Système**

### 💾 **Optimisation Mémoire**

```bash
# Configuration mémoire optimisée
# ~/.hyperion/config.yaml

performance:
  # Cache intelligent
  max_cache_size: "2GB"
  cache_compression: true
  cache_cleanup_interval: 3600

  # Workers
  max_workers: 4  # = nombre de CPU cores
  worker_memory_limit: "512MB"

  # Base de données
  neo4j_memory_limit: "2GB"
  redis_memory_limit: "512MB"

  # ML Models
  model_cache_size: "1GB"
  max_loaded_models: 1  # Ollama
```

### 💽 **Optimisation Disque**

```bash
# Nettoyer les caches
hyperion clean-cache

# Nettoyer les logs anciens
find ~/.hyperion/logs -name "*.log" -mtime +30 -delete

# Nettoyer les anciens modèles Ollama
ollama list | grep -v "llama3.2:1b" | xargs -I {} ollama rm {}

# Optimiser Neo4j
echo "CALL db.schema.nodeTypeProperties();" | cypher-shell
echo "CALL db.indexes();" | cypher-shell

# Vacuum bases si nécessaire
```

### ⚡ **Optimisation Réseau**

```yaml
# Configuration réseau
api:
  # Connection pooling
  connection_pool_size: 20
  connection_timeout: 30
  read_timeout: 60

  # Compression
  enable_gzip: true
  gzip_threshold: 1024

  # Keep-alive
  keep_alive: true
  max_keep_alive_requests: 100

# Services externes
services:
  neo4j:
    pool_size: 10
    max_connection_lifetime: 3600
  redis:
    connection_pool_max_connections: 50
```

---

## 📊 **Monitoring et Alertes**

### 🎯 **Script de Monitoring**

```python
#!/usr/bin/env python3
# hyperion_monitor.py

import psutil
import requests
import time
import json
import smtplib
from datetime import datetime
from email.mime.text import MimeText

class HyperionHealthMonitor:
    def __init__(self, config_file="monitor_config.json"):
        self.config = self.load_config(config_file)
        self.alert_history = []

    def check_hyperion_health(self):
        """Vérifier la santé d'Hyperion"""
        try:
            response = requests.get(
                "http://localhost:8000/health",
                timeout=10
            )
            return response.status_code == 200
        except:
            return False

    def check_services_health(self):
        """Vérifier tous les services"""
        services = {}

        # Neo4j
        try:
            response = requests.get("http://localhost:7474", timeout=5)
            services["neo4j"] = response.status_code == 200
        except:
            services["neo4j"] = False

        # Redis
        try:
            import redis
            r = redis.Redis(host='localhost', port=6379, db=0)
            r.ping()
            services["redis"] = True
        except:
            services["redis"] = False

        # Ollama
        try:
            response = requests.get("http://localhost:11434/api/tags", timeout=5)
            services["ollama"] = response.status_code == 200
        except:
            services["ollama"] = False

        return services

    def check_system_resources(self):
        """Vérifier les ressources système"""
        return {
            "cpu_percent": psutil.cpu_percent(interval=1),
            "memory_percent": psutil.virtual_memory().percent,
            "disk_percent": psutil.disk_usage('/').percent,
            "load_average": psutil.getloadavg()[0] if hasattr(psutil, 'getloadavg') else 0
        }

    def check_hyperion_performance(self):
        """Vérifier les performances d'Hyperion"""
        try:
            # Test API response time
            start = time.time()
            response = requests.get("http://localhost:8000/api/info", timeout=30)
            api_response_time = time.time() - start

            if response.status_code == 200:
                return {
                    "api_response_time": api_response_time,
                    "status": "healthy" if api_response_time < 2.0 else "slow"
                }
        except:
            return {"api_response_time": None, "status": "error"}

    def run_health_check(self):
        """Exécuter check de santé complet"""
        timestamp = datetime.now()

        # Collecte des métriques
        hyperion_health = self.check_hyperion_health()
        services_health = self.check_services_health()
        system_resources = self.check_system_resources()
        hyperion_performance = self.check_hyperion_performance()

        health_report = {
            "timestamp": timestamp.isoformat(),
            "hyperion_health": hyperion_health,
            "services": services_health,
            "system": system_resources,
            "performance": hyperion_performance
        }

        # Détecter problèmes
        issues = self.detect_issues(health_report)

        # Alertes si nécessaire
        if issues:
            self.send_alerts(issues, health_report)

        # Log
        print(f"[{timestamp}] Health Check: {len(issues)} issues detected")

        return health_report

    def detect_issues(self, report):
        """Détecter les problèmes"""
        issues = []

        # Hyperion down
        if not report["hyperion_health"]:
            issues.append({
                "severity": "critical",
                "type": "service_down",
                "message": "Hyperion API is not responding"
            })

        # Services down
        for service, status in report["services"].items():
            if not status:
                issues.append({
                    "severity": "high",
                    "type": "service_down",
                    "message": f"{service} service is not responding"
                })

        # Performance issues
        if report["performance"]["api_response_time"]:
            if report["performance"]["api_response_time"] > 5.0:
                issues.append({
                    "severity": "medium",
                    "type": "performance",
                    "message": f"API response time too high: {report['performance']['api_response_time']:.2f}s"
                })

        # Resource issues
        if report["system"]["cpu_percent"] > 90:
            issues.append({
                "severity": "high",
                "type": "resource",
                "message": f"High CPU usage: {report['system']['cpu_percent']:.1f}%"
            })

        if report["system"]["memory_percent"] > 90:
            issues.append({
                "severity": "high",
                "type": "resource",
                "message": f"High memory usage: {report['system']['memory_percent']:.1f}%"
            })

        if report["system"]["disk_percent"] > 85:
            issues.append({
                "severity": "medium",
                "type": "resource",
                "message": f"High disk usage: {report['system']['disk_percent']:.1f}%"
            })

        return issues

    def send_alerts(self, issues, report):
        """Envoyer alertes"""
        # Filtrer par sévérité
        critical_issues = [i for i in issues if i["severity"] == "critical"]
        high_issues = [i for i in issues if i["severity"] == "high"]

        # Alertes critiques → email immédiat
        if critical_issues:
            self.send_email_alert(critical_issues, report)

        # Alertes importantes → Slack
        if high_issues or critical_issues:
            self.send_slack_alert(issues, report)

    def send_email_alert(self, issues, report):
        """Envoyer alerte email"""
        if not self.config.get("email_enabled", False):
            return

        subject = f"🚨 Hyperion Critical Alert - {len(issues)} issues"

        body = f"""
Hyperion Critical Issues Detected
=================================

Timestamp: {report['timestamp']}

Critical Issues:
{chr(10).join(f"- {issue['message']}" for issue in issues)}

System Status:
- CPU: {report['system']['cpu_percent']:.1f}%
- Memory: {report['system']['memory_percent']:.1f}%
- Disk: {report['system']['disk_percent']:.1f}%

Please check the system immediately.
        """

        # Envoyer email (configuration SMTP dans config)
        # Implementation SMTP...

    def continuous_monitoring(self, interval_seconds=60):
        """Monitoring continu"""
        print(f"🔍 Starting continuous monitoring (interval: {interval_seconds}s)")

        while True:
            try:
                report = self.run_health_check()

                # Sauvegarder rapport
                with open(f"health_reports/health_{int(time.time())}.json", "w") as f:
                    json.dump(report, f, indent=2)

            except Exception as e:
                print(f"❌ Monitoring error: {e}")

            time.sleep(interval_seconds)

# Configuration exemple
config = {
    "email_enabled": True,
    "email_smtp": {
        "host": "smtp.company.com",
        "port": 587,
        "username": "monitoring@company.com",
        "password": "password"
    },
    "slack_webhook": "https://hooks.slack.com/services/...",
    "thresholds": {
        "cpu_percent": 85,
        "memory_percent": 85,
        "disk_percent": 80,
        "api_response_time": 3.0
    }
}

# Lancement
if __name__ == "__main__":
    monitor = HyperionHealthMonitor()
    monitor.continuous_monitoring(interval_seconds=30)
```

---

## 🛠️ **Scripts de Maintenance**

### 🔄 **Script de Maintenance Automatique**

```bash
#!/bin/bash
# hyperion_maintenance.sh

set -euo pipefail

echo "🔧 Starting Hyperion maintenance routine..."

# 1. Backup des données importantes
echo "💾 Backing up data..."
mkdir -p backups/$(date +%Y%m%d)
neo4j-admin dump --database=neo4j --to=backups/$(date +%Y%m%d)/neo4j-backup.dump
cp -r ~/.hyperion/config backups/$(date +%Y%m%d)/

# 2. Nettoyage des caches
echo "🧹 Cleaning caches..."
hyperion clean-cache --all

# 3. Nettoyage des logs anciens
echo "📋 Cleaning old logs..."
find ~/.hyperion/logs -name "*.log" -mtime +7 -delete
find /var/log/neo4j -name "*.log" -mtime +30 -delete

# 4. Optimisation Neo4j
echo "🗃️ Optimizing Neo4j..."
echo "CALL db.index.fulltext.awaitEventuallyConsistentIndexRefresh();" | cypher-shell
echo "CALL gds.graph.list() YIELD graphName CALL gds.graph.drop(graphName) YIELD graphName as dropped;" | cypher-shell

# 5. Optimisation Redis
echo "🔴 Optimizing Redis..."
redis-cli BGREWRITEAOF

# 6. Vérification des mises à jour
echo "📦 Checking for updates..."
pip list --outdated | grep hyperion || echo "Hyperion is up to date"

# 7. Vérification santé
echo "🏥 Health check..."
if hyperion health; then
    echo "✅ All services healthy"
else
    echo "❌ Health check failed"
    exit 1
fi

# 8. Rapport de maintenance
cat > maintenance_report_$(date +%Y%m%d).txt << EOF
Hyperion Maintenance Report
==========================
Date: $(date)
Hyperion Version: $(hyperion --version)

Backups Created:
- Neo4j: backups/$(date +%Y%m%d)/neo4j-backup.dump
- Config: backups/$(date +%Y%m%d)/config/

Cache Cleanup:
- Hyperion cache cleaned
- Old logs cleaned (>7 days)

Optimizations:
- Neo4j indexes refreshed
- Redis AOF rewritten

Health Status: ✅ Healthy
EOF

echo "✅ Maintenance completed successfully!"
echo "📄 Report: maintenance_report_$(date +%Y%m%d).txt"
```

### 🔄 **Recovery Procedures**

```bash
#!/bin/bash
# hyperion_recovery.sh

echo "🆘 Starting Hyperion recovery procedure..."

# 1. Diagnostic complet
echo "🔍 Running full diagnostic..."
hyperion diagnose --export recovery_diagnostic.json

# 2. Arrêt propre des services
echo "⏹️ Stopping services..."
sudo systemctl stop neo4j redis-server
pkill -f ollama

# 3. Vérification intégrité
echo "🔧 Checking data integrity..."

# Neo4j
if [ -f /var/lib/neo4j/data/databases/neo4j/neostore ]; then
    echo "✅ Neo4j data intact"
else
    echo "❌ Neo4j data corrupted, restoring backup..."
    # Restore logic
fi

# 4. Redémarrage services
echo "🔄 Restarting services..."
sudo systemctl start redis-server
sudo systemctl start neo4j

# Attendre que les services soient prêts
sleep 10

# Démarrer Ollama
ollama serve &
sleep 5

# 5. Validation
echo "✅ Testing recovery..."
if hyperion health; then
    echo "🎉 Recovery successful!"
else
    echo "❌ Recovery failed, manual intervention required"
    exit 1
fi
```

---

## 🎉 **Maîtrise du Troubleshooting !**

### ✅ **Ce que Vous Maîtrisez Maintenant**

- 🩺 **Diagnostic** : Identifier rapidement les problèmes avec `hyperion diagnose`
- 🔧 **Résolution** : Résoudre tous les problèmes courants (services, performance, ressources)
- 📊 **Monitoring** : Surveillance proactive avec alertes intelligentes
- 🛠️ **Maintenance** : Scripts automatiques de maintenance et recovery

### 🚀 **Compétences Avancées**

- Optimisation performance selon l'environnement
- Monitoring continu avec Python
- Procedures de recovery automatisées
- Alertes intelligentes multi-canal

### 📚 **Dernière Étape**

👉 **Terminez avec** : [Chapitre 10 - Usage Avancé](10-advanced-usage)

Le dernier chapitre vous révélera :
- Fonctionnalités expertes et cas d'usage avancés
- Intégrations enterprise
- Personnalisation poussée
- Tips & tricks de power user

---

*Parfait ! Vous savez maintenant maintenir Hyperion en parfait état. Rendez-vous au [Chapitre 10](10-advanced-usage) pour les fonctionnalités expertes !* 🔧

---

*Cours Hyperion - Chapitre 09*