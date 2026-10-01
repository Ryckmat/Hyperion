---
title: "Objectifs de service"
toc: true
description: "Indicateurs (SLI), objectifs (SLO) et seuils d'alerte d'Hyperion, alignés sur la suite d'évaluation RAG."
weight: 3
---

## Principes

- Un **SLI** est une mesure (latence, taux de succès), un **SLO** est l'objectif fixé sur cette mesure.
- Chaque SLO a un seuil **d'alerte** (dégradation) et un seuil **critique** (intervention immédiate).
- Les seuils qualité RAG sont ceux de `eval/suites/core.yaml` : la documentation et l'évaluation restent alignées.
- Fenêtre de mesure par défaut : 7 jours glissants.

## Disponibilité

| SLI | Mesure | SLO | Alerte | Critique |
|---|---|---|---|---|
| API disponible | `GET /api/health` en 200 | 99 % | < 99 % | < 95 % |
| Moteurs code disponibles | `GET /api/v2/health` sans erreur Neo4j | 99 % | < 99 % | < 95 % |
| Chat disponible | `POST /api/chat` hors erreur 5xx | 98 % | < 98 % | < 90 % |

Hyperion tourne en local : ces objectifs couvrent les heures d'utilisation, pas une astreinte 24/7.

## Latence

| SLI | Mesure | SLO | Alerte | Critique |
|---|---|---|---|---|
| Réponse chat RAG | `latency_ms` (p95) | < 5 s | > 5 s | > 10 s |
| Requête graphe Neo4j | endpoints `/api/v2/*` (p95) | < 1 s | > 1 s | > 3 s |
| Health check | `/api/health` (p95) | < 500 ms | > 500 ms | > 2 s |

## Qualité des réponses RAG

| SLI | Source | SLO | Alerte | Critique |
|---|---|---|---|---|
| Confiance | `confidence_score` | ≥ 0.7 | < 0.7 | < 0.5 |
| Couverture des sources | `source_coverage` | ≥ 0.6 | < 0.6 | < 0.3 |
| Taux d'hallucination | `hallucination_rate` | ≤ 0.2 | > 0.2 | > 0.5 |
| Pertinence | `relevance_score` | ≥ 0.7 | < 0.7 | < 0.5 |

Mesure en continu via `GET /api/quality/metrics`, et hors ligne via :

```bash
hyperion eval --suite eval/suites/core.yaml
```

## Qualité du code

| SLI | Mesure | SLO |
|---|---|---|
| Tests | `python3 -m pytest` | 100 % réussis |
| Typage | `python3 -m mypy src/` | 0 erreur |
| Lint et format | `ruff check`, `black --check` | 0 erreur |
| Secrets | gitleaks en CI | 0 fuite |

Ces contrôles bloquent la fusion d'une MR, sauf mypy et bandit qui tournent en non bloquant dans la CI.

## Réaction aux dépassements

| Niveau | Action |
|---|---|
| Alerte | Analyser dans la semaine : tendance via `/api/quality/trends`, puis évaluation complète |
| Critique | Appliquer le runbook [operations](operations) sans attendre |
| Dépassement répété | Revoir le seuil ou ouvrir un chantier d'amélioration (modèle, indexation, prompts) |
