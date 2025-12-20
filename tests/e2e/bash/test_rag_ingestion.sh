#!/usr/bin/env bash
set -euo pipefail

# ============================================================================
# TEST: Ingestion RAG
# ============================================================================
# Valide l'ingestion complète Git → Chunks → Embeddings → Qdrant
# ============================================================================

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
source "${SCRIPT_DIR}/utils/common.sh"
source "${SCRIPT_DIR}/utils/colors.sh"

API_BASE="http://localhost:8000"
QDRANT_URL="http://localhost:6333"
TEST_REPO="https://github.com/psf/requests.git"
COLLECTION_NAME="hyperion"

main() {
    print_header "📥 TEST: Ingestion RAG"
    
    # Vérifier pré-requis
    print_section "1. Vérification pré-requis"
    
    if ! check_http_service "${API_BASE}/api/health" "API"; then
        print_error "❌ API non disponible"
        return 1
    fi
    
    if ! check_http_service "${QDRANT_URL}" "Qdrant"; then
        print_error "❌ Qdrant non disponible"
        return 1
    fi
    
    print_success "✅ Services prêts"
    
    # Stats avant ingestion
    print_section "2. État initial Qdrant"
    
    local initial_count=$(curl -s "${QDRANT_URL}/collections/${COLLECTION_NAME}" 2>/dev/null | \
        python3 -c "import sys, json; print(json.load(sys.stdin).get('result', {}).get('points_count', 0))" 2>/dev/null || echo "0")
    
    print_info "   Points avant: ${initial_count}"
    
    # Lancer ingestion
    print_section "3. Lancement ingestion"
    print_info "   Repo: ${TEST_REPO}"
    
    local start_time=$(date +%s)
    
    local response=$(api_request POST "${API_BASE}/api/ingest" \
        "{\"repo_url\": \"${TEST_REPO}\", \"force\": false}" \
        200 2>/dev/null) || {
        print_error "❌ Échec ingestion"
        return 1
    }
    
    local end_time=$(date +%s)
    local duration=$((end_time - start_time))
    
    print_success "✅ Ingestion terminée en ${duration}s"
    
    # Stats après ingestion
    print_section "4. Vérification résultats"
    
    sleep 2 # Laisser Qdrant se stabiliser
    
    local final_count=$(curl -s "${QDRANT_URL}/collections/${COLLECTION_NAME}" 2>/dev/null | \
        python3 -c "import sys, json; print(json.load(sys.stdin).get('result', {}).get('points_count', 0))" 2>/dev/null || echo "0")
    
    local added_points=$((final_count - initial_count))
    
    print_info "   Points après: ${final_count}"
    print_info "   Points ajoutés: ${added_points}"
    
    # Validation
    if [ ${final_count} -gt 0 ]; then
        print_success "✅ Ingestion réussie: ${final_count} chunks totaux"
        return 0
    else
        print_error "❌ Aucun chunk dans Qdrant"
        return 1
    fi
}

main "$@"
