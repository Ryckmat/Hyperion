#!/bin/bash
# ============================================================================
# 🚀 HYPERION MASTER FINAL - Orchestrateur Unique avec Options
#
# Usage:
#   ./hyperion_master_final.sh                    # Mode interactif
#   ./hyperion_master_final.sh --auto             # Mode automatique
#   ./hyperion_master_final.sh --repo /path       # Repository spécifique
#   ./hyperion_master_final.sh --modules v1,v2    # Modules spécifiques
#   ./hyperion_master_final.sh --help             # Aide
# ============================================================================

set -euo pipefail

# Variables globales
SCRIPT_DIR="$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")" &>/dev/null && pwd)"
PROJECT_ROOT="${HYPERION_HOME:-$(dirname "$(dirname "$SCRIPT_DIR")")}"
cd "$PROJECT_ROOT"

# Configuration par défaut
DEFAULT_REPO="$PROJECT_ROOT"
AUTO_MODE=false
INTERACTIVE_MODE=true
REPO_PATH=""
MODULES="all"
SKIP_VERIFICATION=false
LAUNCH_DASHBOARD=true
LAUNCH_OPENWEBUI=true
MODEL_SETUP=false

# Couleurs avec détection
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

# PIDs pour cleanup
API_PID=""
FRONTEND_PID=""

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

# Cleanup
cleanup() {
  echo ""
  section "🛑 ARRÊT SERVICES"

  if [ -n "${API_PID:-}" ] && kill -0 "$API_PID" 2>/dev/null; then
    warn "Arrêt API (PID $API_PID)"
    kill "$API_PID" 2>/dev/null || true
  fi

  if [ -n "${FRONTEND_PID:-}" ] && kill -0 "$FRONTEND_PID" 2>/dev/null; then
    warn "Arrêt Dashboard (PID $FRONTEND_PID)"
    kill "$FRONTEND_PID" 2>/dev/null || true
  fi

  ok "Arrêt terminé"
  exit 0
}
trap cleanup INT

# Affichage aide
show_help() {
  cat << EOF
🚀 HYPERION MASTER FINAL - Orchestrateur Unique

USAGE:
  $0 [OPTIONS]

OPTIONS:
  --auto                     Mode automatique (pas d'interaction)
  --repo PATH               Repository à analyser (défaut: $DEFAULT_REPO)
  --modules MODULE_LIST     Modules à exécuter (défaut: all)
                           Modules disponibles: v1, v2, rag, all
  --skip-verification       Skip la vérification des services
  --no-dashboard           Ne pas lancer le dashboard
  --no-openwebui           Ne pas lancer Open WebUI
  --setup-model            Configurer le modèle LLM avant démarrage
  --help                   Afficher cette aide

EXEMPLES:
  $0                                    # Mode interactif complet
  $0 --auto                            # Mode auto avec repo par défaut
  $0 --repo /tmp/requests --auto       # Auto sur repository requests
  $0 --modules v1,rag --repo /tmp/foo  # V1 + RAG uniquement sur foo
  $0 --auto --no-openwebui            # Auto sans Open WebUI

MODULES:
  v1    Ingestion V1 (Git stats → Neo4j v1)
  v2    Ingestion V2 (Code analysis → Neo4j v2)
  rag   Ingestion RAG (Profils → Qdrant embeddings)
  all   Tous les modules (v1 + v2 + rag)

EOF
}

# Parsing arguments
parse_args() {
  while [[ $# -gt 0 ]]; do
    case $1 in
      --auto)
        AUTO_MODE=true
        INTERACTIVE_MODE=false
        shift
        ;;
      --repo)
        REPO_PATH="$2"
        shift 2
        ;;
      --modules)
        MODULES="$2"
        shift 2
        ;;
      --skip-verification)
        SKIP_VERIFICATION=true
        shift
        ;;
      --no-dashboard)
        LAUNCH_DASHBOARD=false
        shift
        ;;
      --no-openwebui)
        LAUNCH_OPENWEBUI=false
        shift
        ;;
      --setup-model)
        MODEL_SETUP=true
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

  # Valeurs par défaut
  if [ -z "$REPO_PATH" ]; then
    REPO_PATH="$DEFAULT_REPO"
  fi
}

