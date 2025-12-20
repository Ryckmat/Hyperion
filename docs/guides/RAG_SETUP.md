# 🚀 Setup Hyperion RAG - Guide d'installation complet

Ce guide configure le RAG 100% local avec Qdrant + Ollama + BGE embeddings.

---

## 📋 Prérequis

- ✅ Python 3.10+
- ✅ GPU NVIDIA avec CUDA (RTX 4090 détecté)
- ✅ 30 GB RAM minimum
- ✅ 50 GB espace disque libre

---

## 1️⃣ Installation Qdrant (Vector Store)

### Option A : Docker (recommandé)

```bash
# Lancer Qdrant
docker run -d \
  --name qdrant \
  -p 6333:6333 \
  -p 6334:6334 \
  -v $(pwd)/qdrant_storage:/qdrant/storage \
  qdrant/qdrant

# Vérifier
curl http://localhost:6333/
```

### Option B : Installation manuelle

```bash
# Télécharger
wget https://github.com/qdrant/qdrant/releases/download/v1.7.0/qdrant-x86_64-unknown-linux-gnu.tar.gz

# Extraire
tar -xzf qdrant-x86_64-unknown-linux-gnu.tar.gz

# Lancer
./qdrant
```

**Dashboard Qdrant** : http://localhost:6333/dashboard

---

## 2️⃣ Installation Ollama (LLM Local)

```bash
# Installation
curl -fsSL https://ollama.com/install.sh | sh

# Vérifier
ollama --version

# Lancer le service
ollama serve
```

### Télécharger le modèle Qwen 2.5 32B

```bash
# Télécharger (~19 GB, peut prendre 10-15 min)
ollama pull qwen2.5:32b

# Tester
ollama run qwen2.5:32b "Bonjour, peux-tu te présenter ?"
```

**Alternative si 32B trop gros** :
```bash
# Qwen 2.5 14B (plus petit, ~8 GB)
ollama pull qwen2.5:14b

# Ou Llama 3.2 8B (encore plus petit, ~4.7 GB)
ollama pull llama3.2:latest
```

**Configuration** : Editer `.env`
```bash
OLLAMA_MODEL=qwen2.5:32b  # Ou qwen2.5:14b, llama3.2
```

---

## 3️⃣ Installation dépendances Python

```bash
cd /home/kortazo/Documents/Hyperion

# Installer PyTorch avec CUDA (pour GPU)
pip install torch torchvision torchaudio --index-url https://download.pytorch.org/whl/cu121 --break-system-packages

# Installer les dépendances Hyperion
pip install -r requirements.txt --break-system-packages
```

**Vérifier CUDA** :
```bash
python3 -c "import torch; print(f'CUDA disponible: {torch.cuda.is_available()}')"
# Devrait afficher : CUDA disponible: True
```

---

## 4️⃣ Configuration Hyperion

### Mettre à jour `.env`

```bash
# Ajouter à .env
cat >> .env << 'EOF'

# === RAG Configuration ===
QDRANT_HOST=localhost
QDRANT_PORT=6333
QDRANT_COLLECTION=hyperion_repos

# Embeddings (GPU)
EMBEDDING_MODEL=BAAI/bge-large-en-v1.5
EMBEDDING_DEVICE=cuda

# LLM Ollama
OLLAMA_BASE_URL=http://localhost:11434
OLLAMA_MODEL=qwen2.5:32b
LLM_TEMPERATURE=0.1
LLM_TOP_K=5
EOF
```

---

## 5️⃣ Ingestion des données

### Script d'ingestion

Créer `scripts/ingest_rag.py` :

```bash
cd /home/kortazo/Documents/Hyperion
python3 scripts/ingest_rag.py
```

Ce script va :
1. Charger tous les profils YAML
2. Découper en chunks sémantiques
3. Générer embeddings avec BGE-large (GPU)
4. Uploader vers Qdrant

**Durée estimée** : 1-2 minutes pour 1 repo

---

## 6️⃣ Test du RAG

### Test en ligne de commande

```bash
cd /home/kortazo/Documents/Hyperion
python3 scripts/test_rag.py
```

### Test via API

```bash
# Lancer l'API
python3 scripts/run_dashboard.py

# Dans un autre terminal
curl -X POST http://localhost:8000/api/chat \
  -H "Content-Type: application/json" \
  -d '{
    "question": "Qui est le contributeur principal de requests ?",
    "repo": "requests"
  }'
```

---

## 7️⃣ Vérifications

### Qdrant

```bash
# Nombre de points
curl http://localhost:6333/collections/hyperion_repos

# Dashboard
firefox http://localhost:6333/dashboard
```

### Ollama

```bash
# Liste modèles
ollama list

# Info modèle
ollama show qwen2.5:32b
```

### GPU

```bash
# Vérifier utilisation GPU
nvidia-smi

# Devrait montrer Python utilisant la VRAM
```

---

## 🐛 Troubleshooting

### Qdrant ne démarre pas

```bash
# Vérifier port disponible
ss -ltnp | grep 6333

# Logs Docker
docker logs qdrant
```

### Ollama erreur

```bash
# Redémarrer service
systemctl restart ollama

# Vérifier port
ss -ltnp | grep 11434
```

### CUDA pas détecté

```bash
# Vérifier driver NVIDIA
nvidia-smi

# Réinstaller PyTorch
pip uninstall torch
pip install torch --index-url https://download.pytorch.org/whl/cu121
```

### Embeddings lents

```bash
# Vérifier device utilisé
python3 -c "from sentence_transformers import SentenceTransformer; m = SentenceTransformer('BAAI/bge-large-en-v1.5', device='cuda'); print(m.device)"
```

---

## 📊 Utilisation mémoire estimée

| Composant | RAM | VRAM |
|-----------|-----|------|
| Qdrant | ~500 MB | 0 GB |
| BGE-large embeddings | ~1 GB | ~2 GB |
| Qwen 2.5 32B | 0 GB | ~19 GB |
| **Total** | **~2 GB** | **~21 GB** |

**Ta config** : 30 GB RAM, 24 GB VRAM → Largement suffisant ! ✅

---

## ⚡ Performance attendue

Avec ta RTX 4090 :
- **Embedding** : ~100 chunks/sec
- **LLM inference** : ~30 tokens/sec
- **Réponse simple** : 1-2 sec
- **Réponse complexe** : 3-5 sec

---

## 🎯 Prochaine étape

Une fois setup terminé :

```bash
# Lancer le dashboard complet
python3 scripts/run_dashboard.py
```

Dashboard avec chat RAG disponible sur http://localhost:3000 ! 🎉

---

## 💡 Commandes utiles

```bash
# Status services
systemctl status ollama
docker ps | grep qdrant

# Réindexer un repo
python3 scripts/ingest_rag.py --repo requests --clear

# Test rapide
echo '{"question": "Combien de commits ?", "repo": "requests"}' | \
  http POST localhost:8000/api/chat
```

---

**Installation terminée ! Le RAG est prêt à fonctionner ! 🚀**
