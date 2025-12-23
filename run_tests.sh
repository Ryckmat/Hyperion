#!/bin/bash
# Script de lancement rapide des tests Hyperion v2
# Auteur: Ryckman Matthieu

set -e

GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m'

echo -e "${GREEN}🧪 Tests Hyperion v2${NC}"
echo ""

# Vérifier pytest installé
if ! command -v pytest &> /dev/null; then
    echo -e "${YELLOW}⚠️  pytest non installé${NC}"
    echo "Installation: pip install pytest pytest-cov pytest-benchmark"
    exit 1
fi

# Menu
echo "Choisissez une option:"
echo "  1) Tests unitaires"
echo "  2) Tests intégration"
echo "  3) Tests E2E"
echo "  4) Tests + Coverage"
echo "  5) Benchmarks"
echo "  6) Tout"
echo ""
read -p "Option [1-6]: " choice

case $choice in
    1)
        echo -e "${GREEN}▶ Tests unitaires${NC}"
        pytest tests/unit/ -v
        ;;
    2)
        echo -e "${GREEN}▶ Tests intégration${NC}"
        pytest tests/integration/ -v
        ;;
    3)
        echo -e "${GREEN}▶ Tests E2E${NC}"
        pytest tests/e2e/ -v -s
        ;;
    4)
        echo -e "${GREEN}▶ Tests + Coverage${NC}"
        pytest tests/ -v --cov=hyperion.modules --cov-report=html --cov-report=term-missing
        echo ""
        echo -e "${GREEN}✅ Rapport coverage: htmlcov/index.html${NC}"
        ;;
    5)
        echo -e "${GREEN}▶ Benchmarks${NC}"
        pytest tests/benchmarks/ -v --benchmark-only
        ;;
    6)
        echo -e "${GREEN}▶ Tous les tests${NC}"
        pytest tests/ -v
        ;;
    *)
        echo "Option invalide"
        exit 1
        ;;
esac

echo ""
echo -e "${GREEN}✅ Terminé !${NC}"
