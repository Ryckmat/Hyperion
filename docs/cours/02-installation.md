# ⚙️ Chapitre 02 - Installation Hyperion v2.7

**Installez Hyperion sur votre machine** - Guide complet pas-à-pas

*⏱️ Durée estimée : 30 minutes*

---

## 🎯 **Objectifs de ce Chapitre**

À la fin de ce chapitre, vous aurez :
- ✅ Hyperion v2.7 installé et fonctionnel
- ✅ Tous les services démarrés (Neo4j, Redis, Ollama)
- ✅ Configuration de base validée
- ✅ Premier test réussi sur un repository

---

## 📋 **Prérequis Système**

### 💻 **Configuration Minimale**

```yaml
OS: Linux (Ubuntu 20.04+) ou macOS (10.15+)
CPU: 4 cores (8 cores recommandé)
RAM: 8GB (16GB recommandé)
Stockage: 20GB libres (SSD recommandé)
Python: 3.8 à 3.11
Git: 2.25+
```

### 🔍 **Vérification Prérequis**

```bash
# Vérifier Python
python3 --version
# Doit afficher : Python 3.8.x à 3.11.x

# Vérifier Git
git --version
# Doit afficher : git version 2.25 ou plus récent

# Vérifier l'espace disque
df -h
# Doit avoir au moins 20GB libres

# Vérifier la RAM
free -h
# Doit avoir au moins 8GB
```

### ❌ **Problème de Version ?**

#### 🐍 **Python trop ancien/récent**
```bash
# Ubuntu/Debian
sudo apt update
sudo apt install python3.10 python3.10-venv python3.10-pip

# macOS avec Homebrew
brew install python@3.10
```

#### 📝 **Git trop ancien**
```bash
# Ubuntu/Debian
sudo add-apt-repository ppa:git-core/ppa
sudo apt update
sudo apt install git

# macOS
brew upgrade git
```

---

## 🚀 **Installation Hyperion**

### 1️⃣ **Installation via pip (Recommandé)**

#### 📦 **Environnement Virtuel Python**
```bash
# Créer un environnement dédié
python3 -m venv hyperion-env

# Activer l'environnement
source hyperion-env/bin/activate  # Linux/macOS
# hyperion-env\Scripts\activate   # Windows

# Mettre à jour pip
pip install --upgrade pip
```

#### ⚡ **Installation Hyperion**
```bash
# Installation de la dernière version
pip install hyperion==2.7.0

# Vérifier l'installation
hyperion --version
# Doit afficher : Hyperion v2.7.0
```

### 2️⃣ **Installation Développeur (Alternative)**

```bash
# Cloner le repository
git clone https://github.com/your-org/hyperion.git
cd hyperion

# Installation en mode développement
pip install -e ".[dev]"

# Vérifier
hyperion --version
```

### 🎉 **Première Vérification**

```bash
# Test de base
hyperion info

# Devrait afficher quelque chose comme :
# 🤖 Hyperion v2.7.0 - Code Intelligence Platform
# 📊 Status: Ready for setup
# 🔧 Services: Not configured yet
```

---

## 🗃️ **Installation des Services**

Hyperion nécessite 3 services externes pour fonctionner pleinement :

### 1️⃣ **Neo4j (Base de Données Graphe)**

#### 🔧 **Installation Neo4j**

##### Linux (Ubuntu/Debian)
```bash
# Ajouter le repository Neo4j
wget -O - https://debian.neo4j.com/neotechnology.gpg.key | sudo apt-key add -
echo 'deb https://debian.neo4j.com stable 4.4' | sudo tee /etc/apt/sources.list.d/neo4j.list

# Installer
sudo apt update
sudo apt install neo4j=1:4.4.* openjdk-11-jdk

# Démarrer
sudo systemctl enable neo4j
sudo systemctl start neo4j
```

##### macOS
```bash
# Via Homebrew
brew tap neo4j/tap
brew install neo4j@4.4

# Démarrer
brew services start neo4j@4.4
```

#### ⚙️ **Configuration Neo4j**

```bash
# Configurer le mot de passe
sudo neo4j-admin set-initial-password hyperion_secure_2024

# Vérifier que Neo4j fonctionne
curl http://localhost:7474
# Devrait retourner une page HTML Neo4j
```

#### 🌐 **Interface Neo4j Browser**
- Ouvrir : http://localhost:7474
- Username : `neo4j`
- Password : `hyperion_secure_2024`

### 2️⃣ **Redis (Cache & Sessions)**

#### 🔧 **Installation Redis**

##### Linux (Ubuntu/Debian)
```bash
# Installation
sudo apt update
sudo apt install redis-server

# Configuration pour persistance
sudo systemctl enable redis-server
sudo systemctl start redis-server
```

