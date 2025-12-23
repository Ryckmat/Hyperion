#!/bin/bash
# ============================================================================
# 🚀 HYPERION MASTER V2 - Contrôle complet + Ingestion multi-sources
# - Path projet auto (pas de hardcode)
# - Open WebUI auto-configuré (OpenAI-compatible Hyperion)
# - Dashboard en background + Ctrl+C stop tout
# - Ingestion v1 (profils Git) + v2 (Code Analysis)
# ============================================================================

set -euo pipefail

# ----------------------------------------------------------------------------
# Résolution du dossier projet
# ----------------------------------------------------------------------------
SCRIPT_DIR="$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")" &>/dev/null && pwd)"
PROJECT_ROOT="${HYPERION_HOME:-$(dirname "$(dirname "$SCRIPT_DIR")")}"
cd "$PROJECT_ROOT"

# ----------------------------------------------------------------------------
# Vérifier et installer hyperion si nécessaire
# ----------------------------------------------------------------------------
if [ -d "$PROJECT_ROOT/venv" ]; then
  source "$PROJECT_ROOT/venv/bin/activate" 2>/dev/null || true
  if ! pip list 2>/dev/null | grep -q "^hyperion "; then
    echo "   🔧 Installation hyperion en mode éditable..."
    pip install -e . >/dev/null 2>&1 || {
      echo "   ⚠️  Échec installation hyperion"
    }
  fi
fi

# ----------------------------------------------------------------------------
# Couleurs
# ----------------------------------------------------------------------------
GREEN='\033[0;32m'
RED='\033[0;31m'
YELLOW='\033[1;33m'
CYAN='\033[0;36m'
NC='\033[0m'

# ----------------------------------------------------------------------------
# Config
# ----------------------------------------------------------------------------
OPENWEBUI_PORT="${OPENWEBUI_PORT:-3001}"
OPENWEBUI_URL="http://localhost:${OPENWEBUI_PORT}"

HYPERION_PORT="${HYPERION_PORT:-8000}"
HYPERION_OPENAI_BASE_URL="http://host.docker.internal:${HYPERION_PORT}/v1"
HYPERION_MODEL="${HYPERION_MODEL:-hyperion-rag}"

WAIT_MAX_SECONDS="${WAIT_MAX_SECONDS:-300}"
WAIT_STEP_SECONDS="${WAIT_STEP_SECONDS:-2}"

# PID dashboard (pour Ctrl+C stop)
API_PID=""
FRONTEND_PID=""

# ----------------------------------------------------------------------------
# Helpers affichage
# ----------------------------------------------------------------------------
banner() {
  echo "============================================================"
  echo -e "$1"
  echo "============================================================"
}
section() {
  echo ""
  echo -e "${CYAN}------------------------------------------------------------${NC}"
  echo -e "${CYAN}$1${NC}"
  echo -e "${CYAN}------------------------------------------------------------${NC}"
}
ok()   { echo -e "${GREEN}   ✅ $1${NC}"; }
warn() { echo -e "${YELLOW}   ⚠️  $1${NC}"; }
fail() { echo -e "${RED}   ❌ $1${NC}"; }

# ----------------------------------------------------------------------------
# CLEANUP Ctrl+C
# ----------------------------------------------------------------------------
cleanup() {
  echo ""
  banner "🛑 ARRÊT DEMANDÉ (Ctrl+C) — STOP SERVICES"

  if [ -n "${API_PID:-}" ] && kill -0 "$API_PID" 2>/dev/null; then
    warn "Stop API (PID $API_PID)"
    kill "$API_PID" 2>/dev/null || true
    sleep 1
    kill -9 "$API_PID" 2>/dev/null || true
    ok "API stoppée"
  fi

  if [ -n "${FRONTEND_PID:-}" ] && kill -0 "$FRONTEND_PID" 2>/dev/null; then
    warn "Stop Frontend (PID $FRONTEND_PID)"
    kill "$FRONTEND_PID" 2>/dev/null || true
    sleep 1
    kill -9 "$FRONTEND_PID" 2>/dev/null || true
    ok "Frontend stoppé"
  fi

  if docker ps --format '{{.Names}}' | grep -q "^open-webui$"; then
    warn "Stop open-webui"
    docker stop open-webui >/dev/null || true
    ok "open-webui stoppé"
  fi

  echo ""
  ok "Arrêt terminé."
  exit 0
}
trap cleanup INT