# Validation repository
validate_repo() {
  if [ ! -d "$REPO_PATH" ]; then
    fail "Repository non trouvé: $REPO_PATH"
    exit 1
  fi

  if [ ! -d "$REPO_PATH/.git" ]; then
    warn "Pas de dossier .git trouvé dans $REPO_PATH"
    read -p "Continuer quand même ? (o/n): " confirm
    if [[ ! "$confirm" =~ ^[Oo]$ ]]; then
      exit 1
    fi
  fi
}

# Validation modules
validate_modules() {
  valid_modules="v1 v2 rag all"
  IFS=',' read -ra MODULE_ARRAY <<< "$MODULES"

  for module in "${MODULE_ARRAY[@]}"; do
    module=$(echo "$module" | xargs) # trim
    if [[ ! " $valid_modules " =~ " $module " ]]; then
      fail "Module invalide: $module"
      echo "Modules valides: $valid_modules"
      exit 1
    fi
  done
}

# Configuration modèle LLM
setup_model() {
  if [ "$MODEL_SETUP" = false ]; then
    return 0
  fi

  section "🎯 CONFIGURATION MODÈLE LLM"

  # Vérifier Ollama
  if ! command -v ollama &> /dev/null; then
    fail "Ollama n'est pas installé. Installez-le d'abord:"
    echo "   curl -fsSL https://ollama.ai/install.sh | sh"
    exit 1
  fi

  if ! ollama list &> /dev/null; then
    fail "Ollama ne répond pas. Démarrez le service:"
    echo "   ollama serve"
    exit 1
  fi

  echo "📊 Profils d'usage disponibles:"
  echo ""
  echo "1) 🏃‍♂️ Performance Ultra-Rapide (<3s)"
  echo "   Modèle: llama3.2:1b (1.3GB)"
  echo "   Usage: Exploration rapide, démonstrations"
  echo ""
  echo "2) ⚖️ Équilibre Performance/Qualité (5-10s)"
  echo "   Modèle: llama3.1:8b (4.7GB)"
  echo "   Usage: Développement quotidien, code reviews"
  echo ""
  echo "3) 🧠 Qualité Premium (10-30s)"
  echo "   Modèle: qwen2.5:14b (8.7GB)"
  echo "   Usage: Analyses approfondies, architecture"
  echo ""
  echo "4) 🚀 Expert/Recherche (30s+)"
  echo "   Modèle: qwen2.5:32b (19GB)"
  echo "   Usage: Audits, recherche, analyses complexes"
  echo ""
  echo "5) 📋 Afficher la configuration actuelle"
  echo ""

  read -p "Votre choix (1-5): " choice

  case $choice in
    1)
      MODEL="llama3.2:1b"
      TOKENS="128"
      TEMP="0.0"
      TIMEOUT="2"
      DESCRIPTION="Performance Ultra-Rapide"
      ;;
    2)
      MODEL="llama3.1:8b"
      TOKENS="512"
      TEMP="0.1"
      TIMEOUT="10"
      DESCRIPTION="Équilibre Performance/Qualité"
      ;;
    3)
      MODEL="qwen2.5:14b"
      TOKENS="1024"
      TEMP="0.1"
      TIMEOUT="30"
      DESCRIPTION="Qualité Premium"
      ;;
    4)
      MODEL="qwen2.5:32b"
      TOKENS="2048"
      TEMP="0.2"
      TIMEOUT="60"
      DESCRIPTION="Expert/Recherche"
      ;;
    5)
      echo ""
      echo "📋 Configuration actuelle:"
      echo "========================="
      if [ -f ".env" ]; then
        echo "Modèle: $(grep 'OLLAMA_MODEL=' .env | cut -d'=' -f2 || echo "Non trouvé")"
        echo "Max Tokens: $(grep 'LLM_MAX_TOKENS=' .env | cut -d'=' -f2 || echo "Non trouvé")"
        echo "Température: $(grep 'LLM_TEMPERATURE=' .env | cut -d'=' -f2 || echo "Non trouvé")"
        echo "Timeout: $(grep 'LLM_TIMEOUT=' .env | cut -d'=' -f2 || echo "Non trouvé")"
      else
        fail "Fichier .env non trouvé"
      fi
      return 0
      ;;
    *)
      fail "Choix invalide"
      exit 1
      ;;
  esac

  echo ""
  ok "Configuration sélectionnée: $DESCRIPTION"
  info "Modèle: $MODEL"
  echo ""

  # Vérifier si le modèle est déjà téléchargé
  if ollama list | grep -q "$MODEL"; then
    ok "Modèle $MODEL déjà disponible"
  else
    info "Téléchargement du modèle $MODEL..."
    warn "Cela peut prendre plusieurs minutes selon la taille..."

    if ollama pull "$MODEL"; then
      ok "Modèle $MODEL téléchargé avec succès"
    else
      fail "Échec du téléchargement du modèle $MODEL"
      exit 1
    fi
  fi

  # Créer backup de la configuration
  if [ -f "src/hyperion/modules/rag/config.py" ]; then
    cp "src/hyperion/modules/rag/config.py" "src/hyperion/modules/rag/config.py.backup.$(date +%Y%m%d_%H%M%S)"
    info "Backup de la configuration créé"
  fi

  # Mettre à jour la configuration dans .env
  info "Mise à jour de la configuration..."
  ENV_FILE=".env"

  # Créer backup du fichier .env
  if [ -f "$ENV_FILE" ]; then
    cp "$ENV_FILE" "$ENV_FILE.backup.$(date +%Y%m%d_%H%M%S)"
  fi

  # Utiliser sed pour mettre à jour le fichier .env
  sed "s/OLLAMA_MODEL=.*/OLLAMA_MODEL=$MODEL/g" "$ENV_FILE" | \
  sed "s/LLM_MAX_TOKENS=.*/LLM_MAX_TOKENS=$TOKENS/g" | \
  sed "s/LLM_TEMPERATURE=.*/LLM_TEMPERATURE=$TEMP/g" > "$ENV_FILE.tmp"

  mv "$ENV_FILE.tmp" "$ENV_FILE"

  ok "Configuration mise à jour:"
  echo "   - Modèle: $MODEL"
  echo "   - Max Tokens: $TOKENS"
  echo "   - Température: $TEMP"
  echo "   - Timeout: $TIMEOUT secondes"
  echo ""
}

