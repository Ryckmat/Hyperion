#!/bin/bash
# ============================================================================
# 🐳 HYPERION DOCKER - Orchestrateur Docker Compose
#
# Usage:
#   ./scripts/docker/hyperion-docker.sh [OPTIONS]
# ============================================================================

set -euo pipefail

# Variables globales
SCRIPT_DIR="$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")" &>/dev/null && pwd)"
PROJECT_ROOT="$(dirname "$(dirname "$SCRIPT_DIR")")"
cd "$PROJECT_ROOT"

# Configuration par défaut
PROFILE="core"  # core ou full
ACTION="up"     # up, down, restart, logs, status
SERVICE=""      # service spécifique
REPO_PATH=""    # repository à analyser
BUILD=false     # rebuild images
FOLLOW_LOGS=false

# Couleurs
if [ -t 1 ] && [ "${TERM:-}" != "dumb" ] && command -v tput >/dev/null 2>&1; then
  GREEN=$(tput setaf 2)
  RED=$(tput setaf 1)
  YELLOW=$(tput setaf 3)
  CYAN=$(tput setaf 6)
  BOLD=$(tput bold)
  NC=$(tput sgr0)
else
  GREEN='' RED='' YELLOW='' CYAN='' BOLD='' NC=''
fi

# Helpers
ok() { echo -e "${GREEN}✅ $1${NC}"; }
warn() { echo -e "${YELLOW}⚠️ $1${NC}"; }
fail() { echo -e "${RED}❌ $1${NC}"; }
info() { echo -e "${CYAN}ℹ️ $1${NC}"; }
section() {
  echo ""
  echo -e "${CYAN}${BOLD}============================================${NC}"
  echo -e "${CYAN}${BOLD} $1${NC}"
  echo -e "${CYAN}${BOLD}============================================${NC}"
}

# Affichage aide
show_help() {
  cat << 'EOF'
🐳 HYPERION DOCKER v2.7 - Orchestrateur Docker Compose

USAGE:
  ./scripts/docker/hyperion-docker.sh [OPTIONS]

OPTIONS:
  --action ACTION          Action à effectuer (up|down|restart|logs|status|build)
  --profile PROFILE        Profil de services (core|full) - défaut: core
  --service SERVICE        Service spécifique à cibler
  --repo PATH             Repository à analyser (monté dans /mnt/repositories)
  --build                 Rebuild les images avant démarrage
  --follow                Suivre les logs (avec --action logs)
  --help                  Afficher cette aide

ACTIONS:
  up                      Démarrer les services (défaut)
  down                    Arrêter et supprimer les services
  restart                 Redémarrer les services
  logs                    Afficher les logs
  status                  Afficher l'état des services
  build                   Construire les images
  setup                   Configuration initiale (télécharger modèles)

PROFILS:
  core                    Services essentiels: qdrant + ollama + hyperion-api
  full                    Tous les services: core + neo4j + dashboard + open-webui

EXEMPLES:
  ./scripts/docker/hyperion-docker.sh                          # Démarrer services core
  ./scripts/docker/hyperion-docker.sh --profile full           # Démarrer tous les services
  ./scripts/docker/hyperion-docker.sh --action down            # Arrêter tous les services
  ./scripts/docker/hyperion-docker.sh --action logs --follow   # Suivre les logs
  ./scripts/docker/hyperion-docker.sh --action restart --service hyperion-api
  ./scripts/docker/hyperion-docker.sh --action build --build   # Rebuild et démarrer

SERVICES DISPONIBLES:
  - qdrant              Vector database pour RAG
  - ollama              LLM server (llama3.2:1b par défaut)
  - hyperion-api        API FastAPI principale
  - neo4j               Graph database (profil full)
  - hyperion-dashboard  Frontend React (profil full)
  - open-webui          Interface chat (profil full)

PORTS:
  - 6333  Qdrant (vector database)
  - 11434 Ollama (LLM server)
  - 8000  Hyperion API
  - 7474  Neo4j Browser (profil full)
  - 3000  Dashboard React (profil full)
  - 3001  Open WebUI (profil full)

EOF
}

# Parsing arguments
parse_args() {
  while [[ $# -gt 0 ]]; do
    case $1 in
      --action)
        ACTION="$2"
        shift 2
        ;;
      --profile)
        PROFILE="$2"
        shift 2
        ;;
      --service)
        SERVICE="$2"
        shift 2
        ;;
      --repo)
        REPO_PATH="$2"
        shift 2
        ;;
      --build)
        BUILD=true
        shift
        ;;
      --follow)
        FOLLOW_LOGS=true
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

  # Validation action
  case "$ACTION" in
    up|down|restart|logs|status|build|setup) ;;
    *)
      fail "Action invalide: $ACTION"
      exit 1
      ;;
  esac

  # Validation profile
  case "$PROFILE" in
    core|full) ;;
    *)
      fail "Profil invalide: $PROFILE"
      exit 1
      ;;
  esac
}

