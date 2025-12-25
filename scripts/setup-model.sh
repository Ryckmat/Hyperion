#!/bin/bash
# hyperion-model-setup.sh - Configuration automatique des modèles LLM

set -e

echo "🎯 Configuration du modèle LLM pour Hyperion v2.5.0"
echo "=============================================="
echo ""

# Vérifier que Ollama est installé
if ! command -v ollama &> /dev/null; then
    echo "❌ Ollama n'est pas installé. Installez-le d'abord:"
    echo "   curl -fsSL https://ollama.ai/install.sh | sh"
    exit 1
fi

# Vérifier que Ollama fonctionne
if ! ollama list &> /dev/null; then
    echo "❌ Ollama ne répond pas. Démarrez le service:"
    echo "   ollama serve"
    exit 1
fi

echo "📊 Profils d'usage disponibles:"
echo ""
echo "1) 🏃‍♂️ Performance Ultra-Rapide (<3s)"
echo "   Modèle: llama3.2:1b (1.3GB)"
echo "   Usage: Exploration rapide, démonstrations"
echo ""
echo "2) ⚖️ Équilibre Performance/Qualité (5-10s)"
echo "   Modèle: llama3.1:8b (4.7GB)"
echo "   Usage: Développement quotidien, code reviews"
echo ""
echo "3) 🧠 Qualité Premium (10-30s)"
echo "   Modèle: qwen2.5:14b (8.7GB)"
echo "   Usage: Analyses approfondies, architecture"
echo ""
echo "4) 🚀 Expert/Recherche (30s+)"
echo "   Modèle: qwen2.5:32b (19GB)"
echo "   Usage: Audits, recherche, analyses complexes"
echo ""
echo "5) 📋 Afficher la configuration actuelle"
echo ""

read -p "Votre choix (1-5): " choice

case $choice in
    1)
        MODEL="llama3.2:1b"
        TOKENS="128"
        TEMP="0.0"
        TIMEOUT="2"
        DESCRIPTION="Performance Ultra-Rapide"
        ;;
    2)
        MODEL="llama3.1:8b"
        TOKENS="512"
        TEMP="0.1"
        TIMEOUT="10"
        DESCRIPTION="Équilibre Performance/Qualité"
        ;;
    3)
        MODEL="qwen2.5:14b"
        TOKENS="1024"
        TEMP="0.1"
        TIMEOUT="30"
        DESCRIPTION="Qualité Premium"
        ;;
    4)
        MODEL="qwen2.5:32b"
        TOKENS="2048"
        TEMP="0.2"
        TIMEOUT="60"
        DESCRIPTION="Expert/Recherche"
        ;;
    5)
        echo ""
        echo "📋 Configuration actuelle:"
        echo "========================="
        if [ -f "src/hyperion/modules/rag/config.py" ]; then
            echo "Modèle: $(grep 'OLLAMA_MODEL.*=' src/hyperion/modules/rag/config.py | cut -d'"' -f2)"
            echo "Max Tokens: $(grep 'LLM_MAX_TOKENS.*=' src/hyperion/modules/rag/config.py | cut -d'(' -f2 | cut -d')' -f1)"
            echo "Température: $(grep 'LLM_TEMPERATURE.*=' src/hyperion/modules/rag/config.py | cut -d'(' -f2 | cut -d')' -f1)"
            echo "Timeout: $(grep 'LLM_TIMEOUT.*=' src/hyperion/modules/rag/config.py | cut -d'(' -f2 | cut -d')' -f1)"
        else
            echo "❌ Fichier de configuration non trouvé"
        fi
        exit 0
        ;;
    *)
        echo "❌ Choix invalide"
        exit 1
        ;;
esac

echo ""
echo "✅ Configuration sélectionnée: $DESCRIPTION"
echo "📦 Modèle: $MODEL"
echo ""

# Vérifier si le modèle est déjà téléchargé
if ollama list | grep -q "$MODEL"; then
    echo "✅ Modèle $MODEL déjà disponible"
else
    echo "📥 Téléchargement du modèle $MODEL..."
    echo "⏳ Cela peut prendre plusieurs minutes selon la taille..."

    # Télécharger avec une barre de progression visible
    ollama pull "$MODEL"

    if [ $? -eq 0 ]; then
        echo "✅ Modèle $MODEL téléchargé avec succès"
    else
        echo "❌ Échec du téléchargement du modèle $MODEL"
        exit 1
    fi
