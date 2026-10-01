---
title: "Hyperion"
toc: true
description: "Plateforme locale d'analyse de dépôts Git : profilage, graphe de code Neo4j, RAG sur Qdrant et Ollama, API REST et CLI."
weight: 1
---

## Glossaire

- **Profil** : fichier `profile.yaml` produit par l'analyse d'un dépôt (commits, contributeurs, hotspots, métriques).
- **Hotspot** : fichier modifié souvent et par beaucoup de contributeurs, donc à risque.
- **RAG** : Retrieval Augmented Generation, réponse LLM appuyée sur des extraits indexés du dépôt.
- **Chunk** : extrait de texte ou de code indexé dans Qdrant pour le RAG.
- **Embedding** : vecteur numérique d'un chunk, calculé par le modèle d'embeddings.
- **Ingestion** : chargement d'un profil ou du code source dans Neo4j et Qdrant.
- **Graphe de code** : nœuds `Function`, `Class`, `File` et leurs relations dans Neo4j.
- **Analyse d'impact** : liste des fonctions touchées par la modification d'un fichier.
- **Anomalie** : fonction ou fichier hors norme (complexité, taille, documentation).
- **Validation qualité** : contrôle automatique d'une réponse RAG (confiance, hallucination, couverture des sources).
- **Feature store** : cache des features ML calculées par fichier.
- **Registre de modèles** : stockage versionné des modèles ML dans `modeles/`.

## 1. Introduction

Hyperion analyse un dépôt Git et le rend interrogeable. Il répond à trois besoins :

- **Comprendre l'historique** : qui travaille sur quoi, quels fichiers bougent le plus, comment le dépôt évolue entre deux tags de production.
- **Comprendre le code** : quelles fonctions existent, comment elles dépendent les unes des autres, ce qu'une modification va impacter.
- **Poser des questions en langage naturel** : un chat RAG répond à partir des profils et du code indexés, avec une validation qualité de chaque réponse.

Tout tourne en local : aucune donnée de code ne quitte la machine. Le LLM est servi par Ollama, les embeddings sont calculés localement.

**Dépendances externes**

| Service | Rôle | Obligatoire |
|---|---|---|
| Neo4j | Graphe des commits et du code | Pour l'ingestion et l'API v2 |
| Qdrant | Index vectoriel du RAG | Pour le chat |
| Ollama | Génération des réponses LLM | Pour le chat |
| Redis | Cache distribué | Non (cache mémoire par défaut) |

Sans ces services, l'analyse Git, la génération de documentation et l'API de base restent utilisables : les endpoints qui en dépendent répondent en erreur explicite.

## 2. Architecture fonctionnelle

```
 Dépôt Git ──► hyperion profile ──► data/repositories/<repo>/profile.yaml
                                          │
                     ┌────────────────────┼─────────────────────┐
                     ▼                    ▼                     ▼
          hyperion generate      hyperion ingest        ingestion RAG
          (doc Markdown/HTML)    (Neo4j : commits,      (Qdrant : chunks
                                  code, relations)       profil + code)
                                          │                     │
                                          └──────────┬──────────┘
                                                     ▼
                                    API FastAPI (port 8000) + CLI
                                    chat RAG, impact, anomalies, qualité
```

**Cas d'usage**

