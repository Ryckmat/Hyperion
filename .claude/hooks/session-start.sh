#!/bin/bash
# Prépare l'environnement des sessions Claude Code web : dépendances, tests et lint opérationnels.
set -euo pipefail

# Les paquets Debian n'ont pas de RECORD : pip ne peut pas les désinstaller, on les écrase
export PIP_IGNORE_INSTALLED=1

[ "${CLAUDE_CODE_REMOTE:-}" = "true" ] || exit 0
cd "$CLAUDE_PROJECT_DIR"

# Conteneur déjà préparé (reprise de session) : rien à faire
python3 -c "import hyperion, torch, pytest_cov, black, xgboost, bcrypt, pyotp, jwt" 2>/dev/null && exit 0

# torch en version CPU (évite plusieurs Go de CUDA) ; repli sur PyPI si l'index PyTorch est bloqué
if ! python3 -c "import torch" 2>/dev/null; then
  python3 -m pip install -q --retries 0 --timeout 10 --index-url https://download.pytorch.org/whl/cpu torch \
    || python3 -m pip install -q torch
fi
python3 -m pip install -q -r requirements.txt -r requirements-dev.txt
python3 -m pip install -q -e ".[all]"
