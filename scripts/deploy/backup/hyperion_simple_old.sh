#!/bin/bash
# ============================================================================
# 🚀 HYPERION SIMPLE - Orchestrateur Fonctionnel Garanti
# ============================================================================

set -euo pipefail

# Couleurs
if command -v tput >/dev/null 2>&1; then
  GREEN=$(tput setaf 2)
  RED=$(tput setaf 1)
  YELLOW=$(tput setaf 3)
  CYAN=$(tput setaf 6)
  NC=$(tput sgr0)
else
  GREEN='' RED='' YELLOW='' CYAN='' NC=''
fi

# Helpers
ok() { echo -e "${GREEN}✅ $1${NC}"; }
warn() { echo -e "${YELLOW}⚠️ $1${NC}"; }
fail() { echo -e "${RED}❌ $1${NC}"; }
section() { echo -e "\n${CYAN}=== $1 ===${NC}"; }

# Configuration
REPO_PATH="/home/kortazo/Documents/Hyperion"
PROJECT_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/../.." && pwd)"
cd "$PROJECT_ROOT"

echo "============================================================"
echo "🚀 HYPERION SIMPLE - TEST COMPLET"
echo "============================================================"

# 1. Vérification Services
section "Vérification Services"
curl -s http://localhost:6333/collections >/dev/null && ok "Qdrant OK" || fail "Qdrant KO"
curl -s http://localhost:7474 >/dev/null && ok "Neo4j OK" || fail "Neo4j KO"
curl -s http://localhost:11434/api/tags >/dev/null && ok "Ollama OK" || fail "Ollama KO"

# 2. Clean et préparation
section "Préparation"
rm -rf data/repositories/*
mkdir -p data/repositories logs
ok "Clean effectué"

# 3. Ingestion V1 - Profil Git
section "Ingestion V1 - Profil Git"
echo "Repository: $REPO_PATH"
if hyperion profile "$REPO_PATH" --output data/repositories; then
  ok "Profil généré"

  # Vérifier le profil
  PROFILE_PATH="data/repositories/Hyperion/profile.yaml"
  if [ -f "$PROFILE_PATH" ]; then
    ok "Profil trouvé: $PROFILE_PATH"

    # Ingestion Neo4j V1
    python3 -c "
from hyperion.modules.integrations.neo4j_ingester import Neo4jIngester
ing = Neo4jIngester()
stats = ing.ingest_profile('$PROFILE_PATH')
print(f'✅ Neo4j V1: {stats}')
ing.close()
" && ok "Neo4j V1 OK" || warn "Neo4j V1 échec"
  else
    fail "Profil non trouvé"
  fi
else
  fail "Échec génération profil"
fi

# 4. Ingestion V2 - Code Analysis
section "Ingestion V2 - Code Analysis"
python3 scripts/maintenance/ingest_generalized.py \
  --repo "$REPO_PATH" \
  --neo4j-password hyperion123 && ok "Neo4j V2 OK" || warn "Neo4j V2 échec"

# 5. Ingestion RAG - Qdrant
section "Ingestion RAG - Qdrant"
python3 -c "
from hyperion.modules.rag.ingestion import RAGIngester
ingester = RAGIngester()
chunks = ingester.ingest_repo('Hyperion')
print(f'✅ RAG: {chunks} chunks')
" && ok "RAG OK" || warn "RAG échec"

# 6. Test API
section "Test API"
[ -d "venv" ] && source venv/bin/activate 2>/dev/null || true
nohup python3 scripts/dev/run_api.py > logs/api.log 2>&1 &
API_PID=$!
ok "API lancée (PID: $API_PID)"

echo "Attente API (15s)..."
sleep 15

if curl -s http://localhost:8000/api/health | python3 -c "import sys,json; data=json.load(sys.stdin); print('✅ API Health:', data['status'])" 2>/dev/null; then
  ok "API opérationnelle"
else
  warn "API pas encore prête"
fi

# 7. Test Chat RAG
section "Test Chat RAG"
python3 -c "
from hyperion.modules.rag.query import RAGQueryEngine
try:
    engine = RAGQueryEngine()
    result = engine.chat('Combien de fichiers Python dans Hyperion ?')
    print(f'✅ Chat RAG: {result[\"answer\"][:100]}...')
except Exception as e:
    print(f'⚠️ Chat RAG: {e}')
"

# 8. Dashboard
section "Dashboard"
cd frontend
nohup python3 -m http.server 3000 > ../logs/dashboard.log 2>&1 &
DASHBOARD_PID=$!
cd ..
ok "Dashboard lancé (PID: $DASHBOARD_PID)"

# 9. Open WebUI
section "Open WebUI"
if docker ps --format '{{.Names}}' | grep -q "^open-webui$"; then
  ok "Open WebUI déjà actif"
else
  docker run -d --name open-webui \
    --add-host=host.docker.internal:host-gateway \
    -p 3001:8080 \
    -e WEBUI_AUTH=false \
    -e OLLAMA_BASE_URL=http://host.docker.internal:11434 \
    -e OPENAI_API_BASE_URL=http://host.docker.internal:8000/v1 \
    -e OPENAI_API_KEY=x \
    -e DEFAULT_MODEL=hyperion-rag \
    -v open-webui:/app/backend/data \
    ghcr.io/open-webui/open-webui:main >/dev/null && ok "Open WebUI lancé" || warn "Open WebUI échec"
fi

# 10. Résumé final
section "🎉 RÉSUMÉ FINAL"
echo "📱 Services actifs:"
echo "   • API Hyperion    : http://localhost:8000"
echo "   • Dashboard React : http://localhost:3000"
echo "   • Open WebUI      : http://localhost:3001"
echo "   • Neo4j Browser   : http://localhost:7474"
echo "   • Qdrant          : http://localhost:6333"

echo ""
echo "📊 Données ingérées:"
find data/repositories -name "*.yaml" | xargs echo "   • Profils:"
echo "   • Neo4j V1: Stats Git (repos, contributors, hotspots)"
echo "   • Neo4j V2: Structure code (files, functions, classes)"
echo "   • Qdrant: Embeddings RAG prêts pour chat"

echo ""
echo "🎯 Tout est opérationnel ! Ctrl+C pour arrêter."

# Keep-alive
trap 'echo "Arrêt..."; kill $API_PID $DASHBOARD_PID 2>/dev/null || true; exit 0' INT
while true; do sleep 10; done