1. **Onboarding** : un nouvel arrivant interroge le chat (« où est gérée l'authentification ? ») au lieu de lire tout le code.
2. **Revue de changement** : avant de modifier un fichier, `POST /api/v2/impact/analyze` liste les fonctions impactées.
3. **Dette technique** : `POST /api/v2/anomaly/scan` remonte les fonctions trop longues ou trop complexes.
4. **Pilotage** : les hotspots et métriques du profil montrent où concentrer les tests.

Chaque réponse du chat passe par la validation qualité. Selon le mode (`VALIDATION_MODE`), une réponse douteuse est signalée (`flag`) ou refusée (`reject`).

## 3. Architecture technique

| Composant | Technologie | Emplacement |
|---|---|---|
| CLI | Click | `src/hyperion/cli/main.py` |
| API REST | FastAPI + Uvicorn | `src/hyperion/api/` |
| Analyse Git | Python + git | `src/hyperion/core/` |
| RAG | Qdrant, sentence-transformers, Ollama | `src/hyperion/modules/rag/` |
| Graphe | Neo4j | `src/hyperion/modules/integrations/` |
| ML | scikit-learn, XGBoost, MLflow | `src/hyperion/modules/ml/` |
| Sécurité | bcrypt, PyJWT, pyotp | `src/hyperion/modules/security/` |
| Monitoring | structlog, Prometheus | `src/hyperion/modules/monitoring/` |
| Dashboard | Node | `frontend/` |

**Topologie (docker-compose)**

| Service | Port |
|---|---|
| hyperion-api | 8000 |
| Métriques Prometheus | 8090 |
| qdrant | 6333, 6334 |
| ollama | 11434 |
| neo4j | 7474 (navigateur), 7687 (bolt) |
| hyperion-dashboard | 3000 |
| open-webui | 3001 |

**Secrets** : uniquement dans `.env` (modèle : `.env.example`), jamais dans le code. Variables sensibles : `NEO4J_PASSWORD=***REDACTED***`, `JWT_SECRET_KEY=***REDACTED***`. gitleaks bloque tout secret en clair dans la CI.

**Arborescence**

```
src/hyperion/
├── api/          # endpoints REST, compatibilité OpenAI
├── cli/          # commande hyperion
├── core/         # analyse Git
├── modules/      # un dossier par domaine (rag, ml, security, monitoring...)
└── settings.py   # configuration centralisée (.env)
modeles/          # modèles ML de référence
data/             # profils et index générés (ignorés par git)
docs/             # cette documentation
```

## 4. Workflow détaillé

1. **Profiler le dépôt**
   ```bash
   hyperion profile /chemin/vers/depot
   ```
   Produit `data/repositories/<repo>/profile.yaml`. En cas d'échec, vérifier que le chemin est un dépôt Git avec au moins un commit.

2. **Générer la documentation** (optionnel)
   ```bash
   hyperion generate data/repositories/<repo>/profile.yaml --format markdown
   ```

3. **Ingérer dans Neo4j**
   ```bash
   hyperion ingest data/repositories/<repo>/profile.yaml
   ```
   Lit `NEO4J_URI`, `NEO4J_USER`, `NEO4J_PASSWORD` dans `.env`. Si Neo4j est injoignable, la commande s'arrête avec une erreur de connexion : rien n'est écrit partiellement.

4. **Indexer pour le RAG**
   ```bash
   python3 scripts/maintenance/ingest_rag.py --repo <repo>
   ```
   Découpe profil et code en chunks, calcule les embeddings et les charge dans Qdrant.

5. **Interroger**
   ```bash
   curl -X POST http://localhost:8000/api/chat \
     -H "Content-Type: application/json" \
     -d '{"question": "Quels sont les hotspots ?", "repo": "<repo>"}'
   ```
   La réponse contient les sources utilisées et, si la validation est active, un bloc `quality` (confiance, note, avertissements).

**Gestion des erreurs** : un service absent renvoie une erreur 500 avec un message explicite (`Erreur Neo4j: ...`). Les connexions Neo4j sont fermées même en cas d'échec.

## 5. Administration et monitoring

**Santé**

```bash
curl -s http://localhost:8000/api/health      # API, Neo4j, RAG
curl -s http://localhost:8000/api/v2/health   # moteurs v2 (Neo4j code)
hyperion status                                # état de tous les services
```

**Logs**

| Fichier | Contenu |
|---|---|
| `logs/hyperion_AAAAMMJJ.log` | logs applicatifs JSON |
| `audit/hyperion_audit.jsonl` | journal d'audit (actions, utilisateurs) |

```bash
tail -f logs/hyperion_$(date +%Y%m%d).log | jq .
```

**Métriques**

- Prometheus : `http://localhost:8090/metrics` (port de `MetricConfig`).
- Qualité RAG : `GET /api/quality/metrics`, `/api/quality/trends`, `/api/quality/alerts`, `/api/quality/stats`.
- Évaluation RAG hors ligne : `hyperion eval --suite eval/suites/core.yaml`.

Les seuils de service sont définis dans [slo](slo).

## 6. Procédures d'exploitation

**Déploiement**

```bash
cp .env.example .env                                   # puis renseigner les secrets
./scripts/docker/hyperion-docker.sh --profile full     # tous les services
./scripts/docker/hyperion-docker.sh --action status
```

**Quotidien**

- Vérifier `/api/health` et `hyperion status`.
- Consulter `/api/quality/alerts` : une alerte signale une dérive de qualité des réponses.

**Maintenance**

```bash
./scripts/docker/hyperion-docker.sh --action restart --service hyperion-api
python3 scripts/cleanup.py                             # fichiers temporaires
```

**Incident** : appliquer le runbook [operations](operations). Ordre de diagnostic : santé API, puis Neo4j, puis Qdrant, puis Ollama.

## 7. Problèmes connus

| Symptôme | Cause | Solution |
|---|---|---|
| Endpoints `/api/v2/*` en 500 | Neo4j injoignable | Démarrer Neo4j, vérifier `NEO4J_URI` et le mot de passe dans `.env` |
| Chat très lent | Modèle Ollama trop lourd pour la machine | Choisir un modèle plus petit (`OLLAMA_MODEL`), voir [choix du modèle](technique/getting-started/model-selection) |
| Chat sans limite de durée | Aucun timeout sur les appels LLM | Connu : `LLM_TIMEOUT` n'est pas appliqué au client Ollama |
| `ImportError` sur `bcrypt`, `pyotp` ou `jwt` | Dépendances de sécurité absentes | `pip install -r requirements.txt` |
| Embeddings en erreur GPU | CUDA indisponible | Bascule automatique sur CPU ; forcer avec `EMBEDDING_DEVICE=cpu` |
| Alertes comportementales nombreuses | Seuil `anomaly_threshold` à 0.7 | Ajuster le seuil à l'instanciation de `BehavioralAnalyzer` |

## 8. Annexes

- [Runbook d'exploitation](operations)
- [Objectifs de service](slo)
- [Cours](cours) : formation en 10 chapitres
- [Documentation technique](technique) : architecture, références CLI et API, développement
- [Déploiement](deployment) : orchestrateur, Docker, mise en place
- [API](api)
- Versions des composants : `docs/data.yaml`
- Historique : `CHANGELOG.md` à la racine du dépôt
