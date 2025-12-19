#!/bin/bash
# ============================================================================
# HYPERION - SCRIPT DE DÉPLOIEMENT ULTIME
# ============================================================================
# Ce script gère l'installation, configuration et déploiement complet
# de la plateforme Hyperion avec toutes ses composantes.
#
# Auteur: Ryckman
# Date: 19 décembre 2024
# ============================================================================

set -e  # Arrêt si erreur

# Couleurs pour output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
PURPLE='\033[0;35m'
CYAN='\033[0;36m'
NC='\033[0m' # No Color

# ============================================================================
# Variables globales
# ============================================================================

HYPERION_DIR="/home/kortazo/Documents/Hyperion"
INSTALL_LOG="$HYPERION_DIR/install.log"
QDRANT_STORAGE="$HOME/qdrant_storage"

# Flags d'installation
INSTALL_DOCKER=false
INSTALL_QDRANT=false
INSTALL_OLLAMA=false
INSTALL_NEO4J=false
INSTALL_PYTHON_DEPS=false
INGEST_DATA=false
GENERATE_DOCS=false
START_SERVICES=false

# ============================================================================
# Fonctions utilitaires
# ============================================================================

log() {
    echo -e "${GREEN}[$(date +'%H:%M:%S')]${NC} $1" | tee -a "$INSTALL_LOG"
}

log_error() {
    echo -e "${RED}[$(date +'%H:%M:%S')] ❌ $1${NC}" | tee -a "$INSTALL_LOG"
}

log_warn() {
    echo -e "${YELLOW}[$(date +'%H:%M:%S')] ⚠️  $1${NC}" | tee -a "$INSTALL_LOG"
}

log_info() {
    echo -e "${CYAN}[$(date +'%H:%M:%S')] ℹ️  $1${NC}" | tee -a "$INSTALL_LOG"
}

print_header() {
    echo ""
    echo -e "${PURPLE}============================================================${NC}"
    echo -e "${PURPLE}$1${NC}"
    echo -e "${PURPLE}============================================================${NC}"
    echo ""
}

ask_yes_no() {
    while true; do
        read -p "$1 (o/n): " yn
        case $yn in
            [Oo]* ) return 0;;
            [Nn]* ) return 1;;
            * ) echo "Réponds par o (oui) ou n (non).";;
        esac
    done
}

check_command() {
    command -v "$1" &> /dev/null
}

check_service() {
    systemctl is-active --quiet "$1" 2>/dev/null
}

# ============================================================================
# Vérifications système
# ============================================================================

check_system() {
    print_header "🔍 VÉRIFICATION SYSTÈME"
    
    log "Système: $(uname -s) $(uname -r)"
    log "Distribution: $(lsb_release -d | cut -f2)"
    log "Python: $(python3 --version)"
    
    # CPU
    CPU_CORES=$(nproc)
    log "CPU: ${CPU_CORES} cœurs"
    
    # RAM
    RAM_GB=$(free -g | grep Mem | awk '{print $2}')
    log "RAM: ${RAM_GB} GB"
    
    if [ "$RAM_GB" -lt 8 ]; then
        log_warn "RAM faible (${RAM_GB} GB). Au moins 8 GB recommandé."
    fi
    
    # GPU
    if check_command nvidia-smi; then
        GPU_NAME=$(nvidia-smi --query-gpu=name --format=csv,noheader)
        GPU_VRAM=$(nvidia-smi --query-gpu=memory.total --format=csv,noheader)
        log "GPU: ${GPU_NAME} (${GPU_VRAM})"
    else
        log_warn "Pas de GPU NVIDIA détecté"
    fi
    
    # Disque
    DISK_FREE=$(df -h "$HYPERION_DIR" | tail -1 | awk '{print $4}')
    log "Espace disque libre: ${DISK_FREE}"
}

# ============================================================================
# Installation Docker
# ============================================================================

