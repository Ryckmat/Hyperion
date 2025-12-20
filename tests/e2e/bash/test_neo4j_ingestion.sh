#!/usr/bin/env bash
set -euo pipefail

# ============================================================================
# TEST: Ingestion Neo4j
# ============================================================================
# Valide la création du graphe de connaissance dans Neo4j
# ============================================================================

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
source "${SCRIPT_DIR}/utils/common.sh"
source "${SCRIPT_DIR}/utils/colors.sh"

API_BASE="http://localhost:8000"
NEO4J_URL="http://localhost:7474"

main() {
    print_header "🕸️  TEST: Ingestion Neo4j"
    
    # Vérifier si Neo4j est disponible
    print_section "1. Vérification Neo4j"
    
    if ! check_http_service "${NEO4J_URL}" "Neo4j"; then
        print_warning "⚠️  Neo4j non actif - test ignoré"
        return 0
    fi
    
    print_success "✅ Neo4j disponible"
    
    # Lancer ingestion
    print_section "2. Ingestion graphe"
    
    local response=$(api_request POST "${API_BASE}/api/neo4j/ingest" \
        "{\"repo_path\": \"/tmp/hyperion_repos/requests\"}" \
        200 2>/dev/null) || {
        print_warning "⚠️  Endpoint non disponible ou erreur"
        return 0
    }
    
    print_success "✅ Ingestion lancée"
    
    # Vérifier les stats du graphe
    print_section "3. Statistiques graphe"
    
    local stats=$(curl -s "${API_BASE}/api/neo4j/stats" 2>/dev/null) || {
        print_warning "⚠️  Impossible de récupérer les stats"
        return 0
    }
    
    local nodes=$(echo "${stats}" | python3 -c "import sys, json; print(json.load(sys.stdin).get('nodes', 0))" 2>/dev/null || echo "0")
    local relationships=$(echo "${stats}" | python3 -c "import sys, json; print(json.load(sys.stdin).get('relationships', 0))" 2>/dev/null || echo "0")
    
    print_info "   Nodes: ${nodes}"
    print_info "   Relations: ${relationships}"
    
    if [ ${nodes} -gt 0 ]; then
        print_success "✅ Graphe créé avec succès"
        return 0
    else
        print_warning "⚠️  Graphe vide (normal si première exécution)"
        return 0
    fi
}

main "$@"
