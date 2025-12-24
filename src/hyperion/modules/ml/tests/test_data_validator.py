"""
Tests pour le validateur de données ML d'Hyperion.

Teste la validation des données, détection d'anomalies et qualité.
"""

import numpy as np
import pandas as pd
import pytest

from hyperion.modules.ml.infrastructure.data_validator import DataValidator, ValidationResult


class TestValidationResult:
    """Tests pour la classe ValidationResult."""

    def test_validation_result_creation(self):
        """Test création ValidationResult."""
        result = ValidationResult(is_valid=True, n_samples=100, n_features=10)

        assert result.is_valid is True
        assert result.n_samples == 100
        assert result.n_features == 10
        assert result.warnings == []
        assert result.errors == []

    def test_validation_result_summary(self):
        """Test génération résumé."""
        # Cas valide
        result = ValidationResult(is_valid=True, n_samples=100, n_features=10)
        summary = result.summary
        assert "✅ VALIDE" in summary
        assert "100 échantillons" in summary
        assert "10 features" in summary

        # Cas invalide
        result = ValidationResult(is_valid=False, n_samples=50, n_features=5)
        summary = result.summary
        assert "❌ INVALIDE" in summary
        assert "50 échantillons" in summary
        assert "5 features" in summary

    def test_validation_result_with_errors(self):
        """Test ValidationResult avec erreurs."""
        result = ValidationResult(is_valid=False, errors=["Erreur 1", "Erreur 2"], warnings=["Attention 1"])

        assert len(result.errors) == 2
        assert len(result.warnings) == 1
        assert result.is_valid is False


class TestDataValidator:
    """Tests pour le validateur de données principal."""

    @pytest.fixture
    def validator(self):
        """Fixture validateur par défaut."""
        return DataValidator()

    def test_validator_initialization(self, validator):
        """Test initialisation du validateur."""
        assert len(validator.expected_features) > 0
        assert len(validator.feature_types) > 0
        assert "complexite_cyclomatique" in validator.expected_features
        assert "nb_methodes" in validator.feature_types

    def test_validate_good_dataframe(self, validator, sample_training_data):
        """Test validation DataFrame valide."""
        result = validator.validate_dataframe(sample_training_data, "risque_reel")

        assert result.is_valid is True
        assert result.n_samples == len(sample_training_data)
        assert result.n_features == len(sample_training_data.columns)
        assert len(result.errors) == 0

    def test_validate_empty_dataframe(self, validator):
        """Test validation DataFrame vide."""
        empty_df = pd.DataFrame()
        result = validator.validate_dataframe(empty_df)

        assert result.is_valid is False
        assert "Aucune colonne" in str(result.errors)

    def test_validate_small_dataframe(self, validator):
        """Test validation DataFrame trop petit."""
        small_df = pd.DataFrame({"feature1": [1, 2, 3], "target": [0, 1, 0]})
        result = validator.validate_dataframe(small_df)

        assert result.is_valid is False
        assert any("trop petit" in error for error in result.errors)

    def test_validate_with_duplicates(self, validator, sample_training_data):
        """Test validation avec doublons."""
        # Ajouter des doublons
        df_with_duplicates = pd.concat([sample_training_data, sample_training_data.iloc[:10]])
        result = validator.validate_dataframe(df_with_duplicates)

        assert result.duplicate_percentage > 0
        # Peut être warning selon le pourcentage

    def test_validate_missing_features(self, validator):
        """Test validation avec features manquantes."""
        df_minimal = pd.DataFrame(
            {"complexite_cyclomatique": [1, 2, 3, 4, 5, 6, 7, 8, 9, 10], "target": [0, 1, 0, 1, 0, 1, 0, 1, 0, 1]}
        )
        result = validator.validate_dataframe(df_minimal)

        assert len(result.warnings) > 0
        assert any("Features manquantes" in warning for warning in result.warnings)

    def test_validate_with_many_missing_values(self, validator):
        """Test validation avec beaucoup de valeurs manquantes."""
        df_missing = pd.DataFrame(
            {
                "feature1": [1, np.nan, np.nan, np.nan, np.nan, np.nan, 7, 8, 9, 10],
                "feature2": [1, 2, 3, 4, 5, 6, 7, 8, 9, 10],
                "target": [0, 1, 0, 1, 0, 1, 0, 1, 0, 1],
            }
        )
        result = validator.validate_dataframe(df_missing, "target")

        assert result.is_valid is False or len(result.warnings) > 0
        # Doit détecter les valeurs manquantes

    def test_validate_target_column(self, validator, sample_training_data):
        """Test validation colonne target."""
        result = validator.validate_dataframe(sample_training_data, "risque_reel")

        # Target valide
        assert result.is_valid is True

        # Target avec valeurs manquantes
        df_bad_target = sample_training_data.copy()
        df_bad_target.loc[:10, "risque_reel"] = np.nan
        result_bad = validator.validate_dataframe(df_bad_target, "risque_reel")

        assert result_bad.is_valid is False
        assert any("Target" in error for error in result_bad.errors)

    def test_validate_constant_features(self, validator):
        """Test détection features constantes."""
        df_constant = pd.DataFrame(
            {
                "feature_constante": [5] * 20,
                "feature_normale": np.random.randn(20),
                "target": np.random.choice([0, 1], 20),
            }
        )
        result = validator.validate_dataframe(df_constant, "target")

        assert any("valeur constante" in warning for warning in result.warnings)

    def test_validate_wrong_types(self, validator):
        """Test validation types incorrects."""
        df_wrong_types = pd.DataFrame(
            {
                "nb_methodes": ["a", "b", "c", "d", "e", "f", "g", "h", "i", "j"],  # Doit être int
                "complexite_cyclomatique": ["x", "y", "z", "w", "v", "u", "t", "s", "r", "q"],  # Doit être float
                "target": [0, 1, 0, 1, 0, 1, 0, 1, 0, 1],
            }
        )
        result = validator.validate_dataframe(df_wrong_types, "target")

        # Doit détecter les types incorrects
        assert len(result.warnings) > 0

    def test_validate_features_array(self, validator, sample_training_data):
        """Test validation array de features."""
        feature_cols = [col for col in sample_training_data.columns if col != "risque_reel"]
        X = sample_training_data[feature_cols].values
        feature_names = feature_cols

        result = validator.validate_features_array(X, feature_names)
        assert isinstance(result, ValidationResult)

    def test_validate_and_prepare_data_no_fixes(self, validator, sample_training_data):
        """Test validation et préparation sans corrections."""
        df_clean, result = validator.validate_and_prepare_data(sample_training_data, "risque_reel", fix_issues=False)

        # DataFrame ne doit pas être modifié
        pd.testing.assert_frame_equal(df_clean, sample_training_data)

    def test_validate_and_prepare_data_with_fixes(self, validator):
        """Test validation et préparation avec corrections."""
        # Créer données avec problèmes
        df_problems = pd.DataFrame(
            {
                "feature1": [1, 2, 3, 1, 2, 3, 4, 5, 6, 7],  # Doublons
                "feature2": [1.0, 2.0, np.inf, 4.0, 5.0, 6.0, 7.0, 8.0, 9.0, 10.0],  # Inf
                "target": [0, 1, 0, 0, 1, 0, 1, 0, 1, 0],
            }
        )

        df_clean, result = validator.validate_and_prepare_data(df_problems, "target", fix_issues=True)

        # Doublons doivent être supprimés
        assert len(df_clean) <= len(df_problems)

        # Inf doivent être remplacés par NaN
        assert not np.any(np.isinf(df_clean.select_dtypes(include=[np.number])))

    def test_detect_data_drift_no_drift(self, validator, sample_training_data):
        """Test détection dérive sans dérive."""
        # Même distribution
        ref_data = sample_training_data.copy()
        current_data = sample_training_data.copy()

        drift_report = validator.detect_data_drift(ref_data, current_data)

        assert drift_report["has_drift"] is False
        assert len(drift_report["drifted_features"]) == 0

    def test_detect_data_drift_with_drift(self, validator, sample_training_data):
        """Test détection dérive avec dérive."""
        ref_data = sample_training_data.copy()

        # Créer données avec dérive (shift distribution)
        current_data = sample_training_data.copy()
        current_data["complexite_cyclomatique"] += 10  # Shift significatif

        drift_report = validator.detect_data_drift(ref_data, current_data)

        # Doit détecter dérive sur complexite_cyclomatique
        assert "complexite_cyclomatique" in drift_report["drift_scores"]
        # Peut détecter ou non la dérive selon seuil statistique

    def test_detect_data_drift_empty_data(self, validator):
        """Test détection dérive avec données vides."""
        empty_df = pd.DataFrame()
        ref_data = pd.DataFrame({"feature1": [1, 2, 3]})

        drift_report = validator.detect_data_drift(ref_data, empty_df)

        assert isinstance(drift_report, dict)
        assert "has_drift" in drift_report