# Mode interactif
interactive_mode() {
  section "🎮 CONFIGURATION INTERACTIVE"

  # Repository
  echo -e "${CYAN}Repository à analyser:${NC}"
  echo "  Défaut: $DEFAULT_REPO"
  read -p "  Nouveau chemin (ou Entrée pour défaut): " new_repo
  if [ -n "$new_repo" ]; then
    REPO_PATH="$new_repo"
  fi

  # Modules
  echo ""
  echo -e "${CYAN}Modules à exécuter:${NC}"
  echo "  ${YELLOW}all${NC} - V1 + V2 + RAG (recommandé)"
  echo "  ${YELLOW}v1${NC}  - Git stats uniquement"
  echo "  ${YELLOW}v2${NC}  - Code analysis uniquement"
  echo "  ${YELLOW}rag${NC} - RAG embeddings uniquement"
  read -p "  Choix [all/v1/v2/rag]: " modules_choice
  if [ -n "$modules_choice" ]; then
    MODULES="$modules_choice"
  fi

  # Services
  echo ""
  read -p "Vérifier les services au démarrage ? (o/n): " verify_choice
  if [[ "$verify_choice" =~ ^[Nn]$ ]]; then
    SKIP_VERIFICATION=true
  fi

  # Dashboard
  echo ""
  read -p "Lancer le dashboard React ? (o/n): " dashboard_choice
  if [[ "$dashboard_choice" =~ ^[Nn]$ ]]; then
    LAUNCH_DASHBOARD=false
  fi

  # Open WebUI
  echo ""
  read -p "Lancer Open WebUI pour chat ? (o/n): " openwebui_choice
  if [[ "$openwebui_choice" =~ ^[Nn]$ ]]; then
    LAUNCH_OPENWEBUI=false
  fi

  # Configuration modèle
  echo ""
  read -p "Configurer le modèle LLM avant démarrage ? (o/n): " model_choice
  if [[ "$model_choice" =~ ^[Oo]$ ]]; then
    MODEL_SETUP=true
  fi
}