fi

# Créer un backup de la configuration actuelle
if [ -f "src/hyperion/modules/rag/config.py" ]; then
    cp "src/hyperion/modules/rag/config.py" "src/hyperion/modules/rag/config.py.backup.$(date +%Y%m%d_%H%M%S)"
    echo "💾 Backup de la configuration créé"
fi

# Mettre à jour la configuration
echo "📝 Mise à jour de la configuration..."

CONFIG_FILE="src/hyperion/modules/rag/config.py"

# Créer une version temporaire avec les nouvelles valeurs
sed "s/OLLAMA_MODEL.*=.*$/OLLAMA_MODEL = os.getenv(\"OLLAMA_MODEL\", \"$MODEL\")/g" "$CONFIG_FILE" | \
sed "s/LLM_MAX_TOKENS.*=.*$/LLM_MAX_TOKENS = int(os.getenv(\"LLM_MAX_TOKENS\", \"$TOKENS\"))/g" | \
sed "s/LLM_TEMPERATURE.*=.*$/LLM_TEMPERATURE = float(os.getenv(\"LLM_TEMPERATURE\", \"$TEMP\"))/g" | \
sed "s/LLM_TIMEOUT.*=.*$/LLM_TIMEOUT = int(os.getenv(\"LLM_TIMEOUT\", \"$TIMEOUT\"))/g" > "$CONFIG_FILE.tmp"

# Remplacer le fichier original
mv "$CONFIG_FILE.tmp" "$CONFIG_FILE"

echo "✅ Configuration mise à jour:"
echo "   - Modèle: $MODEL"
echo "   - Max Tokens: $TOKENS"
echo "   - Température: $TEMP"
echo "   - Timeout: $TIMEOUT secondes"
echo ""

# Vérifier si l'API Hyperion est en cours d'exécution
if pgrep -f "hyperion.api.main" > /dev/null; then
    echo "🔄 Redémarrage de l'API Hyperion..."
    pkill -f "hyperion.api.main"
    sleep 2

    # Redémarrer en arrière-plan
    cd "$(dirname "$0")/.."
    python -m hyperion.api.main &
    API_PID=$!

    echo "⏳ Attente du démarrage de l'API..."
    sleep 5

    # Vérifier que l'API répond
    if curl -s http://localhost:8000/api/health > /dev/null; then
        echo "✅ API Hyperion redémarrée avec succès (PID: $API_PID)"

        # Test rapide du nouveau modèle
        echo "🧪 Test du nouveau modèle..."
        RESPONSE=$(curl -s -X POST "http://localhost:8000/api/chat" \
            -H "Content-Type: application/json" \
            -d '{"question":"Test de configuration","repo":"test"}' | \
            python -c "import json, sys; data=json.load(sys.stdin); print(data.get('answer', data.get('detail', 'Pas de réponse'))[:100])" 2>/dev/null)

        if [ $? -eq 0 ] && [ ! -z "$RESPONSE" ]; then
            echo "✅ Test réussi - Modèle fonctionnel"
            echo "📝 Réponse: $RESPONSE..."
        else
            echo "⚠️ Test partiel - API démarrée mais modèle peut nécessiter plus de temps"
        fi
    else
        echo "⚠️ API redémarrée mais pas encore accessible"
        echo "   Vérifiez manuellement: curl http://localhost:8000/api/health"
    fi
else
    echo "ℹ️ API Hyperion non en cours d'exécution"
    echo "   Démarrez-la manuellement: python -m hyperion.api.main"
fi

echo ""
echo "🎉 Configuration terminée!"
echo ""
echo "📚 Documentation complète: MODEL_SELECTION_GUIDE.md"
echo "🔧 Pour changer de modèle ultérieurement, relancez ce script"
echo ""
echo "💡 Conseils d'optimisation:"
echo "   - Utilisez GPU pour les gros modèles: export EMBEDDING_DEVICE=cuda"
echo "   - Surveillez l'utilisation RAM avec: htop ou nvidia-smi"
echo "   - Testez les performances: time curl -X POST localhost:8000/api/chat ..."