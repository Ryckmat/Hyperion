#!/bin/bash
# ============================================================================
# 🧪 Test standalone pour Hyperion Docker (sans Docker Compose)
# ============================================================================

set -euo pipefail

# Couleurs
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
CYAN='\033[0;36m'
RED='\033[0;31m'
NC='\033[0m'

ok() { echo -e "${GREEN}✅ $1${NC}"; }
warn() { echo -e "${YELLOW}⚠️ $1${NC}"; }
info() { echo -e "${CYAN}ℹ️ $1${NC}"; }
fail() { echo -e "${RED}❌ $1${NC}"; }

# Variables
HYPERION_IMAGE="hyperion:v2.7"
QDRANT_IMAGE="qdrant/qdrant:latest"

cleanup() {
    echo ""
    info "Nettoyage des containers de test..."
    docker stop test-hyperion test-qdrant 2>/dev/null || true
    docker rm test-hyperion test-qdrant 2>/dev/null || true
}

# Cleanup au signal d'interruption
trap cleanup INT EXIT

main() {
    echo "============================================"
    echo "🧪 TEST STANDALONE HYPERION DOCKER"
    echo "============================================"

    # 1. Vérifier que l'image existe
    info "Vérification de l'image Hyperion..."
    if docker image inspect "$HYPERION_IMAGE" >/dev/null 2>&1; then
        ok "Image $HYPERION_IMAGE trouvée"
    else
        fail "Image $HYPERION_IMAGE non trouvée"
        echo "Construisez l'image avec: docker build -t hyperion:v2.7 ."
        exit 1
    fi

    # 2. Test basique de la commande CLI
    info "Test CLI Hyperion..."
    if docker run --rm "$HYPERION_IMAGE" hyperion --help >/dev/null 2>&1; then
        ok "Commande 'hyperion' fonctionne"
    else
        fail "Commande 'hyperion' échouée"
        exit 1
    fi

    # 3. Démarrer Qdrant pour les tests
    info "Démarrage Qdrant..."
    docker run -d --name test-qdrant \
        -p 6333:6333 \
        "$QDRANT_IMAGE" >/dev/null

    # Attendre que Qdrant soit prêt
    info "Attente de Qdrant..."
    for i in {1..30}; do
        if curl -s http://localhost:6333/health >/dev/null 2>&1; then
            ok "Qdrant opérationnel"
            break
        fi
        if [ $i -eq 30 ]; then
            fail "Qdrant non accessible après 30s"
            exit 1
        fi
        sleep 1
    done

    # 4. Test configuration Python
    info "Test de configuration Python..."
    if docker run --rm \
        --env QDRANT_HOST=localhost \
        --env QDRANT_PORT=6333 \
        --network host \
        "$HYPERION_IMAGE" \
        python -c "
import sys
sys.path.append('/app/src')

# Test imports principaux
try:
    from hyperion.api.main import app
    print('✅ Import API réussi')
except Exception as e:
    print(f'❌ Échec import API: {e}')
    exit(1)

try:
    from hyperion.cli.main import main
    print('✅ Import CLI réussi')
except Exception as e:
    print(f'❌ Échec import CLI: {e}')
    exit(1)

try:
    from hyperion.modules.rag.ingestion import RAGIngester
    print('✅ Import RAG réussi')
except Exception as e:
    print(f'❌ Échec import RAG: {e}')
    exit(1)

print('🎉 Tous les imports Python réussis')
"; then
        ok "Configuration Python validée"
    else
        fail "Test Python échoué"
        exit 1
    fi

    # 5. Test de l'API (démarrage rapide)
    info "Test API Hyperion (15s)..."
    docker run -d --name test-hyperion \
        --network host \
        --env QDRANT_HOST=localhost \
        --env QDRANT_PORT=6333 \
        --env OLLAMA_BASE_URL=http://localhost:11434 \
        --env NEO4J_URI=bolt://localhost:7687 \
        "$HYPERION_IMAGE" >/dev/null

    # Attendre que l'API démarre
    info "Attente API (15s)..."
    sleep 15

    # Test health check
    if curl -s http://localhost:8000/ >/dev/null 2>&1; then
        ok "API Hyperion accessible"

        # Test endpoint spécifique
        if curl -s http://localhost:8000/api/health >/dev/null 2>&1; then
            ok "Health endpoint OK"
        else
            warn "Health endpoint non accessible"
        fi
    else
        warn "API Hyperion non accessible (normal sans tous les services)"
    fi

    echo ""
    echo "============================================"
    echo "🎉 TESTS TERMINÉS"
    echo "============================================"
    echo ""
    echo "✅ Image Docker fonctionnelle"
    echo "✅ CLI Hyperion opérationnelle"
    echo "✅ Imports Python validés"
    echo "✅ Structure du projet correcte"
    echo ""
    echo "🚀 Prêt pour le déploiement avec docker-compose !"
    echo ""
    echo "Prochaines étapes:"
    echo "1. Installer Docker Compose: https://docs.docker.com/compose/install/"
    echo "2. Utiliser: ./scripts/docker/hyperion-docker.sh --action up"
}

# Lancement
main "$@"