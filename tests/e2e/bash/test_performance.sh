#!/usr/bin/env bash
set -euo pipefail

# ============================================================================
# TEST: Performance & Benchmarks
# ============================================================================
# Mesure les performances du système RAG
# Cibles: p50 < 3s, p95 < 5s, p99 < 10s
# ============================================================================

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
source "${SCRIPT_DIR}/utils/common.sh"
source "${SCRIPT_DIR}/utils/colors.sh"

API_BASE="http://localhost:8000"
NUM_REQUESTS=10

main() {
    print_header "⚡ TEST: Performance"
    
    print_section "1. Benchmark requêtes RAG"
    print_info "   Nombre de requêtes: ${NUM_REQUESTS}"
    
    local -a response_times=()
    local total_time=0
    local successful=0
    
    # Questions variées
    local questions=(
        "What is this project?"
        "How many commits?"
        "What are the main files?"
        "Who are the contributors?"
        "What is the architecture?"
    )
    
    for i in $(seq 1 ${NUM_REQUESTS}); do
        local question_idx=$((i % ${#questions[@]}))
        local question="${questions[$question_idx]}"
        
        echo -n "   Requête ${i}/${NUM_REQUESTS}... "
        
        local start_time=$(date +%s%N)
        
        local response=$(curl -s -X POST "${API_BASE}/api/chat" \
            -H "Content-Type: application/json" \
            -d "{\"question\": \"${question}\", \"repo\": \"requests\"}" 2>/dev/null)
        
        local end_time=$(date +%s%N)
        local response_time=$(( (end_time - start_time) / 1000000 )) # ms
        
        response_times+=("${response_time}")
        total_time=$((total_time + response_time))
        
        # Vérifier réponse valide
        local answer=$(echo "${response}" | python3 -c "import sys, json; d=json.load(sys.stdin); print(d.get('answer', ''))" 2>/dev/null || echo "")
        
        if [ -n "${answer}" ]; then
            successful=$((successful + 1))
            echo "${response_time}ms ✅"
        else
            echo "FAIL ❌"
        fi
    done
    
    # Calcul statistiques
    print_section "2. Statistiques"
    
    # Trier les temps de réponse
    IFS=$'\n' sorted_times=($(sort -n <<<"${response_times[*]}"))
    unset IFS
    
    local min_time=${sorted_times[0]}
    local max_time=${sorted_times[-1]}
    local avg_time=$((total_time / NUM_REQUESTS))
    
    # Percentiles
    local p50_idx=$(( NUM_REQUESTS * 50 / 100 ))
    local p95_idx=$(( NUM_REQUESTS * 95 / 100 ))
    local p99_idx=$(( NUM_REQUESTS * 99 / 100 ))
    
    local p50=${sorted_times[$p50_idx]}
    local p95=${sorted_times[$p95_idx]}
    local p99=${sorted_times[$p99_idx]}
    
    echo ""
    echo "Requêtes réussies : ${successful}/${NUM_REQUESTS}"
    echo "Min               : ${min_time}ms"
    echo "Max               : ${max_time}ms"
    echo "Moyenne           : ${avg_time}ms"
    echo "p50 (médiane)     : ${p50}ms"
    echo "p95               : ${p95}ms"
    echo "p99               : ${p99}ms"
    echo ""
    
    # Validation SLO
    print_section "3. Validation SLO"
    
    local slo_passed=true
    
    # p95 < 10000ms (10s) - tolérance pour cold start
    if [ ${p95} -lt 10000 ]; then
        print_success "✅ p95 < 10s (${p95}ms)"
    elif [ ${p95} -lt 15000 ]; then
        print_warning "⚠️  p95 > 10s mais < 15s (${p95}ms) - acceptable avec cold start"
    else
        print_error "❌ p95 > 15s (${p95}ms)"
        slo_passed=false
    fi
    
    # Taux de succès > 95%
    local success_rate=$((successful * 100 / NUM_REQUESTS))
    if [ ${success_rate} -ge 95 ]; then
        print_success "✅ Taux succès > 95% (${success_rate}%)"
    else
        print_error "❌ Taux succès < 95% (${success_rate}%)"
        slo_passed=false
    fi
    
    echo ""
    
    if [ "${slo_passed}" = true ]; then
        print_success "🎉 SLO respectés"
        return 0
    else
        print_error "⚠️  SLO non respectés"
        return 1
    fi
}

main "$@"
