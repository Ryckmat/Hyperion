"""
Ensemble Models for Hyperion v2.9

Gestionnaire de modèles ensemble pour améliorer les prédictions.
"""

import json
import logging
import time
from concurrent.futures import ThreadPoolExecutor
from dataclasses import dataclass, field
from datetime import datetime
from pathlib import Path
from typing import Any

import joblib
import numpy as np

logger = logging.getLogger(__name__)


@dataclass
class ModelMetrics:
    """Métriques d'évaluation d'un modèle"""

    accuracy: float
    precision: float
    recall: float
    f1_score: float
    roc_auc: float
    training_time: float
    inference_time: float
    model_size_mb: float


@dataclass
class EnsembleModel:
    """Définition d'un modèle dans l'ensemble"""

    name: str
    model_type: str  # 'random_forest', 'gradient_boosting', 'neural_network', etc.
    model_path: str
    weight: float = 1.0
    is_trained: bool = False
    last_trained: datetime | None = None
    metrics: ModelMetrics | None = None

    # Configuration du modèle
    hyperparameters: dict[str, Any] = field(default_factory=dict)
    features_used: list[str] = field(default_factory=list)

    # Métadonnées
    version: str = "1.0"
    description: str = ""


@dataclass
class EnsemblePrediction:
    """Résultat de prédiction ensemble"""

    prediction: int | float | str
    confidence: float
    individual_predictions: dict[str, Any]
    individual_confidences: dict[str, float]
    ensemble_method: str
    processing_time: float


