#!/bin/bash
# Script de setup automatique pour Hyperion RAG

set -e

echo "============================================================"
echo "🚀 HYPERION RAG - SETUP AUTOMATIQUE"
echo "============================================================"
echo ""

# ============================================================
# 1. Docker
# ============================================================

echo "📦 1. Configuration Docker..."
echo ""

# Démarrer Docker si pas actif
if ! systemctl is-active --quiet docker; then
    echo "   ⏳ Démarrage Docker..."
    sudo systemctl start docker
    sleep 2
    echo "   ✅ Docker démarré"
else
    echo "   ✅ Docker déjà actif"
fi

# Vérifier que Docker fonctionne
if ! docker ps &>/dev/null; then
    echo "   ❌ Docker ne répond pas, ajout de l'utilisateur au groupe docker..."
    sudo usermod -aG docker $USER
    echo "   ⚠️  Tu dois te déconnecter/reconnecter pour que ça prenne effet"
    echo "   ⚠️  Ensuite relance ce script"
    exit 1
fi

echo ""

# ============================================================
# 2. Qdrant
# ============================================================

echo "🗄️  2. Configuration Qdrant..."
echo ""

# Vérifier si Qdrant existe déjà
if docker ps -a --format '{{.Names}}' | grep -q "^qdrant$"; then
    echo "   ℹ️  Container Qdrant existant trouvé"
    
    # Si arrêté, démarrer
    if ! docker ps --format '{{.Names}}' | grep -q "^qdrant$"; then
        echo "   ⏳ Démarrage Qdrant existant..."
        docker start qdrant
    else
        echo "   ✅ Qdrant déjà actif"
    fi
else
    echo "   ⏳ Création container Qdrant..."
    
    # Créer dossier de stockage
    mkdir -p ~/qdrant_storage
    
    # Lancer Qdrant
    docker run -d \
        --name qdrant \
        -p 6333:6333 \
        -p 6334:6334 \
        -v ~/qdrant_storage:/qdrant/storage \
        qdrant/qdrant
    
    echo "   ✅ Qdrant lancé"
fi

# Attendre que Qdrant soit prêt
echo "   ⏳ Attente Qdrant..."
for i in {1..10}; do
    if curl -s http://localhost:6333/ >/dev/null 2>&1; then
        echo "   ✅ Qdrant opérationnel"
        break
    fi
    sleep 1
done

echo ""

# ============================================================
# 3. Ollama
# ============================================================

echo "🤖 3. Configuration Ollama..."
echo ""

# Vérifier si Ollama est installé
if ! command -v ollama &> /dev/null; then
    echo "   ⏳ Installation Ollama..."
    curl -fsSL https://ollama.com/install.sh | sh
    echo "   ✅ Ollama installé"
else
    echo "   ✅ Ollama déjà installé"
fi

# Démarrer service Ollama si pas actif
if ! systemctl is-active --quiet ollama 2>/dev/null; then
    echo "   ⏳ Démarrage service Ollama..."
    sudo systemctl start ollama 2>/dev/null || {
        echo "   ⚠️  Service systemd non trouvé, lancement manuel..."
        ollama serve &>/dev/null &
        sleep 2
    }
    echo "   ✅ Service Ollama démarré"
else
    echo "   ✅ Service Ollama déjà actif"
fi

# Vérifier si modèle déjà téléchargé
if ollama list | grep -q "qwen2.5:32b"; then
    echo "   ✅ Modèle qwen2.5:32b déjà téléchargé"
else
    echo "   ⏳ Téléchargement qwen2.5:32b (~19 GB, 10-15 min)..."
    echo "   💡 Si trop lent, Ctrl+C et utilise qwen2.5:14b à la place"
    ollama pull qwen2.5:32b
    echo "   ✅ Modèle téléchargé"
fi

echo ""

# ============================================================
# 4. Dépendances Python
# ============================================================

echo "🐍 4. Installation dépendances Python..."
echo ""

cd /home/kortazo/Documents/Hyperion

# PyTorch avec CUDA
if python3 -c "import torch; torch.cuda.is_available()" 2>/dev/null; then
    echo "   ✅ PyTorch CUDA déjà installé"
else
    echo "   ⏳ Installation PyTorch avec CUDA..."
    pip install torch torchvision torchaudio --index-url https://download.pytorch.org/whl/cu121 --break-system-packages
    echo "   ✅ PyTorch installé"
fi

# Autres dépendances
echo "   ⏳ Installation requirements.txt..."
pip install -r requirements.txt --break-system-packages --quiet
echo "   ✅ Dépendances installées"

echo ""

# ============================================================
# 5. Vérifications
# ============================================================

echo "✅ 5. Vérifications finales..."
echo ""

# Docker
if docker ps | grep -q qdrant; then
    echo "   ✅ Qdrant actif (http://localhost:6333)"
else
    echo "   ❌ Qdrant non actif"
fi

# Ollama
if curl -s http://localhost:11434/api/tags >/dev/null 2>&1; then
    echo "   ✅ Ollama actif (http://localhost:11434)"
else
    echo "   ❌ Ollama non actif"
fi

# CUDA
if python3 -c "import torch; print('   ✅ CUDA disponible' if torch.cuda.is_available() else '   ❌ CUDA non disponible')"; then
    :
fi

echo ""

# ============================================================
# Résumé
# ============================================================

echo "============================================================"
echo "🎉 SETUP TERMINÉ !"
echo "============================================================"
echo ""
echo "📋 Services actifs :"
echo "   • Qdrant      : http://localhost:6333"
echo "   • Qdrant UI   : http://localhost:6333/dashboard"
echo "   • Ollama API  : http://localhost:11434"
echo ""
echo "🚀 Prochaines étapes :"
echo ""
echo "   # 1. Ingérer les données"
echo "   python3 scripts/ingest_rag.py"
echo ""
echo "   # 2. Tester le RAG"
echo "   python3 scripts/test_rag.py"
echo ""
echo "   # 3. Ou lancer le dashboard"
echo "   python3 scripts/run_dashboard.py"
echo ""
echo "============================================================"
