# 🧪 PLAN DE TEST & BENCHMARK HYPERION V2

**Auteur** : Ryckman Matthieu  
**Projet** : Hyperion (projet personnel)  
**Version** : 2.0.0  
**Date** : 23 décembre 2024

---

## 📋 TABLE DES MATIÈRES

1. [Objectifs](#objectifs)
2. [Stratégie de test](#stratégie-de-test)
3. [Tests unitaires](#tests-unitaires)
4. [Tests d'intégration](#tests-dintégration)
5. [Tests E2E](#tests-e2e)
6. [Benchmarks performance](#benchmarks-performance)
7. [Critères d'acceptation](#critères-dacceptation)
8. [Environnement de test](#environnement-de-test)

---

## 1. OBJECTIFS

### Objectifs généraux
- ✅ Valider le bon fonctionnement des 8 modules v2
- ✅ Mesurer les performances (temps réponse, mémoire)
- ✅ Garantir 90%+ de couverture de code
- ✅ Identifier les goulots d'étranglement
- ✅ Valider l'intégration avec services existants (Qdrant, Neo4j, Ollama)

### Métriques cibles

| Métrique | Cible | Critique |
|----------|-------|----------|
| **Coverage tests** | ≥ 90% | Oui |
| **Temps réponse RAG** | < 5s p95 | Oui |
| **Temps analyse impact** | < 3s | Oui |
| **Temps indexation code** | < 10s/100 fichiers | Non |
| **Mémoire RAM** | < 2GB | Non |
| **Tests pass** | 100% | Oui |

---

## 2. STRATÉGIE DE TEST

### Pyramide de tests

```
         /\
        /E2E\         5% - Tests end-to-end
       /------\
      /Intégra-\      15% - Tests intégration
     /----------\
    /  Unitaires \    80% - Tests unitaires
   /--------------\
```

### Priorités

| Priorité | Module | Justification |
|----------|--------|---------------|
| **P0** | Impact Analysis | Feature critique pour v2 |
| **P0** | Code Understanding | Feature critique pour v2 |
| **P1** | Anomaly Detection | Sécurité/RGPD important |
| **P1** | RAG (existant) | Validation non-régression |
| **P2** | Onboarding | Nice-to-have |
| **P2** | Autres modules | Stubs, implémentation future |

---

## 3. TESTS UNITAIRES

### 3.1 Module Impact Analysis

#### Test: `test_impact_analyzer.py`

**Scénarios** :
```python
def test_analyzer_initialization(temp_repo):
    """Vérifie initialisation correcte."""
    
def test_analyze_file_simple(temp_repo):
    """Analyse fichier Python basique."""
    
def test_analyze_file_complex(temp_repo):
    """Analyse fichier avec imports multiples."""
    
def test_extract_imports_various_formats(temp_repo):
    """Test imports: from X import Y, import X as Y."""
    
def test_extract_functions_with_decorators(temp_repo):
    """Test extraction fonctions décorées."""
    
def test_extract_classes_inheritance(temp_repo):
    """Test extraction classes avec héritage."""
    
def test_build_dependency_graph_cyclic(temp_repo):
    """Détection dépendances circulaires."""
    
def test_get_impacted_files_depth(temp_repo):
    """Test impact avec profondeur variable."""
```

**Fixtures** :
```python
@pytest.fixture
def temp_repo(tmp_path):
    """Créé repo test avec structure réaliste."""
    
@pytest.fixture
def complex_codebase(tmp_path):
    """Créé 50+ fichiers interdépendants."""
```

#### Test: `test_impact_predictor.py`

**Scénarios** :
```python
def test_extract_features_complete():
    """Extraction toutes features ML."""
    
def test_predict_risk_thresholds():
    """Validation seuils LOW/MEDIUM/HIGH/CRITICAL."""
    
def test_risk_score_normalization():
    """Score toujours entre 0 et 1."""
    
def test_predict_risk_edge_cases():
    """Cas limites: 0 deps, 1000+ deps."""
```

#### Test: `test_impact_report.py`

**Scénarios** :
```python
def test_create_report_complete():
    """Création rapport avec tous champs."""
    
def test_recommendations_by_risk_level():
    """Recommandations adaptées au risque."""
    
def test_to_json_valid():
    """Export JSON valide."""
    
def test_to_markdown_formatting():
    """Export Markdown bien formaté."""
    
def test_save_report_permissions(tmp_path):
    """Gestion erreurs écriture."""
```

### 3.2 Module Understanding

#### Test: `test_understanding_indexer.py`

**Scénarios** :
```python
def test_index_file_complete():
    """Indexation fichier complet."""
    
def test_extract_docstrings_all_types():
    """Docstrings: module, classe, fonction, méthode."""
    
def test_extract_function_signatures_complex():
    """Signatures: args, kwargs, *args, **kwargs, annotations."""
    
def test_extract_comments_multiline():
    """Commentaires inline et multilignes."""
    
def test_index_repository_large(large_repo):
    """Performance sur gros repo (1000+ fichiers)."""
```

### 3.3 Module Anomaly

#### Test: `test_anomaly_detector.py`

**Scénarios** :
```python
def test_detect_high_complexity():
    """Détection complexité > 15."""
    
def test_detect_long_functions():
    """Détection fonctions > 100 lignes."""
    
def test_extract_metrics_accuracy():
    """Précision métriques calculées."""
    
def test_scan_repository_performance(large_repo):
    """Performance scan complet."""
```

#### Test: `test_anomaly_patterns.py`

**Scénarios** :
```python
def test_detect_sql_injection():
    """Détection SQL concatenation."""
    
def test_detect_hardcoded_secrets():
    """Détection passwords/API keys."""
    
def test_detect_command_injection():
    """Détection os.system/subprocess."""
    
def test_check_rgpd_pii_data():
    """Détection données PII non chiffrées."""
    
def test_generate_report_complete():
    """Rapport avec tous types findings."""
```

### 3.4 Coverage cible

```bash
# Exécution tests unitaires
pytest tests/unit/ -v --cov=hyperion.modules --cov-report=html

# Cible par module
- impact/        : ≥ 90%
- understanding/ : ≥ 90%
- anomaly/       : ≥ 90%
- onboarding/    : ≥ 80%
- autres/        : ≥ 70%
```

---

## 4. TESTS D'INTÉGRATION

### 4.1 Workflow Impact Analysis complet

**Fichier** : `tests/integration/test_impact_flow.py`

**Scénario** :
1. Créer repo test avec 20+ fichiers
2. Analyser avec `ImpactAnalyzer`
3. Prédire risque avec `RiskPredictor`
4. Requêter Neo4j avec `GraphTraversal`
5. Générer rapport avec `ImpactReport`
6. Valider cohérence données

**Assertions** :
```python
assert len(dependency_graph) >= 20
assert risk_level in [RiskLevel.LOW, RiskLevel.MEDIUM, RiskLevel.HIGH, RiskLevel.CRITICAL]
assert 0.0 <= risk_score <= 1.0
assert len(report.recommendations) > 0
```

### 4.2 Pipeline Ingestion généralisé

**Fichier** : `tests/integration/test_ingestion_generalized.py`

**Scénario** :
1. Préparer sources test (Git, Docs, Code)
2. Lancer ingestion complète
3. Vérifier indexation Qdrant
4. Vérifier graphe Neo4j
5. Tester requêtes RAG

**Assertions** :
```python
assert stats['git'] > 0
assert stats['docs'] > 0
assert stats['code'] > 0
# Vérifier Qdrant
collection_info = qdrant_client.get_collection("hyperion")
assert collection_info.points_count > 0
# Vérifier Neo4j
result = neo4j_session.run("MATCH (n) RETURN count(n)")
assert result.single()[0] > 0
```

### 4.3 RAG multi-sources

**Fichier** : `tests/integration/test_rag_multi_sources.py`

**Scénario** :
1. Indexer Git + Code + Docs
2. Requête cross-sources: "Où est le calcul de prix et qui l'a modifié?"
3. Valider réponse combine Git + Code

### 4.4 Neo4j + Impact Analysis

**Fichier** : `tests/integration/test_neo4j_impact.py`

**Scénario** :
1. Ingérer code dans Neo4j
2. Créer relations DEPENDS_ON
3. Requêter via GraphTraversal
4. Comparer résultats AST vs Neo4j

---

## 5. TESTS E2E

### 5.1 Workflow utilisateur complet

**Fichier** : `tests/e2e/test_complete_workflow_v2.py`

**Scénario utilisateur** :
```
GIVEN un nouveau repository
WHEN j'exécute le pipeline complet
THEN je peux:
  1. Analyser l'impact d'une modification
  2. Trouver où une feature est implémentée
  3. Détecter anomalies/patterns dangereux
  4. Générer rapport complet
```

**Étapes** :
```python
def test_complete_v2_workflow(sample_repo):
    # 1. Ingestion
    ingestion = GeneralizedIngestion()
    stats = ingestion.run(repo_path=sample_repo)
    
    # 2. Impact analysis
    analyzer = ImpactAnalyzer(sample_repo)
    graph = analyzer.build_dependency_graph()
    predictor = RiskPredictor()
    risk = predictor.predict_risk("core/api.py", graph)
    
    # 3. Code understanding
    engine = UnderstandingQueryEngine(sample_repo)
    response = engine.query("Où est l'authentification ?")
    
    # 4. Anomaly detection
    detector = AnomalyDetector(sample_repo)
    anomalies = detector.scan_repository()
    
    # 5. Rapports
    assert risk is not None
    assert response['confidence'] > 0.5
    assert len(anomalies) >= 0
```

### 5.2 Test CLI

**Fichier** : `tests/e2e/bash/test_cli_v2.sh`

```bash
#!/bin/bash
# Test CLI Hyperion v2

# Test impact analysis
hyperion impact analyze --file src/api.py --repo /path/to/repo
# Expected: rapport JSON généré

# Test understanding
hyperion understand query "Où est le paiement ?" --repo /path/to/repo
# Expected: liste fichiers + score

# Test ingestion
python scripts/maintenance/ingest_generalized.py --repo /path/to/repo
# Expected: stats affichées
```

---

## 6. BENCHMARKS PERFORMANCE

### 6.1 Impact Analysis

**Script** : `tests/benchmarks/bench_impact.py`

```python
import time
from hyperion.modules.impact import ImpactAnalyzer, RiskPredictor

def bench_analyze_small_repo():
    """Benchmark sur petit repo (10 fichiers)."""
    
def bench_analyze_medium_repo():
    """Benchmark sur repo moyen (100 fichiers)."""
    
def bench_analyze_large_repo():
    """Benchmark sur gros repo (1000 fichiers)."""
    
def bench_predict_risk():
    """Benchmark prédiction risque."""
```

**Métriques** :
```
Repo 10 fichiers   : < 1s
Repo 100 fichiers  : < 3s  ✅ CRITIQUE
Repo 1000 fichiers : < 30s
```

### 6.2 Code Understanding

**Script** : `tests/benchmarks/bench_understanding.py`

```python
def bench_index_repository():
    """Benchmark indexation complète."""
    
def bench_query_engine():
    """Benchmark requête RAG."""
```

**Métriques** :
```
Indexation 100 fichiers : < 10s ✅ CRITIQUE
Query response          : < 5s  ✅ CRITIQUE
```

### 6.3 RAG Performance

**Script** : `tests/benchmarks/bench_rag.py`

```python
def bench_rag_query_simple():
    """Requête simple (1 chunk)."""
    
def bench_rag_query_complex():
    """Requête complexe (10+ chunks)."""
    
def bench_rag_with_filters():
    """Requête avec filtres repository."""
```

**Métriques** :
```
Query simple  : < 1s
Query complex : < 5s  ✅ CRITIQUE
P95 latency   : < 5s  ✅ CRITIQUE
```

### 6.4 Ingestion

**Script** : `tests/benchmarks/bench_ingestion.py`

```python
def bench_ingest_git():
    """Benchmark ingestion Git."""
    
def bench_ingest_code():
    """Benchmark ingestion code analysis."""
    
def bench_ingest_docs():
    """Benchmark ingestion documentation."""
```

**Métriques** :
```
Git 1000 commits   : < 30s
Code 100 fichiers  : < 15s
Docs 50 Markdown   : < 5s
```

---

## 7. CRITÈRES D'ACCEPTATION

### 7.1 Tests

| Critère | Cible | Status |
|---------|-------|--------|
| Tests unitaires pass | 100% | ⏳ |
| Tests intégration pass | 100% | ⏳ |
| Tests E2E pass | 100% | ⏳ |
| Coverage globale | ≥ 90% | ⏳ |
| Coverage impact/ | ≥ 95% | ⏳ |
| Coverage understanding/ | ≥ 95% | ⏳ |

### 7.2 Performance

| Critère | Cible | Status |
|---------|-------|--------|
| RAG query p95 | < 5s | ⏳ |
| Impact analysis | < 3s | ⏳ |
| Indexation 100 fichiers | < 10s | ⏳ |
| Mémoire RAM max | < 2GB | ⏳ |

### 7.3 Qualité code

| Critère | Cible | Status |
|---------|-------|--------|
| Ruff/Black pass | 100% | ⏳ |
| Type hints | 100% | ✅ |
| Docstrings | 100% | ✅ |
| Tests par module | ≥ 1 | ✅ |

---

## 8. ENVIRONNEMENT DE TEST

### 8.1 Configuration

```yaml
# pytest.ini
[pytest]
testpaths = tests
python_files = test_*.py
python_classes = Test*
python_functions = test_*
addopts = 
    -v
    --tb=short
    --cov=hyperion.modules
    --cov-report=html
    --cov-report=term-missing
    --durations=10
markers =
    unit: Tests unitaires
    integration: Tests intégration
    e2e: Tests end-to-end
    slow: Tests lents (> 5s)
    benchmark: Benchmarks performance
```

### 8.2 Services requis

```yaml
# docker-compose.test.yml
version: '3.8'
services:
  qdrant-test:
    image: qdrant/qdrant:v1.7.4
    ports:
      - "6334:6333"
    
  neo4j-test:
    image: neo4j:5.15.0
    environment:
      NEO4J_AUTH: neo4j/testpassword
    ports:
      - "7475:7474"
      - "7688:7687"
```

### 8.3 Fixtures globales

```python
# tests/conftest.py
import pytest
from pathlib import Path

@pytest.fixture(scope="session")
def test_repo_root():
    return Path(__file__).parent.parent

@pytest.fixture(scope="session")
def qdrant_test_client():
    from qdrant_client import QdrantClient
    return QdrantClient(host="localhost", port=6334)

@pytest.fixture(scope="session")
def neo4j_test_driver():
    from neo4j import GraphDatabase
    return GraphDatabase.driver(
        "bolt://localhost:7688",
        auth=("neo4j", "testpassword")
    )

@pytest.fixture
def sample_repo(tmp_path):
    """Créé un repository d'exemple pour tests."""
    # TODO: Implémenter création repo réaliste
    pass
```

---

## 9. PLAN D'EXÉCUTION

### Phase 1 : Tests unitaires (2 jours)

```bash
# Jour 1 : Modules prioritaires
pytest tests/unit/test_impact_*.py -v
pytest tests/unit/test_understanding_*.py -v

# Jour 2 : Autres modules
pytest tests/unit/test_anomaly_*.py -v
pytest tests/unit/test_onboarding_*.py -v
```

### Phase 2 : Tests intégration (1 jour)

```bash
# Lancer services test
docker-compose -f docker-compose.test.yml up -d

# Tests intégration
pytest tests/integration/ -v --maxfail=1

# Cleanup
docker-compose -f docker-compose.test.yml down
```

### Phase 3 : Tests E2E (1 jour)

```bash
# Workflow complet
pytest tests/e2e/ -v -s

# CLI tests
./tests/e2e/bash/test_cli_v2.sh
```

### Phase 4 : Benchmarks (1 jour)

```bash
# Performance tests
pytest tests/benchmarks/ -v --benchmark-only

# Génération rapport
pytest-benchmark compare --csv=benchmarks_v2.csv
```

### Phase 5 : Rapport final (0.5 jour)

```bash
# Coverage complet
pytest --cov=hyperion --cov-report=html

# Rapport qualité
ruff check src/ tests/
mypy src/

# Génération rapport final
python scripts/generate_test_report.py
```

---

## 10. COMMANDES RAPIDES

```bash
# Tests complets
make test

# Tests unitaires seulement
make test-unit

# Tests avec coverage
make test-coverage

# Tests lents exclus
pytest -m "not slow"

# Tests d'un module spécifique
pytest tests/unit/test_impact_analyzer.py -v

# Benchmarks
make benchmark

# Linting
make lint

# Format code
make format

# Tout nettoyer
make clean
```

---

## 11. LIVRABLES

### Rapports attendus

1. **coverage_report.html** : Coverage détaillé par module
2. **benchmark_results.json** : Résultats benchmarks
3. **test_summary.md** : Synthèse pass/fail
4. **performance_analysis.pdf** : Analyse performance

### Dashboards

- **Pytest HTML Report** : Détails tests
- **Coverage.py Dashboard** : Visualisation coverage
- **Benchmark Dashboard** : Graphiques performance

---

## 📊 DASHBOARD SUIVI

| Module | Tests Unit | Tests Integ | Coverage | Perf |
|--------|------------|-------------|----------|------|
| impact | ⏳ 0/8 | ⏳ 0/2 | ⏳ 0% | ⏳ |
| understanding | ⏳ 0/3 | ⏳ 0/1 | ⏳ 0% | ⏳ |
| anomaly | ⏳ 0/3 | ⏳ 0/1 | ⏳ 0% | ⏳ |
| onboarding | ⏳ 0/1 | ⏳ 0/0 | ⏳ 0% | ⏳ |
| **TOTAL** | **⏳ 0/15** | **⏳ 0/4** | **⏳ 0%** | **⏳** |

---

**Prêt à démarrer les tests !** 🧪🚀
