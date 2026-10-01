# Hyperion

[![Code style: black](https://img.shields.io/badge/code%20style-black-000000.svg)](https://github.com/psf/black)
[![Ruff](https://img.shields.io/endpoint?url=https://raw.githubusercontent.com/astral-sh/ruff/main/assets/badge/v2.json)](https://github.com/astral-sh/ruff)
[![Tests](https://img.shields.io/badge/tests-305%20passing-green.svg)](#développement)
[![mypy](https://img.shields.io/badge/mypy-0%20erreur-blue.svg)](#développement)

Plateforme locale d'analyse de dépôts Git : profilage de l'historique, graphe de code Neo4j, chat RAG sur Qdrant et Ollama avec validation qualité des réponses, API REST et CLI. Aucune donnée ne quitte la machine.

## Démarrage rapide

```bash
git clone <repository> && cd Hyperion
cp .env.example .env                          # renseigner NEO4J_PASSWORD et JWT_SECRET_KEY
pip install -r requirements.txt && pip install -e .
./scripts/docker/hyperion-docker.sh --profile full

hyperion profile /chemin/vers/depot           # analyser un dépôt
hyperion ingest data/repositories/<repo>/profile.yaml
curl -s http://localhost:8000/api/health
```

`bcrypt`, `pyotp` et `PyJWT` sont obligatoires : sans eux, le module d'authentification refuse de démarrer au lieu de basculer sur un mode dégradé.

## Développement

```bash
pip install -e ".[all]"
python3 -m pytest                    # suite complète (tests/ + src/hyperion/modules/)
python3 -m black --check src/ tests/
python3 -m ruff check src/ tests/
python3 -m mypy src/
```

La CI exécute black, ruff, la suite de tests et gitleaks ; mypy et bandit tournent en non bloquant.

## Documentation

Toute la documentation est dans [`docs/`](docs/_index.md) :

| Page | Contenu |
|---|---|
| [Accueil](docs/_index.md) | Présentation, architecture, workflow, problèmes connus |
| [Exploitation](docs/operations.md) | Runbook : démarrage, contrôles, diagnostic, incidents |
| [Objectifs de service](docs/slo.md) | SLI, SLO et seuils d'alerte |
| [Versions](docs/data.yaml) | Versions et configuration de référence |
| [Cours](docs/cours/_index.md) | Formation en 10 chapitres |
| [Technique](docs/technique/_index.md) | Architecture, références CLI et API, développement |
| [Déploiement](docs/deployment/_index.md) | Orchestrateur, Docker, mise en place |

Historique des versions : [CHANGELOG.md](CHANGELOG.md).

## Licence

Voir [LICENSE](LICENSE).