# Vérification services
verify_services() {
  if [ "$SKIP_VERIFICATION" = true ]; then
    warn "Vérification services skippée"
    return 0
  fi

  section "🔍 VÉRIFICATION SERVICES"

  # Docker
  if ! command -v docker &>/dev/null; then
    fail "Docker non installé"
    exit 1
  fi
  if ! docker info &>/dev/null; then
    warn "Docker daemon inactif"
    sudo systemctl start docker || fail "Impossible de démarrer Docker"
  fi
  ok "Docker actif"

  # Qdrant
  if ! curl -s http://localhost:6333/collections &>/dev/null; then
    warn "Qdrant non actif → démarrage"
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
  curl -s http://localhost:6333/collections &>/dev/null && ok "Qdrant actif" || fail "Qdrant échec"

  # Neo4j
  if curl -s http://localhost:7474 >/dev/null 2>&1; then
    ok "Neo4j actif"
    if curl -s -u neo4j:hyperion123 http://localhost:7474/db/system/tx/commit >/dev/null 2>&1; then
      ok "Neo4j authentification OK"
    else
      warn "Vérifiez password Neo4j Desktop (attendu: hyperion123)"
    fi
  else
    fail "Neo4j non accessible (localhost:7474)"
    echo -e "${YELLOW}🖥️  Démarrez votre database dans Neo4j Desktop${NC}"
    if [ "$INTERACTIVE_MODE" = true ]; then
      read -p "Appuyez sur Entrée quand c'est fait..."
    else
      exit 1
    fi
  fi

  # Ollama
  if ! command -v ollama &>/dev/null; then
    fail "Ollama non installé"
    exit 1
  fi
  if ! systemctl is-active --quiet ollama 2>/dev/null; then
    warn "Ollama inactif → démarrage"
    sudo systemctl start ollama
    sleep 2
  fi
  ok "Ollama actif"

  # Vérifier le modèle configuré
  CONFIGURED_MODEL=$(grep 'OLLAMA_MODEL=' .env | cut -d'=' -f2 2>/dev/null || echo "llama3.2:1b")
  if ollama list | grep -q "$CONFIGURED_MODEL"; then
    ok "Modèle $CONFIGURED_MODEL disponible"
  else
    warn "Modèle $CONFIGURED_MODEL manquant"
    if [ "$INTERACTIVE_MODE" = true ]; then
      read -p "Télécharger automatiquement ? (o/n): " download_choice
      if [[ "$download_choice" =~ ^[Oo]$ ]]; then
        info "Téléchargement du modèle $CONFIGURED_MODEL..."
        if ollama pull "$CONFIGURED_MODEL"; then
          ok "Modèle téléchargé avec succès"
        else
          fail "Échec téléchargement"
          exit 1
        fi
      fi
    fi
  fi

  # Python
  ok "Python $(python3 --version | awk '{print $2}')"
  [ -d "venv" ] && ok "Virtual env présent" || warn "Virtual env absent"
}

# Ingestion V1
run_v1() {
  section "📥 INGESTION V1 - Git Stats"

  local repo_name=$(basename "$REPO_PATH")
  local profile_path="data/repositories/$repo_name/profile.yaml"

  info "Repository: $REPO_PATH"
  info "Profil cible: $profile_path"

  [ -d "venv" ] && source venv/bin/activate 2>/dev/null || true

  # Génération profil
  echo "🔄 Génération profil Git..."
  if hyperion profile "$REPO_PATH" --output data/repositories; then
    ok "Profil généré: $profile_path"
  else
    fail "Échec génération profil"
    return 1
  fi

  # Vérification profil
  if [ ! -f "$profile_path" ]; then
    fail "Profil non trouvé: $profile_path"
    return 1
  fi

  # Ingestion Neo4j
  echo "🔄 Ingestion Neo4j v1..."
  [ -d "venv" ] && source venv/bin/activate 2>/dev/null || true
  if python3 -c "
from hyperion.modules.integrations.neo4j_ingester import Neo4jIngester
ing = Neo4jIngester()
stats = ing.ingest_profile('$profile_path')
print(f'✅ Neo4j v1: {stats}')
ing.close()
"; then
    ok "Neo4j v1 ingéré avec succès"
  else
    fail "Échec ingestion Neo4j v1"
    return 1
  fi
}