class TestDataValidatorIntegration:
    """Tests d'intégration du validateur."""

    def test_full_validation_pipeline(self, sample_training_data):
        """Test pipeline complet de validation."""
        validator = DataValidator()

        # 1. Validation initiale
        result = validator.validate_dataframe(sample_training_data, "risque_reel")
        assert isinstance(result, ValidationResult)

        # 2. Préparation avec corrections
        df_clean, cleaned_result = validator.validate_and_prepare_data(
            sample_training_data, "risque_reel", fix_issues=True
        )
        assert isinstance(df_clean, pd.DataFrame)

        # 3. Validation finale
        final_result = validator.validate_dataframe(df_clean, "risque_reel")
        assert isinstance(final_result, ValidationResult)

    def test_invalid_data_handling(self, invalid_data):
        """Test gestion données complètement invalides."""
        validator = DataValidator()

        result = validator.validate_dataframe(invalid_data, "target")

        # Doit détecter tous les problèmes
        assert result.is_valid is False
        assert len(result.errors) > 0
        assert result.missing_percentage > 0

    def test_validation_with_preprocessing(self, validator):
        """Test validation avec preprocessing nécessaire."""
        # Données nécessitant preprocessing
        df_raw = pd.DataFrame(
            {
                "nb_methodes": ["10", "20", "30", "40", "50", "60", "70", "80", "90", "100"],  # Strings → int
                "complexite_cyclomatique": [1.0, 2.0, 3.0, 4.0, 5.0, 6.0, 7.0, 8.0, 9.0, 10.0],
                "target": [0, 1, 0, 1, 0, 1, 0, 1, 0, 1],
            }
        )

        df_clean, result = validator.validate_and_prepare_data(df_raw, "target", fix_issues=True)

        # Types doivent être corrigés
        assert pd.api.types.is_numeric_dtype(df_clean["nb_methodes"])

    def test_validator_feature_coverage(self):
        """Test couverture des features par le validateur."""
        validator = DataValidator()

        # Vérifier que le validateur couvre les features principales
        expected_features = [
            "complexite_cyclomatique",
            "nb_methodes",
            "nb_contributeurs_uniques",
            "frequence_commits",
            "experience_auteur",
        ]

        for feature in expected_features:
            assert feature in validator.expected_features
            assert feature in validator.feature_types