# ----------------------------------------------------------------------------
# Wait helpers
# ----------------------------------------------------------------------------
wait_container_healthy_or_http() {
  local name="$1"
  local url="$2"
  local max_seconds="${3:-$WAIT_MAX_SECONDS}"
  local step="${4:-$WAIT_STEP_SECONDS}"

  local elapsed=0
  while [ "$elapsed" -lt "$max_seconds" ]; do
    local health
    health=$(docker inspect -f '{{if .State.Health}}{{.State.Health.Status}}{{else}}nohealth{{end}}' "$name" 2>/dev/null || echo "missing")

    if [ "$health" = "healthy" ]; then
      return 0
    fi

    if curl -s "$url" >/dev/null 2>&1; then
      return 0
    fi

    if [ $((elapsed % 10)) -eq 0 ]; then
      echo -e "${CYAN}   ⏳ Démarrage... (health=${health}, elapsed=${elapsed}s)${NC}"
    fi

    sleep "$step"
    elapsed=$((elapsed + step))
  done
  return 1
}

wait_hyperion() {
  local elapsed=0
  while [ "$elapsed" -lt 120 ]; do
    if curl -s "http://localhost:${HYPERION_PORT}/v1/models" >/dev/null 2>&1; then
      return 0
    fi
    sleep 2
    elapsed=$((elapsed + 2))
  done
  return 1
}

# ----------------------------------------------------------------------------
# Ensure services
# ----------------------------------------------------------------------------
ensure_docker() {
  section "🐳 DOCKER"
  if ! command -v docker &>/dev/null; then
    fail "Docker non installé"
    exit 1
  fi
  if ! docker info &>/dev/null; then
    warn "Docker daemon non actif → start"
    sudo systemctl start docker
  fi
  ok "Docker actif"
}

ensure_qdrant() {
  section "📦 QDRANT"
  if ! curl -s http://localhost:6333/collections &>/dev/null; then
    warn "Qdrant non actif → start"
    if docker ps -a --format '{{.Names}}' | grep -q "^qdrant$"; then
      docker start qdrant >/dev/null
    else
      docker run -d --name qdrant \
        -p 6333:6333 -p 6334:6334 \
        -v ~/qdrant_storage:/qdrant/storage:z \
        qdrant/qdrant >/dev/null
    fi
    sleep 3
  fi

  if curl -s http://localhost:6333/collections &>/dev/null; then
    ok "Qdrant actif (http://localhost:6333)"
  else
    fail "Qdrant KO"
  fi
}

ensure_ollama() {
  section "🤖 OLLAMA"
  if ! command -v ollama &>/dev/null; then
    fail "Ollama non installé"
    exit 1
  fi
  if ! systemctl is-active --quiet ollama 2>/dev/null; then
    warn "Service Ollama inactif → start"
    sudo systemctl start ollama
    sleep 2
  fi
  ok "Ollama actif"

  if ollama list | grep -q "qwen2.5:32b"; then
    ok "Modèle qwen2.5:32b disponible"
  else
    warn "Modèle qwen2.5:32b manquant (ollama pull qwen2.5:32b)"
  fi
}

verify_python() {
  section "🐍 PYTHON"
  ok "Python $(python3 --version | awk '{print $2}')"
  if [ -d "venv" ]; then
    ok "Venv présent"
  else
    warn "Venv absent"
  fi
}

verify_system() {
  banner "🔍 VÉRIFICATION SYSTÈME COMPLÈTE"
  ensure_docker
  ensure_qdrant
  ensure_ollama
  verify_python

  section "💬 OPEN WEBUI (STATUT)"
  if docker ps --format '{{.Names}}' | grep -q "^open-webui$"; then
    ok "Open WebUI actif (${OPENWEBUI_URL})"
  else
    warn "Open WebUI non actif"
  fi

  echo ""
  ok "VÉRIFICATION TERMINÉE"
}

# ----------------------------------------------------------------------------
# Ingestion v1 (profils Git)
# ----------------------------------------------------------------------------
run_ingestion_v1() {
  section "📥 INGESTION V1 - Profils Git (Stats agrégées)"
  
  echo ""
  echo -e "${CYAN}Profil YAML à ingérer :${NC}"
  echo -e "${YELLOW}   Format: data/repositories/<nom>/profile.yaml${NC}"
  read -p "   Chemin : " profile_path
  
  if [ -z "$profile_path" ]; then
    warn "Aucun chemin fourni, abandon"
    return 0
  fi
  
  if [ ! -f "$profile_path" ]; then
    fail "Profil introuvable: $profile_path"
    return 1
  fi
  
  echo ""
  echo -e "${YELLOW}Ingestion: $profile_path${NC}"
  read -p "Confirmer ? (o/n): " confirm
  
  if [[ ! "$confirm" =~ ^[Oo]$ ]]; then
    warn "Ingestion v1 annulée"
    return 0
  fi
  
  cd "$PROJECT_ROOT"
  [ -d "venv" ] && source venv/bin/activate 2>/dev/null || true
  
  echo ""
  if python3 -c "
from hyperion.modules.integrations.neo4j_ingester import Neo4jIngester
ing = Neo4jIngester()
stats = ing.ingest_profile('$profile_path')
print(f'✅ Stats: {stats}')
ing.close()
"; then
    echo ""
    ok "Ingestion v1 terminée !"
    echo -e "${GREEN}   Neo4j: :Repo, :Contributor, :Hotspot, :Directory, :Extension${NC}"
  else
    echo ""
    fail "Échec ingestion v1"
    return 1
  fi
}

