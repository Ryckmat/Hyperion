"""
Hyperion v2.9 - Adaptive Training
Entraînement adaptatif pour les modèles ML ensemble
"""

import asyncio
import logging
import time
from collections.abc import Callable
from dataclasses import dataclass
from enum import Enum
from typing import Any

import numpy as np

logger = logging.getLogger(__name__)


class TrainingStrategy(Enum):
    """Stratégies d'entraînement adaptatif"""

    INCREMENTAL = "incremental"
    CURRICULUM = "curriculum"
    ACTIVE_LEARNING = "active_learning"
    ENSEMBLE_BOOSTING = "ensemble_boosting"
    META_LEARNING = "meta_learning"


class LearningPhase(Enum):
    """Phases d'apprentissage"""

    EXPLORATION = "exploration"
    EXPLOITATION = "exploitation"
    CONSOLIDATION = "consolidation"
    ADAPTATION = "adaptation"


@dataclass
class TrainingConfig:
    """Configuration pour l'entraînement adaptatif"""

    strategy: TrainingStrategy = TrainingStrategy.INCREMENTAL
    max_iterations: int = 1000
    patience: int = 50
    learning_rate_decay: float = 0.95
    performance_threshold: float = 0.95
    adaptation_frequency: int = 100
    batch_size: int = 32
    validation_split: float = 0.2


@dataclass
class TrainingMetrics:
    """Métriques d'entraînement"""

    iteration: int
    loss: float
    accuracy: float
    learning_rate: float
    phase: LearningPhase
    timestamp: float
    model_weights: dict[str, float] | None = None


@dataclass
class AdaptationDecision:
    """Décision d'adaptation"""

    action: str
    reason: str
    parameters: dict[str, Any]
    confidence: float
    timestamp: float


class PerformanceMonitor:
    """Moniteur de performance pour l'adaptation"""

    def __init__(self, window_size: int = 50):
        self.window_size = window_size
        self.metrics_history: list[TrainingMetrics] = []
        self.performance_trend = None

    def record_metrics(self, metrics: TrainingMetrics):
        """Enregistre de nouvelles métriques"""
        self.metrics_history.append(metrics)

        # Garder seulement la fenêtre récente
        if len(self.metrics_history) > self.window_size * 2:
            self.metrics_history = self.metrics_history[-self.window_size :]

        self._update_trend()

    def _update_trend(self):
        """Met à jour la tendance de performance"""
        if len(self.metrics_history) < 10:
            return

        recent_metrics = self.metrics_history[-10:]
        older_metrics = self.metrics_history[-20:-10] if len(self.metrics_history) >= 20 else []

        if not older_metrics:
            return

        recent_avg = np.mean([m.accuracy for m in recent_metrics])
        older_avg = np.mean([m.accuracy for m in older_metrics])

        if recent_avg > older_avg + 0.01:
            self.performance_trend = "improving"
        elif recent_avg < older_avg - 0.01:
            self.performance_trend = "declining"
        else:
            self.performance_trend = "stable"

    def get_trend(self) -> str | None:
        """Retourne la tendance actuelle"""
        return self.performance_trend

    def should_adapt(self) -> tuple[bool, str]:
        """Détermine si une adaptation est nécessaire"""
        if len(self.metrics_history) < 20:
            return False, "insufficient_data"

        recent_metrics = self.metrics_history[-10:]

        # Vérifier la stagnation
        recent_accuracies = [m.accuracy for m in recent_metrics]
        if np.std(recent_accuracies) < 0.005:  # Très faible variance
            return True, "performance_plateau"

        # Vérifier la dégradation
        if self.performance_trend == "declining":
            return True, "performance_decline"

        # Vérifier l'overfitting
        if self._detect_overfitting():
            return True, "overfitting_detected"

        return False, "no_adaptation_needed"

    def _detect_overfitting(self) -> bool:
        """Détecte les signes d'overfitting"""
        if len(self.metrics_history) < 30:
            return False

        recent_loss = [m.loss for m in self.metrics_history[-10:]]
        return np.mean(recent_loss) > np.mean([m.loss for m in self.metrics_history[-30:-20]])


