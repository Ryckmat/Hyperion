#!/usr/bin/env bash

# ============================================================================
# UTILITAIRES COMMUNS POUR LES TESTS
# ============================================================================

# Vérifier si un service HTTP est accessible
check_http_service() {
    local url=$1
    local service_name=$2
    local timeout=${3:-5}
    
    if curl -s -f --max-time ${timeout} "${url}" > /dev/null 2>&1; then
        return 0
    else
        return 1
    fi
}

# Attendre qu'un service soit prêt
wait_for_service() {
    local url=$1
    local service_name=$2
    local max_attempts=${3:-30}
    local sleep_time=${4:-2}
    
    local attempt=1
    
    echo "⏳ Attente service ${service_name}..."
    
    while [ ${attempt} -le ${max_attempts} ]; do
        if check_http_service "${url}" "${service_name}" 2; then
            echo "✅ ${service_name} prêt"
            return 0
        fi
        
        echo "   Tentative ${attempt}/${max_attempts}..."
        sleep ${sleep_time}
        attempt=$((attempt + 1))
    done
    
    echo "❌ Timeout: ${service_name} non accessible"
    return 1
}

# Exécuter une requête API et vérifier le status
api_request() {
    local method=$1
    local url=$2
    local data=${3:-""}
    local expected_status=${4:-200}
    
    local response_file=$(mktemp)
    local status_code
    
    if [ -n "${data}" ]; then
        status_code=$(curl -s -w "%{http_code}" -X ${method} \
            -H "Content-Type: application/json" \
            -d "${data}" \
            "${url}" -o "${response_file}" 2>/dev/null)
    else
        status_code=$(curl -s -w "%{http_code}" -X ${method} \
            "${url}" -o "${response_file}" 2>/dev/null)
    fi
    
    if [ "${status_code}" -eq "${expected_status}" ]; then
        cat "${response_file}"
        rm -f "${response_file}"
        return 0
    else
        echo "❌ Status attendu: ${expected_status}, obtenu: ${status_code}" >&2
        cat "${response_file}" >&2
        rm -f "${response_file}"
        return 1
    fi
}

# Mesurer le temps d'exécution
measure_time() {
    local start_time=$(date +%s%N)
    "$@"
    local exit_code=$?
    local end_time=$(date +%s%N)
    local duration=$(( (end_time - start_time) / 1000000 ))
    echo "${duration}" # millisecondes
    return ${exit_code}
}

# Extraire une valeur JSON
json_extract() {
    local json=$1
    local key=$2
    echo "${json}" | python3 -c "import sys, json; print(json.load(sys.stdin).get('${key}', ''))" 2>/dev/null || echo ""
}

# Créer un timestamp
timestamp() {
    date +"%Y-%m-%d %H:%M:%S"
}

# Logger avec timestamp
log() {
    echo "[$(timestamp)] $*"
}
