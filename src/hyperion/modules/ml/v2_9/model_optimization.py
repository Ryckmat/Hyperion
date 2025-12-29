"""
Hyperion v2.9 - Optimisation de Modèles ML
Optimisation automatique des hyperparamètres et performance des modèles
"""

import json
import logging
import time
from dataclasses import asdict, dataclass
from typing import Any

import numpy as np

logger = logging.getLogger(__name__)


@dataclass
class OptimizationConfig:
    """Configuration pour l'optimisation de modèles"""

    optimization_method: str = "random_search"  # random_search, grid_search, bayesian
    max_iterations: int = 50
    cv_folds: int = 5
    scoring_metric: str = "accuracy"
    early_stopping: bool = True
    early_stopping_patience: int = 10
    parallel_jobs: int = 1


@dataclass
class HyperparameterSpace:
    """Espace des hyperparamètres à optimiser"""

    parameter_name: str
    parameter_type: str  # continuous, discrete, categorical
    min_value: float | None = None
    max_value: float | None = None
    values: list[Any] | None = None
    default_value: Any = None


@dataclass
class OptimizationResult:
    """Résultat d'optimisation d'un modèle"""

    optimization_id: str
    model_type: str
    best_params: dict[str, Any]
    best_score: float
    optimization_history: list[dict[str, Any]]
    total_iterations: int
    optimization_time: float
    convergence_achieved: bool