# Vérifications prérequises
check_prerequisites() {
  info "Vérification des prérequis..."

  # Docker
  if ! command -v docker &>/dev/null; then
    fail "Docker n'est pas installé"
    exit 1
  fi

  if ! docker info &>/dev/null; then
    fail "Docker daemon n'est pas actif"
    exit 1
  fi

  # Docker Compose
  if ! docker compose version &>/dev/null; then
    fail "Docker Compose n'est pas disponible"
    exit 1
  fi

  ok "Prérequis validés"
}

# Construction des images
build_images() {
  section "🔨 CONSTRUCTION DES IMAGES"

  local compose_cmd="docker compose"
  if [ "$PROFILE" = "full" ]; then
    compose_cmd="$compose_cmd --profile full"
  fi

  if [ -n "$SERVICE" ]; then
    compose_cmd="$compose_cmd build $SERVICE"
  else
    compose_cmd="$compose_cmd build"
  fi

  info "Construction: $compose_cmd"
  if eval "$compose_cmd"; then
    ok "Images construites avec succès"
  else
    fail "Échec de construction"
    exit 1
  fi
}

# Configuration initiale (téléchargement modèles)
setup_models() {
  section "📥 CONFIGURATION INITIALE"

  info "Démarrage d'Ollama pour télécharger les modèles..."

  # Démarrer uniquement Ollama
  docker compose up -d ollama

  # Attendre qu'Ollama soit prêt
  info "Attente d'Ollama (30s)..."
  sleep 30

  # Vérifier qu'Ollama répond
  if docker compose exec ollama ollama list &>/dev/null; then
    ok "Ollama prêt"
  else
    warn "Ollama pas encore prêt, tentative de connexion..."
  fi

  # Télécharger le modèle par défaut
  info "Téléchargement du modèle llama3.2:1b..."
  if docker compose exec ollama ollama pull llama3.2:1b; then
    ok "Modèle llama3.2:1b téléchargé"
  else
    warn "Échec téléchargement modèle"
  fi

  # Télécharger modèles additionnels optionnels
  echo ""
  read -p "Télécharger des modèles additionnels ? (o/n): " download_more
  if [[ "$download_more" =~ ^[Oo]$ ]]; then
    echo "Modèles disponibles:"
    echo "  1) llama3.1:8b (4.7GB) - Équilibre performance/qualité"
    echo "  2) qwen2.5:14b (8.7GB) - Qualité premium"
    echo "  3) Tous les modèles"
    echo "  4) Passer"

    read -p "Votre choix (1-4): " model_choice
    case $model_choice in
      1)
        info "Téléchargement llama3.1:8b..."
        docker compose exec ollama ollama pull llama3.1:8b
        ;;
      2)
        info "Téléchargement qwen2.5:14b..."
        docker compose exec ollama ollama pull qwen2.5:14b
        ;;
      3)
        info "Téléchargement de tous les modèles (peut prendre du temps)..."
        docker compose exec ollama ollama pull llama3.1:8b
        docker compose exec ollama ollama pull qwen2.5:14b
        ;;
      *)
        info "Téléchargements additionnels passés"
        ;;
    esac
  fi

  # Arrêter Ollama standalone
  docker compose stop ollama

  ok "Configuration initiale terminée"
}

# Démarrage des services
start_services() {
  section "🚀 DÉMARRAGE DES SERVICES"

  local compose_cmd="docker compose"
  if [ "$PROFILE" = "full" ]; then
    compose_cmd="$compose_cmd --profile full"
  fi

  if [ "$BUILD" = true ]; then
    compose_cmd="$compose_cmd build"
  fi

  compose_cmd="$compose_cmd up -d"

  if [ -n "$SERVICE" ]; then
    compose_cmd="$compose_cmd $SERVICE"
  fi

  info "Commande: $compose_cmd"
  if eval "$compose_cmd"; then
    ok "Services démarrés"
  else
    fail "Échec démarrage"
    exit 1
  fi

  # Attendre que les services soient prêts
  info "Attente des services (30s)..."
  sleep 30

  # Vérifications de santé
  check_health
}

# Arrêt des services
stop_services() {
  section "🛑 ARRÊT DES SERVICES"

  local compose_cmd="docker compose"
  if [ "$PROFILE" = "full" ]; then
    compose_cmd="$compose_cmd --profile full"
  fi

  compose_cmd="$compose_cmd down"

  if [ -n "$SERVICE" ]; then
    compose_cmd="docker compose stop $SERVICE"
  fi

  info "Commande: $compose_cmd"
  if eval "$compose_cmd"; then
    ok "Services arrêtés"
  else
    warn "Arrêt partiellement échoué"
  fi
}

# Redémarrage des services
restart_services() {
  section "🔄 REDÉMARRAGE DES SERVICES"

  local compose_cmd="docker compose"
  if [ "$PROFILE" = "full" ]; then
    compose_cmd="$compose_cmd --profile full"
  fi

  if [ -n "$SERVICE" ]; then
    compose_cmd="$compose_cmd restart $SERVICE"
  else
    compose_cmd="$compose_cmd restart"
  fi

  info "Commande: $compose_cmd"
  if eval "$compose_cmd"; then
    ok "Services redémarrés"
    check_health
  else
    fail "Échec redémarrage"
    exit 1
  fi
}