install_docker() {
    print_header "🐋 DOCKER"
    
    if check_command docker; then
        log "✅ Docker déjà installé: $(docker --version)"
        
        # Vérifier si actif
        if ! check_service docker; then
            log "Démarrage Docker..."
            sudo systemctl start docker
            sudo systemctl enable docker
        fi
        
        # Vérifier groupe
        if ! groups | grep -q docker; then
            log "Ajout utilisateur au groupe docker..."
            sudo usermod -aG docker $USER
            log_warn "⚠️  Relance le script dans un nouveau terminal (newgrp docker)"
        fi
        
        return 0
    fi
    
    log "Installation Docker..."
    
    # Manjaro/Arch
    if check_command pacman; then
        sudo pacman -S --noconfirm docker docker-compose
    # Debian/Ubuntu
    elif check_command apt; then
        curl -fsSL https://get.docker.com | sh
    else
        log_error "Distribution non supportée pour installation auto Docker"
        return 1
    fi
    
    sudo systemctl start docker
    sudo systemctl enable docker
    sudo usermod -aG docker $USER
    
    log "✅ Docker installé"
    log_warn "⚠️  Relance le script dans un nouveau terminal (newgrp docker)"
}

# ============================================================================
# Installation Qdrant
# ============================================================================

install_qdrant() {
    print_header "🗄️  QDRANT (Vector Store)"
    
    # Vérifier si container existe
    if docker ps -a --format '{{.Names}}' | grep -q "^qdrant$"; then
        log "✅ Container Qdrant existant"
        
        # Si arrêté, démarrer
        if ! docker ps --format '{{.Names}}' | grep -q "^qdrant$"; then
            log "Démarrage Qdrant..."
            docker start qdrant
        else
            log "Qdrant déjà actif"
        fi
        
        return 0
    fi
    
    log "Création container Qdrant..."
    
    # Créer dossier stockage
    mkdir -p "$QDRANT_STORAGE"
    
    # Lancer container
    docker run -d \
        --name qdrant \
        --restart unless-stopped \
        -p 6333:6333 \
        -p 6334:6334 \
        -v "$QDRANT_STORAGE:/qdrant/storage" \
        qdrant/qdrant
    
    # Attendre disponibilité
    log "Attente démarrage Qdrant..."
    for i in {1..30}; do
        if curl -s http://localhost:6333/ >/dev/null 2>&1; then
            log "✅ Qdrant opérationnel"
            log_info "Dashboard: http://localhost:6333/dashboard"
            return 0
        fi
        sleep 1
    done
    
    log_error "Qdrant n'a pas démarré correctement"
    return 1
}

# ============================================================================
# Installation Ollama
# ============================================================================

install_ollama() {
    print_header "🤖 OLLAMA (LLM Local)"
    
    if check_command ollama; then
        log "✅ Ollama déjà installé: $(ollama --version 2>/dev/null || echo 'version inconnue')"
    else
        log "Installation Ollama..."
        curl -fsSL https://ollama.com/install.sh | sh
        log "✅ Ollama installé"
    fi
    
    # Démarrer service
    if ! check_service ollama; then
        log "Démarrage service Ollama..."
        sudo systemctl start ollama 2>/dev/null || {
            log_warn "Service systemd non disponible, lancement manuel"
            ollama serve &>/dev/null &
            sleep 2
        }
    fi
    
    # Proposer modèles
    echo ""
    log_info "Modèles disponibles:"
    echo "  1. qwen2.5:32b  - 19 GB (meilleur, nécessite GPU)"
    echo "  2. qwen2.5:14b  - 8 GB  (bon compromis)"
    echo "  3. qwen2.5:7b   - 4 GB  (rapide, léger)"
    echo "  4. llama3.2     - 2 GB  (très léger)"
    echo "  5. Aucun (skip)"
    echo ""
    
    read -p "Choix (1-5): " model_choice
    
    case $model_choice in
        1)
            MODEL="qwen2.5:32b"
            ;;
        2)
            MODEL="qwen2.5:14b"
            ;;
        3)
            MODEL="qwen2.5:7b"
            ;;
        4)
            MODEL="llama3.2"
            ;;
        *)
            log "Skip téléchargement modèle"
            return 0
            ;;
    esac
    
    # Vérifier si déjà téléchargé
    if ollama list | grep -q "$MODEL"; then
        log "✅ Modèle $MODEL déjà téléchargé"
    else
        log "Téléchargement $MODEL (peut prendre 5-30 min)..."
        ollama pull "$MODEL"
        log "✅ Modèle téléchargé"
    fi
    
    # Mettre à jour .env
    if grep -q "OLLAMA_MODEL=" "$HYPERION_DIR/.env" 2>/dev/null; then
        sed -i "s/OLLAMA_MODEL=.*/OLLAMA_MODEL=$MODEL/" "$HYPERION_DIR/.env"
    else
        echo "OLLAMA_MODEL=$MODEL" >> "$HYPERION_DIR/.env"
    fi
}

