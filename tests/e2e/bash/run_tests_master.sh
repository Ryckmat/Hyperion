#!/usr/bin/env bash
set -euo pipefail

# ============================================================================
# HYPERION - Script Master Tests E2E
# ============================================================================
# Prépare l'environnement et lance les tests end-to-end
# ============================================================================

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
HYPERION_ROOT="$(cd "${SCRIPT_DIR}/../../.." && pwd)"

source "${SCRIPT_DIR}/utils/common.sh"
source "${SCRIPT_DIR}/utils/colors.sh"

# Configuration
API_BASE="http://localhost:8000"
QDRANT_URL="http://localhost:6333"
OLLAMA_URL="http://localhost:11434"
TEST_REPO="https://github.com/psf/requests.git"

# Variable pour tracker si on a lancé l'API
API_STARTED_BY_US=false

# ============================================================================
# FONCTIONS
# ============================================================================

check_services_running() {
    print_section "Vérification des services"
    
    local all_running=true
    
    # Qdrant
    if check_http_service "${QDRANT_URL}" "Qdrant" 2; then
        print_success "✅ Qdrant opérationnel"
    else
        print_error "❌ Qdrant non accessible"
        print_info "   Lancer avec: docker run -d -p 6333:6333 qdrant/qdrant"
        all_running=false
    fi
    
    # Ollama
    if check_http_service "${OLLAMA_URL}" "Ollama" 2; then
        print_success "✅ Ollama opérationnel"
    else
        print_error "❌ Ollama non accessible"
        print_info "   Lancer avec: systemctl start ollama"
        all_running=false
    fi
    
    # API (optionnel au départ)
    if check_http_service "${API_BASE}/api/health" "API" 2; then
        print_success "✅ API déjà lancée"
    else
        print_warning "⚠️  API non lancée (sera démarrée)"
    fi
    
    if [ "${all_running}" = false ]; then
        print_error "❌ Certains services critiques manquent"
        return 1
    fi
    
    return 0
}

start_api() {
    print_section "Démarrage API Hyperion"
    
    # Vérifier si déjà lancée
    if check_http_service "${API_BASE}/api/health" "API" 2; then
        print_success "✅ API déjà opérationnelle"
        # Détecter le PID si possible
        local api_pid=$(lsof -ti:8000 2>/dev/null | head -1)
        if [ -n "${api_pid}" ]; then
            print_info "   PID: ${api_pid}"
            print_info "   (API non gérée par ce script)"
        fi
        API_STARTED_BY_US=false
        return 0
    fi
    
    # Vérifier venv
    if [ ! -d "${HYPERION_ROOT}/venv" ]; then
        print_error "❌ Virtual environment non trouvé à ${HYPERION_ROOT}/venv"
        print_info "   Créer avec: python -m venv venv && source venv/bin/activate.fish"
        return 1
    fi
    
    print_info "Lancement API en arrière-plan..."
    
    # Lancer API
    cd "${HYPERION_ROOT}"
    
    # Tuer processus existant sur port 8000
    lsof -ti:8000 | xargs kill -9 2>/dev/null || true
    sleep 2
    
    # Lancer API
    (
        source venv/bin/activate
        nohup python -m uvicorn hyperion.api.main:app --host 0.0.0.0 --port 8000 > /tmp/hyperion_api.log 2>&1 &
        echo $! > /tmp/hyperion_api.pid
    )
    
    # Attendre que l'API soit prête
    print_info "Attente démarrage API..."
    if wait_for_service "${API_BASE}/api/health" "API" 30 2; then
        print_success "✅ API démarrée avec succès"
        print_info "   PID: $(cat /tmp/hyperion_api.pid 2>/dev/null || echo 'unknown')"
        print_info "   Logs: /tmp/hyperion_api.log"
        API_STARTED_BY_US=true
        return 0
    else
        print_error "❌ Échec démarrage API"
        print_info "   Voir logs: tail -f /tmp/hyperion_api.log"
        return 1
    fi
}

