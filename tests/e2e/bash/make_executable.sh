#!/usr/bin/env bash
# Script pour rendre tous les fichiers .sh exécutables

cd "$(dirname "$0")"

echo "🔧 Ajout permissions exécution..."

chmod +x run_tests_master.sh
chmod +x test_e2e_complete.sh
chmod +x test_services_health.sh
chmod +x test_rag_ingestion.sh
chmod +x test_rag_query.sh
chmod +x test_neo4j_ingestion.sh
chmod +x test_openwebui_function.sh
chmod +x test_performance.sh
chmod +x QUICKSTART.sh
chmod +x utils/common.sh
chmod +x utils/colors.sh

echo "✅ Tous les scripts sont maintenant exécutables !"
echo ""
echo "🚀 Pour lancer les tests :"
echo "   ./run_tests_master.sh"