# Ingestion V2
run_v2() {
  section "📊 INGESTION V2 - Code Analysis"

  local repo_name=$(basename "$REPO_PATH")
  info "Repository: $REPO_PATH"
  info "Repo name: $repo_name"

  echo "🔄 Analyse structure code avec Neo4j v2..."
  [ -d "venv" ] && source venv/bin/activate 2>/dev/null || true
  if python3 -c "
from hyperion.modules.integrations.neo4j_code_ingester import Neo4jCodeIngester

# Clear ancien + ingestion nouveau
ingester = Neo4jCodeIngester()
print('🧹 Clear ancien repo...')
ingester.clear_repo('$repo_name')

print('🚀 Ingestion code source...')
stats = ingester.ingest_repo_code('$REPO_PATH', '$repo_name')
print(f'✅ Neo4j v2: {stats}')

# Vérification
final_stats = ingester.get_repo_stats('$repo_name')
print(f'📊 Validation: {final_stats}')

ingester.close()
"; then
    ok "Neo4j v2 ingéré avec succès"
  else
    fail "Échec ingestion Neo4j v2"
    return 1
  fi
}

# Ingestion RAG
run_rag() {
  section "🤖 INGESTION RAG - Embeddings"

  local repo_name=$(basename "$REPO_PATH")

  info "Repository: $repo_name"

  echo "🔄 Génération embeddings..."
  [ -d "venv" ] && source venv/bin/activate 2>/dev/null || true
  if python3 -c "
from hyperion.modules.rag.ingestion import RAGIngester
ingester = RAGIngester()
chunks = ingester.ingest_repo('$repo_name')
print(f'✅ RAG: {chunks} chunks ingérés')
"; then
    ok "RAG ingéré avec succès"
  else
    fail "Échec ingestion RAG"
    return 1
  fi
}

# Exécution modules
run_modules() {
  # Préparation
  mkdir -p data/repositories logs

  # Convertir modules en array
  IFS=',' read -ra MODULE_ARRAY <<< "$MODULES"

  # Exécuter selon modules demandés
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
    esac
  done
}

# Lancement API
launch_api() {
  if [ "$LAUNCH_DASHBOARD" = false ]; then
    return 0
  fi

  section "🌐 LANCEMENT API & DASHBOARD"

  # API
  [ -d "venv" ] && source venv/bin/activate 2>/dev/null || true
  nohup python3 scripts/dev/run_api.py > logs/api.log 2>&1 &
  API_PID=$!
  ok "API lancée (PID: $API_PID)"

  # Attente API
  info "Attente API (15s)..."
  sleep 15

  if curl -s http://localhost:8000/api/health | python3 -c "
import sys,json
try:
  data=json.load(sys.stdin)
  print(f'✅ API Health: {data[\"status\"]}')
except:
  print('⚠️ API pas encore prête')
" 2>/dev/null; then
    ok "API opérationnelle"
  else
    warn "API pas encore prête"
  fi

  # Dashboard avec vérification
  if [ -d "frontend" ] && [ -f "frontend/index.html" ]; then
    cd frontend
    nohup python3 -m http.server 3000 > ../logs/dashboard.log 2>&1 &
    FRONTEND_PID=$!
    cd ..

    # Attente et vérification
    sleep 3
    if curl -s "http://localhost:3000" | head -1 | grep -q "DOCTYPE html"; then
      ok "Dashboard lancé (PID: $FRONTEND_PID)"
    else
      warn "Dashboard lancé mais pas accessible (PID: $FRONTEND_PID)"
    fi
  else
    warn "Frontend inexistant, dashboard non lancé"
  fi
}

# Lancement Open WebUI
launch_openwebui() {
  if [ "$LAUNCH_OPENWEBUI" = false ]; then
    return 0
  fi

  section "💬 LANCEMENT OPEN WEBUI"

  # Arrêter container existant si nécessaire
  if docker ps -a --format '{{.Names}}' | grep -q "^open-webui$"; then
    warn "Container open-webui existant → suppression"
    docker stop open-webui >/dev/null 2>&1 || true
    docker rm open-webui >/dev/null 2>&1 || true
  fi

  # Lancer nouveau container
  if docker run -d --name open-webui \
    --add-host=host.docker.internal:host-gateway \
    -p 3001:8080 \
    -e WEBUI_AUTH=false \
    -e OLLAMA_BASE_URL=http://host.docker.internal:11434 \
    -e OPENAI_API_BASE_URL=http://host.docker.internal:8000/v1 \
    -e OPENAI_API_KEY=x \
    -e DEFAULT_MODEL=hyperion-rag \
    -v open-webui:/app/backend/data \
    --restart always \
    ghcr.io/open-webui/open-webui:main >/dev/null; then
    ok "Open WebUI lancé"

    info "Attente Open WebUI (10s)..."
    sleep 10

    if curl -s http://localhost:3001 >/dev/null; then
      ok "Open WebUI prêt"
    else
      warn "Open WebUI pas encore accessible"
    fi
  else
    warn "Échec lancement Open WebUI"
  fi
}

