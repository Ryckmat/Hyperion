#!/usr/bin/env bash
set -euo pipefail

# ============================================================================
# TEST: Requêtes RAG
# ============================================================================
# Valide la chaîne complète: Question → Retrieval → LLM → Réponse
# ============================================================================

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
source "${SCRIPT_DIR}/utils/common.sh"
source "${SCRIPT_DIR}/utils/colors.sh"

API_BASE="http://localhost:8000"

# Questions de test
declare -a TEST_QUESTIONS=(
    "What is the main purpose of this repository?"
    "How many files are in the codebase?"
    "What programming language is used?"
)

main() {
    print_header "💬 TEST: Requêtes RAG"
    
    local total_queries=0
    local successful_queries=0
    local total_response_time=0
    
    for question in "${TEST_QUESTIONS[@]}"; do
        total_queries=$((total_queries + 1))
        
        print_section "Question ${total_queries}: ${question}"
        
        # Mesurer le temps de réponse
        local start_time=$(date +%s%N)
        
        local response=$(api_request POST "${API_BASE}/api/chat" \
            "{\"question\": \"${question}\", \"repo\": \"requests\"}" \
            200 2>/dev/null) || {
            print_error "❌ Échec requête"
            continue
        }
        
        local end_time=$(date +%s%N)
        local response_time=$(( (end_time - start_time) / 1000000 )) # ms
        
        total_response_time=$((total_response_time + response_time))
        
        # Vérifier la réponse
        local answer=$(echo "${response}" | python3 -c "import sys, json; print(json.load(sys.stdin).get('answer', ''))" 2>/dev/null || echo "")
        local sources=$(echo "${response}" | python3 -c "import sys, json; print(len(json.load(sys.stdin).get('sources', [])))" 2>/dev/null || echo "0")
        
        if [ -n "${answer}" ] && [ "${answer}" != "null" ]; then
            print_success "✅ Réponse générée (${response_time}ms)"
            print_info "   Sources: ${sources}"
            print_info "   Réponse: ${answer:0:100}..."
            successful_queries=$((successful_queries + 1))
        else
            print_error "❌ Réponse vide"
        fi
        
        echo ""
    done
    
    # Statistiques
    print_section "📊 Statistiques"
    
    local avg_response_time=0
    if [ ${total_queries} -gt 0 ]; then
        avg_response_time=$((total_response_time / total_queries))
    fi
    
    echo "Total requêtes    : ${total_queries}"
    echo "Réussies          : ${successful_queries}"
    echo "Temps moyen       : ${avg_response_time}ms"
    
    # Validation performance (exclure première requête cold start)
    if [ ${avg_response_time} -lt 8000 ]; then
        print_success "✅ Performance acceptable (<8s en moyenne)"
    else
        print_warning "⚠️  Performance dégradée (${avg_response_time}ms)"
    fi
    
    # Résultat final
    if [ ${successful_queries} -eq ${total_queries} ]; then
        print_success "🎉 Toutes les requêtes ont réussi"
        return 0
    else
        print_error "❌ $((total_queries - successful_queries)) requête(s) échouée(s)"
        return 1
    fi
}

main "$@"