ensure_test_data() {
    print_section "Vérification données test"
    
    # Vérifier si collection existe et a des données
    local points_count=$(curl -s "${QDRANT_URL}/collections/hyperion" 2>/dev/null | \
        python3 -c "import sys, json; print(json.load(sys.stdin).get('result', {}).get('points_count', 0))" 2>/dev/null || echo "0")
    
    print_info "Points dans Qdrant: ${points_count}"
    
    if [ "${points_count}" -gt 100 ]; then
        print_success "✅ Données test présentes (${points_count} points)"
        return 0
    fi
    
    print_warning "⚠️  Peu de données test - ingestion recommandée"
    
    read -p "Ingérer le repo test (${TEST_REPO}) ? [o/N] " -n 1 -r
    echo
    
    if [[ $REPLY =~ ^[Oo]$ ]]; then
        print_info "Lancement ingestion..."
        
        local response=$(curl -s -X POST "${API_BASE}/api/ingest" \
            -H "Content-Type: application/json" \
            -d "{\"repo_url\": \"${TEST_REPO}\", \"force\": false}")
        
        print_success "✅ Ingestion lancée"
        print_info "Attente fin ingestion (30s)..."
        sleep 30
        
        # Vérifier résultat
        local new_count=$(curl -s "${QDRANT_URL}/collections/hyperion" 2>/dev/null | \
            python3 -c "import sys, json; print(json.load(sys.stdin).get('result', {}).get('points_count', 0))" 2>/dev/null || echo "0")
        
        print_info "Points après ingestion: ${new_count}"
    else
        print_warning "⚠️  Tests RAG risquent d'échouer sans données"
    fi
}

run_tests() {
    print_section "Lancement tests E2E"
    
    cd "${SCRIPT_DIR}"
    ./test_e2e_complete.sh
    
    return $?
}

cleanup() {
    print_section "Nettoyage"
    
    # Ne proposer d'arrêter que si on a lancé l'API nous-même
    if [ "${API_STARTED_BY_US}" = true ]; then
        read -p "Arrêter l'API lancée par ce script ? [o/N] " -n 1 -r
        echo
        
        if [[ $REPLY =~ ^[Oo]$ ]]; then
            if [ -f /tmp/hyperion_api.pid ]; then
                local pid=$(cat /tmp/hyperion_api.pid)
                print_info "Arrêt API (PID: ${pid})..."
                kill "${pid}" 2>/dev/null || true
                rm -f /tmp/hyperion_api.pid
                print_success "✅ API arrêtée"
            fi
        fi
    else
        print_info "API non gérée par ce script - conservée en l'état"
    fi
}

# ============================================================================
# MAIN
# ============================================================================

main() {
    print_header "🚀 HYPERION - Master Tests E2E"
    
    echo ""
    print_info "Répertoire Hyperion: ${HYPERION_ROOT}"
    echo ""
    
    # 1. Vérifier services
    if ! check_services_running; then
        print_error "❌ Impossible de continuer sans services critiques"
        exit 1
    fi
    
    # 2. Démarrer API (ou détecter existante)
    if ! start_api; then
        print_error "❌ Impossible de continuer sans API"
        exit 1
    fi
    
    # 3. Vérifier données test
    ensure_test_data
    
    echo ""
    print_info "Prêt à lancer les tests E2E"
    read -p "Continuer ? [O/n] " -n 1 -r
    echo
    
    if [[ ! $REPLY =~ ^[Nn]$ ]]; then
        # 4. Lancer tests
        if run_tests; then
            print_success "🎉 Tests terminés avec succès"
        else
            print_error "⚠️  Certains tests ont échoué"
        fi
    fi
    
    # 5. Nettoyage
    cleanup
    
    echo ""
    print_success "✅ Terminé"
}

# Trap pour cleanup en cas d'interruption
trap cleanup EXIT INT TERM

main "$@"
