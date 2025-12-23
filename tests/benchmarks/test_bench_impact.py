"""
Benchmarks performance pour Impact Analysis.

Auteur: Ryckman Matthieu
Projet: Hyperion (projet personnel)
Version: 2.0.0
"""

import time
from pathlib import Path

import pytest

from hyperion.modules.impact.analyzer import ImpactAnalyzer
from hyperion.modules.impact.predictor import RiskPredictor


@pytest.mark.benchmark
def test_bench_analyze_small_repo(sample_repo, benchmark):
    """Benchmark analyse petit repo (10 fichiers)."""
    analyzer = ImpactAnalyzer(sample_repo)
    
    result = benchmark(analyzer.build_dependency_graph)
    
    assert isinstance(result, dict)
    # Cible: < 1s
    

@pytest.mark.benchmark
@pytest.mark.slow
def test_bench_analyze_large_repo(large_repo, benchmark):
    """Benchmark analyse gros repo (100 fichiers)."""
    analyzer = ImpactAnalyzer(large_repo)
    
    result = benchmark(analyzer.build_dependency_graph)
    
    assert isinstance(result, dict)
    assert len(result) >= 100
    # Cible: < 30s


@pytest.mark.benchmark
def test_bench_predict_risk(sample_repo):
    """Benchmark prédiction risque."""
    analyzer = ImpactAnalyzer(sample_repo)
    graph = analyzer.build_dependency_graph()
    
    predictor = RiskPredictor()
    
    start = time.time()
    for file in graph.keys():
        predictor.predict_risk(file, graph)
    duration = time.time() - start
    
    # Cible: < 0.1s par fichier
    assert duration / len(graph) < 0.1


@pytest.mark.benchmark
def test_bench_get_impacted_files(sample_repo):
    """Benchmark recherche fichiers impactés."""
    analyzer = ImpactAnalyzer(sample_repo)
    analyzer.build_dependency_graph()
    
    files = list(sample_repo.rglob("*.py"))
    
    start = time.time()
    for file in files:
        analyzer.get_impacted_files(file)
    duration = time.time() - start
    
    # Cible: < 0.05s par fichier
    assert duration / len(files) < 0.05
