"""
Feature Engineer pour préparation avancée des données ML.

Génère et transforme les features pour l'entraînement des modèles.
"""

from datetime import datetime

import numpy as np
import pandas as pd

from ..infrastructure.ml_config import ml_config


class FeatureEngineer:
    """
    Générateur et transformateur de features pour ML.

    Responsabilités:
    - Extraction features depuis données brutes
    - Feature engineering avancé
    - Normalisation et scaling
    - Création features temporelles
    """

    def __init__(self):
        """Initialise le feature engineer."""
        self.config = ml_config
        self.feature_transformers = {}

    def extract_basic_features(self, data: dict) -> dict:
        """
        Extrait les features de base depuis les données brutes.

        Args:
            data: Données brutes du repository

        Returns:
            Dictionnaire des features extraites
        """
        features = {}

        # Features qualité code (si disponibles)
        if "code_analysis" in data:
            code_data = data["code_analysis"]
            features.update(
                {
                    "complexite_cyclomatique": code_data.get(
                        "cyclomatic_complexity", 0
                    ),
                    "nb_methodes": code_data.get("method_count", 0),
                    "nb_classes": code_data.get("class_count", 0),
                    "densite_commentaires": code_data.get("comment_ratio", 0.0),
                    "profondeur_heritage": code_data.get("inheritance_depth", 0),
                }
            )

        # Features équipe (si disponibles)
        if "team_data" in data:
            team_data = data["team_data"]
            features.update(
                {
                    "nb_contributeurs_uniques": len(team_data.get("contributors", [])),
                    "experience_moyenne_reviewers": team_data.get(
                        "avg_reviewer_experience", 0
                    ),
                    "distribution_connaissance": team_data.get(
                        "knowledge_distribution", 0
                    ),
                }
            )

        # Features historiques (si disponibles)
        if "history" in data:
            history = data["history"]
            features.update(
                {
                    "nb_bugs_historiques": history.get("bug_count", 0),
                    "nb_hotfixes": history.get("hotfix_count", 0),
                    "frequence_commits": history.get("commit_frequency", 0),
                }
            )

        return features

    def engineer_temporal_features(
        self, data: dict, reference_date: datetime | None = None
    ) -> dict:
        """
        Génère des features temporelles.

        Args:
            data: Données avec timestamps
            reference_date: Date de référence (maintenant si None)

        Returns:
            Features temporelles
        """
        if reference_date is None:
            reference_date = datetime.now()

        features = {}

        # Âge du fichier
        if "creation_date" in data:
            creation_date = pd.to_datetime(data["creation_date"])
            age_days = (reference_date - creation_date).days
            features["age_fichier_jours"] = max(0, age_days)

        # Temps depuis dernière modification
        if "last_modified" in data:
            last_modified = pd.to_datetime(data["last_modified"])
            days_since_change = (reference_date - last_modified).days
            features["jours_depuis_modif"] = max(0, days_since_change)

        # Activité récente
        if "recent_commits" in data:
            recent_commits = data["recent_commits"]
            features["commits_30j"] = len(
                [
                    c
                    for c in recent_commits
                    if (reference_date - pd.to_datetime(c["date"])).days <= 30
                ]
            )
            features["commits_7j"] = len(
                [
                    c
                    for c in recent_commits
                    if (reference_date - pd.to_datetime(c["date"])).days <= 7
                ]
            )

        return features

    def engineer_risk_features(self, data: dict) -> dict:
        """
        Génère des features spécifiques au risque.

        Args:
            data: Données du repository

        Returns:
            Features de risque
        """
        features = {}

        # Complexité et maintenabilité
        if "code_metrics" in data:
            metrics = data["code_metrics"]

            # Score de complexité composite
            complexity_score = (
                metrics.get("cyclomatic_complexity", 0) * 0.4
                + metrics.get("cognitive_complexity", 0) * 0.3
                + metrics.get("npath_complexity", 0) * 0.3
            )
            features["score_complexite_composite"] = complexity_score

            # Ratio test/code
            if metrics.get("code_lines", 0) > 0:
                test_ratio = metrics.get("test_lines", 0) / metrics.get("code_lines", 1)
                features["ratio_test_code"] = min(test_ratio, 2.0)  # Cap à 200%

            # Indice maintenabilité
            features["indice_maintenabilite"] = metrics.get("maintainability_index", 0)

        # Dépendances et couplage
        if "dependencies" in data:
            deps = data["dependencies"]
            features["nb_deps_externes"] = len(deps.get("external", []))
            features["nb_deps_internes"] = len(deps.get("internal", []))
            features["profondeur_dependances"] = deps.get("max_depth", 0)

        # Impact business estimé
        if "business_context" in data:
            business = data["business_context"]
            features["estimation_trafic_affecte"] = business.get("traffic_impact", 0)
            features["score_impact_revenus"] = business.get("revenue_impact", 0)
            features["niveau_criticite_module"] = business.get("criticality_level", 0)

        return features

    def create_interaction_features(self, features: dict) -> dict:
        """
        Crée des features d'interaction entre features existantes.

        Args:
            features: Features de base

        Returns:
            Features d'interaction
        """
        interaction_features = {}

        # Interaction complexité x taille équipe
        if (
            "complexite_cyclomatique" in features
            and "nb_contributeurs_uniques" in features
        ):
            complexity = features["complexite_cyclomatique"]
            team_size = max(features["nb_contributeurs_uniques"], 1)
            interaction_features["complexite_par_contributeur"] = complexity / team_size

        # Interaction fréquence commits x expérience
        if "frequence_commits" in features and "experience_auteur" in features:
            freq = features["frequence_commits"]
            exp = max(features["experience_auteur"], 1)
            interaction_features["velocite_ajustee_experience"] = freq * np.log1p(exp)

        # Ratio bugs/taille
        if "nb_bugs_historiques" in features and "nb_methodes" in features:
            bugs = features["nb_bugs_historiques"]
            size = max(features["nb_methodes"], 1)
            interaction_features["densite_bugs"] = bugs / size

        # Score risque composite
        risk_components = []
        if "complexite_cyclomatique" in features:
            risk_components.append(
                features["complexite_cyclomatique"] / 20
            )  # Normaliser
        if "nb_bugs_historiques" in features:
            risk_components.append(features["nb_bugs_historiques"] / 10)
        if "age_fichier_jours" in features:
            risk_components.append(features["age_fichier_jours"] / 365)

        if risk_components:
            interaction_features["score_risque_composite"] = np.mean(risk_components)

        return interaction_features

    def normalize_features(self, features: dict) -> dict:
        """
        Normalise les features pour l'entraînement ML.

        Args:
            features: Features brutes

        Returns:
            Features normalisées
        """
        normalized = features.copy()

        # Définir les plages normales pour chaque feature
        feature_ranges = {
            "complexite_cyclomatique": (1, 20),
            "nb_methodes": (1, 100),
            "densite_commentaires": (0, 1),
            "nb_contributeurs_uniques": (1, 50),
            "frequence_commits": (0, 10),
            "experience_auteur": (0, 10),
            "age_fichier_jours": (0, 1825),  # 5 ans max
        }

        # Appliquer normalisation
        for feature_name, value in features.items():
            if feature_name in feature_ranges:
                min_val, max_val = feature_ranges[feature_name]
                # Normalisation min-max avec clipping
                normalized_value = (value - min_val) / (max_val - min_val)
                normalized[feature_name] = np.clip(normalized_value, 0, 1)

        return normalized

    def handle_missing_features(
        self, features: dict, target_features: list[str]
    ) -> dict:
        """
        Gère les features manquantes avec des valeurs par défaut.

        Args:
            features: Features disponibles
            target_features: Features attendues

        Returns:
            Features complétées
        """
        complete_features = features.copy()

        # Valeurs par défaut pour features manquantes
        default_values = {
            # Code quality
            "complexite_cyclomatique": 5.0,
            "complexite_cognitive": 3.0,
            "nb_methodes": 10,
            "nb_classes": 3,
            "densite_commentaires": 0.15,
            "profondeur_heritage": 2,
            # Team dynamics
            "nb_contributeurs_uniques": 3,
            "experience_auteur": 2.0,
            "experience_moyenne_reviewers": 2.5,
            "distribution_connaissance": 0.5,
            # Historical
            "nb_bugs_historiques": 2,
            "nb_hotfixes": 0,
            "frequence_commits": 1.0,
            "volatilite_fichier": 0.3,
            # Temporal
            "age_fichier_jours": 30,
            # Business impact
            "estimation_trafic_affecte": 0.1,
            "score_impact_revenus": 0.2,
            "niveau_criticite_module": 0.3,
        }

        # Ajouter features manquantes
        for feature_name in target_features:
            if feature_name not in complete_features:
                complete_features[feature_name] = default_values.get(feature_name, 0.0)

        return complete_features

    def engineer_full_feature_set(
        self, raw_data: dict, target_features: list[str] | None = None
    ) -> dict:
        """
        Pipeline complet de feature engineering.

        Args:
            raw_data: Données brutes
            target_features: Features cibles (toutes si None)

        Returns:
            Features complètes engineerées
        """
        if target_features is None:
            target_features = self.config.features.all_features

        # 1. Extraction features de base
        features = self.extract_basic_features(raw_data)

        # 2. Features temporelles
        temporal_features = self.engineer_temporal_features(raw_data)
        features.update(temporal_features)

        # 3. Features de risque
        risk_features = self.engineer_risk_features(raw_data)
        features.update(risk_features)

        # 4. Features d'interaction
        interaction_features = self.create_interaction_features(features)
        features.update(interaction_features)

        # 5. Compléter features manquantes
        features = self.handle_missing_features(features, target_features)

        # 6. Normalisation
        features = self.normalize_features(features)

        # 7. Filtrer seulement les features demandées
        final_features = {k: features[k] for k in target_features if k in features}

        return final_features

    def extract_features_from_dataframe(self, df: pd.DataFrame) -> pd.DataFrame:
        """
        Extrait features depuis un DataFrame avec données multiples.

        Args:
            df: DataFrame avec colonnes de données brutes

        Returns:
            DataFrame avec features engineerées
        """
        engineered_features = []

        for _, row in df.iterrows():
            # Convertir row en dictionnaire
            raw_data = row.to_dict()

            # Engineer features
            features = self.engineer_full_feature_set(raw_data)
            engineered_features.append(features)

        return pd.DataFrame(engineered_features)


# Instance globale du feature engineer
feature_engineer = FeatureEngineer()