##### macOS
```bash
# Via Homebrew
brew install redis

# Démarrer
brew services start redis
```

#### ✅ **Test Redis**
```bash
# Test de connection
redis-cli ping
# Devrait retourner : PONG
```

### 3️⃣ **Ollama (Modèles LLM Locaux)**

#### 🔧 **Installation Ollama**

##### Linux
```bash
# Installation automatique
curl -fsSL https://ollama.ai/install.sh | sh

# Ou installation manuelle
sudo curl -L https://ollama.ai/download/ollama-linux-amd64 -o /usr/local/bin/ollama
sudo chmod +x /usr/local/bin/ollama
```

##### macOS
```bash
# Via Homebrew
brew install ollama

# Ou téléchargement direct depuis ollama.ai
```

#### 🚀 **Démarrage Ollama**
```bash
# Démarrer le service
ollama serve

# Dans un nouveau terminal, tester
ollama list
# Devrait afficher la liste des modèles (vide au début)
```

#### 📦 **Installation des Modèles**

```bash
# Modèle ultra-rapide (recommandé pour débuter)
ollama pull llama3.2:1b

# Modèle équilibré (recommandé pour usage quotidien)
ollama pull llama3.1:8b

# Vérifier les modèles installés
ollama list
```

**💡 Conseil :** Commencez avec `llama3.2:1b` (1GB) pour tester, puis téléchargez `llama3.1:8b` (4.7GB) si vous avez la bande passante.

---

## ⚙️ **Configuration Hyperion**

### 1️⃣ **Configuration Automatique**

```bash
# Setup automatique avec valeurs par défaut
hyperion setup --auto

# Ou setup interactif
hyperion setup --interactive
```

### 2️⃣ **Configuration Manuelle**

#### 📄 **Fichier de Configuration**

Créer `~/.hyperion/config.yaml` :

```yaml
# Configuration Hyperion v2.7
version: "2.7.0"

# Services
services:
  neo4j:
    url: "bolt://localhost:7687"
    user: "neo4j"
    password: "hyperion_secure_2024"

  redis:
    url: "redis://localhost:6379"
    db: 0

  ollama:
    url: "http://localhost:11434"
    default_model: "llama3.2:1b"

# API Configuration
api:
  host: "0.0.0.0"
  port: 8000
  cors_origins: ["http://localhost:3000", "http://localhost:3001"]

# Performance
performance:
  max_workers: 4
  cache_size: "1GB"
  enable_gpu: false  # true si vous avez un GPU compatible

# Sécurité
security:
  jwt_secret_key: "your-secret-key-here"
  api_rate_limit: 100  # requêtes par minute

# Modèles ML
ml:
  feature_store_path: "~/.hyperion/features"
  mlflow_tracking_uri: "file://~/.hyperion/mlruns"
  model_cache_size: "500MB"
```

#### 🔒 **Générer une Clé de Sécurité**

```bash
# Générer une clé JWT sécurisée
python3 -c "import secrets; print(secrets.token_hex(32))"

# Copier le résultat dans config.yaml
```

---

## 🧪 **Vérification Installation**

### 1️⃣ **Test des Services**

```bash
# Vérifier tous les services
hyperion health

# Devrait afficher :
# ✅ Hyperion Core: Ready
# ✅ Neo4j: Connected (bolt://localhost:7687)
# ✅ Redis: Connected (localhost:6379)
# ✅ Ollama: Connected (http://localhost:11434)
# ✅ Models: llama3.2:1b ready
```

### 2️⃣ **Démarrer Hyperion**

```bash
# Démarrer le serveur
hyperion serve

# Devrait afficher :
# 🚀 Starting Hyperion v2.7.0...
# 📊 API Server: http://localhost:8000
# 🎯 Health Check: http://localhost:8000/health
# 📚 Documentation: http://localhost:8000/docs
# ✅ Ready to analyze repositories!
```

### 3️⃣ **Test Interface Web**

Ouvrir votre navigateur et tester :

#### 🏥 **Health Check**
- URL : http://localhost:8000/health
- Devrait retourner : `{"status": "healthy", "version": "2.7.0"}`

#### 📚 **Documentation API**
- URL : http://localhost:8000/docs
- Interface Swagger avec tous les endpoints

#### 🔍 **Test API Simple**
```bash
# Test avec curl
curl http://localhost:8000/api/info

# Devrait retourner les informations système
```

---

## 🎯 **Premier Test**

### 📂 **Analyser un Repository Test**

