---
title: "Déploiement - Hyperion"
toc: true
description: "Stratégies et guides de déploiement pour Hyperion Architecture en production"
weight: 3
---

![Quality](https://img.shields.io/badge/Quality-100%25-green.svg)
![Services](https://img.shields.io/badge/Services-8_microservices-blue.svg)
![Tests](https://img.shields.io/badge/Tests-189/189-green.svg)

Stratégies et guides de déploiement pour Hyperion Architecture en production

---

## 🎯 **Vue d'ensemble du Déploiement**

Hyperion propose des stratégies de déploiement avancées avec architecture microservices complète :

### 🏗️ **Architecture Déployée**
```yaml
Enterprise Architecture:
  API Gateway: Port 8000 - Routage intelligent + auth + cache
  RAG Pipeline: Port 8001 - Enhanced RAG service
  Analytics Engine: Port 8002 - Intelligence + insights
  Dashboard: Port 3000 - Interface admin avancée
  Chat Interface: Port 3001 - Open WebUI conversationnel
  Monitoring Stack: Port 9090 - Prometheus + métriques
  Neo4j Database: Port 7474/7687 - Graphe de code
  MLflow Platform: Port 5000 - ML tracking + models
```

### 📋 **Options de Déploiement**
1. **🖥️ Standalone Enterprise** : Déploiement orchestré avec hyperion_master.sh
2. **🐳 Docker Enterprise** : 8 services conteneurisés avec profils
3. **☁️ Kubernetes** : Déploiement cloud-native avec monitoring
4. **🏢 Production HA** : Infrastructure haute disponibilité complète

### ✅ **Pré-requis Qualité Atteints**
- **Code Quality** : ✅ 0 erreurs Ruff + 100% Black compliance
- **Tests** : ✅ 189/189 passing (100% success rate)
- **Architecture** : ✅ 8 microservices validés
- **Documentation** : ✅ Guides complets cours/ + technique/

---

## 🖥️ **Déploiement Standalone Enterprise**

### 📋 **Prérequis**

#### 🔧 **Système Enterprise**
```yaml
Requirements:
  OS: Linux (Ubuntu 22.04+ / CentOS 9+)
  CPU: 8 cores minimum, 16 cores recommandé (8 microservices)
  RAM: 16GB minimum, 32GB recommandé (cache distribué)
  Storage: 100GB minimum, NVMe SSD recommandé
  Network: Internet + résolution DNS pour services
  GPU: Optionnel pour accélération ML (CUDA 11.8+)
```

#### 🐍 **Software Stack**
```bash
# Prérequis logiciels
Python 3.11+          # Type safety + performance
Git 2.40+             # Dernières features
Neo4j 5.x             # Graphe de code avancé
Redis 7.0+            # Cache distribué L1/L2
Docker 24.0+          # Containerisation services
Ollama latest         # Models LLM locaux
Prometheus 2.40+      # Monitoring metrics
```

### ⚙️ **Déploiement Orchestré**

#### 🚀 **Lancement Master (Recommandé)**
```bash
# Déploiement automatique avec qualité vérifiée
./scripts/deploy/hyperion_master.sh --profile enterprise

# Options avancées
./scripts/deploy/hyperion_master.sh \
  --profile enterprise \
  --enable-monitoring \
  --enable-cache-l2 \
  --verify-quality \
  --setup-v3

# Vérification post-déploiement
hyperion health --detailed --services-v3
hyperion quality --run-full-check
```

#### ⚡ **Déploiement Docker Simplifié**
```bash
# Lancement architecture complète
./scripts/docker/hyperion-docker.sh --action up --profile enterprise

# Services disponibles immédiatement :
open http://localhost:8000  # API Gateway
open http://localhost:3000  # Dashboard Enterprise
open http://localhost:9090  # Monitoring Prometheus
open http://localhost:7474  # Neo4j Browser
```

### ⚙️ **Installation Production**

#### 1️⃣ **Préparation Système Enterprise**
```bash
# Création utilisateur système avec groupes
sudo adduser hyperion --system --group
sudo usermod -a -G docker hyperion  # Accès Docker pour microservices
sudo mkdir -p /opt/hyperion/{data,logs,config,cache}
sudo chown -R hyperion:hyperion /opt/hyperion

# Configuration firewall (8 services)
sudo ufw allow 8000  # API Gateway
sudo ufw allow 8001  # RAG Pipeline
sudo ufw allow 8002  # Analytics Engine
sudo ufw allow 3000  # Dashboard
sudo ufw allow 3001  # Chat Interface
sudo ufw allow 9090  # Prometheus Monitoring
sudo ufw allow 7474  # Neo4j Browser
sudo ufw allow 7687  # Neo4j Bolt
sudo ufw allow 5000  # MLflow Platform
```

#### 2️⃣ **Installation Hyperion**
```bash
# Installation avec vérification qualité
sudo -u hyperion python3 -m venv /opt/hyperion/venv
sudo -u hyperion /opt/hyperion/venv/bin/pip install hyperion

# Vérification qualité post-installation
cd /opt/hyperion/src
ruff check src/ tests/     # ✅ 0 erreurs expected
black --check src/ tests/  # ✅ 148 files compliant
pytest tests/ -v          # ✅ 189/189 passing

# Configuration environnement
sudo -u hyperion cp enterprise.env /opt/hyperion/.env
```

#### 3️⃣ **Services Système**
```bash
# Services systemd pour architecture
sudo cp services/hyperion-gateway.service /etc/systemd/system/
sudo cp services/hyperion-rag.service /etc/systemd/system/
sudo cp services/hyperion-analytics.service /etc/systemd/system/
sudo cp services/hyperion-monitoring.service /etc/systemd/system/

# Activation services enterprise
sudo systemctl enable hyperion-gateway hyperion-rag hyperion-analytics hyperion-monitoring
sudo systemctl start hyperion-gateway hyperion-rag hyperion-analytics hyperion-monitoring

# Vérification architecture déployée
sudo systemctl status hyperion-*
```

### 📄 **Configuration Production**

#### 🔧 **Environment Variables Enterprise**
```bash
# /opt/hyperion/enterprise.env - Configuration
HYPERION_ENV=production
HYPERION_VERSION=# API Gateway Configuration
GATEWAY_PORT=8000
GATEWAY_HOST=0.0.0.0
GATEWAY_ENABLE_AUTH=true
GATEWAY_RATE_LIMIT_REQUESTS=1000
GATEWAY_CACHE_TTL=300

# Services Architecture
RAG_SERVICE_PORT=8001
RAG_SERVICE_HOST=localhost
ANALYTICS_SERVICE_PORT=8002
ANALYTICS_SERVICE_HOST=localhost
DASHBOARD_PORT=3000
CHAT_INTERFACE_PORT=3001

# Database Configuration
NEO4J_URL=bolt://localhost:7687
NEO4J_USER=hyperion_prod
NEO4J_PASSWORD=<enterprise_secure_password>
NEO4J_MAX_POOL_SIZE=50

# Cache Distribué
REDIS_URL=redis://localhost:6379/0
CACHE_L1_SIZE=1000
CACHE_L2_SIZE=10000
CACHE_DEFAULT_TTL=3600

# ML/LLM Platform
OLLAMA_HOST=http://localhost:11434
MLFLOW_TRACKING_URI=http://localhost:5000
ML_MODEL_CACHE_SIZE=5
FEATURE_STORE_ENABLED=true

# Sécurité Enterprise
JWT_SECRET_KEY=<enterprise_secure_random_key>
JWT_EXPIRATION_HOURS=24
TOTP_ENABLED=true
RBAC_ENABLED=true

# Monitoring
PROMETHEUS_ENABLED=true
PROMETHEUS_PORT=9090
STRUCTURED_LOGGING=true
LOG_LEVEL=INFO
LOG_FILE=/var/log/hyperion/hyperion-v3.log
PERFORMANCE_TRACKING=true

# Quality System
QUALITY_VALIDATION_ENABLED=true
RESPONSE_OPTIMIZATION_ENABLED=true
CONFIDENCE_THRESHOLD=0.8
```

#### 🗂️ **Fichier systemd**
```ini
# /etc/systemd/system/hyperion.service
[Unit]
Description=Hyperion ML Code Intelligence Platform
After=network.target neo4j.service redis.service

[Service]
Type=simple
User=hyperion
Group=hyperion
WorkingDirectory=/opt/hyperion
Environment=PYTHONPATH=/opt/hyperion
ExecStart=/opt/hyperion/venv/bin/hyperion serve --config /opt/hyperion/.env
Restart=always
RestartSec=10

# Security
NoNewPrivileges=true
PrivateTmp=true
ProtectSystem=strict
ProtectHome=true
ReadWritePaths=/opt/hyperion /var/log/hyperion

[Install]
WantedBy=multi-user.target
```

---

## 🐳 **Déploiement Docker Enterprise**

### 🏗️ **Architecture Conteneurisée (8 Services)**

```yaml
# docker-compose.enterprise.yml - Architecture complète
version: '3.8'

services:
  # API Gateway - Service principal
  hyperion-gateway:
    image: hyperion:container_name: hyperion-gateway-v3
    ports:
      - "8000:8000"
    environment:
      - HYPERION_ENV=production
      - GATEWAY_ENABLE_AUTH=true
      - GATEWAY_RATE_LIMIT=1000
      - NEO4J_URL=bolt://neo4j:7687
      - REDIS_URL=redis://redis:6379
    depends_on:
      - neo4j
      - redis
      - prometheus
    volumes:
      - hyperion_data:/app/data
      - hyperion_logs:/app/logs
    networks:
      - hyperion_network
    restart: unless-stopped

  # RAG Pipeline - Enhanced RAG
  hyperion-rag:
    image: hyperion-rag:latest
    container_name: hyperion-rag-v29
    ports:
      - "8001:8001"
    environment:
      - RAG_ENHANCED_PIPELINE=true
      - QUALITY_VALIDATION_ENABLED=true
      - RESPONSE_OPTIMIZATION=true
      - NEO4J_URL=bolt://neo4j:7687
    depends_on:
      - neo4j
      - ollama
    volumes:
      - rag_data:/app/rag
    networks:
      - hyperion_network
    restart: unless-stopped

  # Analytics Engine - Intelligence Platform
  hyperion-analytics:
    image: hyperion-analytics:latest
    container_name: hyperion-analytics-v29
    ports:
      - "8002:8002"
    environment:
      - ANALYTICS_ENGINE_ENABLED=true
      - PATTERN_ANALYSIS_ENABLED=true
      - BEHAVIORAL_ANALYSIS=true
      - REDIS_URL=redis://redis:6379
    depends_on:
      - redis
      - mlflow
    volumes:
      - analytics_data:/app/analytics
    networks:
      - hyperion_network
    restart: unless-stopped

  # Dashboard - Interface Enterprise
  hyperion-dashboard:
    image: hyperion-dashboard:latest
    container_name: hyperion-dashboard-v3
    ports:
      - "3000:3000"
    environment:
      - DASHBOARD_ENTERPRISE_MODE=true
      - API_GATEWAY_URL=http://hyperion-gateway:8000
    depends_on:
      - hyperion-gateway
    networks:
      - hyperion_network
    restart: unless-stopped

  # Chat Interface - Open WebUI
  hyperion-chat:
    image: ghcr.io/open-webui/open-webui:main
    container_name: hyperion-chat
    ports:
      - "3001:8080"
    environment:
      - OLLAMA_BASE_URL=http://ollama:11434
    depends_on:
      - ollama
    volumes:
      - open-webui:/app/backend/data
    networks:
      - hyperion_network
    restart: unless-stopped

  # Prometheus Monitoring
  prometheus:
    image: prom/prometheus:latest
    container_name: hyperion-prometheus
    ports:
      - "9090:9090"
    command:
      - '--config.file=/etc/prometheus/prometheus.yml'
      - '--storage.tsdb.path=/prometheus'
      - '--web.console.libraries=/etc/prometheus/console_libraries'
      - '--web.console.templates=/etc/prometheus/consoles'
    volumes:
      - ./monitoring/prometheus.yml:/etc/prometheus/prometheus.yml
      - prometheus_data:/prometheus
    networks:
      - hyperion_network
    restart: unless-stopped

  # MLflow Platform
  mlflow:
    image: python:3.11-slim
    container_name: hyperion-mlflow
    ports:
      - "5000:5000"
    command: >
      sh -c "pip install mlflow &&
             mlflow server --host 0.0.0.0 --port 5000 --backend-store-uri /mlflow/mlruns"
    volumes:
      - mlflow_data:/mlflow
    networks:
      - hyperion_network
    restart: unless-stopped

  # Neo4j Database v5.x
  neo4j:
    image: neo4j:5-community
    container_name: hyperion-neo4j-v5
    ports:
      - "7474:7474"
      - "7687:7687"
    environment:
      NEO4J_AUTH: neo4j/hyperion_enterprise_password
      NEO4J_dbms_memory_heap_max__size: 4G
      NEO4J_dbms_memory_pagecache_size: 2G
      NEO4J_PLUGINS: '["apoc"]'
    volumes:
      - neo4j_data:/data
      - neo4j_logs:/logs
    networks:
      - hyperion_network
    restart: unless-stopped

  # Redis Cache Distribué
  redis:
    image: redis:7-alpine
    container_name: hyperion-redis-v3
    ports:
      - "6379:6379"
    command: >
      redis-server --appendonly yes --maxmemory 2gb --maxmemory-policy allkeys-lru
    volumes:
      - redis_data:/data
    networks:
      - hyperion_network
    restart: unless-stopped

  # Ollama LLM Server
  ollama:
    image: ollama/ollama:latest
    container_name: hyperion-ollama
    ports:
      - "11434:11434"
    volumes:
      - ollama_data:/root/.ollama
    networks:
      - hyperion_network
    restart: unless-stopped

volumes:
  hyperion_data:
  hyperion_logs:
  rag_data:
  analytics_data:
  neo4j_data:
  neo4j_logs:
  redis_data:
  ollama_data:
  mlflow_data:
  prometheus_data:
  open-webui:

networks:
  hyperion_network:
    driver: bridge
    ipam:
      config:
        - subnet: 172.20.0.0/16
```

### 🚀 **Déploiement Docker**

#### 1️⃣ **Build & Deploy Enterprise**
```bash
# Build images avec qualité vérifiée
docker build -t hyperion:-f Dockerfile.enterprise .

# Vérification qualité pré-déploiement
docker run --rm hyperion:ruff check src/ tests/
docker run --rm hyperion:black --check src/ tests/
docker run --rm hyperion:pytest tests/ -v

# Déploiement architecture complète (8 services)
docker-compose -f docker-compose.enterprise.yml up -d

# Vérification santé des services
docker-compose -f docker-compose.enterprise.yml ps
docker-compose -f docker-compose.enterprise.yml logs hyperion-gateway
```

#### 2️⃣ **Profils de Déploiement**
```bash
# Profil Development (services essentiels)
docker-compose -f docker-compose.enterprise.yml --profile dev up -d

# Profil Production (architecture complète)
docker-compose -f docker-compose.enterprise.yml --profile production up -d

# Profil Monitoring (avec observabilité)
docker-compose -f docker-compose.enterprise.yml --profile monitoring up -d
```

#### 3️⃣ **Scripts Automatisés**
```bash
# Script de déploiement simplifié
./scripts/docker/hyperion-docker.sh --action up --profile enterprise

# Vérification health checks
./scripts/docker/health-check.sh --check-all --timeout 300

# Monitoring des services
./scripts/docker/monitor-services.sh --watch --prometheus
```

#### 4️⃣ **Configuration Volumes**
```bash
# Sauvegarde données enterprise
docker-compose -f docker-compose.enterprise.yml exec neo4j \
  neo4j-admin database dump --database=neo4j --to-path=/data/backups/

# Sauvegarde ML models
docker-compose -f docker-compose.enterprise.yml exec mlflow \
  tar -czf /mlflow/models-backup.tar.gz /mlflow/mlruns

# Restauration complète
docker-compose -f docker-compose.enterprise.yml exec neo4j \
  neo4j-admin database load --database=neo4j --from-path=/data/backups/

# Health checks post-restauration
curl -f http://localhost:8000/health
curl -f http://localhost:9090/metrics
```

---

## ☁️ **Déploiement Kubernetes**

### 🏗️ **Architecture Kubernetes**

```yaml
# k8s-deployment.yaml
apiVersion: apps/v1
kind: Deployment
metadata:
  name: hyperion-app
  labels:
    app: hyperion
spec:
  replicas: 3
  selector:
    matchLabels:
      app: hyperion
  template:
    metadata:
      labels:
        app: hyperion
    spec:
      containers:
      - name: hyperion
        image: hyperion:2.7.0
        ports:
        - containerPort: 8000
        env:
        - name: HYPERION_ENV
          value: "production"
        - name: NEO4J_URL
          valueFrom:
            secretKeyRef:
              name: hyperion-secrets
              key: neo4j-url
        resources:
          requests:
            memory: "2Gi"
            cpu: "500m"
          limits:
            memory: "4Gi"
            cpu: "2"
        livenessProbe:
          httpGet:
            path: /health
            port: 8000
          initialDelaySeconds: 30
          periodSeconds: 10
        readinessProbe:
          httpGet:
            path: /ready
            Port: 8000
          initialDelaySeconds: 5
          periodSeconds: 5

---
apiVersion: v1
kind: Service
metadata:
  name: hyperion-service
spec:
  selector:
    app: hyperion
  ports:
  - port: 80
    targetPort: 8000
  type: LoadBalancer

---
apiVersion: v1
kind: ConfigMap
metadata:
  name: hyperion-config
data:
  HYPERION_ENV: "production"
  LOG_LEVEL: "INFO"
  API_RATE_LIMIT: "200"

---
apiVersion: v1
kind: Secret
metadata:
  name: hyperion-secrets
type: Opaque
stringData:
  neo4j-url: "bolt://neo4j-service:7687"
  neo4j-password: "hyperion_k8s_password"
  jwt-secret: "k8s_secure_jwt_secret"
```

### ⚙️ **Orchestration Complète**

#### 1️⃣ **Neo4j StatefulSet**
```yaml
# neo4j-statefulset.yaml
apiVersion: apps/v1
kind: StatefulSet
metadata:
  name: neo4j
spec:
  serviceName: neo4j-service
  replicas: 1
  selector:
    matchLabels:
      app: neo4j
  template:
    metadata:
      labels:
        app: neo4j
    spec:
      containers:
      - name: neo4j
        image: neo4j:4.4-community
        ports:
        - containerPort: 7474
        - containerPort: 7687
        env:
        - name: NEO4J_AUTH
          value: "neo4j/hyperion_k8s_password"
        volumeMounts:
        - name: neo4j-storage
          mountPath: /data
  volumeClaimTemplates:
  - metadata:
      name: neo4j-storage
    spec:
      accessModes: ["ReadWriteOnce"]
      resources:
        requests:
          storage: 20Gi
```

#### 2️⃣ **Ingress Configuration**
```yaml
# hyperion-ingress.yaml
apiVersion: networking.k8s.io/v1
kind: Ingress
metadata:
  name: hyperion-ingress
  annotations:
    nginx.ingress.kubernetes.io/rewrite-target: /
    cert-manager.io/cluster-issuer: letsencrypt-prod
spec:
  tls:
  - hosts:
    - hyperion.yourdomain.com
    secretName: hyperion-tls
  rules:
  - host: hyperion.yourdomain.com
    http:
      paths:
      - path: /
        pathType: Prefix
        backend:
          service:
            name: hyperion-service
            port:
              number: 80
```

---

## 🏢 **Déploiement Enterprise**

### 🔧 **Architecture Haute Disponibilité**

#### 📊 **Composants HA**
```yaml
High Availability Stack:
  Load Balancer: NGINX/HAProxy
  API Servers: 3+ instances (Active-Active)
  Database: Neo4j Cluster (Core+Read Replicas)
  Cache: Redis Cluster/Sentinel
  Storage: Distributed (Ceph/GlusterFS)
  Monitoring: Prometheus/Grafana/ELK
```

#### 🔀 **Load Balancer Configuration**
```nginx
# nginx.conf
upstream hyperion_backend {
    least_conn;
    server hyperion-1.internal:8000 max_fails=3 fail_timeout=30s;
    server hyperion-2.internal:8000 max_fails=3 fail_timeout=30s;
    server hyperion-3.internal:8000 max_fails=3 fail_timeout=30s;
}

server {
    listen 80;
    server_name hyperion.enterprise.com;

    # Redirection HTTPS
    return 301 https://$server_name$request_uri;
}

server {
    listen 443 ssl http2;
    server_name hyperion.enterprise.com;

    ssl_certificate /etc/ssl/hyperion.crt;
    ssl_certificate_key /etc/ssl/hyperion.key;

    location / {
        proxy_pass http://hyperion_backend;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;

        # Health check
        proxy_next_upstream error timeout invalid_header http_500 http_502 http_503 http_504;
    }

    location /health {
        access_log off;
        proxy_pass http://hyperion_backend;
    }
}
```

### 📊 **Monitoring Production**

#### 🔍 **Prometheus Configuration**
```yaml
# prometheus.yml
global:
  scrape_interval: 15s
  evaluation_interval: 15s

rule_files:
  - "hyperion_alerts.yml"

scrape_configs:
  - job_name: 'hyperion-api'
    static_configs:
      - targets: ['hyperion-1.internal:8000', 'hyperion-2.internal:8000', 'hyperion-3.internal:8000']
    metrics_path: /metrics
    scrape_interval: 30s

  - job_name: 'neo4j'
    static_configs:
      - targets: ['neo4j.internal:2004']

alerting:
  alertmanagers:
    - static_configs:
        - targets:
          - alertmanager:9093
```

#### 🚨 **Alerts Configuration**
```yaml
# hyperion_alerts.yml
groups:
- name: hyperion.rules
  rules:
  - alert: HyperionAPIDown
    expr: up{job="hyperion-api"} == 0
    for: 1m
    labels:
      severity: critical
    annotations:
      summary: "Hyperion API instance down"
      description: "Hyperion API instance {{ $labels.instance }} has been down for more than 1 minute"

  - alert: HyperionHighResponseTime
    expr: hyperion_request_duration_seconds{quantile="0.95"} > 2
    for: 5m
    labels:
      severity: warning
    annotations:
      summary: "Hyperion API high response time"
      description: "95th percentile response time is {{ $value }}s"

  - alert: Neo4jConnectionFailure
    expr: increase(hyperion_neo4j_connection_errors_total[5m]) > 5
    for: 2m
    labels:
      severity: warning
    annotations:
      summary: "Neo4j connection errors"
      description: "Multiple Neo4j connection failures detected"
```

---

## 📊 **Monitoring et Maintenance**

### 🔍 **Health Checks**

#### 🏥 **Endpoint Sanité**
```python
# Health check endpoints
GET /health       # Application status
GET /ready        # Readiness probe
GET /metrics      # Prometheus metrics
GET /status       # Detailed status
```

#### 📊 **Métriques Clés**
```python
Production Metrics:
  ├── API Performance
  │   ├── Response time (p50, p95, p99)
  │   ├── Request rate (RPS)
  │   ├── Error rate (4xx, 5xx)
  │   └── Concurrent connections
  ├── ML Pipeline
  │   ├── Prediction latency
  │   ├── Model accuracy drift
  │   ├── Feature computation time
  │   └── Training job status
  ├── Infrastructure
  │   ├── CPU/Memory usage
  │   ├── Disk I/O
  │   ├── Network latency
  │   └── Service dependencies
  └── Business Metrics
      ├── Repositories analyzed
      ├── Queries processed
      ├── User satisfaction
      └── System utilization
```

### 🔧 **Maintenance Procedures**

#### 📅 **Tâches Régulières**
```bash
# Quotidien
hyperion maintenance --daily
  ├── Health check global
  ├── Backup incrémental
  ├── Log rotation
  └── Performance report

# Hebdomadaire
hyperion maintenance --weekly
  ├── Model retraining check
  ├── Database optimization
  ├── Cache cleanup
  └── Security scan

# Mensuel
hyperion maintenance --monthly
  ├── Full backup
  ├── Capacity planning
  ├── Security audit
  └── Performance analysis
```

#### 🔄 **Rolling Updates**
```bash
# Mise à jour sans interruption
./scripts/rolling_update.sh
  ├── 1. Update instance 1
  ├── 2. Health check
  ├── 3. Update instance 2
  ├── 4. Health check
  └── 5. Update instance 3
```

---

## 🔐 **Sécurité Production**

### 🛡️ **Security Hardening**

#### 🔒 **Configuration Sécurisée**
```bash
# Firewall rules
sudo ufw default deny incoming
sudo ufw default allow outgoing
sudo ufw allow 22/tcp    # SSH (restrict by IP)
sudo ufw allow 443/tcp   # HTTPS
sudo ufw allow 80/tcp    # HTTP (redirect)

# SSL/TLS Configuration
ssl_protocols TLSv1.2 TLSv1.3;
ssl_ciphers HIGH:!aNULL:!MD5;
ssl_prefer_server_ciphers on;
```

#### 🔑 **Secrets Management**
```bash
# Using HashiCorp Vault
vault kv put secret/hyperion \
  jwt_secret="$(openssl rand -base64 32)" \
  neo4j_password="$(openssl rand -base64 16)" \
  api_key="$(openssl rand -hex 32)"

# Environment injection
export JWT_SECRET_KEY="$(vault kv get -field=jwt_secret secret/hyperion)"
```

---

## 🆘 **Troubleshooting Déploiement**

### 🐛 **Problèmes Courants**

#### ❌ **Service ne démarre pas**
```bash
# Diagnostic
sudo systemctl status hyperion
sudo journalctl -u hyperion -f

# Solutions communes
├── Vérifier permissions fichiers
├── Valider configuration .env
├── Tester connectivité bases de données
└── Vérifier ports disponibles
```

#### 📊 **Performance dégradée**
```bash
# Monitoring système
htop
iotop
netstat -tulpn

# Profiling application
hyperion profile --enable-profiling
hyperion debug --performance-analysis
```

#### 🔒 **Problèmes de connexion**
```bash
# Test connectivité
telnet neo4j-host 7687
redis-cli -h redis-host ping
curl http://ollama-host:11434/api/tags
```

---

## 📚 **Scripts de Déploiement**

### 🚀 **Script Master**
```bash
# scripts/deploy/production.sh
#!/bin/bash
set -euo pipefail

DEPLOY_ENV=${1:-production}
VERSION=${2:-latest}

echo "🚀 Déploying Hyperion $VERSION to $DEPLOY_ENV"

# Pre-deployment checks
./scripts/pre_deploy_checks.sh $DEPLOY_ENV

# Database migrations
./scripts/migrate_database.sh $DEPLOY_ENV

# Application deployment
case $DEPLOY_ENV in
  "standalone")
    ./scripts/deploy_standalone.sh $VERSION
    ;;
  "docker")
    ./scripts/deploy_docker.sh $VERSION
    ;;
  "kubernetes")
    ./scripts/deploy_k8s.sh $VERSION
    ;;
esac

# Post-deployment verification
./scripts/post_deploy_verification.sh $DEPLOY_ENV

echo "✅ Deployment completed successfully"
```

---

## 🔗 **Références**

- **[System Overview](system-overview)** : Architecture générale
- **Configuration** : Variables d'environnement
- **Troubleshooting** : Résolution problèmes
- **[Getting Started](../getting-started)** : Installation développement

---

---

## 🎯 **Résumé Déploiement**

### ✅ **Architecture Enterprise Déployée**

| Service | Port | Status | Description |
|---------|------|--------|------------------|
| **API Gateway** | 8000 | ✅ Ready | Routage intelligent + auth + cache |
| **RAG Pipeline** | 8001 | ✅ Enhanced | Response optimization + quality |
| **Analytics Engine** | 8002 | ✅ Intelligence | Pattern + behavioral analysis |
| **Dashboard** | 3000 | ✅ Enterprise | Interface admin avancée |
| **Chat Interface** | 3001 | ✅ Ready | Open WebUI conversationnel |
| **Monitoring** | 9090 | ✅ Active | Prometheus + métriques |
| **Neo4j v5.x** | 7474 | ✅ Enhanced | Graphe de code + APOC |
| **MLflow Platform** | 5000 | ✅ Ready | ML tracking + models |

### 📊 **Métriques Qualité Atteintes**

- **Ruff Linting** : ✅ **0 erreurs** (100% compliance)
- **Black Formatting** : ✅ **148 fichiers** compliant
- **Tests** : ✅ **189/189** passing (100% success)
- **Architecture** : ✅ **8 microservices** validés
- **Documentation** : ✅ **Complète** cours/ + technique/

### 🚀 **Commandes de Déploiement Rapide**

```bash
# Option 1: Orchestrateur Master (Recommandé)
./scripts/deploy/hyperion_master.sh --profile enterprise

# Option 2: Docker Enterprise (8 services)
./scripts/docker/hyperion-docker.sh --action up --profile enterprise

# Option 3: Qualité + Déploiement
ruff check src/ tests/ && black --check src/ tests/ && pytest tests/ -v
./scripts/deploy/hyperion_master.sh --profile enterprise --verify-quality
```

### 🔗 **Services Actifs Post-Déploiement**

```bash
# Vérification santé complète
curl -f http://localhost:8000/health  # API Gateway
curl -f http://localhost:8001/health  # RAG Pipeline
curl -f http://localhost:8002/health  # Analytics
curl -f http://localhost:9090/metrics # Monitoring

# Interfaces Web
open http://localhost:8000  # API Gateway + docs
open http://localhost:3000  # Dashboard Enterprise
open http://localhost:3001  # Chat conversationnel
open http://localhost:7474  # Neo4j Browser
```

---

*Documentation Déploiement - Hyperion Architecture*