# ============================================================================
# Installation Neo4j
# ============================================================================

install_neo4j() {
    print_header "🔷 NEO4J (Graph Database)"
    
    log_info "Neo4j peut être installé via:"
    log_info "  - Docker (recommandé)"
    log_info "  - Neo4j Desktop (GUI)"
    log_info "  - Package natif"
    
    if ! ask_yes_no "Installer Neo4j via Docker ?"; then
        log "Skip Neo4j"
        return 0
    fi
    
    # Vérifier si existe déjà
    if docker ps -a --format '{{.Names}}' | grep -q "^neo4j$"; then
        log "✅ Container Neo4j existant"
        
        if ! docker ps --format '{{.Names}}' | grep -q "^neo4j$"; then
            docker start neo4j
        fi
        
        return 0
    fi
    
    log "Création container Neo4j..."
    
    # Password Neo4j
    read -sp "Mot de passe Neo4j (défaut: hyperion123): " NEO4J_PASSWORD
    echo ""
    NEO4J_PASSWORD=${NEO4J_PASSWORD:-hyperion123}
    
    # Lancer Neo4j
    docker run -d \
        --name neo4j \
        --restart unless-stopped \
        -p 7474:7474 \
        -p 7687:7687 \
        -e NEO4J_AUTH=neo4j/$NEO4J_PASSWORD \
        -v "$HOME/neo4j_data:/data" \
        neo4j:latest
    
    # Mettre à jour .env
    cat >> "$HYPERION_DIR/.env" << EOF

# Neo4j
NEO4J_URI=bolt://localhost:7687
NEO4J_USER=neo4j
NEO4J_PASSWORD=$NEO4J_PASSWORD
NEO4J_DATABASE=neo4j
EOF
    
    log "✅ Neo4j installé"
    log_info "Interface: http://localhost:7474"
}

# ============================================================================
# Installation dépendances Python
# ============================================================================

install_python_deps() {
    print_header "🐍 DÉPENDANCES PYTHON"
    
    cd "$HYPERION_DIR"
    
    # PyTorch avec CUDA
    if python3 -c "import torch; torch.cuda.is_available()" 2>/dev/null; then
        log "✅ PyTorch CUDA déjà installé"
    else
        if check_command nvidia-smi; then
            log "Installation PyTorch avec CUDA..."
            pip install torch torchvision torchaudio \
                --index-url https://download.pytorch.org/whl/cu121 \
                --break-system-packages
        else
            log "Installation PyTorch CPU..."
            pip install torch torchvision torchaudio \
                --index-url https://download.pytorch.org/whl/cpu \
                --break-system-packages
        fi
        log "✅ PyTorch installé"
    fi
    
    # Requirements.txt
    log "Installation requirements.txt..."
    pip install -r requirements.txt --break-system-packages --quiet
    log "✅ Dépendances installées"
}

# ============================================================================
# Ingestion données
# ============================================================================

