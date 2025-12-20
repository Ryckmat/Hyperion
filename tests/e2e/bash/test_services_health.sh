#!/usr/bin/env bash
set -euo pipefail

# ============================================================================
# TEST: Santé des Services
# ============================================================================
# Vérifie que tous les services Hyperion sont opérationnels
# ============================================================================

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
source "${SCRIPT_DIR}/utils/common.sh"
source "${SCRIPT_DIR}/utils/colors.sh"

# URLs des services
API_BASE="http://localhost:8000"
QDRANT_URL="http://localhost:6333"
NEO4J_URL="http://localhost:7474"
OLLAMA_URL="http://localhost:11434"
OPENWEBUI_URL="http://localhost:3000"

main() {
    print_header "🏥 TEST: Santé Services"
    
    local all_healthy=true
    
    # Test 1: API FastAPI
    print_section "1. API FastAPI"
    if check_http_service "${API_BASE}/api/health" "API"; then
        print_success "✅ API FastAPI opérationnelle"
    else
        print_error "❌ API FastAPI inaccessible"
        all_healthy=false
    fi
    
    # Test 2: Qdrant
    print_section "2. Qdrant Vector DB"
    if check_http_service "${QDRANT_URL}" "Qdrant"; then
        print_success "✅ Qdrant opérationnel"
        
        # Vérifier les collections
        local collections=$(curl -s "${QDRANT_URL}/collections" | python3 -c "import sys, json; print(len(json.load(sys.stdin).get('result', {}).get('collections', [])))" 2>/dev/null || echo "0")
        print_info "   Collections: ${collections}"
    else
        print_error "❌ Qdrant inaccessible"
        all_healthy=false
    fi
    
    # Test 3: Ollama
    print_section "3. Ollama LLM"
    if check_http_service "${OLLAMA_URL}" "Ollama"; then
        print_success "✅ Ollama opérationnel"
        
        # Liste des modèles
        local models=$(curl -s "${OLLAMA_URL}/api/tags" | python3 -c "import sys, json; print(len(json.load(sys.stdin).get('models', [])))" 2>/dev/null || echo "0")
        print_info "   Modèles disponibles: ${models}"
    else
        print_error "❌ Ollama inaccessible"
        all_healthy=false
    fi
    
    # Test 4: Neo4j (optionnel)
    print_section "4. Neo4j Graph DB (optionnel)"
    if check_http_service "${NEO4J_URL}" "Neo4j"; then
        print_success "✅ Neo4j opérationnel"
    else
        print_warning "⚠️  Neo4j non actif (optionnel)"
    fi
    
    # Test 5: OpenWebUI
    print_section "5. OpenWebUI"
    if check_http_service "${OPENWEBUI_URL}" "OpenWebUI"; then
        print_success "✅ OpenWebUI opérationnel"
    else
        print_warning "⚠️  OpenWebUI inaccessible"
    fi
    
    # Résumé
    echo ""
    if [ "${all_healthy}" = true ]; then
        print_success "🎉 Tous les services critiques sont opérationnels"
        return 0
    else
        print_error "❌ Certains services critiques sont indisponibles"
        return 1
    fi
}

main "$@"
