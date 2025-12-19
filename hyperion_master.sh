#!/bin/bash
# ============================================================================
# HYPERION MASTER - Contrôle complet avec vérification automatique
# ============================================================================
# Vérifie et démarre automatiquement tous les composants nécessaires
# ============================================================================

set -e

cd /home/kortazo/Documents/Hyperion

# Couleurs
GREEN='\033[0;32m'
RED='\033[0;31m'
YELLOW='\033[1;33m'
CYAN='\033[0;36m'
NC='\033[0m'

echo "============================================================"
echo "🚀 HYPERION MASTER - Contrôle complet"
echo "============================================================"
echo ""

# ============================================================================
# FONCTION : Importer la fonction Hyperion RAG dans Open WebUI
# ============================================================================

import_hyperion_function() {
    echo -e "${CYAN}   📦 Import fonction Hyperion RAG...${NC}"
    
    FUNCTION_FILE="config/openwebui_hyperion_function.py"
    
    if [ ! -f "$FUNCTION_FILE" ]; then
        echo -e "${RED}   ❌ Fichier fonction non trouvé: $FUNCTION_FILE${NC}"
        return 1
    fi
    
    # Lire le contenu de la fonction
    FUNCTION_CONTENT=$(cat "$FUNCTION_FILE")
    
    # Échapper pour JSON
    FUNCTION_CONTENT_ESCAPED=$(echo "$FUNCTION_CONTENT" | python3 -c 'import json,sys; print(json.dumps(sys.stdin.read()))')
    
    # Créer le JSON pour l'API
    JSON_PAYLOAD=$(cat <<EOF
{
    "id": "hyperion_rag",
    "name": "Hyperion RAG",
    "type": "pipe",
    "content": $FUNCTION_CONTENT_ESCAPED,
    "meta": {
        "description": "Connecte Open WebUI au RAG Hyperion pour interroger les repos Git analysés"
    }
}
EOF
)
    
    # Attendre que Open WebUI soit prêt
    for i in {1..30}; do
        if curl -s http://localhost:3001/api/config &>/dev/null; then
            break
        fi
        sleep 1
    done
    
    # Créer un compte admin si nécessaire et récupérer le token
    SIGNUP_RESPONSE=$(curl -s -X POST "http://localhost:3001/api/v1/auths/signup" \
        -H "Content-Type: application/json" \
        -d '{"name":"admin", "email":"admin@hyperion.local", "password":"hyperion123"}' 2>/dev/null || echo "{}")
    
    # Extraire le token (soit du signup, soit on essaie signin)
    TOKEN=$(echo "$SIGNUP_RESPONSE" | python3 -c 'import json,sys; d=json.loads(sys.stdin.read()); print(d.get("token",""))' 2>/dev/null)
    
    if [ -z "$TOKEN" ]; then
        # Essayer signin si signup a échoué (compte existe déjà)
        SIGNIN_RESPONSE=$(curl -s -X POST "http://localhost:3001/api/v1/auths/signin" \
            -H "Content-Type: application/json" \
            -d '{"email":"admin@hyperion.local", "password":"hyperion123"}' 2>/dev/null || echo "{}")
        TOKEN=$(echo "$SIGNIN_RESPONSE" | python3 -c 'import json,sys; d=json.loads(sys.stdin.read()); print(d.get("token",""))' 2>/dev/null)
    fi
    
    if [ -z "$TOKEN" ]; then
        echo -e "${YELLOW}   ⚠️  Impossible d'obtenir un token, import manuel requis${NC}"
        return 1
    fi
    
    # Vérifier si la fonction existe déjà
    EXISTING=$(curl -s -X GET "http://localhost:3001/api/v1/functions/" \
        -H "Authorization: Bearer $TOKEN" \
        -H "Content-Type: application/json" 2>/dev/null)
    
    if echo "$EXISTING" | grep -q "hyperion_rag"; then
        echo -e "${GREEN}   ✅ Fonction Hyperion RAG déjà présente${NC}"
        return 0
    fi
    
    # Importer la fonction
    RESPONSE=$(curl -s -X POST "http://localhost:3001/api/v1/functions/create" \
        -H "Authorization: Bearer $TOKEN" \
        -H "Content-Type: application/json" \
        -d "$JSON_PAYLOAD" 2>/dev/null)
    
    if echo "$RESPONSE" | grep -q "hyperion_rag"; then
        # Activer la fonction
        curl -s -X POST "http://localhost:3001/api/v1/functions/id/hyperion_rag/toggle" \
            -H "Authorization: Bearer $TOKEN" \
            -H "Content-Type: application/json" &>/dev/null
        echo -e "${GREEN}   ✅ Fonction Hyperion RAG importée et activée${NC}"
    else
        echo -e "${YELLOW}   ⚠️  Erreur import fonction: $RESPONSE${NC}"
        return 1
    fi
}