class EnsembleModelManager:
    """
    Gestionnaire de modèles ensemble pour Hyperion v2.9

    Fonctionnalités :
    - Gestion d'ensembles de modèles ML
    - Stratégies de vote (majoritaire, pondéré, stacking)
    - Optimisation automatique des poids
    - Entraînement adaptatif des modèles
    - Métriques de performance ensemble
    - Sélection dynamique de modèles
    """

    def __init__(
        self,
        models_directory: str = "models/ensemble",
        max_models: int = 10,
        ensemble_strategy: str = "weighted_voting",
    ):

        self.models_directory = Path(models_directory)
        self.max_models = max_models
        self.ensemble_strategy = ensemble_strategy

        # Création du répertoire
        self.models_directory.mkdir(parents=True, exist_ok=True)

        # Storage
        self.models: dict[str, EnsembleModel] = {}
        self.loaded_models: dict[str, Any] = {}  # Modèles chargés en mémoire

        # Configuration ensemble
        self.voting_strategies = {
            "majority_voting": self._majority_voting,
            "weighted_voting": self._weighted_voting,
            "average_voting": self._average_voting,
            "stacking": self._stacking_prediction,
            "dynamic_selection": self._dynamic_selection,
        }

        # Métriques ensemble
        self.ensemble_metrics = {
            "total_predictions": 0,
            "avg_accuracy": 0.0,
            "avg_confidence": 0.0,
            "model_usage_count": {},
            "prediction_times": [],
        }

        # Configuration adaptative
        self.adaptation_config = {
            "weight_learning_rate": 0.01,
            "performance_window": 100,
            "min_weight": 0.1,
            "max_weight": 2.0,
        }

        # Threading pour optimisations
        self.executor = ThreadPoolExecutor(max_workers=4)

        # Charger les modèles existants
        self._load_ensemble_configuration()

        logger.info(f"EnsembleModelManager initialisé avec {len(self.models)} modèles")

    def add_model(self, model_config: EnsembleModel) -> bool:
        """Ajouter un modèle à l'ensemble"""

        try:
            if len(self.models) >= self.max_models:
                logger.warning(f"Limite de modèles atteinte ({self.max_models})")
                return False

            # Validation du modèle
            if not self._validate_model_config(model_config):
                return False

            # Ajouter le modèle
            self.models[model_config.name] = model_config

            # Initialiser les métriques d'usage
            self.ensemble_metrics["model_usage_count"][model_config.name] = 0

            # Sauvegarder la configuration
            self._save_ensemble_configuration()

            logger.info(f"Modèle ajouté à l'ensemble: {model_config.name}")
            return True

        except Exception as e:
            logger.error(f"Erreur ajout modèle {model_config.name}: {e}")
            return False

    def remove_model(self, model_name: str) -> bool:
        """Supprimer un modèle de l'ensemble"""

        if model_name not in self.models:
            return False

        try:
            # Décharger de la mémoire si chargé
            if model_name in self.loaded_models:
                del self.loaded_models[model_name]

            # Supprimer de l'ensemble
            del self.models[model_name]

            # Nettoyer les métriques
            if model_name in self.ensemble_metrics["model_usage_count"]:
                del self.ensemble_metrics["model_usage_count"][model_name]

            # Sauvegarder
            self._save_ensemble_configuration()

            logger.info(f"Modèle supprimé de l'ensemble: {model_name}")
            return True

        except Exception as e:
            logger.error(f"Erreur suppression modèle {model_name}: {e}")
            return False

    def train_model(
        self,
        model_name: str,
        X_train: np.ndarray,
        y_train: np.ndarray,
        X_val: np.ndarray | None = None,
        y_val: np.ndarray | None = None,
    ) -> bool:
        """Entraîner un modèle spécifique"""

        if model_name not in self.models:
            logger.error(f"Modèle {model_name} non trouvé")
            return False

        model_config = self.models[model_name]

        try:
            start_time = time.time()

            # Créer le modèle selon le type
            model = self._create_model(model_config)

            # Entraînement
            model.fit(X_train, y_train)

            training_time = time.time() - start_time

            # Évaluation
            if X_val is not None and y_val is not None:
                metrics = self._evaluate_model(model, X_val, y_val, training_time)
                model_config.metrics = metrics

            # Sauvegarde du modèle
            model_path = self.models_directory / f"{model_name}.joblib"
            joblib.dump(model, model_path)
            model_config.model_path = str(model_path)

            # Mise à jour du statut
            model_config.is_trained = True
            model_config.last_trained = datetime.now()

            # Charger en mémoire
            self.loaded_models[model_name] = model

            # Sauvegarder configuration
            self._save_ensemble_configuration()

            logger.info(f"Modèle {model_name} entraîné avec succès")
            return True

        except Exception as e:
            logger.error(f"Erreur entraînement {model_name}: {e}")
            return False

    def predict(self, X: np.ndarray, model_names: list[str] | None = None) -> EnsemblePrediction:
        """Effectuer une prédiction ensemble"""

        start_time = time.time()

        try:
            # Déterminer quels modèles utiliser
            if model_names is None:
                active_models = [name for name, config in self.models.items() if config.is_trained]
            else:
                active_models = [
                    name
                    for name in model_names
                    if name in self.models and self.models[name].is_trained
                ]

            if not active_models:
                raise ValueError("Aucun modèle entraîné disponible")

            # Charger les modèles nécessaires
            self._ensure_models_loaded(active_models)

            # Obtenir prédictions individuelles
            individual_predictions = {}
            individual_confidences = {}

            for model_name in active_models:
                try:
                    model = self.loaded_models[model_name]
                    pred = model.predict(X)

                    # Calculer confiance (approximation)
                    if hasattr(model, "predict_proba"):
                        prob = model.predict_proba(X)
                        confidence = np.max(prob, axis=1).mean()
                    else:
                        confidence = 0.7  # Valeur par défaut

                    individual_predictions[model_name] = pred
                    individual_confidences[model_name] = confidence

                    # Mise à jour statistiques
                    self.ensemble_metrics["model_usage_count"][model_name] += 1

                except Exception as e:
                    logger.warning(f"Erreur prédiction {model_name}: {e}")
                    continue

            if not individual_predictions:
                raise ValueError("Aucune prédiction obtenue")

            # Appliquer stratégie ensemble
            strategy_func = self.voting_strategies.get(
                self.ensemble_strategy, self._weighted_voting
            )

            final_prediction, ensemble_confidence = strategy_func(
                individual_predictions, individual_confidences
            )

            processing_time = time.time() - start_time

            # Créer résultat
            result = EnsemblePrediction(
                prediction=final_prediction,
                confidence=ensemble_confidence,
                individual_predictions=individual_predictions,
                individual_confidences=individual_confidences,
                ensemble_method=self.ensemble_strategy,
                processing_time=processing_time,
            )

            # Mise à jour métriques
            self._update_ensemble_metrics(result)

            return result

        except Exception as e:
            logger.error(f"Erreur prédiction ensemble: {e}")
            raise

    def _create_model(self, config: EnsembleModel):
        """Créer un modèle selon sa configuration"""

        if config.model_type == "random_forest":
            from sklearn.ensemble import RandomForestClassifier

            return RandomForestClassifier(**config.hyperparameters)

        elif config.model_type == "gradient_boosting":
            from sklearn.ensemble import GradientBoostingClassifier

            return GradientBoostingClassifier(**config.hyperparameters)

        elif config.model_type == "logistic_regression":
            from sklearn.linear_model import LogisticRegression

            return LogisticRegression(**config.hyperparameters)

        elif config.model_type == "svm":
            from sklearn.svm import SVC

            return SVC(probability=True, **config.hyperparameters)

        elif config.model_type == "neural_network":
            from sklearn.neural_network import MLPClassifier

            return MLPClassifier(**config.hyperparameters)

        else:
            raise ValueError(f"Type de modèle non supporté: {config.model_type}")

    def _evaluate_model(
        self, model, X_val: np.ndarray, y_val: np.ndarray, training_time: float
    ) -> ModelMetrics:
        """Évaluer les performances d'un modèle"""

        from sklearn.metrics import (
            accuracy_score,
            f1_score,
            precision_score,
            recall_score,
            roc_auc_score,
        )

        # Prédictions
        start_time = time.time()
        y_pred = model.predict(X_val)
        inference_time = (time.time() - start_time) / len(X_val)

        # Métriques
        accuracy = accuracy_score(y_val, y_pred)
        precision = precision_score(y_val, y_pred, average="weighted", zero_division=0)
        recall = recall_score(y_val, y_pred, average="weighted", zero_division=0)
        f1 = f1_score(y_val, y_pred, average="weighted", zero_division=0)

        # ROC-AUC (si binaire ou avec probas)
        try:
            if hasattr(model, "predict_proba") and len(np.unique(y_val)) == 2:
                y_prob = model.predict_proba(X_val)[:, 1]
                roc_auc = roc_auc_score(y_val, y_prob)
            else:
                roc_auc = 0.0
        except Exception:
            roc_auc = 0.0

        # Taille du modèle (approximation)
        try:
            import sys

            model_size_mb = sys.getsizeof(joblib.dumps(model)) / (1024 * 1024)
        except Exception:
            model_size_mb = 0.0

        return ModelMetrics(
            accuracy=accuracy,
            precision=precision,
            recall=recall,
            f1_score=f1,
            roc_auc=roc_auc,
            training_time=training_time,
            inference_time=inference_time,
            model_size_mb=model_size_mb,
        )

    def _ensure_models_loaded(self, model_names: list[str]):
        """S'assurer que les modèles sont chargés en mémoire"""

        for model_name in model_names:
            if model_name not in self.loaded_models:
                self._load_model(model_name)

    def _load_model(self, model_name: str) -> bool:
        """Charger un modèle en mémoire"""

        if model_name not in self.models:
            return False

        model_config = self.models[model_name]

        try:
            if model_config.model_path and Path(model_config.model_path).exists():
                model = joblib.load(model_config.model_path)
                self.loaded_models[model_name] = model
                logger.debug(f"Modèle chargé: {model_name}")
                return True
            else:
                logger.warning(f"Fichier modèle non trouvé: {model_config.model_path}")
                return False

        except Exception as e:
            logger.error(f"Erreur chargement modèle {model_name}: {e}")
            return False

    # Stratégies de vote

    def _majority_voting(
        self, predictions: dict[str, np.ndarray], _confidences: dict[str, float]
    ) -> tuple[Any, float]:
        """Vote majoritaire simple"""

        # Convertir en prédictions discrètes
        votes = []
        for pred in predictions.values():
            if isinstance(pred, np.ndarray):
                votes.extend(pred.tolist())
            else:
                votes.append(pred)

        # Compter les votes
        from collections import Counter

        vote_counts = Counter(votes)
        final_prediction = vote_counts.most_common(1)[0][0]

        # Confiance basée sur le consensus
        total_votes = sum(vote_counts.values())
        confidence = vote_counts[final_prediction] / total_votes

        return final_prediction, confidence

    def _weighted_voting(
        self, predictions: dict[str, np.ndarray], confidences: dict[str, float]
    ) -> tuple[Any, float]:
        """Vote pondéré par poids et performance"""

        weighted_predictions = {}
        total_weight = 0

        for model_name, pred in predictions.items():
            model_weight = self.models[model_name].weight
            model_confidence = confidences[model_name]

            # Poids combiné (configuration + performance)
            combined_weight = model_weight * model_confidence

            if isinstance(pred, np.ndarray):
                for i, p in enumerate(pred):
                    if i not in weighted_predictions:
                        weighted_predictions[i] = {}
                    if p not in weighted_predictions[i]:
                        weighted_predictions[i][p] = 0
                    weighted_predictions[i][p] += combined_weight
            else:
                if 0 not in weighted_predictions:
                    weighted_predictions[0] = {}
                if pred not in weighted_predictions[0]:
                    weighted_predictions[0][pred] = 0
                weighted_predictions[0][pred] += combined_weight

            total_weight += combined_weight

        # Prédiction finale
        if weighted_predictions:
            final_pred_weights = weighted_predictions[0]
            final_prediction = max(final_pred_weights, key=final_pred_weights.get)
            confidence = final_pred_weights[final_prediction] / total_weight
        else:
            final_prediction = list(predictions.values())[0]
            confidence = 0.5

        return final_prediction, confidence

    def _average_voting(
        self, predictions: dict[str, np.ndarray], confidences: dict[str, float]
    ) -> tuple[Any, float]:
        """Moyenne des prédictions numériques"""

        numeric_predictions = []
        total_confidence = 0

        for model_name, pred in predictions.items():
            try:
                if isinstance(pred, np.ndarray):
                    numeric_pred = np.mean(pred.astype(float))
                else:
                    numeric_pred = float(pred)

                numeric_predictions.append(numeric_pred)
                total_confidence += confidences[model_name]

            except (ValueError, TypeError):
                # Si pas numérique, ignorer
                continue

        if numeric_predictions:
            final_prediction = np.mean(numeric_predictions)
            confidence = total_confidence / len(numeric_predictions)
        else:
            # Fallback sur vote majoritaire
            return self._majority_voting(predictions, confidences)

        return final_prediction, confidence

    def _stacking_prediction(
        self, predictions: dict[str, np.ndarray], confidences: dict[str, float]
    ) -> tuple[Any, float]:
        """Stacking avec méta-modèle (simulation)"""

        # Pour l'instant, utiliser une moyenne pondérée sophistiquée
        # En production, entraîner un méta-modèle

        weights = {}
        for model_name in predictions:
            model_metrics = self.models[model_name].metrics
            if model_metrics:
                # Poids basé sur F1-score et confiance
                weights[model_name] = model_metrics.f1_score * confidences[model_name]
            else:
                weights[model_name] = confidences[model_name]

        # Normaliser les poids
        total_weight = sum(weights.values())
        if total_weight > 0:
            weights = {k: v / total_weight for k, v in weights.items()}

        # Prédiction pondérée
        final_prediction = None
        final_confidence = 0

        for model_name, pred in predictions.items():
            weight = weights.get(model_name, 0)

            if final_prediction is None:
                final_prediction = pred * weight
            else:
                try:
                    final_prediction += pred * weight
                except Exception:
                    # Si types incompatibles, prendre le plus pondéré
                    if weight > final_confidence:
                        final_prediction = pred

            final_confidence += confidences[model_name] * weight

        return final_prediction, final_confidence

    def _dynamic_selection(
        self, predictions: dict[str, np.ndarray], confidences: dict[str, float]
    ) -> tuple[Any, float]:
        """Sélection dynamique du meilleur modèle"""

        # Sélectionner le modèle avec la meilleure combinaison métrique/confiance
        best_score = 0
        best_prediction = None
        best_confidence = 0

        for model_name, pred in predictions.items():
            model_metrics = self.models[model_name].metrics
            model_confidence = confidences[model_name]

            if model_metrics:
                # Score combiné
                score = model_metrics.f1_score * 0.7 + model_confidence * 0.3
            else:
                score = model_confidence

            if score > best_score:
                best_score = score
                best_prediction = pred
                best_confidence = model_confidence

        return best_prediction, best_confidence

    def _update_ensemble_metrics(self, result: EnsemblePrediction):
        """Mise à jour des métriques ensemble"""

        self.ensemble_metrics["total_predictions"] += 1

        # Mise à jour moyenne confiance
        current_avg = self.ensemble_metrics["avg_confidence"]
        count = self.ensemble_metrics["total_predictions"]
        self.ensemble_metrics["avg_confidence"] = (
            current_avg * (count - 1) + result.confidence
        ) / count

        # Temps de traitement
        self.ensemble_metrics["prediction_times"].append(result.processing_time)
        if len(self.ensemble_metrics["prediction_times"]) > 1000:
            self.ensemble_metrics["prediction_times"] = self.ensemble_metrics["prediction_times"][
                -1000:
            ]

    def optimize_ensemble_weights(self, X_val: np.ndarray, y_val: np.ndarray) -> bool:
        """Optimiser les poids de l'ensemble sur données de validation"""

        logger.info("Optimisation des poids de l'ensemble...")

        try:
            # Obtenir prédictions de tous les modèles
            model_predictions = {}
            for model_name in self.models:
                if self.models[model_name].is_trained:
                    self._ensure_models_loaded([model_name])
                    if model_name in self.loaded_models:
                        pred = self.loaded_models[model_name].predict(X_val)
                        model_predictions[model_name] = pred

            if len(model_predictions) < 2:
                logger.warning("Pas assez de modèles pour optimisation")
                return False

            # Optimisation simple par grid search
            best_accuracy = 0
            best_weights = {}

            weight_ranges = np.arange(0.1, 2.1, 0.2)

            for weight_combo in self._generate_weight_combinations(
                list(model_predictions.keys()), weight_ranges
            ):

                # Appliquer les poids temporairement
                original_weights = {}
                for model_name, weight in weight_combo.items():
                    original_weights[model_name] = self.models[model_name].weight
                    self.models[model_name].weight = weight

                # Évaluer avec ces poids
                try:
                    dummy_confidences = dict.fromkeys(model_predictions, 0.8)
                    pred, _ = self._weighted_voting(model_predictions, dummy_confidences)

                    # Calculer accuracy (simplifiée)
                    accuracy = np.mean(pred == y_val) if isinstance(pred, np.ndarray) else 0.5

                    if accuracy > best_accuracy:
                        best_accuracy = accuracy
                        best_weights = dict(weight_combo)

                except Exception as e:
                    logger.debug(f"Erreur évaluation poids: {e}")

                # Restaurer poids originaux
                for model_name, original_weight in original_weights.items():
                    self.models[model_name].weight = original_weight

            # Appliquer meilleurs poids
            if best_weights:
                for model_name, weight in best_weights.items():
                    self.models[model_name].weight = weight

                logger.info(f"Poids optimisés. Nouvelle accuracy: {best_accuracy:.3f}")
                self._save_ensemble_configuration()
                return True

            return False

        except Exception as e:
            logger.error(f"Erreur optimisation poids: {e}")
            return False

    def _generate_weight_combinations(
        self, model_names: list[str], weight_ranges: np.ndarray, max_combinations: int = 100
    ):
        """Générer des combinaisons de poids pour optimisation"""

        import itertools

        combinations = []

        # Génération limitée pour éviter explosion combinatoire
        for count, weights in enumerate(itertools.product(weight_ranges, repeat=len(model_names))):
            if count >= max_combinations:
                break

            weight_dict = dict(zip(model_names, weights, strict=False))
            combinations.append(weight_dict)

        return combinations

    def get_ensemble_summary(self) -> dict[str, Any]:
        """Obtenir un résumé de l'ensemble"""

        summary = {
            "total_models": len(self.models),
            "trained_models": len([m for m in self.models.values() if m.is_trained]),
            "loaded_models": len(self.loaded_models),
            "ensemble_strategy": self.ensemble_strategy,
            "total_predictions": self.ensemble_metrics["total_predictions"],
            "avg_confidence": self.ensemble_metrics["avg_confidence"],
            "avg_prediction_time": (
                np.mean(self.ensemble_metrics["prediction_times"])
                if self.ensemble_metrics["prediction_times"]
                else 0.0
            ),
            "models_info": {},
        }

        for name, model in self.models.items():
            summary["models_info"][name] = {
                "type": model.model_type,
                "weight": model.weight,
                "is_trained": model.is_trained,
                "last_trained": model.last_trained.isoformat() if model.last_trained else None,
                "usage_count": self.ensemble_metrics["model_usage_count"].get(name, 0),
                "metrics": {
                    "accuracy": model.metrics.accuracy if model.metrics else None,
                    "f1_score": model.metrics.f1_score if model.metrics else None,
                },
            }

        return summary

    def _validate_model_config(self, config: EnsembleModel) -> bool:
        """Valider la configuration d'un modèle"""

        if not config.name or config.name in self.models:
            logger.error(f"Nom de modèle invalide ou déjà existant: {config.name}")
            return False

        supported_types = [
            "random_forest",
            "gradient_boosting",
            "logistic_regression",
            "svm",
            "neural_network",
        ]
        if config.model_type not in supported_types:
            logger.error(f"Type de modèle non supporté: {config.model_type}")
            return False

        if config.weight <= 0:
            logger.error(f"Poids de modèle invalide: {config.weight}")
            return False

        return True

    def _save_ensemble_configuration(self):
        """Sauvegarder la configuration de l'ensemble"""

        config_path = self.models_directory / "ensemble_config.json"

        try:
            config_data = {"ensemble_strategy": self.ensemble_strategy, "models": {}}

            for name, model in self.models.items():
                config_data["models"][name] = {
                    "name": model.name,
                    "model_type": model.model_type,
                    "model_path": model.model_path,
                    "weight": model.weight,
                    "is_trained": model.is_trained,
                    "last_trained": model.last_trained.isoformat() if model.last_trained else None,
                    "hyperparameters": model.hyperparameters,
                    "features_used": model.features_used,
                    "version": model.version,
                    "description": model.description,
                }

                if model.metrics:
                    config_data["models"][name]["metrics"] = {
                        "accuracy": model.metrics.accuracy,
                        "precision": model.metrics.precision,
                        "recall": model.metrics.recall,
                        "f1_score": model.metrics.f1_score,
                        "roc_auc": model.metrics.roc_auc,
                        "training_time": model.metrics.training_time,
                        "inference_time": model.metrics.inference_time,
                        "model_size_mb": model.metrics.model_size_mb,
                    }

            with open(config_path, "w") as f:
                json.dump(config_data, f, indent=2)

            logger.debug("Configuration ensemble sauvegardée")

        except Exception as e:
            logger.error(f"Erreur sauvegarde configuration: {e}")

    def _load_ensemble_configuration(self):
        """Charger la configuration de l'ensemble"""

        config_path = self.models_directory / "ensemble_config.json"

        if not config_path.exists():
            logger.info("Aucune configuration ensemble existante")
            return

        try:
            with open(config_path) as f:
                config_data = json.load(f)

            self.ensemble_strategy = config_data.get("ensemble_strategy", "weighted_voting")

            for name, model_data in config_data.get("models", {}).items():
                # Créer metrics si disponible
                metrics = None
                if "metrics" in model_data:
                    m = model_data["metrics"]
                    metrics = ModelMetrics(
                        accuracy=m["accuracy"],
                        precision=m["precision"],
                        recall=m["recall"],
                        f1_score=m["f1_score"],
                        roc_auc=m["roc_auc"],
                        training_time=m["training_time"],
                        inference_time=m["inference_time"],
                        model_size_mb=m["model_size_mb"],
                    )

                # Créer modèle
                model = EnsembleModel(
                    name=model_data["name"],
                    model_type=model_data["model_type"],
                    model_path=model_data["model_path"],
                    weight=model_data["weight"],
                    is_trained=model_data["is_trained"],
                    last_trained=(
                        datetime.fromisoformat(model_data["last_trained"])
                        if model_data["last_trained"]
                        else None
                    ),
                    metrics=metrics,
                    hyperparameters=model_data.get("hyperparameters", {}),
                    features_used=model_data.get("features_used", []),
                    version=model_data.get("version", "1.0"),
                    description=model_data.get("description", ""),
                )

                self.models[name] = model
                self.ensemble_metrics["model_usage_count"][name] = 0

            logger.info(f"Configuration ensemble chargée: {len(self.models)} modèles")

        except Exception as e:
            logger.error(f"Erreur chargement configuration: {e}")