# ----------------------------------------------------------------------------
# Ingestion v2 (multi-sources)
# ----------------------------------------------------------------------------
run_ingestion_v2() {
  section "📥 INGESTION V2 - Code Analysis (Structure détaillée)"
  
  echo ""
  echo -e "${CYAN}Repository à analyser :${NC}"
  read -p "   Chemin (ex: /tmp/requests) : " repo_path
  
  if [ -z "$repo_path" ]; then
    warn "Aucun chemin fourni, abandon"
    return 0
  fi
  
  if [ ! -d "$repo_path" ]; then
    fail "Repository non trouvé: $repo_path"
    return 1
  fi
  
  echo ""
  read -p "   Ingérer documentation ? (o/n): " with_docs
  
  CMD="python3 scripts/maintenance/ingest_generalized.py --repo \"$repo_path\""
  
  if [[ "$with_docs" =~ ^[Oo]$ ]]; then
    if [ -d "$repo_path/docs" ]; then
      CMD="$CMD --docs \"$repo_path/docs\""
      ok "Documentation trouvée"
    else
      warn "Dossier docs non trouvé, ignoré"
    fi
  fi
  
  echo ""
  echo -e "${YELLOW}Commande: $CMD${NC}"
  read -p "Confirmer ? (o/n): " confirm
  
  if [[ ! "$confirm" =~ ^[Oo]$ ]]; then
    warn "Ingestion v2 annulée"
    return 0
  fi
  
  cd "$PROJECT_ROOT"
  [ -d "venv" ] && source venv/bin/activate 2>/dev/null || true
  
  echo ""
  if eval "$CMD"; then
    echo ""
    ok "Ingestion v2 terminée !"
    echo -e "${GREEN}   Neo4j: :File, :Function, :Class + :DEPENDS_ON${NC}"
  else
    echo ""
    fail "Échec ingestion v2"
    return 1
  fi
}

# ----------------------------------------------------------------------------
# Open WebUI
# ----------------------------------------------------------------------------
start_openwebui() {
  section "💬 OPEN WEBUI — LANCEMENT"

  if docker ps --format '{{.Names}}' | grep -q "^open-webui$"; then
    ok "Open WebUI déjà actif"
  else
    if docker ps -a --format '{{.Names}}' | grep -q "^open-webui$"; then
      warn "Redémarrage container open-webui..."
      docker start open-webui >/dev/null
    else
      warn "Création container open-webui..."
      docker run -d \
        --name open-webui \
        --add-host=host.docker.internal:host-gateway \
        -p ${OPENWEBUI_PORT}:8080 \
        -e WEBUI_AUTH=false \
        -e OLLAMA_BASE_URL=http://host.docker.internal:11434 \
        -e OPENAI_API_BASE_URL=${HYPERION_OPENAI_BASE_URL} \
        -e OPENAI_API_KEY=x \
        -e DEFAULT_MODEL=${HYPERION_MODEL} \
        -e ENABLE_MODEL_SELECTOR=true \
        -v open-webui:/app/backend/data \
        --restart always \
        ghcr.io/open-webui/open-webui:main >/dev/null
    fi
  fi

  echo -e "${CYAN}   ⏳ Attente Open WebUI...${NC}"
  if ! wait_container_healthy_or_http "open-webui" "${OPENWEBUI_URL}/" "${WAIT_MAX_SECONDS}" "${WAIT_STEP_SECONDS}"; then
    fail "Open WebUI ne répond pas"
    return 1
  fi
  ok "Open WebUI prêt : ${OPENWEBUI_URL}"

  if command -v xdg-open &>/dev/null; then
    xdg-open "${OPENWEBUI_URL}" >/dev/null 2>&1 &
  fi
}

