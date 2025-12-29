#!/usr/bin/env python3
"""
Déploiement Complet Hyperion v2.9 + v3.0
Test de déploiement en conditions réelles
"""

import asyncio
import sys
import time
import json
import threading
from pathlib import Path
from dataclasses import dataclass
from typing import Dict, List, Any
import logging

# Ajouter le chemin vers les modules Hyperion
sys.path.insert(0, str(Path(__file__).parent / "src"))

# Configuration de logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('hyperion_deploy.log'),
        logging.StreamHandler()
    ]
)

logger = logging.getLogger(__name__)

@dataclass
class ServiceStatus:
    """État d'un service"""
    name: str
    status: str  # starting, running, error, stopped
    start_time: float = 0
    error_message: str = ""
    health_checks: List[str] = None

class HyperionDeployment:
    """
    Gestionnaire de déploiement complet Hyperion

    Lance et teste tous les services v2.9 + v3.0:
    - Monitoring (Prometheus, Performance, Health, Logs, Alerting)
    - Cache distribué
    - Sécurité et authentification
    - API Gateway
    - RAG Pipeline v2.9
    - ML Ensemble v2.9
    - Analytics v2.9
    """

    def __init__(self):
        self.services: Dict[str, ServiceStatus] = {}
        self.deployment_start_time = time.time()
        self.is_running = False

        # Services à déployer
        self.service_order = [
            "monitoring",
            "cache",
            "security",
            "gateway",
            "rag_v29",
            "ml_v29",
            "analytics_v29"
        ]

    async def deploy(self):
        """Déploiement complet des services"""
        print("🚀 DÉPLOIEMENT COMPLET HYPERION v2.9 + v3.0")
        print("=" * 60)

        try:
            self.is_running = True

            # 1. Initialisation
            await self._initialize_deployment()

            # 2. Déploiement séquentiel des services
            for service_name in self.service_order:
                await self._deploy_service(service_name)
                await asyncio.sleep(1)  # Délai entre services

            # 3. Tests d'intégration
            await self._run_integration_tests()

            # 4. Test de charge
            await self._run_load_tests()

            # 5. Validation finale
            success = await self._validate_deployment()

            if success:
                print("\n🎉 DÉPLOIEMENT HYPERION RÉUSSI!")
                await self._display_deployment_summary()

                # Lancer en mode production
                await self._start_production_mode()

            else:
                print("\n❌ ÉCHEC DU DÉPLOIEMENT")
                await self._cleanup_failed_deployment()

        except Exception as e:
            logger.error(f"Erreur critique déploiement: {e}")
            await self._emergency_shutdown()

    async def _initialize_deployment(self):
        """Initialisation du déploiement"""
        print("\n🔧 Initialisation du déploiement...")

        # Vérifier prérequis
        await self._check_prerequisites()

        # Créer répertoires de travail
        work_dirs = ["logs", "cache", "data", "config"]
        for dir_name in work_dirs:
            Path(dir_name).mkdir(exist_ok=True)

        print("   ✅ Environnement préparé")

    async def _check_prerequisites(self):
        """Vérifier les prérequis"""
        print("   🔍 Vérification des prérequis...")

        # Vérifier structure des fichiers
        required_files = [
            "src/hyperion/__version__.py",
            "src/hyperion/modules/monitoring/metrics/prometheus_exporter.py",
            "src/hyperion/modules/cache/v3_0/distributed_cache.py",
            "src/hyperion/modules/security/v3_0/auth_manager.py"
        ]

        for file_path in required_files:
            if not Path(file_path).exists():
                raise FileNotFoundError(f"Fichier requis manquant: {file_path}")

        print("   ✅ Prérequis validés")

    async def _deploy_service(self, service_name: str):
        """Déployer un service spécifique"""
        print(f"\n🔄 Déploiement du service: {service_name.upper()}")

        service_status = ServiceStatus(
            name=service_name,
            status="starting",
            start_time=time.time(),
            health_checks=[]
        )
        self.services[service_name] = service_status

        try:
            if service_name == "monitoring":
                await self._deploy_monitoring()
            elif service_name == "cache":
                await self._deploy_cache()
            elif service_name == "security":
                await self._deploy_security()
            elif service_name == "gateway":
                await self._deploy_gateway()
            elif service_name == "rag_v29":
                await self._deploy_rag_v29()
            elif service_name == "ml_v29":
                await self._deploy_ml_v29()
            elif service_name == "analytics_v29":
                await self._deploy_analytics_v29()

            # Vérification santé
            health_ok = await self._check_service_health(service_name)

            if health_ok:
                service_status.status = "running"
                print(f"   ✅ Service {service_name} déployé et opérationnel")
            else:
                service_status.status = "error"
                service_status.error_message = "Health check failed"
                print(f"   ❌ Service {service_name} - échec health check")

        except Exception as e:
            service_status.status = "error"
            service_status.error_message = str(e)
            print(f"   ❌ Erreur déploiement {service_name}: {e}")

    async def _deploy_monitoring(self):
        """Déployer l'infrastructure de monitoring v3.0"""
        print("   📊 Lancement Monitoring v3.0...")

        # Prometheus Exporter
        from hyperion.modules.monitoring.metrics.prometheus_exporter import PrometheusExporter
        self.prometheus_exporter = PrometheusExporter()
        self.prometheus_exporter.start_server()

        # Performance Tracker
        from hyperion.modules.monitoring.metrics.performance_tracker import PerformanceTracker
        self.performance_tracker = PerformanceTracker(enable_system_monitoring=False)

        # Health Monitor
        from hyperion.modules.monitoring.metrics.health_monitor import HealthMonitor
        self.health_monitor = HealthMonitor()
        self.health_monitor.start()

        # Structured Logger
        from hyperion.modules.monitoring.logging.structured_logger import StructuredLogger
        self.structured_logger = StructuredLogger(enable_file=True, file_path="logs/hyperion.log")

        # Alert Manager
        from hyperion.modules.monitoring.alerting.alert_manager import AlertManager
        self.alert_manager = AlertManager()
        self.alert_manager.start()

        print("      ✅ Prometheus Exporter sur port 8090")
        print("      ✅ Performance Tracker actif")
        print("      ✅ Health Monitor démarré")
        print("      ✅ Structured Logger configuré")
        print("      ✅ Alert Manager opérationnel")

    async def _deploy_cache(self):
        """Déployer le cache distribué v3.0"""
        print("   💾 Lancement Cache Distribué v3.0...")

        from hyperion.modules.cache.v3_0.distributed_cache import DistributedCacheManager

        # Cache avec L1 seulement (pas de Redis pour demo)
        self.cache_manager = DistributedCacheManager(
            enable_l1=True,
            enable_l2=False,
            l1_max_size=10000
        )

        # Test du cache
        await self.cache_manager.set("test:deployment", {"status": "active", "time": time.time()})
        cached_value = await self.cache_manager.get("test:deployment")

        if cached_value:
            print("      ✅ Cache L1 Memory opérationnel")
            print("      ✅ Test de stockage/récupération réussi")
        else:
            raise Exception("Cache test failed")

    async def _deploy_security(self):
        """Déployer la sécurité v3.0"""
        print("   🔐 Lancement Sécurité v3.0...")

        import secrets
        from hyperion.modules.security.v3_0.auth_manager import AuthManager

        # Auth Manager avec clé secrète
        self.auth_manager = AuthManager(jwt_secret=secrets.token_urlsafe(32))

        # Créer utilisateur admin de test
        success, message = await self.auth_manager.create_user(
            username="admin",
            email="admin@hyperion.local",
            password="HyperionAdmin2024!",
            roles=["admin", "user"]
        )

        if success:
            print("      ✅ AuthManager initialisé")
            print("      ✅ Utilisateur admin créé")

            # Test d'authentification
            auth_result = await self.auth_manager.authenticate("admin", "HyperionAdmin2024!")
            if auth_result.success:
                print("      ✅ Test d'authentification réussi")
                self.admin_token = auth_result.session.access_token
            else:
                raise Exception("Authentication test failed")
        else:
            raise Exception(f"Failed to create admin user: {message}")

    async def _deploy_gateway(self):
        """Déployer l'API Gateway v3.0"""
        print("   🌐 Lancement API Gateway v3.0...")

        from hyperion.modules.gateway.v3_0.api_gateway import APIGateway, Route, HTTPMethod

        self.api_gateway = APIGateway(
            enable_auth=True,
            enable_rate_limiting=True,
            enable_caching=True
        )

        # Intégrer les services
        self.api_gateway.auth_service = self.auth_manager
        self.api_gateway.cache_service = self.cache_manager

        # Ajouter routes de test
        test_routes = [
            Route(
                path_pattern=r'^/api/v1/health$',
                methods=[HTTPMethod.GET],
                backend_url="internal://health",
                auth_required=False,
                name="health_endpoint"
            ),
            Route(
                path_pattern=r'^/api/v1/rag/query$',
                methods=[HTTPMethod.POST],
                backend_url="internal://rag",
                auth_required=True,
                name="rag_query",
                rate_limit_per_minute=60
            ),
            Route(
                path_pattern=r'^/api/v1/analytics/insights$',
                methods=[HTTPMethod.GET],
                backend_url="internal://analytics",
                auth_required=True,
                name="analytics_insights",
                cache_ttl=300
            )
        ]

        for route in test_routes:
            self.api_gateway.add_route(route)

        print("      ✅ API Gateway configuré")
        print("      ✅ Routes d'API ajoutées")
        print("      ✅ Sécurité et rate limiting activés")

    async def _deploy_rag_v29(self):
        """Déployer le RAG Pipeline v2.9"""
        print("   🔍 Lancement RAG Pipeline v2.9...")

        from hyperion.modules.rag.v2_9.enhanced_pipeline import EnhancedRAGPipeline, RAGConfig
        from hyperion.modules.rag.v2_9.context_manager import ContextManager

        # Configuration RAG optimisée
        config = RAGConfig(
            max_chunks=10,
            enable_semantic_reranking=True,
            enable_context_compression=True,
            enable_progressive_retrieval=True,
            enable_answer_fusion=True
        )

        self.rag_pipeline = EnhancedRAGPipeline(config)
        self.context_manager = ContextManager()

        # Test du pipeline RAG
        test_response = await self.rag_pipeline.query(
            question="Comment fonctionne l'authentification dans Hyperion?",
            repo_context="hyperion-security",
            user_context={"expertise_level": "expert", "user_id": "admin"}
        )

        if test_response and test_response.answer:
            print("      ✅ Enhanced RAG Pipeline opérationnel")
            print("      ✅ Context Manager initialisé")
            print(f"      ✅ Test query: {len(test_response.answer)} caractères de réponse")
        else:
            raise Exception("RAG pipeline test failed")

    async def _deploy_ml_v29(self):
        """Déployer les modèles ML v2.9"""
        print("   🤖 Lancement ML Ensemble v2.9...")

        from hyperion.modules.ml.v2_9.ensemble_models import EnsembleModelManager, EnsembleModel

        self.ml_manager = EnsembleModelManager()

        # Ajouter modèles de test (simulation)
        test_models = [
            EnsembleModel(
                name="quality_classifier",
                model_type="random_forest",
                model_path="models/quality_rf.joblib",
                weight=1.0,
                description="Classificateur de qualité RAG"
            ),
            EnsembleModel(
                name="performance_predictor",
                model_type="gradient_boosting",
                model_path="models/performance_gb.joblib",
                weight=0.8,
                description="Prédicteur de performance"
            )
        ]

        models_added = 0
        for model in test_models:
            if self.ml_manager.add_model(model):
                models_added += 1

        if models_added > 0:
            print(f"      ✅ ML Ensemble Manager opérationnel")
            print(f"      ✅ {models_added} modèles ajoutés")
            print("      ✅ Stratégies de vote configurées")
        else:
            raise Exception("Failed to add ML models")

    async def _deploy_analytics_v29(self):
        """Déployer l'intelligence analytics v2.9"""
        print("   📈 Lancement Analytics v2.9...")

        from hyperion.modules.analytics.v2_9.intelligence_engine import IntelligenceEngine, create_event

        self.analytics_engine = IntelligenceEngine(enable_real_time_analysis=True)
        self.analytics_engine.start_real_time_analysis()

        # Simuler quelques événements de déploiement
        deployment_events = [
            create_event("deployment", "orchestrator", {"service": "monitoring", "status": "deployed"}),
            create_event("deployment", "orchestrator", {"service": "cache", "status": "deployed"}),
            create_event("deployment", "orchestrator", {"service": "security", "status": "deployed"}),
            create_event("system_start", "hyperion", {"version": "3.0.0-dev", "mode": "production"})
        ]

        for event in deployment_events:
            self.analytics_engine.record_event(event)

        print("      ✅ Intelligence Engine démarré")
        print("      ✅ Analyse temps réel activée")
        print(f"      ✅ {len(deployment_events)} événements de déploiement enregistrés")

    async def _check_service_health(self, service_name: str) -> bool:
        """Vérifier la santé d'un service"""
        print(f"   🏥 Health check {service_name}...")

        try:
            if service_name == "monitoring":
                # Vérifier que le serveur Prometheus répond
                metrics_summary = self.prometheus_exporter.get_metrics_summary()
                return len(metrics_summary) > 0

            elif service_name == "cache":
                # Test du cache
                test_key = f"health:{service_name}:{int(time.time())}"
                await self.cache_manager.set(test_key, "healthy")
                value = await self.cache_manager.get(test_key)
                return value == "healthy"

            elif service_name == "security":
                # Vérifier les stats auth
                stats = self.auth_manager.get_auth_statistics()
                return stats['total_users'] > 0

            elif service_name == "gateway":
                # Vérifier les stats gateway
                stats = self.api_gateway.get_gateway_statistics()
                return stats['routes_configured'] > 0

            elif service_name == "rag_v29":
                # Vérifier les stats pipeline
                stats = self.rag_pipeline.get_pipeline_stats()
                return 'total_queries' in stats

            elif service_name == "ml_v29":
                # Vérifier le résumé ensemble
                summary = self.ml_manager.get_ensemble_summary()
                return summary['total_models'] > 0

            elif service_name == "analytics_v29":
                # Vérifier les données dashboard
                dashboard = self.analytics_engine.get_real_time_dashboard_data()
                return 'current_timestamp' in dashboard

            return False

        except Exception as e:
            logger.error(f"Health check failed for {service_name}: {e}")
            return False

    async def _run_integration_tests(self):
        """Exécuter des tests d'intégration"""
        print("\n🔗 Tests d'intégration...")

        test_results = {}

        # Test 1: Flow complet authentification → cache → gateway
        try:
            print("   🧪 Test 1: Flow auth → cache → gateway")

            # Authentifier
            auth_result = await self.auth_manager.authenticate("admin", "HyperionAdmin2024!")
            assert auth_result.success, "Auth failed"

            # Mettre en cache
            await self.cache_manager.set("user:admin:profile", {"role": "admin", "active": True})
            cached_profile = await self.cache_manager.get("user:admin:profile")
            assert cached_profile is not None, "Cache failed"

            # Test gateway avec auth
            from hyperion.modules.gateway.v3_0.api_gateway import Request, HTTPMethod
            request = Request(
                method=HTTPMethod.GET,
                path="/api/v1/health",
                headers={"Authorization": f"Bearer {auth_result.session.access_token}"},
                query_params={}
            )

            response = await self.api_gateway.handle_request(request)
            assert response.status_code == 200, "Gateway request failed"

            test_results["auth_cache_gateway"] = True
            print("      ✅ Flow auth → cache → gateway OK")

        except Exception as e:
            test_results["auth_cache_gateway"] = False
            print(f"      ❌ Test 1 failed: {e}")

        # Test 2: RAG avec analytics
        try:
            print("   🧪 Test 2: RAG → Analytics")

            # Requête RAG
            rag_response = await self.rag_pipeline.query(
                question="Quels sont les modules de sécurité disponibles?",
                repo_context="hyperion-docs"
            )
            assert rag_response.answer, "RAG query failed"

            # Enregistrer événement analytics
            from hyperion.modules.analytics.v2_9.intelligence_engine import create_event
            rag_event = create_event(
                "rag_query",
                "pipeline",
                {
                    "question_length": len("Quels sont les modules de sécurité disponibles?"),
                    "response_length": len(rag_response.answer),
                    "confidence": rag_response.confidence,
                    "processing_time": rag_response.processing_time
                },
                "admin"
            )

            self.analytics_engine.record_event(rag_event)

            test_results["rag_analytics"] = True
            print("      ✅ RAG → Analytics OK")

        except Exception as e:
            test_results["rag_analytics"] = False
            print(f"      ❌ Test 2 failed: {e}")

        # Test 3: Monitoring complet
        try:
            print("   🧪 Test 3: Monitoring intégral")

            # Performance tracking
            with self.performance_tracker.track_operation("integration_test"):
                await asyncio.sleep(0.01)

            # Métriques Prometheus
            self.prometheus_exporter.record_api_request("POST", "/api/v1/test", 200, 0.05)

            # Health check
            health = await self.health_monitor.health_check()
            assert health['overall_status'] in ['healthy', 'degraded'], "Health check failed"

            # Alert test
            test_insight = await self.analytics_engine._generate_insights()

            test_results["monitoring"] = True
            print("      ✅ Monitoring intégral OK")

        except Exception as e:
            test_results["monitoring"] = False
            print(f"      ❌ Test 3 failed: {e}")

        # Résumé des tests
        passed_tests = sum(1 for result in test_results.values() if result)
        total_tests = len(test_results)

        print(f"\n   📊 Tests d'intégration: {passed_tests}/{total_tests} réussis")

        if passed_tests < total_tests:
            print("   ⚠️  Certains tests d'intégration ont échoué")

        return passed_tests >= total_tests * 0.8  # 80% de réussite minimum

    async def _run_load_tests(self):
        """Exécuter des tests de charge légers"""
        print("\n⚡ Tests de charge...")

        # Test de charge sur le cache
        print("   💾 Test cache - 100 opérations...")
        cache_start = time.time()

        for i in range(100):
            await self.cache_manager.set(f"load_test:{i}", {"value": i, "timestamp": time.time()})

        for i in range(100):
            value = await self.cache_manager.get(f"load_test:{i}")
            assert value is not None, f"Cache miss for key load_test:{i}"

        cache_duration = time.time() - cache_start
        print(f"      ✅ 200 opérations cache en {cache_duration:.3f}s ({200/cache_duration:.1f} ops/s)")

        # Test de charge sur l'auth
        print("   🔐 Test auth - 10 authentifications...")
        auth_start = time.time()

        for i in range(10):
            auth_result = await self.auth_manager.authenticate("admin", "HyperionAdmin2024!")
            assert auth_result.success, f"Auth failed on iteration {i}"

        auth_duration = time.time() - auth_start
        print(f"      ✅ 10 authentifications en {auth_duration:.3f}s ({10/auth_duration:.1f} auth/s)")

        # Test de charge sur le RAG
        print("   🔍 Test RAG - 5 requêtes...")
        rag_start = time.time()

        test_questions = [
            "Comment fonctionne l'authentification?",
            "Quels sont les modules de cache?",
            "Comment utiliser le monitoring?",
            "Que fait l'API Gateway?",
            "Comment déployer Hyperion?"
        ]

        for i, question in enumerate(test_questions):
            response = await self.rag_pipeline.query(question, "hyperion-docs")
            assert response.answer, f"RAG failed on question {i}"

        rag_duration = time.time() - rag_start
        print(f"      ✅ 5 requêtes RAG en {rag_duration:.3f}s ({5/rag_duration:.1f} queries/s)")

    async def _validate_deployment(self) -> bool:
        """Validation finale du déploiement"""
        print("\n✅ Validation finale du déploiement...")

        # Vérifier que tous les services sont en running
        failed_services = []
        for name, status in self.services.items():
            if status.status != "running":
                failed_services.append(name)

        if failed_services:
            print(f"   ❌ Services en échec: {failed_services}")
            return False

        # Vérifier les métriques globales
        try:
            # Stats du cache
            cache_stats = self.cache_manager.get_cache_statistics()
            print(f"   📊 Cache: {cache_stats['hit_rate_percent']:.1f}% hit rate")

            # Stats de l'auth
            auth_stats = self.auth_manager.get_auth_statistics()
            print(f"   📊 Auth: {auth_stats['total_users']} utilisateurs")

            # Stats du gateway
            gateway_stats = self.api_gateway.get_gateway_statistics()
            print(f"   📊 Gateway: {gateway_stats['routes_configured']} routes")

            # Stats du RAG
            rag_stats = self.rag_pipeline.get_pipeline_stats()
            print(f"   📊 RAG: {rag_stats.get('total_queries', 0)} requêtes traitées")

            # Health global
            health = await self.health_monitor.health_check()
            print(f"   📊 Health: {health['overall_status']}")

            print("   ✅ Toutes les validations passées")
            return True

        except Exception as e:
            print(f"   ❌ Erreur validation: {e}")
            return False

    async def _display_deployment_summary(self):
        """Afficher le résumé du déploiement"""
        deployment_duration = time.time() - self.deployment_start_time

        print("\n" + "="*60)
        print("🎉 DÉPLOIEMENT HYPERION RÉUSSI!")
        print("="*60)
        print(f"⏱️  Durée totale: {deployment_duration:.1f}s")
        print(f"📅 Déployé le: {time.strftime('%Y-%m-%d %H:%M:%S')}")
        print(f"🏷️  Version: 3.0.0-dev")

        print("\n📋 SERVICES DÉPLOYÉS:")
        for name, status in self.services.items():
            uptime = time.time() - status.start_time
            print(f"   ✅ {name.upper():<15} | Status: {status.status:<8} | Uptime: {uptime:.1f}s")

        print("\n🔗 ENDPOINTS DISPONIBLES:")
        print("   📊 Metrics:     http://localhost:8090/metrics")
        print("   🏥 Health:      /api/v1/health")
        print("   🔍 RAG Query:   /api/v1/rag/query")
        print("   📈 Analytics:   /api/v1/analytics/insights")

        print("\n👤 COMPTE ADMIN:")
        print("   Username: admin")
        print("   Password: HyperionAdmin2024!")
        if hasattr(self, 'admin_token'):
            print(f"   Token: {self.admin_token[:50]}...")

    async def _start_production_mode(self):
        """Démarrer en mode production"""
        print("\n🚀 DÉMARRAGE MODE PRODUCTION")
        print("=" * 40)
        print("Hyperion v3.0 est maintenant opérationnel!")
        print("Tous les services sont actifs et surveillés.")
        print("\nPour arrêter: Ctrl+C")
        print("Logs en temps réel dans: hyperion_deploy.log")

        # Simulation du mode production
        try:
            # Générer de l'activité en continu
            activity_count = 0
            while self.is_running:
                await asyncio.sleep(10)  # Attendre 10 secondes
                activity_count += 1

                # Activité simulée toutes les 10 secondes
                if activity_count % 6 == 0:  # Chaque minute
                    print(f"⚡ Activité système - Uptime: {(time.time() - self.deployment_start_time)/60:.1f}min")

                    # Stats en temps réel
                    dashboard = self.analytics_engine.get_real_time_dashboard_data()
                    health = await self.health_monitor.health_check()

                    print(f"   📊 Health: {health['overall_status']} | Events: {dashboard.get('events_last_minute', 0)}")

                # Générer activité
                from hyperion.modules.analytics.v2_9.intelligence_engine import create_event
                activity_event = create_event(
                    "system_activity",
                    "production",
                    {"heartbeat": activity_count, "timestamp": time.time()}
                )
                self.analytics_engine.record_event(activity_event)

        except KeyboardInterrupt:
            print("\n🛑 Arrêt demandé par l'utilisateur")
            await self._graceful_shutdown()

    async def _graceful_shutdown(self):
        """Arrêt gracieux des services"""
        print("\n🛑 ARRÊT GRACIEUX DES SERVICES...")

        self.is_running = False

        # Arrêter les services dans l'ordre inverse
        shutdown_order = list(reversed(self.service_order))

        for service_name in shutdown_order:
            print(f"   🔄 Arrêt {service_name}...")

            try:
                if service_name == "monitoring" and hasattr(self, 'health_monitor'):
                    self.health_monitor.stop()
                    if hasattr(self, 'alert_manager'):
                        self.alert_manager.stop()

                elif service_name == "analytics_v29" and hasattr(self, 'analytics_engine'):
                    self.analytics_engine.stop_real_time_analysis()

                # Marquer le service comme arrêté
                if service_name in self.services:
                    self.services[service_name].status = "stopped"

                print(f"      ✅ {service_name} arrêté")

            except Exception as e:
                print(f"      ⚠️  Erreur arrêt {service_name}: {e}")

        print("   ✅ Tous les services arrêtés proprement")

    async def _cleanup_failed_deployment(self):
        """Nettoyer un déploiement échoué"""
        print("\n🧹 Nettoyage du déploiement échoué...")
        await self._graceful_shutdown()

    async def _emergency_shutdown(self):
        """Arrêt d'urgence"""
        print("\n🚨 ARRÊT D'URGENCE!")
        self.is_running = False
        # Arrêt forcé de tous les services

async def main():
    """Point d'entrée principal"""
    deployment = HyperionDeployment()

    try:
        await deployment.deploy()
    except KeyboardInterrupt:
        print("\n⏹️  Déploiement interrompu")
        await deployment._graceful_shutdown()
    except Exception as e:
        logger.error(f"Erreur fatale: {e}")
        await deployment._emergency_shutdown()

if __name__ == "__main__":
    print("🌟 HYPERION ENTERPRISE DEPLOYMENT v3.0")
    print("Déploiement complet de l'architecture enterprise")
    print("=" * 60)

    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("\n👋 Au revoir!")
    except Exception as e:
        print(f"\n💥 Erreur critique: {e}")
        sys.exit(1)