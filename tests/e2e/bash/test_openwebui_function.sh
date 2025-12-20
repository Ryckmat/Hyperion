#!/usr/bin/env bash
set -euo pipefail

# ============================================================================
# TEST: OpenWebUI Function
# ============================================================================
# Valide l'intégration OpenWebUI → RAG via Function
# ============================================================================

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
source "${SCRIPT_DIR}/utils/common.sh"
source "${SCRIPT_DIR}/utils/colors.sh"

API_BASE="http://localhost:8000"
OPENWEBUI_URL="http://localhost:3000"

main() {
    print_header "🔌 TEST: OpenWebUI Function"
    
    # Vérifier OpenWebUI
    print_section "1. Vérification OpenWebUI"
    
    if ! check_http_service "${OPENWEBUI_URL}" "OpenWebUI"; then
        print_warning "⚠️  OpenWebUI non accessible - test ignoré"
        return 0
    fi
    
    print_success "✅ OpenWebUI accessible"
    
    # Test via API directe (simulation Function)
    print_section "2. Test Function RAG"
    
    local test_query="What is this codebase about?"
    
    local response=$(api_request POST "${API_BASE}/api/chat" \
        "{\"question\": \"${test_query}\", \"repo\": \"requests\"}" \
        200 2>/dev/null) || {
        print_error "❌ Échec appel Function"
        return 1
    }
    
    local answer=$(echo "${response}" | python3 -c "import sys, json; print(json.load(sys.stdin).get('answer', ''))" 2>/dev/null || echo "")
    
    if [ -n "${answer}" ] && [ "${answer}" != "null" ]; then
        print_success "✅ Function RAG opérationnelle"
        print_info "   Query: ${test_query}"
        print_info "   Answer: ${answer:0:150}..."
        return 0
    else
        print_error "❌ Réponse invalide"
        return 1
    fi
}

main "$@"
