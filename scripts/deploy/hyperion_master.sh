#!/bin/bash
# ============================================================================
# 🚀 HYPERION MASTER - Contrôle complet (esthétique + supervision)
# - Path projet auto (pas de hardcode)
# - Open WebUI auto-configuré (OpenAI-compatible Hyperion)
# - Dashboard en background + Ctrl+C stop tout
# - Affichage "bandeaux" comme avant
# ============================================================================

set -euo pipefail

# ----------------------------------------------------------------------------
# Résolution du dossier projet (pas de hardcode)
# - Priorité 1 : variable HYPERION_HOME si définie
# - Sinon : dossier parent du script (hyperion_master.sh) => racine projet
# ----------------------------------------------------------------------------
SCRIPT_DIR="$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")" &>/dev/null && pwd)"
PROJECT_ROOT="${HYPERION_HOME:-$(dirname "$(dirname "$SCRIPT_DIR")")}"
cd "$PROJECT_ROOT"

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
  # Attendre que l'API Hyperion soit dispo
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
    echo "   Installation : sudo pacman -S docker"
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

  echo -e "${CYAN}   ⏳ Attente Open WebUI (jusqu'à ${WAIT_MAX_SECONDS}s)...${NC}"
  if ! wait_container_healthy_or_http "open-webui" "${OPENWEBUI_URL}/" "${WAIT_MAX_SECONDS}" "${WAIT_STEP_SECONDS}"; then
    fail "Open WebUI ne répond pas dans le délai"
    echo -e "${YELLOW}   Logs (tail 120):${NC}"
    docker logs --tail 120 open-webui || true
    exit 1
  fi
  ok "Open WebUI prêt : ${OPENWEBUI_URL}"

  section "🔌 OPEN WEBUI → TEST HYPERION"
  echo -e "${CYAN}   ⏳ Attente Hyperion (/v1/models) ...${NC}"
  if wait_hyperion; then
    ok "Hyperion API prête sur http://localhost:${HYPERION_PORT}"
    if docker exec -it open-webui sh -lc "apk add --no-cache curl >/dev/null 2>&1 || true; curl -s ${HYPERION_OPENAI_BASE_URL}/models >/dev/null 2>&1"; then
      ok "Hyperion joignable depuis Open WebUI (${HYPERION_OPENAI_BASE_URL})"
      ok "Default model: ${HYPERION_MODEL}"
    else
      warn "Test Open WebUI→Hyperion KO (souvent transitoire, retenter dans 5–10s)"
    fi
  else
    warn "Hyperion API pas prête → on skip le test Open WebUI→Hyperion"
  fi

  if command -v xdg-open &>/dev/null; then
    xdg-open "${OPENWEBUI_URL}" >/dev/null 2>&1 &
  fi
}

# ----------------------------------------------------------------------------
# Dashboard (background) - CORRIGÉ
# ----------------------------------------------------------------------------
start_dashboard_background() {
  section "🌐 DASHBOARD REACT — LANCEMENT"
  mkdir -p logs

  # Lancer API en arrière-plan
  cd "$PROJECT_ROOT"
  nohup python3 scripts/dev/run_api.py > logs/api.log 2>&1 &
  API_PID=$!
  ok "API lancée (PID ${API_PID})"

  # Attendre que l'API démarre
  sleep 5

  # Lancer frontend en arrière-plan
  cd "$PROJECT_ROOT/frontend"
  nohup python3 -m http.server 3000 > "$PROJECT_ROOT/logs/dashboard.log" 2>&1 &
  FRONTEND_PID=$!

  ok "Dashboard lancé (PID ${FRONTEND_PID})"
  echo -e "${GREEN}   • Logs API: tail -f logs/api.log${NC}"
  echo -e "${GREEN}   • Logs Dashboard: tail -f logs/dashboard.log${NC}"
  echo -e "${GREEN}   • Front: http://localhost:3000${NC}"
  echo -e "${GREEN}   • API  : http://localhost:${HYPERION_PORT}${NC}"
}

# ----------------------------------------------------------------------------
# Vérification complète (esthétique)
# ----------------------------------------------------------------------------
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
# MAIN
# ----------------------------------------------------------------------------
banner "🚀 HYPERION MASTER - Contrôle complet"
echo ""

read -p "Vérifier et démarrer les services ? (o/n): " do_verify
read -p "Ingérer Neo4j (graphe) ? (o/n): " do_neo4j
read -p "Ingérer RAG (Qdrant) ? (o/n): " do_ingest
read -p "Générer documentation ? (o/n): " do_docs
read -p "Lancer dashboard React ? (o/n): " do_dashboard
read -p "Lancer Open WebUI (chat) ? (o/n): " do_openwebui

echo ""
banner "🎯 Récapitulatif"
[[ "$do_verify" =~ ^[Oo]$ ]] && echo "✅ Vérification services"
[[ "$do_neo4j" =~ ^[Oo]$ ]] && echo "✅ Ingestion Neo4j"
[[ "$do_ingest" =~ ^[Oo]$ ]] && echo "✅ Ingestion RAG"
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

# NOTE : l'API Hyperion vient du dashboard, donc on le lance AVANT Open WebUI
if [[ "$do_dashboard" =~ ^[Oo]$ ]]; then
  ensure_ollama
  start_dashboard_background
fi

if [[ "$do_openwebui" =~ ^[Oo]$ ]]; then
  ensure_docker
  start_openwebui
fi

echo ""
banner "🎉 TERMINÉ !"
echo ""
echo "📱 Services actifs :"
[[ "$do_dashboard" =~ ^[Oo]$ ]] && echo "   • Dashboard React : http://localhost:3000 (logs: logs/dashboard.log)"
[[ "$do_openwebui" =~ ^[Oo]$ ]] && echo "   • Open WebUI      : ${OPENWEBUI_URL}"
echo "   • Hyperion API    : http://localhost:${HYPERION_PORT}"
echo "   • API Docs        : http://localhost:${HYPERION_PORT}/docs"
echo ""
echo "✅ Hyperion OpenAI base URL : ${HYPERION_OPENAI_BASE_URL}"
echo "✅ Default model           : ${HYPERION_MODEL}"
echo ""
echo -e "${CYAN}🔎 Supervision active. Ctrl+C pour tout arrêter.${NC}"

# Keep-alive superviseur
while true; do
  sleep 2
done
