# 🚀 Script d'installation ultime Hyperion

Script interactif qui gère **TOUT** :
- Installation services (Docker, Qdrant, Ollama, Neo4j)
- Configuration système
- Ingestion données
- Génération documentation
- Lancement services

---

## 📦 Utilisation

### Installation complète (tout automatique)

```bash
cd /home/kortazo/Documents/Hyperion
chmod +x scripts/setup_hyperion.sh
./scripts/setup_hyperion.sh
```

**Menu interactif** :
```
1. Tout installer (installation complète)    ← Recommandé
2. Installation personnalisée (choix modules)
3. Vérifier l'installation existante
4. Lancer les services
5. Quitter
```

---

## ✨ Fonctionnalités

### 1. Installation complète (Option 1)

Installe TOUT automatiquement :
- ✅ Docker
- ✅ Qdrant (vector store)
- ✅ Ollama (LLM local)
- ✅ Neo4j (optionnel)
- ✅ Dépendances Python
- ✅ Ingestion données
- ✅ Génération docs
- ✅ Démarrage services

**Durée** : 30-60 min (dont 15-30 min téléchargement modèle)

### 2. Installation personnalisée (Option 2)

Choisis ce que tu veux installer :
- Docker ? (o/n)
- Qdrant ? (o/n)
- Ollama ? (o/n)
- Neo4j ? (o/n)
- Python deps ? (o/n)
- Ingérer données ? (o/n)
- Générer docs ? (o/n)
- Démarrer services ? (o/n)

### 3. Vérification (Option 3)

Vérifie l'état de l'installation :
- Docker : ✅/❌
- Qdrant : ✅/❌
- Ollama : ✅/❌
- Neo4j : ✅/❌
- Python : ✅/❌
- CUDA : ✅/❌
- Repos analysés : X
- Docs générées : X

### 4. Lancer services (Option 4)

Menu lancement :
1. Dashboard complet (API + Frontend)
2. API uniquement
3. Test RAG interactif
4. Tous en arrière-plan

---

## 🎯 Choix modèles Ollama

Le script propose :
```
1. qwen2.5:32b  - 19 GB (meilleur, GPU requis)
2. qwen2.5:14b  - 8 GB  (bon compromis)
3. qwen2.5:7b   - 4 GB  (rapide, léger)
4. llama3.2     - 2 GB  (très léger)
5. Aucun (skip)
```

**Recommandation** : qwen2.5:32b (ta RTX 4090 peut le gérer)

---

## 🔧 Fonctionnalités intelligentes

### Détection automatique
- ✅ Vérifie si déjà installé (skip si présent)
- ✅ Détecte GPU (installe PyTorch CUDA ou CPU)
- ✅ Adapte selon distribution (Arch/Debian)
- ✅ Gère groupe Docker automatiquement

### Sécurité
- ✅ Log complet : `install.log`
- ✅ Arrêt si erreur (`set -e`)
- ✅ Validation inputs utilisateur
- ✅ Backup config existante

### User-friendly
- ✅ Couleurs dans terminal
- ✅ Barres de progression
- ✅ Messages clairs
- ✅ Aide contextuelle

---

## 📊 Exemple d'utilisation

### Première installation

```bash
./scripts/setup_hyperion.sh

# Menu
Choix (1-5): 1  # Tout installer

# Le script fait TOUT automatiquement
# Tu attends 30-60 min
# C'est terminé !
```

### Ajout module après

```bash
./scripts/setup_hyperion.sh

# Menu
Choix (1-5): 2  # Installation personnalisée

Installer Docker ? n  # Déjà fait
Installer Qdrant ? n  # Déjà fait
Installer Ollama ? n  # Déjà fait
Installer Neo4j ? o   # Ajouter Neo4j
...
```

### Vérifier installation

```bash
./scripts/setup_hyperion.sh

# Menu
Choix (1-5): 3  # Vérification

# Affiche état de tout
```

### Lancer dashboard

```bash
./scripts/setup_hyperion.sh

# Menu
Choix (1-5): 4  # Lancer services

# Sous-menu
Choix (1-4): 1  # Dashboard complet

# Dashboard sur http://localhost:3000
```

---

## 🐛 Troubleshooting

### Docker permission denied

Le script gère automatiquement :
```bash
sudo usermod -aG docker $USER
newgrp docker  # Ou relancer script
```

### Ollama ne démarre pas

```bash
# Le script tente systemd puis fallback manuel
sudo systemctl start ollama
# ou
ollama serve &
```

### Qdrant timeout

```bash
# Le script attend 30 sec
# Si échec, check logs:
docker logs qdrant
```

### PyTorch CUDA non détecté

```bash
# Le script détecte auto, mais si problème:
pip uninstall torch
pip install torch --index-url https://download.pytorch.org/whl/cu121
```

---

## 📋 Fichiers créés

```
~/qdrant_storage/          # Données Qdrant
~/neo4j_data/              # Données Neo4j (si installé)
$HYPERION_DIR/install.log  # Log installation
$HYPERION_DIR/.env         # Config (màj auto)
```

---

## 🎉 Après installation

```bash
# Vérifier tout marche
curl http://localhost:6333/       # Qdrant
curl http://localhost:11434/      # Ollama
curl http://localhost:7474/       # Neo4j (optionnel)

# Lancer dashboard
python3 scripts/run_dashboard.py

# Ou tester RAG
python3 scripts/test_rag.py
```

---

## 💡 Astuces

### Installation rapide (nuit)
```bash
# Option 1 + laisser tourner
# Au réveil : tout installé !
```

### Installation progressive
```bash
# Jour 1: Docker + Qdrant
# Jour 2: Ollama + modèle
# Jour 3: Ingestion + docs
```

### Réinstallation propre
```bash
# Supprimer containers
docker rm -f qdrant neo4j

# Supprimer données
rm -rf ~/qdrant_storage ~/neo4j_data

# Relancer script
./scripts/setup_hyperion.sh
```

---

🚀 **Script ultime prêt ! Lance-le et dors, au réveil tout sera installé ! 😴**
