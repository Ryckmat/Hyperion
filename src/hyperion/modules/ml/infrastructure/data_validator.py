"""
Validation des données ML pour assurer qualité et cohérence.

Valide les données d'entrée, features et targets pour les modèles ML.
Détecte les problèmes de qualité, dérive, et anomalies dans les données.
"""

from typing import Any

import numpy as np
import pandas as pd
from pydantic import BaseModel

from .ml_config import ml_config


class ValidationResult(BaseModel):
    """Résultat de validation des données."""

    is_valid: bool
    warnings: list[str] = []
    errors: list[str] = []
    suggestions: list[str] = []

    # Statistiques
    n_samples: int = 0
    n_features: int = 0
    missing_percentage: float = 0.0
    duplicate_percentage: float = 0.0

    # Qualité features
    feature_coverage: dict[str, float] = {}
    feature_types: dict[str, str] = {}

    @property
    def summary(self) -> str:
        """Résumé de validation."""
        status = "✅ VALIDE" if self.is_valid else "❌ INVALIDE"
        return f"{status} | {self.n_samples} échantillons | {self.n_features} features"


class DataValidator:
    """
    Validateur professionnel pour données ML.

    Vérifie:
    - Complétude des features
    - Types de données corrects
    - Valeurs manquantes/aberrantes
    - Distribution des données
    - Dérive de données (data drift)
    """

    def __init__(self):
        """Initialise le validateur."""
        self.expected_features = ml_config.features.all_features
        self.feature_types = self._infer_expected_types()

    def _infer_expected_types(self) -> dict[str, str]:
        """Infère les types attendus pour chaque feature."""
        types = {}

        # Features numériques entières
        integer_features = [
            "nb_methodes",
            "nb_classes",
            "nb_contributeurs_uniques",
            "nb_bugs_historiques",
            "nb_hotfixes",
            "nb_dependances_circulaires",
            "nb_deps_externes",
            "nb_conflits_versions",
            "nb_discussions_pr",
        ]

        # Features numériques flottantes
        float_features = [
            "complexite_cyclomatique",
            "complexite_cognitive",
            "complexite_npath",
            "densite_commentaires",
            "delta_couverture_tests",
            "profondeur_heritage",
            "couplage_entrant",
            "cohesion_classe",
            "indice_maintenabilite",
            "frequence_commits",
            "experience_auteur",
            "volatilite_fichier",
            "profondeur_dependances",
            "risque_breaking_changes",
            "fan_in_fan_out",
            "experience_moyenne_reviewers",
            "vitesse_approbation",
            "distribution_connaissance",
            "facteur_bus",
            "estimation_trafic_affecte",
            "score_impact_revenus",
            "niveau_criticite_module",
            "difficulte_rollback",
        ]

        # Features temporelles (jours)
        temporal_features = ["age_fichier_jours"]

        for feature in self.expected_features:
            if feature in integer_features:
                types[feature] = "integer"
            elif feature in float_features:
                types[feature] = "float"
            elif feature in temporal_features:
                types[feature] = "temporal"
            else:
                types[feature] = "numeric"  # Par défaut

        return types

    def validate_dataframe(
        self, df: pd.DataFrame, target_column: str | None = None
    ) -> ValidationResult:
        """
        Valide un DataFrame complet.

        Args:
            df: DataFrame à valider
            target_column: Colonne target si supervision

        Returns:
            Résultat de validation détaillé
        """
        result = ValidationResult(is_valid=True, n_samples=len(df), n_features=len(df.columns))

        # Validation basique structure
        self._validate_structure(df, result)

        # Validation features spécifiques
        self._validate_features(df, result)

        # Validation qualité données
        self._validate_data_quality(df, result)

        # Validation target si fournie
        if target_column and target_column in df.columns:
            self._validate_target(df[target_column], result)

        # Validation distributions
        self._validate_distributions(df, result)

        # Déterminer validité globale
        result.is_valid = len(result.errors) == 0

        return result

    def validate_features_array(self, X: np.ndarray, feature_names: list[str]) -> ValidationResult:
        """
        Valide un array de features.

        Args:
            X: Array features
            feature_names: Noms des features

        Returns:
            Résultat validation
        """
        # Convertir en DataFrame pour validation uniformisée
        df = pd.DataFrame(X, columns=feature_names)
        return self.validate_dataframe(df)

    def _validate_structure(self, df: pd.DataFrame, result: ValidationResult):
        """Valide la structure générale du DataFrame."""

        # Vérifier taille minimale
        if len(df) < 10:
            result.errors.append(f"Dataset trop petit: {len(df)} échantillons (minimum 10)")

        if len(df.columns) == 0:
            result.errors.append("Aucune colonne dans le dataset")
            return

        # Vérifier duplicatas
        duplicates = df.duplicated().sum()
        duplicate_pct = (duplicates / len(df)) * 100
        result.duplicate_percentage = duplicate_pct

        if duplicate_pct > 10:
            result.warnings.append(f"Beaucoup de duplicatas: {duplicate_pct:.1f}%")
        elif duplicate_pct > 0:
            result.suggestions.append(f"Quelques duplicatas détectés: {duplicate_pct:.1f}%")

    def _validate_features(self, df: pd.DataFrame, result: ValidationResult):
        """Valide les features attendues."""

        missing_features = set(self.expected_features) - set(df.columns)
        extra_features = set(df.columns) - set(self.expected_features)

        # Features manquantes
        if missing_features:
            result.warnings.append(
                f"Features manquantes ({len(missing_features)}): {list(missing_features)[:5]}..."
                if len(missing_features) > 5
                else f"Features manquantes: {list(missing_features)}"
            )

        # Features supplémentaires
        if extra_features:
            result.suggestions.append(
                f"Features supplémentaires détectées: {list(extra_features)[:5]}..."
                if len(extra_features) > 5
                else f"Features supplémentaires: {list(extra_features)}"
            )

        # Couverture des features
        for feature in self.expected_features:
            if feature in df.columns:
                non_null_pct = (1 - df[feature].isna().mean()) * 100
                result.feature_coverage[feature] = non_null_pct

                if non_null_pct < 50:
                    result.errors.append(
                        f"Feature {feature}: trop de valeurs manquantes ({100-non_null_pct:.1f}%)"
                    )
                elif non_null_pct < 80:
                    result.warnings.append(
                        f"Feature {feature}: beaucoup de valeurs manquantes ({100-non_null_pct:.1f}%)"
                    )

    def _validate_data_quality(self, df: pd.DataFrame, result: ValidationResult):
        """Valide la qualité générale des données."""

        # Valeurs manquantes globales
        total_missing = df.isna().sum().sum()
        total_values = df.shape[0] * df.shape[1]
        missing_pct = (total_missing / total_values) * 100
        result.missing_percentage = missing_pct

        if missing_pct > 20:
            result.errors.append(f"Trop de valeurs manquantes: {missing_pct:.1f}%")
        elif missing_pct > 10:
            result.warnings.append(f"Beaucoup de valeurs manquantes: {missing_pct:.1f}%")

        # Validation types de données
        for column in df.columns:
            if column in self.feature_types:
                expected_type = self.feature_types[column]
                self._validate_column_type(df[column], column, expected_type, result)
                result.feature_types[column] = str(df[column].dtype)

    def _validate_column_type(
        self, series: pd.Series, column: str, expected_type: str, result: ValidationResult
    ):
        """Valide le type d'une colonne."""

        # Ignorer valeurs manquantes pour validation type
        non_null_series = series.dropna()

        if len(non_null_series) == 0:
            return

        if expected_type == "integer":
            if not pd.api.types.is_integer_dtype(non_null_series):
                # Vérifier si convertible
                try:
                    pd.to_numeric(non_null_series, downcast="integer")
                except (ValueError, TypeError):
                    result.warnings.append(f"Feature {column}: type attendu integer")

        elif expected_type == "float":
            if not pd.api.types.is_numeric_dtype(non_null_series):
                result.warnings.append(f"Feature {column}: type attendu float")

        elif expected_type == "temporal":
            # Vérifier que les valeurs sont positives pour âge en jours
            if (non_null_series < 0).any():
                result.errors.append(
                    f"Feature {column}: valeurs négatives détectées (âge en jours)"
                )

    def _validate_target(self, target: pd.Series, result: ValidationResult):
        """Valide la colonne target."""

        # Vérifier valeurs manquantes
        missing_target = target.isna().sum()
        if missing_target > 0:
            result.errors.append(f"Target: {missing_target} valeurs manquantes")

        # Vérifier distribution
        unique_values = target.dropna().unique()
        if len(unique_values) < 2:
            result.errors.append("Target: moins de 2 classes uniques")
        elif len(unique_values) > 10:
            result.suggestions.append(f"Target: beaucoup de classes ({len(unique_values)})")

        # Vérifier équilibrage classes
        if len(unique_values) <= 10:  # Classification
            value_counts = target.value_counts()
            min_class_pct = (value_counts.min() / len(target)) * 100

            if min_class_pct < 5:
                result.warnings.append(
                    f"Classes déséquilibrées: classe minoritaire {min_class_pct:.1f}%"
                )

    def _validate_distributions(self, df: pd.DataFrame, result: ValidationResult):
        """Valide les distributions des features."""

        numeric_cols = df.select_dtypes(include=[np.number]).columns

        for col in numeric_cols:
            series = df[col].dropna()
            if len(series) == 0:
                continue

            # Détecter valeurs constantes
            if series.nunique() == 1:
                result.warnings.append(f"Feature {col}: valeur constante")
                continue

            # Détecter outliers extrêmes (> 3 IQR)
            Q1, Q3 = series.quantile([0.25, 0.75])
            IQR = Q3 - Q1

            if IQR > 0:
                outlier_bounds = (Q1 - 3 * IQR, Q3 + 3 * IQR)
                outliers = series[(series < outlier_bounds[0]) | (series > outlier_bounds[1])]
                outlier_pct = (len(outliers) / len(series)) * 100

                if outlier_pct > 5:
                    result.warnings.append(
                        f"Feature {col}: beaucoup d'outliers ({outlier_pct:.1f}%)"
                    )

    def validate_and_prepare_data(
        self, df: pd.DataFrame, target_column: str | None = None, fix_issues: bool = True
    ) -> tuple[pd.DataFrame, ValidationResult]:
        """
        Valide et prépare les données en corrigeant automatiquement certains problèmes.

        Args:
            df: DataFrame original
            target_column: Colonne target
            fix_issues: Corriger automatiquement les problèmes

        Returns:
            DataFrame nettoyé et résultat validation
        """
        # Validation initiale
        result = self.validate_dataframe(df, target_column)

        if not fix_issues:
            return df.copy(), result

        # Copie pour modifications
        df_clean = df.copy()

        # Corrections automatiques
        fixes_applied = []

        # Supprimer duplicatas complets
        if result.duplicate_percentage > 0:
            initial_len = len(df_clean)
            df_clean = df_clean.drop_duplicates()
            removed = initial_len - len(df_clean)
            if removed > 0:
                fixes_applied.append(f"Supprimé {removed} duplicatas")

        # Convertir types si possible
        for col in df_clean.columns:
            if col in self.feature_types:
                expected_type = self.feature_types[col]
                if expected_type in ["integer", "float"]:
                    try:
                        df_clean[col] = pd.to_numeric(df_clean[col], errors="coerce")
                        if expected_type == "integer":
                            df_clean[col] = df_clean[col].round().astype("Int64")
                    except Exception:
                        pass

        # Remplacer valeurs infinies
        numeric_cols = df_clean.select_dtypes(include=[np.number]).columns
        inf_replacements = 0
        for col in numeric_cols:
            inf_mask = np.isinf(df_clean[col])
            if inf_mask.any():
                df_clean.loc[inf_mask, col] = np.nan
                inf_replacements += inf_mask.sum()

        if inf_replacements > 0:
            fixes_applied.append(f"Remplacé {inf_replacements} valeurs infinies par NaN")

        # Ajouter corrections au résultat
        if fixes_applied:
            result.suggestions.extend([f"✓ {fix}" for fix in fixes_applied])

        return df_clean, result

    def detect_data_drift(
        self, reference_df: pd.DataFrame, current_df: pd.DataFrame, threshold: float = 0.1
    ) -> dict[str, Any]:
        """
        Détecte la dérive des données entre deux datasets.

        Args:
            reference_df: Dataset de référence
            current_df: Dataset actuel
            threshold: Seuil de dérive acceptable

        Returns:
            Rapport de dérive détaillé
        """
        drift_report = {
            "has_drift": False,
            "drifted_features": [],
            "drift_scores": {},
            "summary": "",
        }

        common_features = set(reference_df.columns) & set(current_df.columns)

        for feature in common_features:
            if feature in reference_df.select_dtypes(include=[np.number]).columns:
                # Test Kolmogorov-Smirnov pour features numériques
                from scipy import stats

                ref_data = reference_df[feature].dropna()
                curr_data = current_df[feature].dropna()

                if len(ref_data) > 0 and len(curr_data) > 0:
                    ks_stat, p_value = stats.ks_2samp(ref_data, curr_data)

                    drift_report["drift_scores"][feature] = {
                        "ks_statistic": ks_stat,
                        "p_value": p_value,
                        "has_drift": p_value < 0.05,  # Seuil significatif
                    }

                    if p_value < 0.05:
                        drift_report["drifted_features"].append(feature)

        drift_report["has_drift"] = len(drift_report["drifted_features"]) > 0

        if drift_report["has_drift"]:
            drift_report["summary"] = (
                f"Dérive détectée sur {len(drift_report['drifted_features'])} features"
            )
        else:
            drift_report["summary"] = "Aucune dérive significative détectée"

        return drift_report


# Instance globale du validateur
data_validator = DataValidator()
