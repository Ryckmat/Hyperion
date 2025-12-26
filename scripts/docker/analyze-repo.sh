#!/bin/bash
# ============================================================================
# 🔍 Script d'analyse de repository avec Hyperion Docker
# ============================================================================

set -euo pipefail

# Configuration
SCRIPT_DIR="$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")" &>/dev/null && pwd)"
PROJECT_ROOT="$(dirname "$(dirname "$SCRIPT_DIR")")"

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

# Aide
show_help() {
  cat << 'EOF'
🔍 Analyse de repository avec Hyperion Docker

USAGE:
  ./scripts/docker/analyze-repo.sh REPO_PATH [OPTIONS]

ARGUMENTS:
  REPO_PATH              Chemin vers le repository à analyser

OPTIONS:
  --modules MODULE_LIST  Modules à exécuter (v1,v2,rag ou all) - défaut: all
  --skip-start          Ne pas démarrer les services (supposer qu'ils tournent)
  --help                Afficher cette aide

EXEMPLES:
  ./scripts/docker/analyze-repo.sh /home/user/mon-projet
  ./scripts/docker/analyze-repo.sh /home/user/requests --modules v2,rag
  ./scripts/docker/analyze-repo.sh . --skip-start

ÉTAPES:
  1. Vérification du repository
  2. Démarrage des services Hyperion (si nécessaire)
  3. Génération du profil Git (module v1)
  4. Analyse du code source (module v2)
  5. Génération des embeddings RAG (module rag)
  6. Tests de validation

EOF
}

# Variables
REPO_PATH=""
MODULES="all"
SKIP_START=false

# Parsing arguments
parse_args() {
  if [ $# -eq 0 ]; then
    show_help
    exit 1
  fi

  REPO_PATH="$1"
  shift

  while [[ $# -gt 0 ]]; do
    case $1 in
      --modules)
        MODULES="$2"
        shift 2
        ;;
      --skip-start)
        SKIP_START=true
        shift
        ;;
      --help|-h)
        show_help
        exit 0
        ;;
      *)
        echo "Option inconnue: $1"
        show_help
        exit 1
        ;;
    esac
  done
}

# Validation repository
validate_repo() {
  info "Validation du repository: $REPO_PATH"

  if [ ! -d "$REPO_PATH" ]; then
    fail "Repository non trouvé: $REPO_PATH"
    exit 1
  fi

  # Convertir en chemin absolu
  REPO_PATH="$(realpath "$REPO_PATH")"

  if [ ! -d "$REPO_PATH/.git" ]; then
    warn "Pas de dossier .git trouvé dans $REPO_PATH"
    read -p "Continuer quand même ? (o/n): " confirm
    if [[ ! "$confirm" =~ ^[Oo]$ ]]; then
      exit 1
    fi
  fi

  ok "Repository validé: $(basename "$REPO_PATH")"
}

# Démarrage des services
start_services() {
  if [ "$SKIP_START" = true ]; then
    info "Démarrage des services skippé"
    return 0
  fi

  info "Démarrage des services Hyperion..."

  cd "$PROJECT_ROOT"

  # Vérifier si les services tournent déjà
  if curl -s http://localhost:8000/api/health &>/dev/null; then
    info "API Hyperion déjà opérationnelle"
  else
    info "Démarrage de la stack core..."
    ./scripts/docker/hyperion-docker.sh --action up --profile core

    # Attendre que l'API soit prête
    info "Attente de l'API..."
    for i in {1..12}; do
      if curl -s http://localhost:8000/api/health &>/dev/null; then
        ok "API Hyperion opérationnelle"
        break
      fi
      if [ $i -eq 12 ]; then
        fail "API Hyperion ne répond pas après 2 minutes"
        exit 1
      fi
      sleep 10
    done
  fi
}

# Analyse V1 - Profil Git
run_v1() {
  info "📥 Analyse V1 - Profil Git"

  local repo_name=$(basename "$REPO_PATH")

  # Exécuter la commande dans le container
  if docker compose exec hyperion-api hyperion profile "/mnt/repositories/$(basename "$REPO_PATH")" --output /app/data/repositories; then
    ok "Profil Git généré pour $repo_name"
  else
    fail "Échec génération profil Git"
    return 1
  fi

  # Vérifier le profil généré
  local profile_path="./data/repositories/$repo_name/profile.yaml"
  if [ -f "$profile_path" ]; then
    ok "Profil sauvé: $profile_path"
  else
    warn "Profil non trouvé: $profile_path"
  fi
}

# Analyse V2 - Code source
run_v2() {
  info "📊 Analyse V2 - Code source"

  local repo_name=$(basename "$REPO_PATH")

  # Exécuter l'ingestion code dans le container
  if docker compose exec hyperion-api python3 -c "
from hyperion.modules.integrations.neo4j_code_ingester import Neo4jCodeIngester

repo_path = '/mnt/repositories/$(basename "$REPO_PATH")'
repo_name = '$repo_name'

ingester = Neo4jCodeIngester()
print('🧹 Clear ancien repo...')
ingester.clear_repo(repo_name)

print('🚀 Ingestion code source...')
stats = ingester.ingest_repo_code(repo_path, repo_name)
print(f'✅ Neo4j v2: {stats}')

final_stats = ingester.get_repo_stats(repo_name)
print(f'📊 Validation: {final_stats}')

ingester.close()
"; then
    ok "Analyse V2 terminée pour $repo_name"
  else
    fail "Échec analyse V2"
    return 1
  fi
}

