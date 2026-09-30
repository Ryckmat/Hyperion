---
name: check
description: Vérifie qu'une modification passe la CI Hyperion (black, ruff, tests). À lancer avant tout commit ou push.
---

Exécuter dans l'ordre, s'arrêter au premier échec et le corriger :

1. `python3 -m black --check src/ tests/` (en cas d'échec : `python3 -m black src/ tests/`)
2. `python3 -m ruff check src/ tests/` (corrections sûres : `python3 -m ruff check --fix src/ tests/`)
3. Tests ciblés sur les modules modifiés (`git diff --name-only`), puis `python3 -m pytest tests/ -m "not slow and not e2e" -q`
4. `python3 -m mypy src/` : signaler les nouvelles erreurs sans bloquer

Terminer par un bilan court : étape, statut, erreurs restantes.
