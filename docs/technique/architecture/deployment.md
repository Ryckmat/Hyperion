# 🚀 Déploiement - Hyperion v2.7

Stratégies et guides de déploiement pour Hyperion v2.7 en production

---

## 🎯 **Vue d'ensemble du Déploiement**

Hyperion v2.7 propose plusieurs stratégies de déploiement adaptées aux besoins entreprise :

### 📋 **Options de Déploiement**
1. **🖥️ Standalone Local** : Installation sur machine unique
2. **🐳 Docker Compose** : Orchestration conteneurisée
3. **☁️ Cloud Native** : Déploiement Kubernetes
4. **🏢 Enterprise** : Infrastructure haute disponibilité

---

## 🖥️ **Déploiement Standalone**

### 📋 **Prérequis**

#### 🔧 **Système**
```yaml
Requirements:
  OS: Linux (Ubuntu 20.04+ / CentOS 8+)
  CPU: 4 cores minimum, 8 cores recommandé
  RAM: 8GB minimum, 16GB recommandé
  Storage: 50GB minimum, SSD recommandé
  Network: Internet pour modèles LLM
```

#### 🐍 **Software**
```bash
# Prérequis logiciels
Python 3.8+
Git 2.25+
Neo4j 4.4+
Redis 6.0+
Docker 20.10+ (optionnel)
```

### ⚙️ **Installation Production**

#### 1️⃣ **Préparation Système**
```bash
# Création utilisateur système
sudo adduser hyperion --system --group
sudo mkdir -p /opt/hyperion
sudo chown hyperion:hyperion /opt/hyperion

# Configuration firewall
sudo ufw allow 8000  # API Hyperion
sudo ufw allow 7474  # Neo4j Browser
sudo ufw allow 7687  # Neo4j Bolt
```

#### 2️⃣ **Installation Hyperion**
```bash
# Installation dans environnement dédié
sudo -u hyperion python3 -m venv /opt/hyperion/venv
sudo -u hyperion /opt/hyperion/venv/bin/pip install hyperion

# Configuration environnement
sudo -u hyperion cp production.env /opt/hyperion/.env
```

#### 3️⃣ **Services Système**
```bash
# Service systemd pour Hyperion
sudo cp hyperion.service /etc/systemd/system/
sudo systemctl enable hyperion
sudo systemctl start hyperion
```

### 📄 **Configuration Production**

#### 🔧 **Environment Variables**
```bash
# /opt/hyperion/.env
HYPERION_ENV=production
HYPERION_PORT=8000
HYPERION_HOST=0.0.0.0

# Base de données
NEO4J_URL=bolt://localhost:7687
NEO4J_USER=hyperion_prod
NEO4J_PASSWORD=<secure_password>

# Cache
REDIS_URL=redis://localhost:6379/0

# ML/LLM
OLLAMA_HOST=http://localhost:11434
MLFLOW_TRACKING_URI=file:///opt/hyperion/mlruns

# Sécurité
JWT_SECRET_KEY=<secure_random_key>
API_RATE_LIMIT=100

# Logging
LOG_LEVEL=INFO
LOG_FILE=/var/log/hyperion/hyperion.log
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

## 🐳 **Déploiement Docker**

### 🏗️ **Architecture Conteneurisée**

```yaml
# docker-compose.prod.yml
version: '3.8'

services:
  hyperion:
    image: hyperion:2.7.0
    container_name: hyperion-app
    ports:
      - "8000:8000"
    environment:
      - HYPERION_ENV=production
      - NEO4J_URL=bolt://neo4j:7687
      - REDIS_URL=redis://redis:6379
    depends_on:
      - neo4j
      - redis
      - ollama
    volumes:
      - hyperion_data:/app/data
      - hyperion_logs:/app/logs
    networks:
      - hyperion_network
    restart: unless-stopped

  neo4j:
    image: neo4j:4.4-community
    container_name: hyperion-neo4j
    ports:
      - "7474:7474"
      - "7687:7687"
    environment:
      NEO4J_AUTH: neo4j/hyperion_secure_password
      NEO4J_dbms_memory_heap_max__size: 2G
    volumes:
      - neo4j_data:/data
      - neo4j_logs:/logs
    networks:
      - hyperion_network
    restart: unless-stopped

  redis:
    image: redis:6-alpine
    container_name: hyperion-redis
    ports:
      - "6379:6379"
    volumes:
      - redis_data:/data
    networks:
      - hyperion_network
    restart: unless-stopped
    command: redis-server --appendonly yes

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
  neo4j_data:
  neo4j_logs:
  redis_data:
  ollama_data:

networks:
  hyperion_network:
    driver: bridge
```

### 🚀 **Déploiement Docker**

#### 1️⃣ **Build & Deploy**
```bash
# Build image production
docker build -t hyperion:2.7.0 -f Dockerfile.prod .

# Déploiement avec compose
docker-compose -f docker-compose.prod.yml up -d

# Vérification santé
docker-compose ps
docker-compose logs hyperion
```

#### 2️⃣ **Configuration Volumes**
```bash
# Sauvegarde données
docker-compose exec neo4j neo4j-admin dump --database=neo4j --to=/data/neo4j-backup.dump

# Restauration
docker-compose exec neo4j neo4j-admin load --database=neo4j --from=/data/neo4j-backup.dump
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
./scripts/rolling_update.sh v2.7.1
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

- **[System Overview](system-overview.md)** : Architecture générale
- **[Configuration](../user-guide/configuration.md)** : Variables d'environnement
- **[Troubleshooting](../reference/troubleshooting.md)** : Résolution problèmes
- **[Getting Started](../getting-started/)** : Installation développement

---

*Documentation déploiement mise à jour pour Hyperion v2.7.0 - Décembre 2024*