# ============================================================================
# FONCTION : Vérification complète du système
# ============================================================================

verify_system() {
    echo ""
    echo -e "${CYAN}============================================================${NC}"
    echo -e "${CYAN}🔍 VÉRIFICATION SYSTÈME COMPLÈTE${NC}"
    echo -e "${CYAN}============================================================${NC}"
    echo ""
    
    # 1. Docker
    echo -e "${CYAN}🐳 Docker...${NC}"
    if ! command -v docker &>/dev/null; then
        echo -e "${RED}   ❌ Docker non installé${NC}"
        echo "   Installation : sudo pacman -S docker"
        return 1
    fi
    if ! docker info &>/dev/null; then
        echo -e "${YELLOW}   ⚠️  Docker daemon non actif, démarrage...${NC}"
        sudo systemctl start docker
    fi
    echo -e "${GREEN}   ✅ Docker actif${NC}"
    
    # 2. Qdrant
    echo -e "${CYAN}📦 Qdrant...${NC}"
    if ! curl -s http://localhost:6333/collections &>/dev/null; then
        echo -e "${YELLOW}   ⚠️  Qdrant non actif, démarrage...${NC}"
        if docker ps -a --format '{{.Names}}' | grep -q "^qdrant$"; then
            docker start qdrant &>/dev/null
        else
            docker run -d --name qdrant \
                -p 6333:6333 -p 6334:6334 \
                -v ~/qdrant_storage:/qdrant/storage:z \
                qdrant/qdrant &>/dev/null
        fi
        sleep 3
    fi
    if curl -s http://localhost:6333/collections &>/dev/null; then
        echo -e "${GREEN}   ✅ Qdrant actif (http://localhost:6333)${NC}"
    else
        echo -e "${RED}   ❌ Qdrant n'a pas démarré${NC}"
    fi
    
    # 3. Ollama
    echo -e "${CYAN}🤖 Ollama...${NC}"
    if ! command -v ollama &>/dev/null; then
        echo -e "${RED}   ❌ Ollama non installé${NC}"
        echo "   Installation : curl -fsSL https://ollama.ai/install.sh | sh"
        return 1
    fi
    if ! systemctl is-active --quiet ollama 2>/dev/null; then
        echo -e "${YELLOW}   ⚠️  Service Ollama inactif, démarrage...${NC}"
        sudo systemctl start ollama
        sleep 2
    fi
    if systemctl is-active --quiet ollama 2>/dev/null; then
        echo -e "${GREEN}   ✅ Ollama actif${NC}"
        # Vérifier modèle
        if ollama list | grep -q "qwen2.5:32b"; then
            echo -e "${GREEN}   ✅ Modèle qwen2.5:32b disponible${NC}"
        else
            echo -e "${YELLOW}   ⚠️  Modèle qwen2.5:32b manquant${NC}"
            echo "   Téléchargement : ollama pull qwen2.5:32b"
        fi
    else
        echo -e "${RED}   ❌ Ollama non actif${NC}"
    fi
    
    # 4. Neo4j (optionnel)
    echo -e "${CYAN}🔷 Neo4j (optionnel)...${NC}"
    if curl -s http://localhost:7474 &>/dev/null; then
        echo -e "${GREEN}   ✅ Neo4j actif (http://localhost:7474)${NC}"
    else
        echo -e "${YELLOW}   ⚠️  Neo4j non actif (optionnel)${NC}"
        read -p "   Démarrer Neo4j ? (o/n): " start_neo4j
        if [[ "$start_neo4j" =~ ^[Oo]$ ]]; then
            if docker ps -a --format '{{.Names}}' | grep -q "^neo4j$"; then
                docker start neo4j &>/dev/null
            else
                docker run -d --name neo4j \
                    -p 7474:7474 -p 7687:7687 \
                    -e NEO4J_AUTH=neo4j/hyperion123 \
                    neo4j &>/dev/null
            fi
            sleep 3
            echo -e "${GREEN}   ✅ Neo4j démarré${NC}"
        fi
    fi
    
    # 5. Python + venv
    echo -e "${CYAN}🐍 Python...${NC}"
    echo -e "${GREEN}   ✅ Python $(python3 --version | cut -d' ' -f2)${NC}"
    
    if [ -d "venv" ]; then
        echo -e "${GREEN}   ✅ Venv présent${NC}"
    else
        echo -e "${YELLOW}   ⚠️  Venv absent${NC}"
        read -p "   Créer venv ? (o/n): " create_venv
        if [[ "$create_venv" =~ ^[Oo]$ ]]; then
            python3 -m venv venv
            source venv/bin/activate
            pip install -r requirements.txt --quiet
            echo -e "${GREEN}   ✅ Venv créé et dépendances installées${NC}"
        fi
    fi
    
    # 6. PyTorch CUDA
    echo -e "${CYAN}🔥 PyTorch CUDA...${NC}"
    if python3 -c "import torch; exit(0 if torch.cuda.is_available() else 1)" 2>/dev/null; then
        GPU=$(python3 -c "import torch; print(torch.cuda.get_device_name(0))" 2>/dev/null)
        echo -e "${GREEN}   ✅ CUDA disponible : $GPU${NC}"
    else
        echo -e "${YELLOW}   ⚠️  CUDA non disponible${NC}"
        echo "   Installation : pip install torch torchvision --index-url https://download.pytorch.org/whl/cu121"
    fi
    
    # 7. Dépendances Python RAG
    echo -e "${CYAN}📦 Dépendances Python RAG...${NC}"
    MISSING=()
    for pkg in qdrant_client sentence_transformers langchain torch; do
        if ! python3 -c "import $pkg" 2>/dev/null; then
            MISSING+=("$pkg")
        fi
    done
    
    if [ ${#MISSING[@]} -eq 0 ]; then
        echo -e "${GREEN}   ✅ Toutes les dépendances présentes${NC}"
    else
        echo -e "${YELLOW}   ⚠️  Packages manquants : ${MISSING[*]}${NC}"
        read -p "   Installer maintenant ? (o/n): " install_deps
        if [[ "$install_deps" =~ ^[Oo]$ ]]; then
            pip install qdrant-client sentence-transformers langchain langchain-community torch --break-system-packages --quiet
            echo -e "${GREEN}   ✅ Dépendances installées${NC}"
        fi
    fi
    
    # 8. Open WebUI
    echo -e "${CYAN}💬 Open WebUI...${NC}"
    if docker ps --format '{{.Names}}' | grep -q "^open-webui$"; then
        echo -e "${GREEN}   ✅ Open WebUI actif (http://localhost:3001)${NC}"
    else
        echo -e "${YELLOW}   ⚠️  Open WebUI non actif${NC}"
        read -p "   Démarrer Open WebUI ? (o/n): " start_openwebui
        if [[ "$start_openwebui" =~ ^[Oo]$ ]]; then
            if docker ps -a --format '{{.Names}}' | grep -q "^open-webui$"; then
                echo -e "${YELLOW}   ♻️  Redémarrage container existant...${NC}"
                docker start open-webui &>/dev/null
            else
                echo -e "${YELLOW}   🚀 Création container Open WebUI...${NC}"
                docker run -d \
                    --name open-webui \
                    --add-host=host.docker.internal:host-gateway \
                    -p 3001:8080 \
                    -e OLLAMA_BASE_URL=http://host.docker.internal:11434 \
                    -e WEBUI_AUTH=false \
                    -e VECTOR_DB=qdrant \
                    -e QDRANT_URI=http://host.docker.internal:6333 \
                    -v open-webui:/app/backend/data \
                    --restart always \
                    ghcr.io/open-webui/open-webui:main &>/dev/null
            fi
            sleep 8
            if curl -s http://localhost:3001 &>/dev/null; then
                echo -e "${GREEN}   ✅ Open WebUI démarré (http://localhost:3001)${NC}"
                # Importer la fonction Hyperion RAG
                import_hyperion_function
            else
                echo -e "${RED}   ❌ Open WebUI n'a pas démarré${NC}"
            fi
        fi
    fi
    
    echo ""
    echo -e "${GREEN}✅ VÉRIFICATION TERMINÉE${NC}"
    echo ""
}

# ============================================================================
# MENU PRINCIPAL
# ============================================================================

# Demander ce qu'on veut faire
read -p "Vérifier et démarrer les services ? (o/n): " do_verify
read -p "Ingérer Neo4j (graphe) ? (o/n): " do_neo4j
read -p "Ingérer RAG (Qdrant) ? (o/n): " do_ingest
read -p "Générer documentation ? (o/n): " do_docs
read -p "Lancer dashboard React ? (o/n): " do_dashboard
read -p "Lancer Open WebUI (chat) ? (o/n): " do_openwebui

echo ""
echo "============================================================"
echo "🎯 Récapitulatif"
echo "============================================================"
[[ "$do_verify" =~ ^[Oo]$ ]] && echo "✅ Vérification services"
[[ "$do_neo4j" =~ ^[Oo]$ ]] && echo "✅ Ingestion Neo4j"
[[ "$do_ingest" =~ ^[Oo]$ ]] && echo "✅ Ingestion RAG"
[[ "$do_docs" =~ ^[Oo]$ ]] && echo "✅ Génération docs"
[[ "$do_dashboard" =~ ^[Oo]$ ]] && echo "✅ Lancement dashboard React"
[[ "$do_openwebui" =~ ^[Oo]$ ]] && echo "✅ Lancement Open WebUI"
echo ""

read -p "Confirmer ? (o/n): " confirm
[[ ! "$confirm" =~ ^[Oo]$ ]] && echo "Annulé." && exit 0

echo ""
echo "============================================================"
echo "🚀 EXÉCUTION"
echo "============================================================"

# 0. Vérification système
if [[ "$do_verify" =~ ^[Oo]$ ]]; then
    verify_system
fi

# 1. Neo4j
if [[ "$do_neo4j" =~ ^[Oo]$ ]]; then
    echo ""
    echo "🔷 Ingestion Neo4j..."
    
    # Vérifier Neo4j actif
    if ! curl -s http://localhost:7474 &>/dev/null; then
        echo "   ⚠️  Neo4j non actif, démarrage..."
        if docker ps -a --format '{{.Names}}' | grep -q "^neo4j$"; then
            docker start neo4j
        else
            docker run -d --name neo4j \
                -p 7474:7474 -p 7687:7687 \
                -e NEO4J_AUTH=neo4j/hyperion123 \
                neo4j
        fi
        sleep 5
    fi
    
    shopt -s nullglob
    profiles=(data/repositories/*/profile.yaml)
    for profile in "${profiles[@]}"; do
        if [ -f "$profile" ]; then
            REPO=$(basename $(dirname "$profile"))
            echo "   → $REPO"
            python3 -m hyperion.cli.main ingest "$profile" --clear
        fi
    done
fi

# 2. RAG
if [[ "$do_ingest" =~ ^[Oo]$ ]]; then
    echo ""
    echo "📥 Ingestion RAG..."
    
    # Vérifier Qdrant actif
    if ! curl -s http://localhost:6333/collections &>/dev/null; then
        echo "   ⚠️  Qdrant non actif, démarrage..."
        if docker ps -a --format '{{.Names}}' | grep -q "^qdrant$"; then
            docker start qdrant
        else
            docker run -d --name qdrant \
                -p 6333:6333 -p 6334:6334 \
                -v ~/qdrant_storage:/qdrant/storage:z \
                qdrant/qdrant
        fi
        sleep 3
    fi
    
    # Vérifier Ollama actif
    if ! systemctl is-active --quiet ollama 2>/dev/null; then
        echo "   ⚠️  Ollama non actif, démarrage..."
        sudo systemctl start ollama
        sleep 2
    fi
    
    # Vérifier modèle
    if ! ollama list | grep -q "qwen2.5:32b"; then
        echo "   ❌ Modèle qwen2.5:32b manquant"
        echo "   Téléchargement : ollama pull qwen2.5:32b (19 GB)"
        exit 1
    fi
    
    python3 scripts/ingest_rag.py
fi

# 3. Docs
if [[ "$do_docs" =~ ^[Oo]$ ]]; then
    echo ""
    echo "📝 Génération documentation..."
    shopt -s nullglob
    profiles=(data/repositories/*/profile.yaml)
    for profile in "${profiles[@]}"; do
        [ -f "$profile" ] && python3 -m hyperion.cli.main generate "$profile"
    done
fi

# 4. Dashboard React
if [[ "$do_dashboard" =~ ^[Oo]$ ]]; then
    echo ""
    echo "🌐 Lancement dashboard React..."
    
    # Vérifier Ollama pour l'API
    if ! systemctl is-active --quiet ollama 2>/dev/null; then
        echo "   ⚠️  Ollama non actif, démarrage..."
        sudo systemctl start ollama
        sleep 2
    fi
    
    python3 scripts/run_dashboard.py
fi

# 5. Open WebUI
if [[ "$do_openwebui" =~ ^[Oo]$ ]]; then
    echo ""
    echo "💬 Lancement Open WebUI..."
    
    # Vérifier si déjà actif
    if docker ps --format '{{.Names}}' | grep -q "^open-webui$"; then
        echo "   ✅ Open WebUI déjà actif"
    else
        # Vérifier si container existe
        if docker ps -a --format '{{.Names}}' | grep -q "^open-webui$"; then
            echo "   ♻️  Redémarrage container..."
            docker start open-webui
        else
            echo "   🚀 Création container Open WebUI..."
            docker run -d \
                --name open-webui \
                --add-host=host.docker.internal:host-gateway \
                -p 3001:8080 \
                -e OLLAMA_BASE_URL=http://host.docker.internal:11434 \
                -e WEBUI_AUTH=false \
                -e VECTOR_DB=qdrant \
                -e QDRANT_URI=http://host.docker.internal:6333 \
                -v open-webui:/app/backend/data \
                --restart always \
                ghcr.io/open-webui/open-webui:main
        fi
        
        echo "   ⏳ Attente démarrage..."
        sleep 10
        
        if curl -s http://localhost:3001 &>/dev/null; then
            echo "   ✅ Open WebUI prêt !"
            
            # Importer la fonction Hyperion RAG
            import_hyperion_function
            
            echo ""
            echo "   🌐 Open WebUI : http://localhost:3001"
            echo "   🤖 Modèle      : qwen2.5:32b (auto-détecté)"
            echo "   🔌 Hyperion RAG : Sélectionner 'Hyperion RAG' dans les modèles"
            echo ""
            
            # Ouvrir navigateur
            if command -v xdg-open &>/dev/null; then
                xdg-open http://localhost:3001 &>/dev/null &
            fi
        else
            echo "   ❌ Open WebUI n'a pas démarré"
            echo "   Logs : docker logs open-webui"
        fi
    fi
fi

echo ""
echo "============================================================"
echo "🎉 TERMINÉ !"
echo "============================================================"
echo ""
echo "📱 Services actifs :"
[[ "$do_dashboard" =~ ^[Oo]$ ]] && echo "   • Dashboard React : http://localhost:3000"
[[ "$do_openwebui" =~ ^[Oo]$ ]] && echo "   • Open WebUI Chat : http://localhost:3001"
echo "   • API Hyperion    : http://localhost:8000"
echo "   • API Docs        : http://localhost:8000/docs"
echo ""