class AdaptiveTrainer:
    """Entraîneur adaptatif pour modèles ML"""

    def __init__(self, config: TrainingConfig = None):
        self.config = config or TrainingConfig()
        self.performance_monitor = PerformanceMonitor()
        self.adaptation_history: list[AdaptationDecision] = []
        self.current_phase = LearningPhase.EXPLORATION
        self.learning_rate = 0.001
        self.model_ensemble = {}
        self.training_active = False

    async def train_adaptive(
        self,
        model_name: str,
        X_train: np.ndarray,
        y_train: np.ndarray,
        X_val: np.ndarray,
        y_val: np.ndarray,
        progress_callback: Callable | None = None,
    ) -> dict[str, Any]:
        """Entraîne un modèle de manière adaptative"""
        logger.info(f"Démarrage entraînement adaptatif pour {model_name}")
        self.training_active = True
        start_time = time.time()

        try:
            # Initialiser l'entraînement
            best_accuracy = 0.0
            patience_counter = 0
            iteration = 0

            while iteration < self.config.max_iterations and self.training_active:
                # Phase d'entraînement
                batch_indices = self._select_training_batch(X_train, y_train, iteration)
                X_batch = X_train[batch_indices]
                y_batch = y_train[batch_indices]

                # Simuler entraînement (remplacer par vraie logique ML)
                loss, accuracy = await self._train_iteration(
                    model_name, X_batch, y_batch, X_val, y_val
                )

                # Enregistrer métriques
                metrics = TrainingMetrics(
                    iteration=iteration,
                    loss=loss,
                    accuracy=accuracy,
                    learning_rate=self.learning_rate,
                    phase=self.current_phase,
                    timestamp=time.time(),
                )
                self.performance_monitor.record_metrics(metrics)

                # Vérifier amélioration
                if accuracy > best_accuracy:
                    best_accuracy = accuracy
                    patience_counter = 0
                else:
                    patience_counter += 1

                # Adaptation si nécessaire
                if iteration % self.config.adaptation_frequency == 0:
                    await self._check_and_adapt()

                # Callback de progression
                if progress_callback:
                    progress_callback(
                        {
                            "iteration": iteration,
                            "loss": loss,
                            "accuracy": accuracy,
                            "best_accuracy": best_accuracy,
                            "phase": self.current_phase.value,
                        }
                    )

                # Critères d'arrêt
                if patience_counter >= self.config.patience:
                    logger.info("Arrêt par patience")
                    break

                if accuracy >= self.config.performance_threshold:
                    logger.info("Seuil de performance atteint")
                    break

                iteration += 1
                await asyncio.sleep(0.001)  # Permettre autres tâches

            training_time = time.time() - start_time

            results = {
                "model_name": model_name,
                "final_accuracy": best_accuracy,
                "total_iterations": iteration,
                "training_time": training_time,
                "adaptations_made": len(self.adaptation_history),
                "final_phase": self.current_phase.value,
            }

            logger.info(f"Entraînement terminé: {results}")
            return results

        except Exception as e:
            logger.error(f"Erreur lors de l'entraînement adaptatif: {e}")
            raise
        finally:
            self.training_active = False

    def _select_training_batch(
        self, X_train: np.ndarray, _y_train: np.ndarray, iteration: int
    ) -> np.ndarray:
        """Sélectionne un batch selon la stratégie"""
        total_samples = len(X_train)

        if self.config.strategy == TrainingStrategy.INCREMENTAL:
            # Batch aléatoire standard
            return np.random.choice(total_samples, self.config.batch_size, replace=False)

        elif self.config.strategy == TrainingStrategy.CURRICULUM:
            # Commencer par exemples faciles
            difficulty_progress = min(1.0, iteration / (self.config.max_iterations * 0.5))
            easy_samples = int(total_samples * (1 - difficulty_progress))
            total_samples - easy_samples

            # Mélanger faciles et difficiles
            easy_indices = np.arange(easy_samples)
            hard_indices = np.arange(easy_samples, total_samples)

            n_easy = int(self.config.batch_size * (1 - difficulty_progress))
            n_hard = self.config.batch_size - n_easy

            selected_easy = np.random.choice(
                easy_indices, min(n_easy, len(easy_indices)), replace=False
            )
            selected_hard = np.random.choice(
                hard_indices, min(n_hard, len(hard_indices)), replace=False
            )

            return np.concatenate([selected_easy, selected_hard])

        elif self.config.strategy == TrainingStrategy.ACTIVE_LEARNING:
            # Sélectionner exemples incertains (simulation)
            uncertainty_scores = np.random.random(total_samples)
            uncertain_indices = np.argsort(uncertainty_scores)[-self.config.batch_size * 2 :]
            return np.random.choice(uncertain_indices, self.config.batch_size, replace=False)

        else:
            return np.random.choice(total_samples, self.config.batch_size, replace=False)

    async def _train_iteration(
        self,
        _model_name: str,
        _X_batch: np.ndarray,
        _y_batch: np.ndarray,
        _X_val: np.ndarray,
        _y_val: np.ndarray,
    ) -> tuple[float, float]:
        """Exécute une itération d'entraînement"""
        # Simulation d'entraînement
        # En vraie implémentation, utiliser le vrai modèle ML

        # Simuler loss décroissante avec bruit
        base_loss = 1.0 / (1.0 + len(self.performance_monitor.metrics_history) * 0.01)
        noise = np.random.normal(0, 0.1)
        loss = max(0.01, base_loss + noise)

        # Simuler accuracy croissante avec plateau
        base_accuracy = min(0.95, 0.5 + len(self.performance_monitor.metrics_history) * 0.001)
        accuracy_noise = np.random.normal(0, 0.02)
        accuracy = min(0.98, max(0.1, base_accuracy + accuracy_noise))

        # Petit délai pour simuler computation
        await asyncio.sleep(0.001)

        return loss, accuracy

    async def _check_and_adapt(self):
        """Vérifie si adaptation nécessaire et l'applique"""
        should_adapt, reason = self.performance_monitor.should_adapt()

        if should_adapt:
            adaptation = self._decide_adaptation(reason)
            await self._apply_adaptation(adaptation)
            self.adaptation_history.append(adaptation)
            logger.info(f"Adaptation appliquée: {adaptation.action} ({adaptation.reason})")

    def _decide_adaptation(self, reason: str) -> AdaptationDecision:
        """Décide quelle adaptation appliquer"""
        adaptations = {
            "performance_plateau": {
                "action": "increase_learning_rate",
                "parameters": {"multiplier": 1.5},
                "confidence": 0.7,
            },
            "performance_decline": {
                "action": "decrease_learning_rate",
                "parameters": {"multiplier": 0.8},
                "confidence": 0.8,
            },
            "overfitting_detected": {
                "action": "add_regularization",
                "parameters": {"strength": 0.01},
                "confidence": 0.9,
            },
        }

        adaptation_config = adaptations.get(
            reason, {"action": "no_action", "parameters": {}, "confidence": 0.5}
        )

        return AdaptationDecision(
            action=adaptation_config["action"],
            reason=reason,
            parameters=adaptation_config["parameters"],
            confidence=adaptation_config["confidence"],
            timestamp=time.time(),
        )

    async def _apply_adaptation(self, adaptation: AdaptationDecision):
        """Applique une adaptation"""
        if adaptation.action == "increase_learning_rate":
            multiplier = adaptation.parameters.get("multiplier", 1.2)
            self.learning_rate *= multiplier
            self.learning_rate = min(0.1, self.learning_rate)  # Cap maximum

        elif adaptation.action == "decrease_learning_rate":
            multiplier = adaptation.parameters.get("multiplier", 0.8)
            self.learning_rate *= multiplier
            self.learning_rate = max(0.0001, self.learning_rate)  # Cap minimum

        elif adaptation.action == "add_regularization":
            # En vraie implémentation, ajuster les paramètres du modèle
            logger.info("Régularisation ajoutée")

        elif adaptation.action == "change_phase":
            new_phase = adaptation.parameters.get("phase", LearningPhase.ADAPTATION)
            self.current_phase = new_phase

        # Simuler changement de phase automatique
        metrics_count = len(self.performance_monitor.metrics_history)
        if metrics_count > 100 and self.current_phase == LearningPhase.EXPLORATION:
            self.current_phase = LearningPhase.EXPLOITATION
        elif metrics_count > 300 and self.current_phase == LearningPhase.EXPLOITATION:
            self.current_phase = LearningPhase.CONSOLIDATION

    def stop_training(self):
        """Arrête l'entraînement en cours"""
        self.training_active = False
        logger.info("Arrêt de l'entraînement demandé")

    def get_training_summary(self) -> dict[str, Any]:
        """Retourne un résumé de l'entraînement"""
        if not self.performance_monitor.metrics_history:
            return {"status": "no_training_data"}

        latest_metrics = self.performance_monitor.metrics_history[-1]

        return {
            "current_phase": self.current_phase.value,
            "latest_accuracy": latest_metrics.accuracy,
            "latest_loss": latest_metrics.loss,
            "current_learning_rate": self.learning_rate,
            "total_iterations": len(self.performance_monitor.metrics_history),
            "adaptations_count": len(self.adaptation_history),
            "performance_trend": self.performance_monitor.get_trend(),
            "training_active": self.training_active,
        }

    def get_adaptation_history(self) -> list[dict[str, Any]]:
        """Retourne l'historique des adaptations"""
        return [
            {
                "action": adapt.action,
                "reason": adapt.reason,
                "confidence": adapt.confidence,
                "timestamp": adapt.timestamp,
                "parameters": adapt.parameters,
            }
            for adapt in self.adaptation_history
        ]


# Instance globale avec configuration par défaut
default_adaptive_trainer = AdaptiveTrainer()