```bash
# Créer un repository de test
mkdir ~/test-hyperion
cd ~/test-hyperion
git init
echo "# Test Project" > README.md
git add README.md
git commit -m "Initial commit"

# Analyser avec Hyperion
hyperion profile ~/test-hyperion

# Devrait analyser et afficher :
# 🔍 Analyzing repository: test-hyperion
# 📊 Files analyzed: 1
# 📈 Complexity score: Low
# ✅ Analysis completed!
```

### 💬 **Test du Chat**

```bash
# Tester le chat IA (depuis un autre terminal)
curl -X POST http://localhost:8000/api/chat \
  -H "Content-Type: application/json" \
  -d '{
    "message": "Hello, peux-tu m'\''expliquer ce qu'\''est Hyperion ?",
    "repository": "test-hyperion"
  }'

# Devrait retourner une réponse explicative
```

---

## 🐛 **Troubleshooting Installation**

### ❌ **Problèmes Courants**

#### 🔌 **"Neo4j connection failed"**
```bash
# Vérifier que Neo4j fonctionne
sudo systemctl status neo4j

# Redémarrer si nécessaire
sudo systemctl restart neo4j

# Vérifier les logs
sudo journalctl -u neo4j -f
```

#### 🔴 **"Redis connection refused"**
```bash
# Vérifier Redis
redis-cli ping

# Redémarrer si nécessaire
sudo systemctl restart redis-server

# macOS
brew services restart redis
```

#### 🤖 **"Ollama model not found"**
```bash
# Vérifier les modèles installés
ollama list

# Installer le modèle manquant
ollama pull llama3.2:1b

# Vérifier qu'Ollama fonctionne
ollama serve  # Dans un terminal séparé
```

#### 🐍 **"Module not found" lors de l'import**
```bash
# Vérifier l'environnement virtuel
which python3
# Doit pointer vers votre environnement Hyperion

# Réinstaller si nécessaire
pip uninstall hyperion
pip install hyperion==2.7.0
```

### 🔧 **Debug Mode**

```bash
# Démarrer Hyperion en mode debug
hyperion serve --debug --log-level DEBUG

# Logs détaillés pour identifier les problèmes
```

### 📞 **Obtenir de l'Aide**

```bash
# Informations système complètes
hyperion diagnose

# Génère un rapport avec :
# - Versions des services
# - Configuration actuelle
# - Logs d'erreur récents
# - État des connexions
```

---

## 🎉 **Installation Réussie !**

### ✅ **Checklist Finale**

- [ ] Python 3.8+ installé et fonctionnel
- [ ] Hyperion v2.7.0 installé via pip
- [ ] Neo4j installé et accessible (port 7474)
- [ ] Redis installé et fonctionnel
- [ ] Ollama installé avec au moins un modèle LLM
- [ ] Configuration `~/.hyperion/config.yaml` créée
- [ ] `hyperion health` retourne tout ✅
- [ ] `hyperion serve` démarre sans erreur
- [ ] Test API sur http://localhost:8000/health réussi
- [ ] Premier repository analysé avec succès

### 🚀 **Vous êtes prêt !**

Hyperion est maintenant installé et fonctionnel sur votre machine. Vous avez :

- 🤖 **IA locale** pour analyser votre code
- 📊 **API complète** pour intégrations
- 🔍 **Chat intelligent** pour poser des questions
- 📈 **Modèles ML** pour prédictions avancées

---

## 📚 **Prochaines Étapes**

### 🎯 **Chapitre 03 - Premier Usage**

Maintenant que Hyperion est installé, vous allez apprendre à :
- Analyser votre premier "vrai" repository
- Comprendre les métriques générées
- Utiliser le chat IA pour explorer votre code
- Générer votre première documentation

👉 **Continuez avec** : [Chapitre 03 - Premier Usage](03-premier-usage.md)

### 💡 **Configuration Avancée (Optionnel)**

Si vous voulez optimiser votre installation :
- [Configuration Avancée](../technique/user-guide/configuration.md) : Tuning performance
- [Architecture](../technique/architecture/system-overview.md) : Comprendre l'architecture
- [Déploiement](../technique/architecture/deployment.md) : Installation en production

---

## 📖 **Récapitulatif du Chapitre**

### ✅ **Ce que vous avez fait :**
- Installé Hyperion v2.7 et ses dépendances
- Configuré Neo4j, Redis et Ollama
- Créé la configuration de base
- Vérifié que tout fonctionne
- Testé votre première analyse

### ⏭️ **Au prochain chapitre :**
- Analyser un repository complet
- Explorer les résultats et métriques
- Premiers pas avec le chat IA
- Générer de la documentation automatique

---

*Félicitations ! Vous avez installé Hyperion avec succès. Rendez-vous au [Chapitre 03](03-premier-usage.md) !* 🎉

---

*Cours Hyperion v2.7.0 - Chapitre 02 - Décembre 2024*