# ----------------------------------------------------------------------------
# Dashboard
# ----------------------------------------------------------------------------
start_dashboard_background() {
  section "🌐 DASHBOARD REACT — LANCEMENT"
  mkdir -p logs

  if [ ! -d "$PROJECT_ROOT/venv" ]; then
    fail "Virtual environment non trouvé"
    return 1
  fi

  cd "$PROJECT_ROOT"
  nohup bash -c "source venv/bin/activate && python3 scripts/dev/run_api.py" > logs/api.log 2>&1 &
  API_PID=$!
  ok "API lancée (PID ${API_PID})"

  echo -e "${CYAN}   ⏳ Attente API (max 60s)...${NC}"
  local elapsed=0
  while [ $elapsed -lt 60 ]; do
    if curl -s "http://localhost:${HYPERION_PORT}/api/health" >/dev/null 2>&1; then
      ok "API prête (http://localhost:${HYPERION_PORT})"
      break
    fi
    sleep 2
    elapsed=$((elapsed + 2))
  done

  cd "$PROJECT_ROOT/frontend"
  nohup python3 -m http.server 3000 > "$PROJECT_ROOT/logs/dashboard.log" 2>&1 &
  FRONTEND_PID=$!

  ok "Dashboard lancé (PID ${FRONTEND_PID})"
  echo -e "${GREEN}   • Front: http://localhost:3000${NC}"
  echo -e "${GREEN}   • API  : http://localhost:${HYPERION_PORT}${NC}"
}

# ----------------------------------------------------------------------------
# MAIN
# ----------------------------------------------------------------------------
banner "🚀 HYPERION MASTER V2 - Contrôle complet"
echo ""

read -p "Vérifier et démarrer les services ? (o/n): " do_verify

echo ""
echo -e "${CYAN}Quelle ingestion souhaitez-vous ?${NC}"
echo "  ${YELLOW}all${NC} - V1 + V2 (profils Git + Code Analysis)"
echo "  ${YELLOW}1${NC}   - V1 uniquement (profils Git → Stats agrégées)"
echo "  ${YELLOW}2${NC}   - V2 uniquement (Code Analysis → Structure)"
echo "  ${YELLOW}n${NC}   - Aucune"
read -p "Choix [all/1/2/n]: " ingest_choice

read -p "Générer documentation ? (o/n): " do_docs
read -p "Lancer dashboard React ? (o/n): " do_dashboard
read -p "Lancer Open WebUI (chat) ? (o/n): " do_openwebui

echo ""
banner "🎯 Récapitulatif"
[[ "$do_verify" =~ ^[Oo]$ ]] && echo "✅ Vérification services"
case "$ingest_choice" in
  all)
    echo "✅ Ingestion V1 (profils Git)"
    echo "✅ Ingestion V2 (Code Analysis)"
    ;;
  1)
    echo "✅ Ingestion V1 (profils Git)"
    ;;
  2)
    echo "✅ Ingestion V2 (Code Analysis)"
    ;;
esac
[[ "$do_docs" =~ ^[Oo]$ ]] && echo "✅ Génération docs"
[[ "$do_dashboard" =~ ^[Oo]$ ]] && echo "✅ Lancement dashboard React"
[[ "$do_openwebui" =~ ^[Oo]$ ]] && echo "✅ Lancement Open WebUI"
echo ""

read -p "Confirmer ? (o/n): " confirm
[[ ! "$confirm" =~ ^[Oo]$ ]] && echo "Annulé." && exit 0

echo ""
banner "🚀 EXÉCUTION"

# 0) Vérif
if [[ "$do_verify" =~ ^[Oo]$ ]]; then
  verify_system
fi

# 1) Ingestion
case "$ingest_choice" in
  all)
    run_ingestion_v1
    run_ingestion_v2
    ;;
  1)
    run_ingestion_v1
    ;;
  2)
    run_ingestion_v2
    ;;
esac

# 2) Dashboard (lance l'API)
if [[ "$do_dashboard" =~ ^[Oo]$ ]]; then
  ensure_ollama
  start_dashboard_background
fi

# 3) Open WebUI
if [[ "$do_openwebui" =~ ^[Oo]$ ]]; then
  ensure_docker
  start_openwebui
fi

echo ""
banner "🎉 TERMINÉ !"
echo ""
echo "📱 Services actifs :"
[[ "$do_dashboard" =~ ^[Oo]$ ]] && echo "   • Dashboard React : http://localhost:3000"
[[ "$do_openwebui" =~ ^[Oo]$ ]] && echo "   • Open WebUI      : ${OPENWEBUI_URL}"
echo "   • Hyperion API    : http://localhost:${HYPERION_PORT}"
echo ""
echo -e "${CYAN}🔎 Supervision active. Ctrl+C pour tout arrêter.${NC}"

# Keep-alive superviseur
while true; do
  sleep 2
done