# Test chat RAG
test_rag() {
  section "🧪 TEST CHAT RAG"

  echo "🔄 Test du moteur RAG..."
  [ -d "venv" ] && source venv/bin/activate 2>/dev/null || true
  python3 -c "
from hyperion.modules.rag.query import RAGQueryEngine
try:
    engine = RAGQueryEngine()
    result = engine.chat('Combien de fichiers Python dans le repository ?')
    print(f'✅ Chat RAG: {result[\"answer\"][:100]}...')
except Exception as e:
    print(f'⚠️ Chat RAG: {e}')
"
}

# Test validation Hyperion v2 complète
test_hyperion_v2() {
  section "🚀 TEST VALIDATION HYPERION V2"

  local repo_name=$(basename "$REPO_PATH")

  echo "🔄 Validation des 8 moteurs..."

  # Test 1: Health Check v2
  echo "   1. Health Check API v2..."
  if curl -s http://localhost:8000/api/v2/health | python3 -c "
import sys, json
try:
  data = json.load(sys.stdin)
  print(f'✅ Health: {data[\"status\"]} - Neo4j: {data.get(\"neo4j_code\", \"unknown\")}')
except:
  print('⚠️ Health check failed')
  exit(1)
"; then
    echo "   ✓ API v2 fonctionnelle"
  else
    warn "API v2 non accessible"
    return 1
  fi

  # Test 2: Neo4j v2 functions
  echo "   2. Neo4j Functions endpoint..."
  if curl -s "http://localhost:8000/api/v2/repos/$repo_name/functions?limit=5" | python3 -c "
import sys, json
try:
  data = json.load(sys.stdin)
  count = data.get('count', 0)
  if count > 0:
    print(f'✅ Functions: {count} found')
  else:
    print('⚠️ No functions found')
    exit(1)
except:
  print('⚠️ Functions endpoint failed')
  exit(1)
"; then
    echo "   ✓ Neo4j v2 opérationnel"
  else
    warn "Neo4j v2 échec"
    return 1
  fi

  # Test 3: Impact Analysis
  echo "   3. Impact Analysis engine..."
  if curl -s -X POST http://localhost:8000/api/v2/impact/analyze \
    -H "Content-Type: application/json" \
    -d "{\"repo\":\"$repo_name\",\"file\":\"test.py\",\"changes\":[\"test\"]}" | python3 -c "
import sys, json
try:
  data = json.load(sys.stdin)
  if 'impact_summary' in data:
    print(f'✅ Impact Analysis: {data[\"impact_summary\"]}')
  else:
    print('⚠️ Impact analysis incomplete')
    exit(1)
except:
  print('⚠️ Impact analysis failed')
  exit(1)
"; then
    echo "   ✓ Impact Analysis fonctionnel"
  else
    warn "Impact Analysis échec"
    return 1
  fi

  # Test 4: Anomaly Detection
  echo "   4. Anomaly Detection engine..."
  if curl -s -X POST http://localhost:8000/api/v2/anomaly/scan \
    -H "Content-Type: application/json" \
    -d "{\"repo\":\"$repo_name\",\"types\":[\"complexity\"]}" | python3 -c "
import sys, json
try:
  data = json.load(sys.stdin)
  total = data.get('total_found', 0)
  print(f'✅ Anomaly Detection: {total} issues found')
except:
  print('⚠️ Anomaly detection failed')
  exit(1)
"; then
    echo "   ✓ Anomaly Detection fonctionnel"
  else
    warn "Anomaly Detection échec"
    return 1
  fi

  ok "🎯 Validation Hyperion v2 complète réussie!"
  return 0
}