ingest_data() {
    print_header "📥 INGESTION DONNÉES"
    
    cd "$HYPERION_DIR"
    
    # Lister repos disponibles
    REPOS=($(ls -d data/repositories/*/ 2>/dev/null | xargs -n 1 basename))
    
    if [ ${#REPOS[@]} -eq 0 ]; then
        log_warn "Aucun repo analysé trouvé dans data/repositories/"
        log_info "Lance d'abord: hyperion profile /path/to/repo"
        return 0
    fi
    
    log_info "Repos disponibles: ${REPOS[*]}"
    
    if ask_yes_no "Ingérer tous les repos ?"; then
        log "Ingestion complète..."
        python3 scripts/ingest_rag.py
    else
        echo "Quel repo ingérer ?"
        select repo in "${REPOS[@]}" "Aucun"; do
            if [ "$repo" = "Aucun" ]; then
                return 0
            elif [ -n "$repo" ]; then
                log "Ingestion $repo..."
                python3 scripts/ingest_rag.py --repo "$repo"
                break
            fi
        done
    fi
    
    log "✅ Ingestion terminée"
}

# ============================================================================
# Génération documentation
# ============================================================================

generate_docs() {
    print_header "📝 GÉNÉRATION DOCUMENTATION"
    
    cd "$HYPERION_DIR"
    
    PROFILES=($(ls data/repositories/*/profile.yaml 2>/dev/null))
    
    if [ ${#PROFILES[@]} -eq 0 ]; then
        log_warn "Aucun profil trouvé"
        return 0
    fi
    
    log "Génération documentation pour ${#PROFILES[@]} repos..."
    
    for profile in "${PROFILES[@]}"; do
        REPO_NAME=$(dirname "$profile" | xargs basename)
        log "  → $REPO_NAME"
        python3 -m hyperion.cli.main generate "$profile" >/dev/null 2>&1
    done
    
    log "✅ Documentation générée dans docs/generated/"
}

# ============================================================================
# Menu interactif
# ============================================================================

show_menu() {
    print_header "🚀 HYPERION - DÉPLOIEMENT INTERACTIF"
    
    echo "Que veux-tu installer/configurer ?"
    echo ""
    echo "  1. Tout installer (installation complète)"
    echo "  2. Installation personnalisée (choix modules)"
    echo "  3. Vérifier l'installation existante"
    echo "  4. Lancer les services"
    echo "  5. Quitter"
    echo ""
    
    read -p "Choix (1-5): " choice
    
    case $choice in
        1)
            INSTALL_DOCKER=true
            INSTALL_QDRANT=true
            INSTALL_OLLAMA=true
            INSTALL_NEO4J=true
            INSTALL_PYTHON_DEPS=true
            INGEST_DATA=true
            GENERATE_DOCS=true
            START_SERVICES=true
            ;;
        2)
            ask_yes_no "Installer Docker ?" && INSTALL_DOCKER=true
            ask_yes_no "Installer Qdrant ?" && INSTALL_QDRANT=true
            ask_yes_no "Installer Ollama ?" && INSTALL_OLLAMA=true
            ask_yes_no "Installer Neo4j ?" && INSTALL_NEO4J=true
            ask_yes_no "Installer dépendances Python ?" && INSTALL_PYTHON_DEPS=true
            ask_yes_no "Ingérer les données ?" && INGEST_DATA=true
            ask_yes_no "Générer documentation ?" && GENERATE_DOCS=true
            ask_yes_no "Démarrer services ?" && START_SERVICES=true
            ;;
        3)
            check_installation
            exit 0
            ;;
        4)
            start_services
            exit 0
            ;;
        5)
            log "Au revoir !"
            exit 0
            ;;
        *)
            log_error "Choix invalide"
            exit 1
            ;;
    esac
}

# ============================================================================
# Vérification installation
# ============================================================================