class ModelOptimizer:
    """Optimiseur de modèles ML"""

    def __init__(self, config: OptimizationConfig = None):
        self.config = config or OptimizationConfig()
        self.optimization_history: list[OptimizationResult] = []

    def optimize_model(
        self,
        model_class,
        X_train: np.ndarray,
        y_train: np.ndarray,
        hyperparameter_space: list[HyperparameterSpace],
        X_val: np.ndarray | None = None,
        y_val: np.ndarray | None = None,
    ) -> OptimizationResult:
        """Optimise les hyperparamètres d'un modèle"""
        start_time = time.time()
        optimization_id = f"opt_{int(time.time())}_{hash(str(model_class))}"

        logger.info(f"Démarrage optimisation modèle: {optimization_id}")

        if self.config.optimization_method == "random_search":
            result = self._random_search_optimization(
                model_class, X_train, y_train, hyperparameter_space, X_val, y_val, optimization_id
            )
        elif self.config.optimization_method == "grid_search":
            result = self._grid_search_optimization(
                model_class, X_train, y_train, hyperparameter_space, X_val, y_val, optimization_id
            )
        elif self.config.optimization_method == "bayesian":
            result = self._bayesian_optimization(
                model_class, X_train, y_train, hyperparameter_space, X_val, y_val, optimization_id
            )
        else:
            raise ValueError(
                f"Méthode d'optimisation non supportée: {self.config.optimization_method}"
            )

        result.optimization_time = time.time() - start_time
        self.optimization_history.append(result)

        logger.info(
            f"Optimisation terminée: {optimization_id}, meilleur score: {result.best_score:.4f}"
        )

        return result

    def _random_search_optimization(
        self,
        model_class,
        X_train: np.ndarray,
        y_train: np.ndarray,
        hyperparameter_space: list[HyperparameterSpace],
        X_val: np.ndarray | None,
        y_val: np.ndarray | None,
        optimization_id: str,
    ) -> OptimizationResult:
        """Recherche aléatoire d'hyperparamètres"""
        best_params = {}
        best_score = -np.inf
        optimization_history = []
        convergence_count = 0

        for iteration in range(self.config.max_iterations):
            # Générer des paramètres aléatoires
            current_params = self._sample_random_parameters(hyperparameter_space)

            # Évaluer le modèle
            try:
                score = self._evaluate_model(
                    model_class, current_params, X_train, y_train, X_val, y_val
                )

                # Mettre à jour le meilleur
                if score > best_score:
                    best_score = score
                    best_params = current_params.copy()
                    convergence_count = 0
                else:
                    convergence_count += 1

                # Enregistrer l'historique
                optimization_history.append(
                    {
                        "iteration": iteration,
                        "params": current_params,
                        "score": score,
                        "is_best": score == best_score,
                    }
                )

                logger.debug(f"Iteration {iteration}: score={score:.4f}, meilleur={best_score:.4f}")

                # Arrêt précoce
                if (
                    self.config.early_stopping
                    and convergence_count >= self.config.early_stopping_patience
                ):
                    logger.info(f"Arrêt précoce après {iteration+1} itérations")
                    break

            except Exception as e:
                logger.warning(f"Erreur évaluation iteration {iteration}: {e}")
                continue

        return OptimizationResult(
            optimization_id=optimization_id,
            model_type=str(model_class),
            best_params=best_params,
            best_score=best_score,
            optimization_history=optimization_history,
            total_iterations=len(optimization_history),
            optimization_time=0.0,  # Sera mis à jour
            convergence_achieved=convergence_count < self.config.early_stopping_patience,
        )

    def _grid_search_optimization(
        self,
        model_class,
        X_train: np.ndarray,
        y_train: np.ndarray,
        hyperparameter_space: list[HyperparameterSpace],
        X_val: np.ndarray | None,
        y_val: np.ndarray | None,
        optimization_id: str,
    ) -> OptimizationResult:
        """Recherche sur grille d'hyperparamètres"""
        # Générer toutes les combinaisons possibles
        param_combinations = self._generate_grid_combinations(hyperparameter_space)

        best_params = {}
        best_score = -np.inf
        optimization_history = []

        for i, params in enumerate(param_combinations):
            if i >= self.config.max_iterations:
                break

            try:
                score = self._evaluate_model(model_class, params, X_train, y_train, X_val, y_val)

                if score > best_score:
                    best_score = score
                    best_params = params.copy()

                optimization_history.append(
                    {
                        "iteration": i,
                        "params": params,
                        "score": score,
                        "is_best": score == best_score,
                    }
                )

                logger.debug(f"Grid iteration {i}: score={score:.4f}")

            except Exception as e:
                logger.warning(f"Erreur évaluation grid {i}: {e}")
                continue

        return OptimizationResult(
            optimization_id=optimization_id,
            model_type=str(model_class),
            best_params=best_params,
            best_score=best_score,
            optimization_history=optimization_history,
            total_iterations=len(optimization_history),
            optimization_time=0.0,
            convergence_achieved=True,
        )

    def _bayesian_optimization(
        self,
        model_class,
        X_train: np.ndarray,
        y_train: np.ndarray,
        hyperparameter_space: list[HyperparameterSpace],
        X_val: np.ndarray | None,
        y_val: np.ndarray | None,
        optimization_id: str,
    ) -> OptimizationResult:
        """Optimisation bayésienne (implémentation simplifiée)"""
        # Pour cette version simplifiée, on utilise une stratégie adaptative
        best_params = {}
        best_score = -np.inf
        optimization_history = []

        # Commencer par des échantillons aléatoires
        initial_samples = min(10, self.config.max_iterations // 4)

        for iteration in range(self.config.max_iterations):
            if iteration < initial_samples:
                # Phase d'exploration aléatoire
                current_params = self._sample_random_parameters(hyperparameter_space)
            else:
                # Phase d'exploitation/exploration guidée
                current_params = self._sample_guided_parameters(
                    hyperparameter_space, optimization_history, best_params
                )

            try:
                score = self._evaluate_model(
                    model_class, current_params, X_train, y_train, X_val, y_val
                )

                if score > best_score:
                    best_score = score
                    best_params = current_params.copy()

                optimization_history.append(
                    {
                        "iteration": iteration,
                        "params": current_params,
                        "score": score,
                        "is_best": score == best_score,
                        "acquisition_type": (
                            "exploration" if iteration < initial_samples else "exploitation"
                        ),
                    }
                )

                logger.debug(f"Bayesian iteration {iteration}: score={score:.4f}")

            except Exception as e:
                logger.warning(f"Erreur évaluation bayésienne {iteration}: {e}")
                continue

        return OptimizationResult(
            optimization_id=optimization_id,
            model_type=str(model_class),
            best_params=best_params,
            best_score=best_score,
            optimization_history=optimization_history,
            total_iterations=len(optimization_history),
            optimization_time=0.0,
            convergence_achieved=True,
        )

    def _sample_random_parameters(
        self, hyperparameter_space: list[HyperparameterSpace]
    ) -> dict[str, Any]:
        """Échantillonne des paramètres aléatoirement"""
        params = {}

        for param_space in hyperparameter_space:
            if param_space.parameter_type == "continuous":
                if param_space.min_value is not None and param_space.max_value is not None:
                    value = np.random.uniform(param_space.min_value, param_space.max_value)
                    params[param_space.parameter_name] = value
                else:
                    params[param_space.parameter_name] = param_space.default_value

            elif param_space.parameter_type == "discrete":
                if param_space.min_value is not None and param_space.max_value is not None:
                    value = np.random.randint(
                        int(param_space.min_value), int(param_space.max_value) + 1
                    )
                    params[param_space.parameter_name] = value
                else:
                    params[param_space.parameter_name] = param_space.default_value

            elif param_space.parameter_type == "categorical":
                if param_space.values:
                    value = np.random.choice(param_space.values)
                    params[param_space.parameter_name] = value
                else:
                    params[param_space.parameter_name] = param_space.default_value

            else:
                params[param_space.parameter_name] = param_space.default_value

        return params

    def _sample_guided_parameters(
        self,
        hyperparameter_space: list[HyperparameterSpace],
        _history: list[dict[str, Any]],
        best_params: dict[str, Any],
    ) -> dict[str, Any]:
        """Échantillonne des paramètres de manière guidée (simplifié)"""
        # Stratégie simple: mélange exploration/exploitation
        if np.random.random() < 0.3:  # 30% exploration
            return self._sample_random_parameters(hyperparameter_space)
        else:  # 70% exploitation autour des meilleurs paramètres
            return self._sample_around_best(hyperparameter_space, best_params)

    def _sample_around_best(
        self, hyperparameter_space: list[HyperparameterSpace], best_params: dict[str, Any]
    ) -> dict[str, Any]:
        """Échantillonne autour des meilleurs paramètres"""
        params = best_params.copy()

        for param_space in hyperparameter_space:
            param_name = param_space.parameter_name

            if param_name not in params:
                continue

            if param_space.parameter_type == "continuous":
                current_value = params[param_name]
                # Ajouter du bruit gaussien
                noise_scale = (param_space.max_value - param_space.min_value) * 0.1
                new_value = np.random.normal(current_value, noise_scale)
                # Contraindre dans les limites
                new_value = np.clip(new_value, param_space.min_value, param_space.max_value)
                params[param_name] = new_value

            elif param_space.parameter_type == "discrete":
                current_value = params[param_name]
                # Petit décalage aléatoire
                shift = np.random.randint(-2, 3)
                new_value = current_value + shift
                # Contraindre dans les limites
                new_value = np.clip(new_value, param_space.min_value, param_space.max_value)
                params[param_name] = int(new_value)

            elif param_space.parameter_type == "categorical":
                # Parfois changer, parfois garder
                if np.random.random() < 0.3 and param_space.values:
                    params[param_name] = np.random.choice(param_space.values)

        return params

    def _generate_grid_combinations(
        self, hyperparameter_space: list[HyperparameterSpace]
    ) -> list[dict[str, Any]]:
        """Génère toutes les combinaisons pour la recherche sur grille"""
        import itertools

        param_grids = {}

        for param_space in hyperparameter_space:
            param_name = param_space.parameter_name

            if param_space.parameter_type == "continuous":
                # Discrétiser l'espace continu
                if param_space.min_value is not None and param_space.max_value is not None:
                    values = np.linspace(param_space.min_value, param_space.max_value, 5)
                    param_grids[param_name] = values.tolist()
                else:
                    param_grids[param_name] = [param_space.default_value]

            elif param_space.parameter_type == "discrete":
                if param_space.min_value is not None and param_space.max_value is not None:
                    values = list(range(int(param_space.min_value), int(param_space.max_value) + 1))
                    param_grids[param_name] = values
                else:
                    param_grids[param_name] = [param_space.default_value]

            elif param_space.parameter_type == "categorical":
                if param_space.values:
                    param_grids[param_name] = param_space.values
                else:
                    param_grids[param_name] = [param_space.default_value]

            else:
                param_grids[param_name] = [param_space.default_value]

        # Générer toutes les combinaisons
        param_names = list(param_grids.keys())
        param_values = [param_grids[name] for name in param_names]

        combinations = []
        for combination in itertools.product(*param_values):
            param_dict = dict(zip(param_names, combination, strict=False))
            combinations.append(param_dict)

        return combinations

    def _evaluate_model(
        self,
        model_class,
        params: dict[str, Any],
        X_train: np.ndarray,
        y_train: np.ndarray,
        X_val: np.ndarray | None = None,
        y_val: np.ndarray | None = None,
    ) -> float:
        """Évalue un modèle avec des paramètres donnés"""
        try:
            # Créer le modèle avec les paramètres
            model = model_class(**params)

            # Entraîner le modèle
            model.fit(X_train, y_train)

            # Évaluer
            if X_val is not None and y_val is not None:
                # Utiliser l'ensemble de validation
                if hasattr(model, "score"):
                    score = model.score(X_val, y_val)
                else:
                    predictions = model.predict(X_val)
                    score = self._calculate_score(y_val, predictions)
            else:
                # Cross-validation sur l'ensemble d'entraînement
                score = self._cross_validate_model(model, X_train, y_train)

            return score

        except Exception as e:
            logger.warning(f"Erreur évaluation modèle: {e}")
            return -np.inf

    def _cross_validate_model(self, model, X: np.ndarray, y: np.ndarray) -> float:
        """Validation croisée simple"""
        try:
            from sklearn.model_selection import cross_val_score

            scores = cross_val_score(
                model, X, y, cv=self.config.cv_folds, scoring=self.config.scoring_metric
            )
            return scores.mean()
        except ImportError:
            # Validation croisée manuelle simple
            from sklearn.model_selection import KFold

            kfold = KFold(n_splits=self.config.cv_folds, shuffle=True, random_state=42)
            scores = []

            for train_idx, val_idx in kfold.split(X):
                X_train_fold, X_val_fold = X[train_idx], X[val_idx]
                y_train_fold, y_val_fold = y[train_idx], y[val_idx]

                # Créer une nouvelle instance du modèle
                fold_model = type(model)(**model.get_params())
                fold_model.fit(X_train_fold, y_train_fold)

                if hasattr(fold_model, "score"):
                    score = fold_model.score(X_val_fold, y_val_fold)
                else:
                    predictions = fold_model.predict(X_val_fold)
                    score = self._calculate_score(y_val_fold, predictions)

                scores.append(score)

            return np.mean(scores)
        except Exception:
            # Fallback: score sur l'ensemble d'entraînement
            if hasattr(model, "score"):
                return model.score(X, y)
            else:
                predictions = model.predict(X)
                return self._calculate_score(y, predictions)

    def _calculate_score(self, y_true: np.ndarray, y_pred: np.ndarray) -> float:
        """Calcule un score simple"""
        if self.config.scoring_metric == "accuracy":
            return np.mean(y_true == y_pred)
        elif self.config.scoring_metric == "mse":
            return -np.mean((y_true - y_pred) ** 2)
        elif self.config.scoring_metric == "mae":
            return -np.mean(np.abs(y_true - y_pred))
        else:
            # Défaut: accuracy pour classification
            return np.mean(y_true == y_pred)

    def get_optimization_history(self) -> list[OptimizationResult]:
        """Retourne l'historique des optimisations"""
        return self.optimization_history.copy()

    def export_results(self, optimization_id: str, output_path: str) -> bool:
        """Exporte les résultats d'optimisation"""
        try:
            result = next(
                (r for r in self.optimization_history if r.optimization_id == optimization_id), None
            )
            if not result:
                logger.error(f"Optimisation non trouvée: {optimization_id}")
                return False

            with open(output_path, "w", encoding="utf-8") as f:
                json.dump(asdict(result), f, indent=2, ensure_ascii=False)

            logger.info(f"Résultats exportés: {output_path}")
            return True

        except Exception as e:
            logger.error(f"Erreur export résultats: {e}")
            return False


class AutoML:
    """Interface AutoML pour optimisation automatique"""

    def __init__(self):
        self.optimizer = ModelOptimizer()
        self.model_configs = self._get_default_model_configs()

    def _get_default_model_configs(self) -> dict[str, dict[str, Any]]:
        """Configurations par défaut pour différents types de modèles"""
        return {
            "random_forest": {
                "hyperparameters": [
                    HyperparameterSpace("n_estimators", "discrete", 10, 200, default_value=100),
                    HyperparameterSpace("max_depth", "discrete", 3, 20, default_value=None),
                    HyperparameterSpace("min_samples_split", "discrete", 2, 20, default_value=2),
                    HyperparameterSpace("min_samples_leaf", "discrete", 1, 10, default_value=1),
                ]
            },
            "gradient_boosting": {
                "hyperparameters": [
                    HyperparameterSpace("n_estimators", "discrete", 50, 300, default_value=100),
                    HyperparameterSpace(
                        "learning_rate", "continuous", 0.01, 0.3, default_value=0.1
                    ),
                    HyperparameterSpace("max_depth", "discrete", 3, 10, default_value=6),
                ]
            },
            "svm": {
                "hyperparameters": [
                    HyperparameterSpace("C", "continuous", 0.1, 100, default_value=1.0),
                    HyperparameterSpace(
                        "gamma",
                        "categorical",
                        values=["scale", "auto", 0.001, 0.01, 0.1, 1],
                        default_value="scale",
                    ),
                    HyperparameterSpace(
                        "kernel",
                        "categorical",
                        values=["rbf", "poly", "sigmoid"],
                        default_value="rbf",
                    ),
                ]
            },
        }

    def auto_optimize(
        self,
        model_type: str,
        X_train: np.ndarray,
        y_train: np.ndarray,
        X_val: np.ndarray | None = None,
        y_val: np.ndarray | None = None,
    ) -> OptimizationResult:
        """Optimisation automatique d'un type de modèle"""
        if model_type not in self.model_configs:
            raise ValueError(f"Type de modèle non supporté: {model_type}")

        # Pour cette implémentation, on simule avec des modèles factices
        model_config = self.model_configs[model_type]

        class DummyModel:
            def __init__(self, **params):
                self.params = params

            def fit(self, _X, _y):
                return self

            def predict(self, X):
                return np.random.randint(0, 2, size=X.shape[0])

            def score(self, X, y):
                pred = self.predict(X)
                return np.mean(pred == y) + np.random.normal(0, 0.1)

            def get_params(self):
                return self.params

        return self.optimizer.optimize_model(
            DummyModel, X_train, y_train, model_config["hyperparameters"], X_val, y_val
        )


# Instances globales
default_model_optimizer = ModelOptimizer()
default_automl = AutoML()


# Fonctions utilitaires
def optimize_model(
    model_class,
    X_train: np.ndarray,
    y_train: np.ndarray,
    hyperparameter_space: list[HyperparameterSpace],
) -> OptimizationResult:
    """Optimisation rapide d'un modèle"""
    return default_model_optimizer.optimize_model(
        model_class, X_train, y_train, hyperparameter_space
    )


def auto_optimize_model(
    model_type: str, X_train: np.ndarray, y_train: np.ndarray
) -> OptimizationResult:
    """Auto-optimisation d'un modèle par type"""
    return default_automl.auto_optimize(model_type, X_train, y_train)
