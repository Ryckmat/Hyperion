#!/bin/bash
# HYPERION MASTER - Contrôle TOUT avec sélection

cd /home/kortazo/Documents/Hyperion

echo "============================================================"
echo "🚀 HYPERION MASTER - Contrôle complet"
echo "============================================================"
echo ""

# Demander ce qu'on veut faire
read -p "Installer services (Docker/Qdrant/Ollama/Neo4j) ? (o/n): " do_setup
read -p "Ingérer Neo4j (graphe) ? (o/n): " do_neo4j
read -p "Ingérer RAG (Qdrant) ? (o/n): " do_ingest
read -p "Générer documentation ? (o/n): " do_docs
read -p "Lancer dashboard ? (o/n): " do_dashboard

echo ""
echo "============================================================"
echo "🎯 Récapitulatif"
echo "============================================================"
[[ "$do_setup" =~ ^[Oo]$ ]] && echo "✅ Setup services"
[[ "$do_neo4j" =~ ^[Oo]$ ]] && echo "✅ Ingestion Neo4j"
[[ "$do_ingest" =~ ^[Oo]$ ]] && echo "✅ Ingestion RAG"
[[ "$do_docs" =~ ^[Oo]$ ]] && echo "✅ Génération docs"
[[ "$do_dashboard" =~ ^[Oo]$ ]] && echo "✅ Lancement dashboard"
echo ""

read -p "Confirmer ? (o/n): " confirm
[[ ! "$confirm" =~ ^[Oo]$ ]] && echo "Annulé." && exit 0

echo ""
echo "============================================================"
echo "🚀 EXÉCUTION"
echo "============================================================"

# 1. Setup
if [[ "$do_setup" =~ ^[Oo]$ ]]; then
    echo ""
    echo "📦 1. Setup services..."
    ./scripts/setup_hyperion.sh
fi

# 2. Neo4j
if [[ "$do_neo4j" =~ ^[Oo]$ ]]; then
    echo ""
    echo "🔷 2. Ingestion Neo4j..."
    for profile in data/repositories/*/profile.yaml 2>/dev/null; do
        if [ -f "$profile" ]; then
            REPO=$(basename $(dirname "$profile"))
            echo "   → $REPO"
            python3 -m hyperion.cli.main ingest "$profile" --clear
        fi
    done
fi

# 3. RAG
if [[ "$do_ingest" =~ ^[Oo]$ ]]; then
    echo ""
    echo "📥 3. Ingestion RAG..."
    python3 scripts/ingest_rag.py
fi

# 4. Docs
if [[ "$do_docs" =~ ^[Oo]$ ]]; then
    echo ""
    echo "📝 4. Génération documentation..."
    for profile in data/repositories/*/profile.yaml 2>/dev/null; do
        [ -f "$profile" ] && python3 -m hyperion.cli.main generate "$profile"
    done
fi

# 5. Dashboard
if [[ "$do_dashboard" =~ ^[Oo]$ ]]; then
    echo ""
    echo "🌐 5. Lancement dashboard..."
    python3 scripts/run_dashboard.py
fi

echo ""
echo "============================================================"
echo "🎉 TERMINÉ !"
echo "============================================================"