check_installation() {
    print_header "✅ VÉRIFICATION INSTALLATION"
    
    # Docker
    if check_command docker && docker ps &>/dev/null; then
        log "✅ Docker: $(docker --version)"
    else
        log_error "Docker: Non installé ou non accessible"
    fi
    
    # Qdrant
    if curl -s http://localhost:6333/ >/dev/null 2>&1; then
        log "✅ Qdrant: http://localhost:6333"
    else
        log_error "Qdrant: Non actif"
    fi
    
    # Ollama
    if curl -s http://localhost:11434/api/tags >/dev/null 2>&1; then
        MODELS=$(ollama list | tail -n +2 | awk '{print $1}' | tr '\n' ', ')
        log "✅ Ollama: Actif (Modèles: $MODELS)"
    else
        log_error "Ollama: Non actif"
    fi
    
    # Neo4j
    if curl -s http://localhost:7474/ >/dev/null 2>&1; then
        log "✅ Neo4j: http://localhost:7474"
    else
        log_warn "Neo4j: Non actif (optionnel)"
    fi
    
    # Python
    if python3 -c "import hyperion" 2>/dev/null; then
        log "✅ Hyperion Python: Installé"
    else
        log_error "Hyperion Python: Module non trouvé"
    fi
    
    # CUDA
    if python3 -c "import torch; assert torch.cuda.is_available()" 2>/dev/null; then
        GPU=$(python3 -c "import torch; print(torch.cuda.get_device_name(0))")
        log "✅ CUDA: $GPU"
    else
        log_warn "CUDA: Non disponible (CPU uniquement)"
    fi
    
    # Données
    REPOS_COUNT=$(ls -d data/repositories/*/ 2>/dev/null | wc -l)
    log_info "Repos analysés: $REPOS_COUNT"
    
    DOCS_COUNT=$(ls -d docs/generated/*/ 2>/dev/null | wc -l)
    log_info "Docs générées: $DOCS_COUNT"
}

# ============================================================================
# Démarrage services
# ============================================================================

start_services() {
    print_header "🚀 DÉMARRAGE SERVICES"
    
    echo "Services disponibles:"
    echo "  1. Dashboard complet (API + Frontend)"
    echo "  2. API uniquement"
    echo "  3. Test RAG interactif"
    echo "  4. Tous les services"
    echo ""
    
    read -p "Choix (1-4): " choice
    
    cd "$HYPERION_DIR"
    
    case $choice in
        1)
            log "Lancement dashboard..."
            python3 scripts/run_dashboard.py
            ;;
        2)
            log "Lancement API..."
            python3 scripts/run_api.py
            ;;
        3)
            log "Lancement test RAG..."
            python3 scripts/test_rag.py
            ;;
        4)
            log "Lancement dashboard en arrière-plan..."
            nohup python3 scripts/run_dashboard.py &>/dev/null &
            log "✅ Dashboard actif: http://localhost:3000"
            log "✅ API active: http://localhost:8000"
            ;;
    esac
}

# ============================================================================
# Fonction principale
# ============================================================================

main() {
    # Créer log
    mkdir -p "$HYPERION_DIR"
    echo "" > "$INSTALL_LOG"
    
    print_header "🚀 HYPERION - INSTALLATION ULTIME"
    
    # Vérifier système
    check_system
    
    # Menu interactif
    show_menu
    
    # Exécuter installations
    [ "$INSTALL_DOCKER" = true ] && install_docker
    [ "$INSTALL_QDRANT" = true ] && install_qdrant
    [ "$INSTALL_OLLAMA" = true ] && install_ollama
    [ "$INSTALL_NEO4J" = true ] && install_neo4j
    [ "$INSTALL_PYTHON_DEPS" = true ] && install_python_deps
    [ "$INGEST_DATA" = true ] && ingest_data
    [ "$GENERATE_DOCS" = true ] && generate_docs
    
    # Vérification finale
    check_installation
    
    # Résumé
    print_header "🎉 INSTALLATION TERMINÉE"
    
    log "📋 Services actifs:"
    curl -s http://localhost:6333/ >/dev/null 2>&1 && log "  • Qdrant: http://localhost:6333"
    curl -s http://localhost:11434/ >/dev/null 2>&1 && log "  • Ollama: http://localhost:11434"
    curl -s http://localhost:7474/ >/dev/null 2>&1 && log "  • Neo4j: http://localhost:7474"
    
    echo ""
    log "🚀 Prochaines étapes:"
    log "  • Lancer dashboard: ./scripts/setup_hyperion.sh (option 4)"
    log "  • Tester RAG: python3 scripts/test_rag.py"
    log "  • Analyser repo: hyperion profile /path/to/repo"
    
    echo ""
    log_info "Log complet: $INSTALL_LOG"
    
    # Démarrer services si demandé
    [ "$START_SERVICES" = true ] && start_services
}

# ============================================================================
# Exécution
# ============================================================================

main "$@"