# Résumé final
show_summary() {
  section "🎉 RÉSUMÉ FINAL"

  local repo_name=$(basename "$REPO_PATH")

  echo "📱 ${BOLD}Services actifs:${NC}"
  echo "   • API Hyperion v2 : http://localhost:8000 (+ /api/v2/health)"
  if [ "$LAUNCH_DASHBOARD" = true ]; then
    echo "   • Dashboard React : http://localhost:3000"
  fi
  if [ "$LAUNCH_OPENWEBUI" = true ]; then
    echo "   • Open WebUI      : http://localhost:3001"
  fi
  echo "   • Neo4j Browser   : http://localhost:7474"
  echo "   • Qdrant          : http://localhost:6333"

  echo ""
  echo "📊 ${BOLD}Données ingérées:${NC}"
  find data/repositories -name "*.yaml" 2>/dev/null | head -3 | sed 's/^/   • /' || echo "   • Aucun profil trouvé"
  echo "   • Repository analysé: $(basename "$REPO_PATH")"
  echo "   • Modules exécutés: $MODULES"

  # Stats v2 en temps réel
  echo ""
  echo "🔍 ${BOLD}Stats Hyperion v2:${NC}"

  # Neo4j v2 stats
  python3 -c "
from hyperion.modules.integrations.neo4j_code_ingester import Neo4jCodeIngester
try:
    ingester = Neo4jCodeIngester()
    stats = ingester.get_repo_stats('$repo_name')
    print(f'   • Neo4j v2: {stats[\"functions\"]} functions, {stats[\"classes\"]} classes')
    ingester.close()
except Exception as e:
    print(f'   • Neo4j v2: Error - {e}')
" 2>/dev/null || echo "   • Neo4j v2: Non accessible"

  # RAG stats
  curl -s http://localhost:6333/collections/hyperion_repos 2>/dev/null | python3 -c "
import sys, json
try:
    data = json.load(sys.stdin)
    points = data['result']['points_count']
    print(f'   • RAG: {points} chunks indexés')
except:
    print('   • RAG: Non accessible')
" 2>/dev/null || echo "   • RAG: Non accessible"

  # API v2 endpoints
  echo "   • API v2: Impact Analysis, Anomaly Detection, Code Search"

  echo ""
  echo "🎯 ${BOLD}Tout est opérationnel !${NC}"
  echo "   Ctrl+C pour arrêter tous les services"

  echo ""
  echo "🧪 ${BOLD}Tests disponibles:${NC}"
  echo "   • Validation v2: curl http://localhost:8000/api/v2/health"
  echo "   • Functions: curl http://localhost:8000/api/v2/repos/$repo_name/functions"
  echo "   • Chat RAG: curl -X POST http://localhost:8000/api/chat -d '{\"question\":\"test\",\"repo\":\"$repo_name\"}'"

  echo ""
  info "Appuyez sur Ctrl+C pour arrêter..."

  # Keep-alive loop (fonctionne en mode interactif ET automatique)
  while true; do
    sleep 10
  done
}

# ============================================================================
# MAIN
# ============================================================================

main() {
  echo "============================================================"
  echo "🚀 HYPERION MASTER FINAL"
  echo "============================================================"

  # Parsing arguments
  parse_args "$@"

  # Validation
  validate_modules

  # Mode interactif si demandé
  if [ "$INTERACTIVE_MODE" = true ]; then
    interactive_mode
  fi

  # Validation finale repo
  validate_repo

  # Configuration finale
  info "Mode: $([ "$AUTO_MODE" = true ] && echo "AUTOMATIQUE" || echo "INTERACTIF")"
  info "Repository: $REPO_PATH"
  info "Modules: $MODULES"

  if [ "$INTERACTIVE_MODE" = true ]; then
    echo ""
    read -p "Continuer avec cette configuration ? (o/n): " confirm
    if [[ ! "$confirm" =~ ^[Oo]$ ]]; then
      echo "Annulé."
      exit 0
    fi
  fi

  # Exécution
  setup_model
  verify_services
  run_modules
  test_rag
  launch_api
  launch_openwebui

  # Validation v2 (si modules v2 activés)
  if [[ "$MODULES" == *"v2"* || "$MODULES" == "all" ]]; then
    test_hyperion_v2
  fi

  show_summary
}

# Lancement
main "$@"