# Analyse RAG - Embeddings
run_rag() {
  info "🤖 Analyse RAG - Embeddings"

  local repo_name=$(basename "$REPO_PATH")

  # Exécuter l'ingestion RAG dans le container
  if docker compose exec hyperion-api python3 -c "
from hyperion.modules.rag.ingestion import RAGIngester

repo_name = '$repo_name'

ingester = RAGIngester()
chunks = ingester.ingest_repo(repo_name)
print(f'✅ RAG: {chunks} chunks ingérés')
"; then
    ok "Analyse RAG terminée pour $repo_name"
  else
    fail "Échec analyse RAG"
    return 1
  fi
}

# Test de validation
run_tests() {
  info "🧪 Tests de validation"

  local repo_name=$(basename "$REPO_PATH")

  echo "1. Test API Health..."
  if curl -s http://localhost:8000/api/health | python3 -c "
import sys, json
try:
  data = json.load(sys.stdin)
  print(f'✅ Health: {data[\"status\"]}')
except:
  print('❌ Health check failed')
  exit(1)
"; then
    echo "   ✓ API opérationnelle"
  else
    warn "API non accessible"
  fi

  echo "2. Test Chat RAG..."
  if curl -s -X POST http://localhost:8000/api/chat \
    -H "Content-Type: application/json" \
    -d "{\"question\":\"Combien de fichiers dans ce repository ?\",\"repo\":\"$repo_name\"}" | python3 -c "
import sys, json
try:
  data = json.load(sys.stdin)
  answer = data.get('answer', 'No answer')
  print(f'✅ Chat RAG: {answer[:100]}...')
except Exception as e:
  print(f'❌ Chat RAG failed: {e}')
"; then
    echo "   ✓ Chat RAG opérationnel"
  else
    warn "Chat RAG échec"
  fi

  ok "Tests terminés"
}

# Résumé final
show_summary() {
  local repo_name=$(basename "$REPO_PATH")

  echo ""
  echo "============================================"
  echo "🎉 ANALYSE TERMINÉE"
  echo "============================================"
  echo ""
  echo "Repository analysé : $repo_name"
  echo "Modules exécutés   : $MODULES"
  echo ""
  echo "📊 Données générées:"
  if [ -f "./data/repositories/$repo_name/profile.yaml" ]; then
    echo "  ✅ Profil Git     : data/repositories/$repo_name/profile.yaml"
  else
    echo "  ❌ Profil Git     : Non généré"
  fi
  echo ""
  echo "🌐 Services actifs:"
  echo "  • API Hyperion : http://localhost:8000"
  echo "  • API Docs     : http://localhost:8000/docs"
  echo "  • Health Check : http://localhost:8000/api/health"
  echo ""
  echo "🧪 Tests disponibles:"
  echo "  curl http://localhost:8000/api/health"
  echo "  curl http://localhost:8000/api/v2/repos/$repo_name/functions"
  echo "  curl -X POST http://localhost:8000/api/chat -d '{\"question\":\"test\",\"repo\":\"$repo_name\"}'"
}

# Exécution des modules
run_modules() {
  cd "$PROJECT_ROOT"

  # Convertir modules en array
  IFS=',' read -ra MODULE_ARRAY <<< "$MODULES"

  for module in "${MODULE_ARRAY[@]}"; do
    module=$(echo "$module" | xargs) # trim

    case "$module" in
      "all")
        run_v1 && run_v2 && run_rag
        ;;
      "v1")
        run_v1
        ;;
      "v2")
        run_v2
        ;;
      "rag")
        run_rag
        ;;
      *)
        warn "Module inconnu: $module"
        ;;
    esac
  done
}

# Fonction principale
main() {
  echo "============================================"
  echo "🔍 ANALYSE REPOSITORY HYPERION DOCKER"
  echo "============================================"

  parse_args "$@"

  validate_repo
  start_services

  # Créer le lien symbolique pour que Docker puisse accéder au repo
  local repo_parent="$(dirname "$REPO_PATH")"
  local repo_name="$(basename "$REPO_PATH")"

  info "Préparation accès repository..."

  # Le repository doit être accessible dans /mnt/repositories pour le container
  # On s'assure que le mount point existe et pointe vers le bon endroit
  if [ ! -d "/home/kortazo/Documents/$(basename "$REPO_PATH")" ]; then
    warn "Repository $REPO_PATH n'est pas dans /home/kortazo/Documents/"
    warn "Le docker-compose.yml monte /home/kortazo/Documents:/mnt/repositories"
    warn "Veuillez ajuster le mount ou déplacer votre repository"
    exit 1
  fi

  run_modules
  run_tests
  show_summary
}

# Lancement
main "$@"