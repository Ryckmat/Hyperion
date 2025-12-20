#!/usr/bin/env bash
set -euo pipefail

# ============================================================================
# HYPERION - Tests End-to-End Complets
# ============================================================================
# Orchestrateur principal des tests E2E
# Valide le flux complet : Services → Ingestion → RAG → OpenWebUI
# ============================================================================

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
source "${SCRIPT_DIR}/utils/common.sh"
source "${SCRIPT_DIR}/utils/colors.sh"

# Configuration
API_BASE="http://localhost:8000"
QDRANT_URL="http://localhost:6333"
NEO4J_URL="http://localhost:7474"
OLLAMA_URL="http://localhost:11434"
OPENWEBUI_URL="http://localhost:3000"
DASHBOARD_URL="http://localhost:3000"

# ============================================================================
# FONCTIONS DE TEST
# ============================================================================

run_test_suite() {
    local test_name=$1
    local test_script=$2
    
    print_section "Test: ${test_name}"
    
    if bash "${SCRIPT_DIR}/${test_script}"; then
        print_success "✅ ${test_name} - PASSED"
        return 0
    else
        print_error "❌ ${test_name} - FAILED"
        return 1
    fi
}

# ============================================================================
# TESTS E2E
# ============================================================================

main() {
    print_header "🧪 HYPERION - Tests End-to-End"
    
    local total_tests=0
    local passed_tests=0
    local failed_tests=0
    
    # Test 1: Santé des services
    total_tests=$((total_tests + 1))
    if run_test_suite "Santé Services" "test_services_health.sh"; then
        passed_tests=$((passed_tests + 1))
    else
        failed_tests=$((failed_tests + 1))
        print_warning "⚠️  Services non opérationnels - tests suivants risquent d'échouer"
    fi
    
    # Test 2: Ingestion RAG
    total_tests=$((total_tests + 1))
    if run_test_suite "Ingestion RAG" "test_rag_ingestion.sh"; then
        passed_tests=$((passed_tests + 1))
    else
        failed_tests=$((failed_tests + 1))
    fi
    
    # Test 3: Requêtes RAG
    total_tests=$((total_tests + 1))
    if run_test_suite "Requêtes RAG" "test_rag_query.sh"; then
        passed_tests=$((passed_tests + 1))
    else
        failed_tests=$((failed_tests + 1))
    fi
    
    # Test 4: Ingestion Neo4j
    total_tests=$((total_tests + 1))
    if run_test_suite "Ingestion Neo4j" "test_neo4j_ingestion.sh"; then
        passed_tests=$((passed_tests + 1))
    else
        failed_tests=$((failed_tests + 1))
    fi
    
    # Test 5: Function OpenWebUI
    total_tests=$((total_tests + 1))
    if run_test_suite "OpenWebUI Function" "test_openwebui_function.sh"; then
        passed_tests=$((passed_tests + 1))
    else
        failed_tests=$((failed_tests + 1))
    fi
    
    # Test 6: Performance
    total_tests=$((total_tests + 1))
    if run_test_suite "Performance" "test_performance.sh"; then
        passed_tests=$((passed_tests + 1))
    else
        failed_tests=$((failed_tests + 1))
    fi
    
    # ============================================================================
    # RAPPORT FINAL
    # ============================================================================
    
    echo ""
    print_header "📊 RÉSULTATS TESTS E2E"
    echo ""
    echo "Total tests    : ${total_tests}"
    echo "✅ Réussis     : ${passed_tests}"
    echo "❌ Échoués     : ${failed_tests}"
    echo ""
    
    if [ ${failed_tests} -eq 0 ]; then
        print_success "🎉 TOUS LES TESTS SONT PASSÉS !"
        return 0
    else
        print_error "⚠️  ${failed_tests} test(s) échoué(s)"
        return 1
    fi
}

main "$@"
