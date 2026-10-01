---
title: "Impact Analysis Engine"
toc: true
description: "Module : hyperion.modules.impact"
weight: 3
---

**Module** : `hyperion.modules.impact`
**Version** : **Component** : Impact Analysis Engine

---

## Vue d'ensemble

Le module **Impact Analysis Engine** prédit les zones de code impactées par une modification, permettant de :
- Réduire les risques de déploiement
- Identifier les dépendances cachées
- Prioriser les tests nécessaires
- Coordonner les équipes affectées

## Architecture

```
impact/
├── analyzer.py         # Parsing AST + graphe dépendances
├── predictor.py        # ML risk prediction (RF/IF)
├── graph_traversal.py  # Requêtes Neo4j Cypher
└── report.py           # Génération rapports JSON/Markdown
```

## Composants

### 1. ImpactAnalyzer

**Responsabilité** : Analyse statique du code Python via AST.

**Méthodes clés** :
- `analyze_file(file_path)` : Extrait imports, fonctions, classes
- `build_dependency_graph()` : Construit le graphe complet
- `get_impacted_files(modified_file)` : Retourne fichiers affectés

**Exemple d'usage** :
```python
from hyperion.modules.impact import ImpactAnalyzer

analyzer = ImpactAnalyzer("/path/to/repo")
graph = analyzer.build_dependency_graph()
impacted = analyzer.get_impacted_files("utils.py")
```

### 2. RiskPredictor

**Responsabilité** : Prédiction ML du niveau de risque.

**Niveaux de risque** :
- `LOW` : < 5 fichiers impactés
- `MEDIUM` : 5-10 fichiers
- `HIGH` : 10-20 fichiers
- `CRITICAL` : > 20 fichiers

**Features ML** :
- Nombre de fichiers impactés
- Nombre d'appels de fonctions
- Complexité cyclomatique
- Couverture de tests
- Ancienneté de la dernière modification

**Exemple d'usage** :
```python
from hyperion.modules.impact import RiskPredictor

predictor = RiskPredictor()
risk_level = predictor.predict_risk("api.py", dependency_graph)
risk_score = predictor.get_risk_score("api.py", dependency_graph)
```

### 3. GraphTraversal

**Responsabilité** : Requêtes avancées Neo4j.

**Requêtes Cypher** :
- `find_dependencies(file, max_depth)` : Dépendances transitives
- `find_reverse_dependencies(file)` : Qui dépend de ce fichier
- `shortest_path(source, target)` : Plus court chemin
- `get_impact_scope(file)` : Statistiques globales

**Exemple d'usage** :
```python
from hyperion.modules.impact import GraphTraversal

traversal = GraphTraversal("bolt://localhost:7687")
scope = traversal.get_impact_scope("core/api.py")
print(f"Fichiers impactés: {scope['files_depending_on_this']}")
```

### 4. ImpactReport

**Responsabilité** : Génération de rapports structurés.

**Formats supportés** :
- JSON : Machine-readable
- Markdown : Human-readable
- HTML : À venir

**Exemple d'usage** :
```python
from hyperion.modules.impact import ImpactReport

report_gen = ImpactReport()
report = report_gen.create_report(
    file_path="api.py",
    risk_level="high",
    risk_score=0.85,
    impacted_files=["handler.py", "utils.py"],
    dependencies=["config.py"]
)

# Export
report_gen.save_report(report, "reports/impact", format="json")
```

## Workflow complet

```python
from hyperion.modules.impact import (
    ImpactAnalyzer, 
    RiskPredictor, 
    GraphTraversal, 
    ImpactReport
)

# 1. Analyse
analyzer = ImpactAnalyzer("/path/to/repo")
graph = analyzer.build_dependency_graph()

# 2. Prédiction
predictor = RiskPredictor()
risk_level = predictor.predict_risk("modified_file.py", graph)
risk_score = predictor.get_risk_score("modified_file.py", graph)

# 3. Traversal Neo4j (optionnel)
traversal = GraphTraversal()
scope = traversal.get_impact_scope("modified_file.py")

# 4. Rapport
report_gen = ImpactReport()
report = report_gen.create_report(
    file_path="modified_file.py",
    risk_level=risk_level.value,
    risk_score=risk_score,
    impacted_files=list(graph.get("modified_file.py", set())),
    dependencies=scope["dependencies"]
)

# 5. Export
report_gen.save_report(report, "impact_report", format="markdown")
```

## Cas d'usage

### 1. Pre-commit hook

Analyser l'impact avant commit :
```bash
python -m hyperion.modules.impact --files $(git diff --name-only)
```

### 2. Code review

Générer rapport d'impact pour une MR :
```bash
hyperion impact analyze --mr 1234 --output reports/
```

### 3. Estimation d'efforts

Utiliser le risk score pour estimer :
```python
if risk_score > 0.8:
    print("Review senior requise + tests E2E")
elif risk_score > 0.5:
    print("Tests unitaires + intégration")
else:
    print("Tests de base suffisants")
```

## TODO

- [ ] Implémenter modèle ML (Random Forest)
- [ ] Intégration continue Neo4j
- [ ] Support multi-langages (JavaScript, Java)
- [ ] Dashboard visualisation D3.js
- [ ] Alertes temps réel (Slack/Email)

## Références

- AST parsing: `ast` module Python
- ML: `scikit-learn` (Isolation Forest, Random Forest)
- Neo4j: `neo4j` driver Python
- Graph algorithms: Dijkstra, BFS
