# Hyperion

Plateforme d'analyse de dépôts Git : profilage, RAG (Qdrant + Ollama), graphe Neo4j, API FastAPI, CLI Click.

## Structure
- `src/hyperion/core/` : analyse Git (`git_analyzer.py`)
- `src/hyperion/cli/main.py` : CLI `hyperion` (profile, generate, export, ingest, info)
- `src/hyperion/api/` : API FastAPI (`main.py`, `v2_endpoints.py`, `openai_compat.py`)
- `src/hyperion/modules/` : un sous-dossier par domaine (rag, anomaly, impact, quality, gateway, cache, security, ml...)
- `tests/` : `unit/`, `integration/`, `api/`, `rag/`, `e2e/`, `benchmarks/`, `validation/`
- `eval/` : évaluation RAG (`eval/run.py`, suites YAML dans `eval/suites/`)
- `scripts/` : déploiement, docker, setup, maintenance
- `modeles/`, `mlruns/`, `models/` : artefacts ML, ne pas modifier à la main

## Commandes
```bash
pip install -e ".[all]"                  # installation dev
python3 -m pytest tests/unit -q                     # tests rapides
python3 -m pytest tests/ -m "not slow and not e2e"  # hors tests lents
python3 -m black --check src/ tests/                # format (CI)
python3 -m ruff check src/ tests/                   # lint (CI)
python3 -m mypy src/                                # typage (non bloquant en CI)
```
Toujours passer par `python3 -m` : les binaires `pytest`/`ruff` du PATH peuvent venir d'un autre environnement.
La CI (`.github/workflows/ci.yml`) exécute black, ruff, pytest et gitleaks : les faire passer en local avant de pousser.

## Conventions
- Python >= 3.10, lignes de 100 caractères, black + ruff (isort, bugbear, pyupgrade)
- Docstrings et messages utilisateur en français
- `pytest.ini` est prioritaire sur `[tool.pytest.ini_options]` de `pyproject.toml`
- Marqueurs pytest stricts : `unit`, `integration`, `e2e`, `slow`, `benchmark`
- Services externes (Neo4j, Qdrant, Ollama) : toujours mockés dans les tests unitaires
- Configuration via `.env` (modèle : `.env.example`) ; aucun secret en clair, gitleaks tourne en CI
- Pas de tiret cadratin dans la doc ni les messages
