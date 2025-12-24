"""
Pipeline d'entraînement ML orchestré pour Hyperion v3.0.

Pipeline complet qui gère:
- Préparation et validation des données
- Feature engineering
- Entraînement des modèles
- Validation et métriques
- Sauvegarde avec MLflow
"""

import time
from datetime import datetime
from typing import Any

import numpy as np
import pandas as pd
from sklearn.ensemble import IsolationForest, RandomForestClassifier
from sklearn.linear_model import LogisticRegression
from sklearn.metrics import (
    accuracy_score,
    classification_report,
    f1_score,
    precision_score,
    recall_score,
)
from sklearn.model_selection import cross_val_score, train_test_split
from xgboost import XGBClassifier

from ..infrastructure.data_validator import data_validator
from ..infrastructure.ml_config import ml_config
from ..infrastructure.model_registry import model_registry


class TrainingPipeline:
    """
    Pipeline d'entraînement ML professionnel pour les modèles Hyperion.

    Orchestré les étapes complètes:
    1. Validation et préparation données
    2. Feature engineering
    3. Entraînement ensemble de modèles
    4. Validation croisée et métriques
    5. Sauvegarde avec versioning
    """

    def __init__(self):
        """Initialise le pipeline d'entraînement."""
        self.config = ml_config
        self.trained_models = {}
        self.training_results = {}

    def train_risk_predictor(
        self,
        training_data: pd.DataFrame,
        target_column: str = "risque_reel",
        test_size: float = 0.2,
        save_models: bool = True,
    ) -> dict[str, Any]:
        """
        Entraîne l'ensemble de modèles pour prédiction de risque.

        Args:
            training_data: Données d'entraînement avec features et target
            target_column: Nom de la colonne target
            test_size: Proportion du test set
            save_models: Sauvegarder les modèles entraînés

        Returns:
            Résultats d'entraînement détaillés
        """
        print("🚀 Démarrage entraînement RiskPredictor ML")
        start_time = time.time()

        # 1. Validation et préparation des données
        print("📋 1. Validation des données...")
        df_clean, validation_result = data_validator.validate_and_prepare_data(
            training_data, target_column, fix_issues=True
        )

        if not validation_result.is_valid:
            raise ValueError(f"Données invalides: {validation_result.errors}")

        print(f"   ✅ {validation_result.summary}")

        # 2. Séparation features/target
        feature_cols = [col for col in df_clean.columns if col != target_column]
        X = df_clean[feature_cols]
        y = df_clean[target_column]

        print(f"   📊 {len(X)} échantillons, {len(feature_cols)} features")

        # 3. Split train/test
        X_train, X_test, y_train, y_test = train_test_split(
            X,
            y,
            test_size=test_size,
            random_state=self.config.training.random_state,
            stratify=y if y.nunique() <= 10 else None,
        )

        # 4. Entraînement des modèles
        models_results = {}

        # Random Forest
        print("🌳 2. Entraînement Random Forest...")
        rf_model, rf_results = self._train_random_forest(X_train, y_train, X_test, y_test)
        models_results["random_forest"] = rf_results

        # XGBoost
        print("⚡ 3. Entraînement XGBoost...")
        xgb_model, xgb_results = self._train_xgboost(X_train, y_train, X_test, y_test)
        models_results["xgboost"] = xgb_results

        # Isolation Forest (pour détection anomalies)
        print("🎯 4. Entraînement Isolation Forest...")
        iso_model, iso_results = self._train_isolation_forest(X_train, y_train, X_test, y_test)
        models_results["isolation_forest"] = iso_results

        # Meta-learner pour ensemble
        print("🎭 5. Entraînement Meta-learner...")
        meta_model, meta_results = self._train_meta_learner([rf_model, xgb_model], X_train, y_train, X_test, y_test)
        models_results["meta_learner"] = meta_results

        # 5. Résultats globaux
        training_time = time.time() - start_time

        results = {
            "training_time_seconds": training_time,
            "validation_result": validation_result.dict(),
            "models_results": models_results,
            "best_model": self._find_best_model(models_results),
            "ensemble_performance": meta_results,
            "feature_names": feature_cols,
            "training_samples": len(X_train),
            "test_samples": len(X_test),
        }

        # 6. Sauvegarde des modèles si demandée
        if save_models:
            print("💾 6. Sauvegarde des modèles...")
            self._save_trained_models(
                {
                    "random_forest": rf_model,
                    "xgboost": xgb_model,
                    "isolation_forest": iso_model,
                    "meta_learner": meta_model,
                },
                results,
            )

        print(f"✅ Entraînement terminé en {training_time:.1f}s")
        print(f"   🎯 Meilleur modèle: {results['best_model']['name']} ({results['best_model']['f1']:.3f} F1)")

        return results

    def _train_random_forest(self, X_train, y_train, X_test, y_test) -> tuple[Any, dict]:
        """Entraîne le modèle Random Forest."""
        config = self.config.get_model_config("risk_predictor_rf")

        model = RandomForestClassifier(**config.hyperparameters)

        # Entraînement
        model.fit(X_train, y_train)

        # Prédictions
        y_pred = model.predict(X_test)
        y_proba = model.predict_proba(X_test)

        # Métriques
        metrics = self._calculate_metrics(y_test, y_pred, y_proba)

        # Cross-validation
        cv_scores = cross_val_score(model, X_train, y_train, cv=self.config.training.cross_validation_folds)

        results = {
            "model_type": "RandomForest",
            "hyperparameters": config.hyperparameters,
            "metrics": metrics,
            "cv_score_mean": cv_scores.mean(),
            "cv_score_std": cv_scores.std(),
            "feature_importance": dict(zip(X_train.columns, model.feature_importances_)),
        }

        return model, results

    def _train_xgboost(self, X_train, y_train, X_test, y_test) -> tuple[Any, dict]:
        """Entraîne le modèle XGBoost."""
        config = self.config.get_model_config("risk_predictor_xgb")

        model = XGBClassifier(**config.hyperparameters)

        # Entraînement
        model.fit(X_train, y_train)

        # Prédictions
        y_pred = model.predict(X_test)
        y_proba = model.predict_proba(X_test)

        # Métriques
        metrics = self._calculate_metrics(y_test, y_pred, y_proba)

        # Cross-validation
        cv_scores = cross_val_score(model, X_train, y_train, cv=self.config.training.cross_validation_folds)

        results = {
            "model_type": "XGBoost",
            "hyperparameters": config.hyperparameters,
            "metrics": metrics,
            "cv_score_mean": cv_scores.mean(),
            "cv_score_std": cv_scores.std(),
            "feature_importance": dict(zip(X_train.columns, model.feature_importances_)),
        }

        return model, results

    def _train_isolation_forest(self, X_train, y_train, X_test, y_test) -> tuple[Any, dict]:
        """Entraîne l'Isolation Forest pour détection d'anomalies."""
        config = self.config.get_model_config("anomaly_detector")

        model = IsolationForest(**config.hyperparameters)

        # Entraînement sur données normales uniquement
        normal_data = X_train[y_train == 0] if 0 in y_train.values else X_train
        model.fit(normal_data)

        # Prédictions (scores d'anomalie)
        anomaly_scores = model.decision_function(X_test)
        predictions = model.predict(X_test)  # -1 = anomalie, 1 = normal

        results = {
            "model_type": "IsolationForest",
            "hyperparameters": config.hyperparameters,
            "normal_samples_training": len(normal_data),
            "anomaly_score_mean": anomaly_scores.mean(),
            "anomaly_score_std": anomaly_scores.std(),
            "anomalies_detected": (predictions == -1).sum(),
        }

        return model, results

    def _train_meta_learner(self, base_models: list[Any], X_train, y_train, X_test, y_test) -> tuple[Any, dict]:
        """Entraîne le meta-learner pour ensemble."""

        # Générer prédictions des modèles de base
        train_meta_features = []
        test_meta_features = []

        for model in base_models:
            train_pred = model.predict_proba(X_train)
            test_pred = model.predict_proba(X_test)

            train_meta_features.append(train_pred)
            test_meta_features.append(test_pred)

        # Combiner features
        X_train_meta = np.column_stack(train_meta_features)
        X_test_meta = np.column_stack(test_meta_features)

        # Meta-learner (Logistic Regression simple)
        meta_model = LogisticRegression(random_state=self.config.training.random_state, max_iter=1000)

        # Entraînement
        meta_model.fit(X_train_meta, y_train)

        # Prédictions
        y_pred = meta_model.predict(X_test_meta)
        y_proba = meta_model.predict_proba(X_test_meta)

        # Métriques
        metrics = self._calculate_metrics(y_test, y_pred, y_proba)

        results = {
            "model_type": "MetaLearner",
            "base_models_count": len(base_models),
            "meta_features_dimension": X_train_meta.shape[1],
            "metrics": metrics,
        }

        # Stocker modèles de base avec meta-learner
        ensemble_model = {"meta_learner": meta_model, "base_models": base_models}

        return ensemble_model, results

    def _calculate_metrics(self, y_true, y_pred, y_proba=None) -> dict[str, float]:
        """Calcule les métriques de performance."""
        metrics = {
            "accuracy": accuracy_score(y_true, y_pred),
            "precision": precision_score(y_true, y_pred, average="weighted", zero_division=0),
            "recall": recall_score(y_true, y_pred, average="weighted", zero_division=0),
            "f1": f1_score(y_true, y_pred, average="weighted", zero_division=0),
        }

        # Ajouter classification report
        report = classification_report(y_true, y_pred, output_dict=True, zero_division=0)
        metrics["classification_report"] = report

        return metrics

    def _find_best_model(self, models_results: dict) -> dict[str, Any]:
        """Trouve le meilleur modèle basé sur le F1 score."""
        best_model = {"name": None, "f1": 0}

        for model_name, results in models_results.items():
            if "metrics" in results and "f1" in results["metrics"]:
                f1_score = results["metrics"]["f1"]
                if f1_score > best_model["f1"]:
                    best_model = {
                        "name": model_name,
                        "f1": f1_score,
                        "accuracy": results["metrics"]["accuracy"],
                        "precision": results["metrics"]["precision"],
                        "recall": results["metrics"]["recall"],
                    }

        return best_model

    def _save_trained_models(self, models: dict[str, Any], training_results: dict):
        """Sauvegarde les modèles entraînés avec métadonnées."""

        for model_name, model in models.items():
            if model_name in training_results["models_results"]:
                results = training_results["models_results"][model_name]

                # Métadonnées pour le registry
                metadata = {
                    "model_type": results.get("model_type", model_name),
                    "accuracy": results.get("metrics", {}).get("accuracy"),
                    "precision": results.get("metrics", {}).get("precision"),
                    "recall": results.get("metrics", {}).get("recall"),
                    "f1_score": results.get("metrics", {}).get("f1"),
                    "training_features": training_results["feature_names"],
                    "training_samples": training_results["training_samples"],
                    "hyperparameters": results.get("hyperparameters", {}),
                    "tags": {
                        "purpose": "risk_prediction",
                        "training_date": datetime.now().strftime("%Y-%m-%d"),
                        "pipeline_version": "3.0.0",
                    },
                }

                # Sauvegarde
                try:
                    version = model_registry.save_model(
                        model=model,
                        name=f"risk_predictor_{model_name}",
                        model_type=results.get("model_type", model_name),
                        metadata=metadata,
                    )
                    print(f"   ✅ {model_name} sauvegardé v{version}")

                except Exception as e:
                    print(f"   ⚠️ Erreur sauvegarde {model_name}: {e}")

    def train_bug_predictor(
        self, training_data: pd.DataFrame, target_column: str = "bug_dans_30j", save_model: bool = True
    ) -> dict[str, Any]:
        """
        Entraîne le prédicteur de bugs.

        Args:
            training_data: Données d'entraînement historiques
            target_column: Colonne target (bug dans 30j)
            save_model: Sauvegarder le modèle

        Returns:
            Résultats d'entraînement
        """
        print("🐛 Entraînement BugPredictor...")

        # Configuration XGBoost optimisée pour prédiction temporelle
        config = self.config.get_model_config("bug_predictor")
        model = XGBClassifier(**config.hyperparameters)

        # Validation données
        df_clean, validation_result = data_validator.validate_and_prepare_data(
            training_data, target_column, fix_issues=True
        )

        feature_cols = [col for col in df_clean.columns if col != target_column]
        X = df_clean[feature_cols]
        y = df_clean[target_column]

        # Split temporal (plus récent = test)
        split_idx = int(len(X) * 0.8)
        X_train, X_test = X.iloc[:split_idx], X.iloc[split_idx:]
        y_train, y_test = y.iloc[:split_idx], y.iloc[split_idx:]

        # Entraînement
        model.fit(X_train, y_train)

        # Validation
        y_pred = model.predict(X_test)
        y_proba = model.predict_proba(X_test)
        metrics = self._calculate_metrics(y_test, y_pred, y_proba)

        results = {
            "model_type": "BugPredictor",
            "metrics": metrics,
            "feature_importance": dict(zip(feature_cols, model.feature_importances_)),
            "temporal_split": True,
            "training_samples": len(X_train),
        }

        if save_model:
            metadata = {
                "model_type": "XGBoost",
                "purpose": "bug_prediction",
                "horizon_days": 30,
                **{f"metric_{k}": v for k, v in metrics.items() if isinstance(v, (int, float))},
            }

            model_registry.save_model(
                model=model, name="bug_predictor_xgboost", model_type="XGBoost", metadata=metadata
            )

        print(f"✅ BugPredictor entraîné (F1: {metrics['f1']:.3f})")
        return results

    def validate_all_models(self) -> dict[str, Any]:
        """Valide tous les modèles entraînés."""
        print("🔍 Validation de tous les modèles...")

        models_info = model_registry.list_models()
        validation_results = {}

        for model_info in models_info:
            if model_info["status"] == "trained":
                try:
                    # Charger modèle
                    model, metadata = model_registry.load_model(
                        model_info["name"], model_info["version"], return_metadata=True
                    )

                    # Vérifications basiques
                    validation_results[model_info["name"]] = {
                        "loadable": True,
                        "version": model_info["version"],
                        "accuracy": metadata.accuracy,
                        "f1_score": metadata.f1_score,
                        "training_samples": metadata.training_samples,
                        "status": "validé",
                    }

                except Exception as e:
                    validation_results[model_info["name"]] = {"loadable": False, "error": str(e), "status": "erreur"}

        print(f"✅ Validation terminée: {len(validation_results)} modèles vérifiés")
        return validation_results


# Instance globale du pipeline
training_pipeline = TrainingPipeline()