# Affichage des logs
show_logs() {
  section "📝 LOGS DES SERVICES"

  local compose_cmd="docker compose"
  if [ "$PROFILE" = "full" ]; then
    compose_cmd="$compose_cmd --profile full"
  fi

  compose_cmd="$compose_cmd logs"

  if [ "$FOLLOW_LOGS" = true ]; then
    compose_cmd="$compose_cmd -f"
  fi

  if [ -n "$SERVICE" ]; then
    compose_cmd="$compose_cmd $SERVICE"
  fi

  info "Commande: $compose_cmd"
  eval "$compose_cmd"
}

# Status des services
show_status() {
  section "📊 ÉTAT DES SERVICES"

  echo "Services Docker Compose:"
  docker compose ps

  echo ""
  echo "Health checks:"

  # Qdrant
  if curl -s http://localhost:6333/health &>/dev/null; then
    ok "Qdrant (6333) - Opérationnel"
  else
    fail "Qdrant (6333) - Non accessible"
  fi

  # Ollama
  if curl -s http://localhost:11434/api/tags &>/dev/null; then
    ok "Ollama (11434) - Opérationnel"
  else
    fail "Ollama (11434) - Non accessible"
  fi

  # Hyperion API
  if curl -s http://localhost:8000/api/health &>/dev/null; then
    ok "Hyperion API (8000) - Opérationnel"
  else
    fail "Hyperion API (8000) - Non accessible"
  fi

  if [ "$PROFILE" = "full" ]; then
    # Neo4j
    if curl -s http://localhost:7474/ &>/dev/null; then
      ok "Neo4j (7474) - Opérationnel"
    else
      fail "Neo4j (7474) - Non accessible"
    fi

    # Dashboard
    if curl -s http://localhost:3000/ &>/dev/null; then
      ok "Dashboard (3000) - Opérationnel"
    else
      fail "Dashboard (3000) - Non accessible"
    fi

    # Open WebUI
    if curl -s http://localhost:3001/ &>/dev/null; then
      ok "Open WebUI (3001) - Opérationnel"
    else
      fail "Open WebUI (3001) - Non accessible"
    fi
  fi

  echo ""
  echo "URLs d'accès:"
  echo "  • API Hyperion     : http://localhost:8000"
  echo "  • API Health       : http://localhost:8000/api/health"
  echo "  • API Docs         : http://localhost:8000/docs"
  echo "  • Qdrant           : http://localhost:6333"
  if [ "$PROFILE" = "full" ]; then
    echo "  • Neo4j Browser    : http://localhost:7474"
    echo "  • Dashboard        : http://localhost:3000"
    echo "  • Open WebUI       : http://localhost:3001"
  fi
}

# Vérifications de santé
check_health() {
  info "Vérification de la santé des services..."

  # Attendre un peu plus pour les services lents
  sleep 10

  local all_healthy=true

  # Qdrant
  if curl -s http://localhost:6333/health &>/dev/null; then
    ok "Qdrant opérationnel"
  else
    warn "Qdrant non accessible"
    all_healthy=false
  fi

  # Ollama
  if curl -s http://localhost:11434/api/tags &>/dev/null; then
    ok "Ollama opérationnel"
  else
    warn "Ollama non accessible"
    all_healthy=false
  fi

  # API Hyperion (plus tolérant)
  local api_ready=false
  for i in {1..6}; do
    if curl -s http://localhost:8000/api/health &>/dev/null; then
      ok "API Hyperion opérationnelle"
      api_ready=true
      break
    else
      info "API Hyperion pas encore prête (tentative $i/6)..."
      sleep 10
    fi
  done

  if [ "$api_ready" = false ]; then
    warn "API Hyperion non accessible après 60s"
    all_healthy=false
  fi

  if [ "$all_healthy" = true ]; then
    ok "Tous les services core sont opérationnels"
  else
    warn "Certains services ne répondent pas encore"
    info "Utilisez '--action logs' pour diagnostiquer"
  fi
}

# Fonction principale
main() {
  echo "============================================================"
  echo "🐳 HYPERION DOCKER v2.7"
  echo "============================================================"

  parse_args "$@"

  info "Action: $ACTION"
  info "Profil: $PROFILE"
  [ -n "$SERVICE" ] && info "Service: $SERVICE"

  check_prerequisites

  case "$ACTION" in
    setup)
      setup_models
      ;;
    build)
      build_images
      ;;
    up)
      if [ "$BUILD" = true ]; then
        build_images
      fi
      start_services
      ;;
    down)
      stop_services
      ;;
    restart)
      restart_services
      ;;
    logs)
      show_logs
      ;;
    status)
      show_status
      ;;
  esac

  if [ "$ACTION" = "up" ]; then
    echo ""
    section "🎉 DÉMARRAGE TERMINÉ"
    info "Stack Hyperion v2.7 opérationnelle!"
    info "Utilisez '--action status' pour vérifier l'état"
    info "Utilisez '--action logs --follow' pour suivre les logs"
  fi
}

# Lancement
main "$@"