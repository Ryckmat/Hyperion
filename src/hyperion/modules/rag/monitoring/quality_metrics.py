"""
Système de tracking et agrégation des métriques qualité RAG

Ce module collecte, stocke et agrège les métriques de qualité
des réponses pour monitoring et amélioration continue.
"""

import logging
import sqlite3
from datetime import datetime, timedelta
from pathlib import Path

logger = logging.getLogger(__name__)


class QualityMetricsTracker:
    """
    Collecteur et agrégateur de métriques qualité RAG

    Stocke les métriques dans SQLite pour persistance et
    fournit des agrégations pour monitoring et dashboards.
    """

    def __init__(self, db_path: str = "data/quality_metrics.db"):
        """
        Initialiser le tracker

        Args:
            db_path: Chemin vers base SQLite des métriques
        """
        self.db_path = Path(db_path)
        self.db_path.parent.mkdir(parents=True, exist_ok=True)

        # Cache en mémoire pour performances
        self._metrics_cache = {}
        self._cache_timestamp = None
        self._cache_ttl_seconds = 30  # Cache 30 secondes

        # Initialiser base de données
        self._init_database()

        logger.info(f"QualityMetricsTracker initialisé - DB: {self.db_path}")

    def _init_database(self):
        """Initialiser schéma base de données SQLite"""
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()

                # Table principale des métriques
                cursor.execute(
                    """
                    CREATE TABLE IF NOT EXISTS response_quality (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        timestamp DATETIME DEFAULT CURRENT_TIMESTAMP,
                        question_hash TEXT NOT NULL,
                        repo_filter TEXT,

                        -- Scores principaux
                        confidence REAL NOT NULL,
                        quality_grade TEXT NOT NULL,
                        action TEXT NOT NULL,

                        -- Analyse hallucinations
                        hallucination_detected BOOLEAN NOT NULL,
                        hallucination_severity TEXT NOT NULL,
                        semantic_consistency REAL,

                        -- Métriques techniques
                        processing_time REAL,
                        validation_time REAL,
                        num_sources INTEGER,
                        avg_source_score REAL,

                        -- Détails réponse
                        answer_length INTEGER,
                        question_length INTEGER,
                        primary_weakness TEXT,

                        -- Métadonnées
                        validator_version TEXT,
                        answer_modified BOOLEAN DEFAULT FALSE
                    )
                """
                )

                # Index pour performances
                cursor.execute(
                    """
                    CREATE INDEX IF NOT EXISTS idx_timestamp
                    ON response_quality(timestamp)
                """
                )

                cursor.execute(
                    """
                    CREATE INDEX IF NOT EXISTS idx_repo_timestamp
                    ON response_quality(repo_filter, timestamp)
                """
                )

                cursor.execute(
                    """
                    CREATE INDEX IF NOT EXISTS idx_action_timestamp
                    ON response_quality(action, timestamp)
                """
                )

                # Table alertes qualité
                cursor.execute(
                    """
                    CREATE TABLE IF NOT EXISTS quality_alerts (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        timestamp DATETIME DEFAULT CURRENT_TIMESTAMP,
                        alert_type TEXT NOT NULL,
                        severity TEXT NOT NULL,
                        message TEXT NOT NULL,
                        threshold_value REAL,
                        actual_value REAL,
                        resolved BOOLEAN DEFAULT FALSE,
                        resolved_at DATETIME
                    )
                """
                )

                conn.commit()
                logger.debug("Schéma base de données initialisé")

        except Exception as e:
            logger.error(f"Erreur initialisation base données: {e}")
            raise

    def track_response(
        self,
        validation_result: dict,
        processing_time: float,
        question: str,
        repo: str = None,
        **_kwargs,
    ):
        """
        Enregistrer métriques d'une réponse validée

        Args:
            validation_result: Résultat complet de validation
            processing_time: Temps traitement total de la requête
            question: Question pour hash anonyme
            repo: Repository filtré (optionnel)
            **kwargs: Métadonnées additionnelles
        """
        try:
            # Extraire données du résultat validation
            hall_analysis = validation_result["hallucination_analysis"]
            validation_meta = validation_result["validation_metadata"]

            # Hash anonyme de la question
            question_hash = str(abs(hash(question)) % 100000)

            # Préparer données pour insertion
            metrics_data = {
                "question_hash": question_hash,
                "repo_filter": repo or "all",
                "confidence": validation_result["confidence"],
                "quality_grade": validation_result["quality_grade"],
                "action": validation_result["action"],
                "hallucination_detected": hall_analysis["is_hallucination"],
                "hallucination_severity": hall_analysis["severity"],
                "semantic_consistency": hall_analysis.get("semantic_consistency", 0.0),
                "processing_time": processing_time,
                "validation_time": validation_meta.get("validation_time", 0.0),
                "num_sources": validation_meta.get("num_sources", 0),
                "avg_source_score": validation_meta.get("avg_source_score", 0.0),
                "answer_length": validation_meta.get("answer_length", 0),
                "question_length": validation_meta.get("question_length", 0),
                "primary_weakness": validation_result["confidence_factors"]["primary_weakness"],
                "validator_version": validation_meta.get("validator_version", "unknown"),
                "answer_modified": validation_result.get("answer_modified", False),
            }

            # Insérer en base
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()

                placeholders = ", ".join(["?" for _ in metrics_data.values()])
                columns = ", ".join(metrics_data.keys())

                cursor.execute(
                    f"""
                    INSERT INTO response_quality ({columns})
                    VALUES ({placeholders})
                """,
                    list(metrics_data.values()),
                )

                conn.commit()

            # Invalider cache
            self._invalidate_cache()

            # Vérifier alertes
            self._check_quality_alerts(metrics_data)

            logger.debug(f"Métriques trackées: {question_hash} - {validation_result['action']}")

        except Exception as e:
            logger.error(f"Erreur tracking métriques: {e}")

    def get_metrics_summary(self, hours: int = 24, repo: str = None) -> dict:
        """
        Obtenir résumé des métriques sur une période

        Args:
            hours: Période en heures (défaut 24h)
            repo: Filtrer sur repository (optionnel)

        Returns:
            Dictionnaire avec métriques agrégées
        """
        try:
            # Vérifier cache
            cache_key = f"summary_{hours}_{repo or 'all'}"
            if self._is_cache_valid() and cache_key in self._metrics_cache:
                return self._metrics_cache[cache_key]

            since = datetime.now() - timedelta(hours=hours)

            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()

                # Construire clause WHERE
                where_clause = "WHERE timestamp > ?"
                params = [since]

                if repo:
                    where_clause += " AND repo_filter = ?"
                    params.append(repo)

                # Métriques principales
                cursor.execute(
                    f"""
                    SELECT
                        COUNT(*) as total_responses,
                        AVG(confidence) as avg_confidence,
                        COUNT(CASE WHEN action = 'accept' THEN 1 END) as accepted,
                        COUNT(CASE WHEN action = 'flag' THEN 1 END) as flagged,
                        COUNT(CASE WHEN action = 'reject' THEN 1 END) as rejected,
                        COUNT(CASE WHEN hallucination_detected = 1 THEN 1 END) as hallucinations,
                        COUNT(CASE WHEN answer_modified = 1 THEN 1 END) as modified_answers,
                        AVG(processing_time) as avg_processing_time,
                        AVG(validation_time) as avg_validation_time,
                        AVG(semantic_consistency) as avg_semantic_consistency
                    FROM response_quality
                    {where_clause}
                """,
                    params,
                )

                main_metrics = cursor.fetchone()

                # Distribution par grade qualité
                cursor.execute(
                    f"""
                    SELECT quality_grade, COUNT(*)
                    FROM response_quality
                    {where_clause}
                    GROUP BY quality_grade
                    ORDER BY COUNT(*) DESC
                """,
                    params,
                )

                quality_distribution = dict(cursor.fetchall())

                # Distribution par sévérité hallucinations
                cursor.execute(
                    f"""
                    SELECT hallucination_severity, COUNT(*)
                    FROM response_quality
                    {where_clause}
                    GROUP BY hallucination_severity
                    ORDER BY COUNT(*) DESC
                """,
                    params,
                )

                hallucination_distribution = dict(cursor.fetchall())

                # Top faiblesses
                cursor.execute(
                    f"""
                    SELECT primary_weakness, COUNT(*) as count
                    FROM response_quality
                    {where_clause}
                    GROUP BY primary_weakness
                    ORDER BY count DESC
                    LIMIT 5
                """,
                    params,
                )

                top_weaknesses = [
                    {"weakness": row[0], "count": row[1]} for row in cursor.fetchall()
                ]

            # Calculer ratios et métriques dérivées
            (
                total,
                avg_conf,
                accepted,
                flagged,
                rejected,
                halluc,
                modified,
                avg_time,
                avg_val_time,
                avg_sem,
            ) = main_metrics

            summary = {
                "period_hours": hours,
                "repository": repo or "all",
                "total_responses": total or 0,
                "avg_confidence": round(avg_conf or 0, 3),
                "acceptance_rate": round((accepted or 0) / max(total, 1) * 100, 1),
                "flag_rate": round((flagged or 0) / max(total, 1) * 100, 1),
                "rejection_rate": round((rejected or 0) / max(total, 1) * 100, 1),
                "hallucination_rate": round((halluc or 0) / max(total, 1) * 100, 1),
                "answer_modification_rate": round((modified or 0) / max(total, 1) * 100, 1),
                "avg_processing_time": round(avg_time or 0, 2),
                "avg_validation_time": round(avg_val_time or 0, 3),
                "avg_semantic_consistency": round(avg_sem or 0, 3),
                "quality_distribution": quality_distribution,
                "hallucination_distribution": hallucination_distribution,
                "top_weaknesses": top_weaknesses,
                "generated_at": datetime.now().isoformat(),
            }

            # Cache résultat
            self._cache_result(cache_key, summary)

            return summary

        except Exception as e:
            logger.error(f"Erreur calcul métriques summary: {e}")
            return self._get_empty_summary(hours, repo)

    def get_trend_data(self, days: int = 7, repo: str = None) -> list[dict]:
        """
        Obtenir données de tendance pour graphiques

        Args:
            days: Nombre de jours (défaut 7)
            repo: Repository à filtrer (optionnel)

        Returns:
            Liste de points de données par jour
        """
        try:
            since = datetime.now() - timedelta(days=days)

            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()

                where_clause = "WHERE timestamp > ?"
                params = [since]

                if repo:
                    where_clause += " AND repo_filter = ?"
                    params.append(repo)

                cursor.execute(
                    f"""
                    SELECT
                        DATE(timestamp) as date,
                        COUNT(*) as total_responses,
                        AVG(confidence) as avg_confidence,
                        COUNT(CASE WHEN action = 'accept' THEN 1 END) * 100.0 / COUNT(*) as acceptance_rate,
                        COUNT(CASE WHEN hallucination_detected = 1 THEN 1 END) * 100.0 / COUNT(*) as hallucination_rate,
                        AVG(processing_time) as avg_processing_time,
                        AVG(semantic_consistency) as avg_semantic_consistency
                    FROM response_quality
                    {where_clause}
                    GROUP BY DATE(timestamp)
                    ORDER BY date
                """,
                    params,
                )

                trend_data = [
                    {
                        "date": row[0],
                        "total_responses": row[1],
                        "avg_confidence": round(row[2], 3),
                        "acceptance_rate": round(row[3], 1),
                        "hallucination_rate": round(row[4], 1),
                        "avg_processing_time": round(row[5], 2),
                        "avg_semantic_consistency": round(row[6], 3),
                    }
                    for row in cursor.fetchall()
                ]

                return trend_data

        except Exception as e:
            logger.error(f"Erreur calcul trends: {e}")
            return []

    def get_quality_alerts(self, resolved: bool = False) -> list[dict]:
        """
        Obtenir alertes qualité actives ou résolues

        Args:
            resolved: Inclure alertes résolues (défaut False)

        Returns:
            Liste d'alertes avec détails
        """
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()

                where_clause = "WHERE resolved = ?" if not resolved else ""
                params = [False] if not resolved else []

                cursor.execute(
                    f"""
                    SELECT
                        id, timestamp, alert_type, severity, message,
                        threshold_value, actual_value, resolved, resolved_at
                    FROM quality_alerts
                    {where_clause}
                    ORDER BY timestamp DESC
                    LIMIT 50
                """,
                    params,
                )

                alerts = [
                    {
                        "id": row[0],
                        "timestamp": row[1],
                        "alert_type": row[2],
                        "severity": row[3],
                        "message": row[4],
                        "threshold_value": row[5],
                        "actual_value": row[6],
                        "resolved": bool(row[7]),
                        "resolved_at": row[8],
                    }
                    for row in cursor.fetchall()
                ]

                return alerts

        except Exception as e:
            logger.error(f"Erreur récupération alertes: {e}")
            return []

    def _check_quality_alerts(self, _metrics_data: dict):
        """
        Vérifier conditions d'alerte basées sur nouvelles métriques

        Args:
            metrics_data: Données métriques de la réponse courante
        """
        try:
            # Obtenir métriques récentes (1h) pour détecter tendances
            recent_metrics = self.get_metrics_summary(hours=1)

            alerts_to_create = []

            # Alerte taux hallucination élevé
            if recent_metrics["hallucination_rate"] > 25 and recent_metrics["total_responses"] >= 5:
                alerts_to_create.append(
                    {
                        "alert_type": "HIGH_HALLUCINATION_RATE",
                        "severity": "HIGH",
                        "message": f"Taux d'hallucination élevé: {recent_metrics['hallucination_rate']:.1f}% (>25%)",
                        "threshold_value": 25.0,
                        "actual_value": recent_metrics["hallucination_rate"],
                    }
                )

            # Alerte taux rejet élevé
            if recent_metrics["rejection_rate"] > 15 and recent_metrics["total_responses"] >= 5:
                alerts_to_create.append(
                    {
                        "alert_type": "HIGH_REJECTION_RATE",
                        "severity": "MEDIUM",
                        "message": f"Taux de rejet élevé: {recent_metrics['rejection_rate']:.1f}% (>15%)",
                        "threshold_value": 15.0,
                        "actual_value": recent_metrics["rejection_rate"],
                    }
                )

            # Alerte confiance faible
            if recent_metrics["avg_confidence"] < 0.6 and recent_metrics["total_responses"] >= 5:
                alerts_to_create.append(
                    {
                        "alert_type": "LOW_CONFIDENCE",
                        "severity": "MEDIUM",
                        "message": f"Confiance moyenne faible: {recent_metrics['avg_confidence']:.2f} (<0.6)",
                        "threshold_value": 0.6,
                        "actual_value": recent_metrics["avg_confidence"],
                    }
                )

            # Alerte validation lente
            if (
                recent_metrics["avg_validation_time"] > 1.0
                and recent_metrics["total_responses"] >= 3
            ):
                alerts_to_create.append(
                    {
                        "alert_type": "SLOW_VALIDATION",
                        "severity": "LOW",
                        "message": f"Validation lente: {recent_metrics['avg_validation_time']:.2f}s (>1.0s)",
                        "threshold_value": 1.0,
                        "actual_value": recent_metrics["avg_validation_time"],
                    }
                )

            # Créer alertes en base
            if alerts_to_create:
                self._create_alerts(alerts_to_create)

        except Exception as e:
            logger.error(f"Erreur vérification alertes: {e}")

    def _create_alerts(self, alerts: list[dict]):
        """Créer alertes en base de données"""
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()

                for alert in alerts:
                    # Vérifier si alerte similaire existe déjà (dernière heure)
                    recent_alert = cursor.execute(
                        """
                        SELECT id FROM quality_alerts
                        WHERE alert_type = ?
                        AND timestamp > datetime('now', '-1 hour')
                        AND resolved = FALSE
                    """,
                        (alert["alert_type"],),
                    ).fetchone()

                    if not recent_alert:  # Pas d'alerte récente similaire
                        cursor.execute(
                            """
                            INSERT INTO quality_alerts
                            (alert_type, severity, message, threshold_value, actual_value)
                            VALUES (?, ?, ?, ?, ?)
                        """,
                            (
                                alert["alert_type"],
                                alert["severity"],
                                alert["message"],
                                alert["threshold_value"],
                                alert["actual_value"],
                            ),
                        )

                        logger.warning(f"Alerte créée: {alert['alert_type']} - {alert['message']}")

                conn.commit()

        except Exception as e:
            logger.error(f"Erreur création alertes: {e}")

    def _is_cache_valid(self) -> bool:
        """Vérifier validité du cache"""
        if not self._cache_timestamp:
            return False

        return (datetime.now() - self._cache_timestamp).total_seconds() < self._cache_ttl_seconds

    def _cache_result(self, key: str, result: dict):
        """Mettre en cache un résultat"""
        if not hasattr(self, "_metrics_cache"):
            self._metrics_cache = {}

        self._metrics_cache[key] = result
        self._cache_timestamp = datetime.now()

    def _invalidate_cache(self):
        """Invalider le cache"""
        self._metrics_cache = {}
        self._cache_timestamp = None

    def _get_empty_summary(self, hours: int, repo: str) -> dict:
        """Résumé vide en cas d'erreur"""
        return {
            "period_hours": hours,
            "repository": repo or "all",
            "total_responses": 0,
            "avg_confidence": 0.0,
            "acceptance_rate": 0.0,
            "flag_rate": 0.0,
            "rejection_rate": 0.0,
            "hallucination_rate": 0.0,
            "answer_modification_rate": 0.0,
            "avg_processing_time": 0.0,
            "avg_validation_time": 0.0,
            "avg_semantic_consistency": 0.0,
            "quality_distribution": {},
            "hallucination_distribution": {},
            "top_weaknesses": [],
            "generated_at": datetime.now().isoformat(),
            "error": "Erreur calcul métriques",
        }

    def get_database_stats(self) -> dict:
        """Obtenir statistiques base de données"""
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()

                # Taille base
                cursor.execute("SELECT COUNT(*) FROM response_quality")
                total_records = cursor.fetchone()[0]

                # Plus ancien/récent
                cursor.execute(
                    """
                    SELECT MIN(timestamp), MAX(timestamp)
                    FROM response_quality
                """
                )
                oldest, newest = cursor.fetchone()

                # Taille fichier
                file_size = self.db_path.stat().st_size if self.db_path.exists() else 0

                return {
                    "total_records": total_records,
                    "oldest_record": oldest,
                    "newest_record": newest,
                    "database_size_bytes": file_size,
                    "database_size_mb": round(file_size / (1024 * 1024), 2),
                    "database_path": str(self.db_path),
                }

        except Exception as e:
            logger.error(f"Erreur stats base: {e}")
            return {"error": str(e)}
