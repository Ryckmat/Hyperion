"""
Tests unitaires pour RiskPredictor.

Auteur: Ryckman Matthieu
Projet: Hyperion (projet personnel)
Version: 2.0.0
"""

from hyperion.modules.impact.predictor import RiskLevel, RiskPredictor


def test_predictor_initialization():
    """Test initialisation du prédicteur."""
    predictor = RiskPredictor()
    assert hasattr(predictor, "feature_names")
    assert len(predictor.feature_names) > 0


def test_extract_features():
    """Test extraction de features."""
    predictor = RiskPredictor()
    features = predictor.extract_features(
        "test.py", {"test.py": {"dep1.py", "dep2.py"}}
    )

    assert "num_impacted_files" in features
    assert "complexity_score" in features
    assert features["num_impacted_files"] == 2


def test_predict_risk_low():
    """Test prédiction risque faible."""
    predictor = RiskPredictor()
    risk = predictor.predict_risk("test.py", {"test.py": set()})

    assert risk == RiskLevel.LOW


def test_predict_risk_medium():
    """Test prédiction risque moyen."""
    predictor = RiskPredictor()
    deps = {f"dep{i}.py" for i in range(7)}
    risk = predictor.predict_risk("test.py", {"test.py": deps})

    assert risk == RiskLevel.MEDIUM


def test_predict_risk_high():
    """Test prédiction risque élevé."""
    predictor = RiskPredictor()
    deps = {f"dep{i}.py" for i in range(15)}
    risk = predictor.predict_risk("test.py", {"test.py": deps})

    assert risk == RiskLevel.HIGH


def test_get_risk_score():
    """Test calcul du score de risque."""
    predictor = RiskPredictor()
    score = predictor.get_risk_score("test.py", {"test.py": set()})

    assert isinstance(score, float)
    assert 0.0 <= score <= 1.0
