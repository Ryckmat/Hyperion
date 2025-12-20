#!/usr/bin/env bash

# ============================================================================
# HYPERION - Guide Rapide Tests E2E
# ============================================================================

cat << 'EOF'

╔════════════════════════════════════════════════════════════════╗
║              🧪 HYPERION - Tests E2E - Guide Rapide            ║
╚════════════════════════════════════════════════════════════════╝

📋 PRÉREQUIS
────────────
✓ Qdrant lancé       : docker run -d -p 6333:6333 qdrant/qdrant
✓ Ollama lancé       : systemctl start ollama
✓ Modèle téléchargé  : ollama pull qwen2.5:32b
✓ Venv créé          : python -m venv venv

🚀 MÉTHODE RECOMMANDÉE : Script Master
──────────────────────────────────────

cd tests/e2e/bash
./run_tests_master.sh

Le script va automatiquement :
  1. Vérifier que Qdrant et Ollama tournent
  2. Lancer l'API Hyperion
  3. Vérifier les données test (propose ingestion si besoin)
  4. Lancer tous les tests E2E
  5. Afficher le rapport final
  6. Proposer le nettoyage

⚡ MÉTHODE MANUELLE : Tests seuls
─────────────────────────────────

Si API déjà lancée et données présentes :

cd tests/e2e/bash
./test_e2e_complete.sh

🔍 TESTS INDIVIDUELS
────────────────────

./test_services_health.sh       # Santé services
./test_rag_ingestion.sh         # Ingestion
./test_rag_query.sh             # Requêtes
./test_neo4j_ingestion.sh       # Neo4j
./test_openwebui_function.sh    # OpenWebUI
./test_performance.sh           # Benchmarks

📊 CRITÈRES DE SUCCÈS
─────────────────────

✓ Tous services accessibles (API, Qdrant, Ollama)
✓ Ingestion réussie (points ajoutés à Qdrant)
✓ Réponses RAG générées
✓ Performance p95 < 15s (tolérance cold start)
✓ Taux succès > 95%

🐛 TROUBLESHOOTING
──────────────────

API non accessible :
  → Vérifier logs : tail -f /tmp/hyperion_api.log
  → Relancer : ./run_tests_master.sh

Performance dégradée :
  → Normal pour première requête (cold start)
  → Requêtes suivantes ~700-900ms

Données manquantes :
  → Script master propose ingestion automatique
  → Ou manuel : curl -X POST http://localhost:8000/api/ingest \
                  -H "Content-Type: application/json" \
                  -d '{"repo_url": "https://github.com/psf/requests.git"}'

📚 DOCUMENTATION COMPLÈTE
─────────────────────────

Voir : README.md
Changelog : CHANGELOG.md

═══════════════════════════════════════════════════════════════════
EOF
