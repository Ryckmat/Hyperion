#!/usr/bin/env python3
"""
Test de Déploiement Simplifié Hyperion v2.9 + v3.0
Test sans dépendances externes pour validation du déploiement
"""

import asyncio
import sys
import time
from pathlib import Path

# Ajouter le chemin vers les modules Hyperion
sys.path.insert(0, str(Path(__file__).parent / "src"))


class SimpleDeploymentTest:
    """Test de déploiement simplifié"""

    def __init__(self):
        self.services = {}
        self.test_results = {}

    async def test_full_deployment(self):
        """Test complet du déploiement"""
        print("🚀 HYPERION v2.9 + v3.0 - DÉPLOIEMENT SIMPLIFIÉ")
        print("=" * 60)

        # Tests de déploiement des services
        await self.test_monitoring_v3()
        await self.test_cache_v3()
        await self.test_security_v3()
        await self.test_gateway_v3()
        await self.test_rag_v29()
        await self.test_ml_v29()
        await self.test_analytics_v29()

        # Tests d'intégration
        await self.test_integration_flows()

        # Résumé final
        self.print_final_summary()

    async def test_monitoring_v3(self):
        """Test du système de monitoring v3.0"""
        print("\n📊 Test Monitoring v3.0...")

        try:
            # Test Performance Tracker
            from hyperion.modules.monitoring.metrics.performance_tracker import PerformanceTracker

            tracker = PerformanceTracker(enable_system_monitoring=False)

            # Test tracking d'opération
            with tracker.track_operation("test_deployment"):
                await asyncio.sleep(0.01)  # Simuler travail

            stats = tracker.get_operation_stats("test_deployment")
            print(f"   ✅ PerformanceTracker: {len(stats)} métriques collectées")

            # Test Structured Logger
            from hyperion.modules.monitoring.logging.structured_logger import StructuredLogger

            logger = StructuredLogger(enable_file=False)
            logger.set_context(deployment_id="test_001")
            logger.info("Test de déploiement en cours")
            print("   ✅ StructuredLogger: logs structurés")

            # Test Health Monitor
            from hyperion.modules.monitoring.metrics.health_monitor import HealthMonitor

            health_monitor = HealthMonitor()
            health_status = health_monitor.get_system_health()
            print(f"   ✅ HealthMonitor: status={health_status['status']}")

            self.services["monitoring"] = True
            self.test_results["monitoring"] = True
            print("   ✅ Monitoring v3.0 - DÉPLOYÉ")

        except Exception as e:
            print(f"   ❌ Erreur monitoring: {e}")
            self.test_results["monitoring"] = False

    async def test_cache_v3(self):
        """Test du système de cache v3.0"""
        print("\n💾 Test Cache Distribué v3.0...")

        try:
            from hyperion.modules.cache.v3_0.distributed_cache import DistributedCacheManager

            # Initialiser avec L1 seulement (pas de Redis)
            cache_manager = DistributedCacheManager(
                enable_l1=True, enable_l2=False, l1_max_size=100
            )

            # Test set/get
            test_key = "deployment:test"
            test_value = {"service": "test", "status": "ok", "timestamp": time.time()}

            success = await cache_manager.set(test_key, test_value, ttl=60)
            print(f"   ✅ Cache SET: {success}")

            retrieved = await cache_manager.get(test_key)
            print(f"   ✅ Cache GET: {retrieved is not None}")

            # Test avec tags
            await cache_manager.set("tagged:service", "test_service", tags=["deployment", "test"])
            invalidated = await cache_manager.invalidate_by_tags(["deployment"])
            print(f"   ✅ Invalidation par tags: {invalidated} clés")

            # Stats
            stats = cache_manager.get_cache_statistics()
            print(f"   ✅ Stats cache: {stats['total_operations']} opérations")

            self.services["cache"] = cache_manager
            self.test_results["cache"] = True
            print("   ✅ Cache v3.0 - DÉPLOYÉ")

        except Exception as e:
            print(f"   ❌ Erreur cache: {e}")
            self.test_results["cache"] = False

    async def test_security_v3(self):
        """Test du système de sécurité v3.0"""
        print("\n🔐 Test Sécurité v3.0...")

        try:
            import secrets

            from hyperion.modules.security.v3_0.auth_manager import AuthManager

            # Initialiser sans dépendances JWT externes
            auth_manager = AuthManager(jwt_secret=secrets.token_urlsafe(32))

            # Test création utilisateur
            success, message = await auth_manager.create_user(
                username="test_deploy",
                email="test@hyperion-deploy.com",
                password="TestDeploy123!",
                roles=["user"],
            )
            print(f"   ✅ Création utilisateur: {success}")

            if success:
                # Test authentification
                result = await auth_manager.authenticate("test_deploy", "TestDeploy123!")
                print(f"   ✅ Authentification: {result.success}")

                if result.session:
                    # Test vérification session
                    session = await auth_manager.verify_session(result.session.access_token)
                    print(f"   ✅ Vérification session: {session is not None}")

            # Stats
            stats = auth_manager.get_auth_statistics()
            print(f"   ✅ Stats auth: {stats['total_users']} utilisateurs")

            self.services["auth"] = auth_manager
            self.test_results["security"] = True
            print("   ✅ Sécurité v3.0 - DÉPLOYÉ")

        except Exception as e:
            print(f"   ❌ Erreur sécurité: {e}")
            self.test_results["security"] = False

    async def test_gateway_v3(self):
        """Test de l'API Gateway v3.0"""
        print("\n🌐 Test API Gateway v3.0...")

        try:
            from hyperion.modules.gateway.v3_0.api_gateway import (
                APIGateway,
                HTTPMethod,
                Request,
                Route,
            )

            # Initialiser sans authentification pour test
            gateway = APIGateway(enable_auth=False)

            # Ajouter route de test
            test_route = Route(
                path_pattern=r"^/api/deployment/test$",
                methods=[HTTPMethod.GET, HTTPMethod.POST],
                backend_url="http://localhost:8001/test",
                auth_required=False,
                name="deployment_test",
            )
            gateway.add_route(test_route)

            # Créer requête de test
            test_request = Request(
                method=HTTPMethod.GET,
                path="/api/deployment/test",
                headers={"Content-Type": "application/json"},
                query_params={"deployment": "test"},
                client_ip="127.0.0.1",
            )

            # Traiter requête
            response = await gateway.handle_request(test_request)
            print(f"   ✅ Requête traitée: status={response.status_code}")

            # Health check
            health = await gateway.health_check()
            print(f"   ✅ Health check: {health['status']}")

            # Stats
            stats = gateway.get_gateway_statistics()
            print(f"   ✅ Stats gateway: {stats['total_requests']} requêtes")

            self.services["gateway"] = gateway
            self.test_results["gateway"] = True
            print("   ✅ API Gateway v3.0 - DÉPLOYÉ")

        except Exception as e:
            print(f"   ❌ Erreur gateway: {e}")
            self.test_results["gateway"] = False

    async def test_rag_v29(self):
        """Test du pipeline RAG v2.9"""
        print("\n🔍 Test RAG Pipeline v2.9...")

        try:
            from hyperion.modules.rag.v2_9.context_manager import ContextManager
            from hyperion.modules.rag.v2_9.enhanced_pipeline import EnhancedRAGPipeline, RAGConfig

            # Configuration pour test
            config = RAGConfig(
                max_chunks=3, enable_semantic_reranking=True, enable_context_compression=True
            )

            rag_pipeline = EnhancedRAGPipeline(config)

            # Test requête RAG
            response = await rag_pipeline.query(
                question="Comment déployer Hyperion ?",
                repo_context="hyperion-deployment",
                user_context={"test_mode": True},
            )

            print(f"   ✅ Requête RAG: réponse de {len(response.answer)} caractères")
            print(f"   ✅ Sources: {len(response.sources)} trouvées")
            print(f"   ✅ Confiance: {response.confidence:.2f}")

            # Test contexte
            context_mgr = ContextManager()
            context_mgr.get_or_create_context(
                "deployment_test", "test_user"
            )  # Test context creation

            context_mgr.add_conversation_turn(
                session_id="deployment_test",
                user_id="test_user",
                query="Test de déploiement",
                response=response.answer,
                sources_used=[s.source for s in response.sources],
            )

            print("   ✅ Contexte conversationnel mis à jour")

            # Stats
            stats = rag_pipeline.get_pipeline_stats()
            print(f"   ✅ Stats RAG: {stats['total_queries']} requêtes")

            self.services["rag"] = rag_pipeline
            self.test_results["rag"] = True
            print("   ✅ RAG v2.9 - DÉPLOYÉ")

        except Exception as e:
            print(f"   ❌ Erreur RAG v2.9: {e}")
            self.test_results["rag"] = False

    async def test_ml_v29(self):
        """Test ML Ensemble v2.9"""
        print("\n🤖 Test ML Ensemble v2.9...")

        try:
            import numpy as np

            from hyperion.modules.ml.v2_9.ensemble_models import EnsembleModel, EnsembleModelManager

            manager = EnsembleModelManager()

            # Ajouter modèle de test
            test_model = EnsembleModel(
                name="deployment_test_model",
                model_type="random_forest",
                model_path="/tmp/test_deployment_model.joblib",
                weight=1.0,
                hyperparameters={"n_estimators": 10},
            )

            success = manager.add_model(test_model)
            print(f"   ✅ Modèle ajouté: {success}")

            # Test données factices
            X_train = np.random.random((50, 5))
            y_train = np.random.randint(0, 2, 50)
            X_val = np.random.random((10, 5))
            y_val = np.random.randint(0, 2, 10)

            # Test entraînement
            trained = await asyncio.create_task(
                asyncio.to_thread(
                    manager.train_model, "deployment_test_model", X_train, y_train, X_val, y_val
                )
            )
            print(f"   ✅ Entraînement: {trained}")

            if trained:
                # Test prédiction
                X_test = np.random.random((3, 5))
                prediction = await asyncio.create_task(asyncio.to_thread(manager.predict, X_test))
                print(f"   ✅ Prédiction: confiance={prediction.confidence:.2f}")

            # Résumé
            summary = manager.get_ensemble_summary()
            print(f"   ✅ Ensemble: {summary['total_models']} modèles")

            self.services["ml"] = manager
            self.test_results["ml"] = True
            print("   ✅ ML Ensemble v2.9 - DÉPLOYÉ")

        except Exception as e:
            print(f"   ❌ Erreur ML v2.9: {e}")
            self.test_results["ml"] = False

    async def test_analytics_v29(self):
        """Test Analytics v2.9"""
        print("\n📈 Test Analytics v2.9...")

        try:
            from hyperion.modules.analytics.v2_9.intelligence_engine import (
                IntelligenceEngine,
                create_event,
            )

            engine = IntelligenceEngine(enable_real_time_analysis=False)

            # Générer événements de test de déploiement
            deployment_events = [
                create_event("service_start", "monitoring", {"status": "ok"}),
                create_event("service_start", "cache", {"status": "ok"}),
                create_event("service_start", "security", {"status": "ok"}),
                create_event("service_start", "gateway", {"status": "ok"}),
                create_event("deployment_test", "system", {"phase": "validation"}),
                create_event("health_check", "system", {"status": "healthy"}),
            ]

            for event in deployment_events:
                engine.record_event(event)

            print(f"   ✅ Événements enregistrés: {len(deployment_events)}")

            # Générer insights
            await engine._generate_insights()
            insights = engine.get_current_insights()
            print(f"   ✅ Insights générés: {len(insights)}")

            # Résumé
            summary = engine.get_analytics_summary(hours=1)
            print(
                f"   ✅ Résumé: {summary.total_events} événements, {summary.unique_users} utilisateurs"
            )

            # Dashboard
            dashboard = engine.get_real_time_dashboard_data()
            print(f"   ✅ Dashboard: {dashboard['total_events']} événements totaux")

            self.services["analytics"] = engine
            self.test_results["analytics"] = True
            print("   ✅ Analytics v2.9 - DÉPLOYÉ")

        except Exception as e:
            print(f"   ❌ Erreur Analytics v2.9: {e}")
            self.test_results["analytics"] = False

    async def test_integration_flows(self):
        """Test des flux d'intégration"""
        print("\n🔄 Tests d'Intégration...")

        try:
            integration_tests = [
                self.test_auth_cache_flow(),
                self.test_rag_analytics_flow(),
                self.test_monitoring_integration(),
            ]

            results = await asyncio.gather(*integration_tests, return_exceptions=True)

            success_count = sum(1 for result in results if result is True)
            total_tests = len(integration_tests)

            print(f"   📊 Intégration: {success_count}/{total_tests} tests réussis")

            self.test_results["integration"] = success_count >= total_tests * 0.8  # 80% de réussite

        except Exception as e:
            print(f"   ❌ Erreur intégration: {e}")
            self.test_results["integration"] = False

    async def test_auth_cache_flow(self):
        """Test flux Auth → Cache"""
        try:
            if "auth" in self.services and "cache" in self.services:
                # Simuler stockage session en cache
                session_data = {"user_id": "test_deploy", "timestamp": time.time()}

                cache_success = await self.services["cache"].set(
                    "session:test_deploy", session_data, ttl=300, tags=["auth", "session"]
                )

                cached_session = await self.services["cache"].get("session:test_deploy")

                print("   ✅ Auth → Cache: session stockée")
                return cache_success and cached_session is not None
            return False
        except Exception:
            return False

    async def test_rag_analytics_flow(self):
        """Test flux RAG → Analytics"""
        try:
            if "rag" in self.services and "analytics" in self.services:
                # Simuler requête RAG avec analytique
                from hyperion.modules.analytics.v2_9.intelligence_engine import create_event

                rag_event = create_event(
                    "rag_query",
                    "deployment_test",
                    {"question": "Comment déployer ?", "confidence": 0.85, "sources_count": 3},
                    "test_user",
                )

                self.services["analytics"].record_event(rag_event)
                print("   ✅ RAG → Analytics: événement enregistré")
                return True
            return False
        except Exception:
            return False

    async def test_monitoring_integration(self):
        """Test intégration monitoring"""
        try:
            if "monitoring" in self.services:
                # Simuler tracking d'opération intégrée
                from hyperion.modules.monitoring.logging.structured_logger import default_logger

                default_logger.set_context(deployment="test", integration_test=True)

                with default_logger.track_operation("integration_test"):
                    await asyncio.sleep(0.01)

                print("   ✅ Monitoring: opération trackée")
                return True
            return False
        except Exception:
            return False

    def print_final_summary(self):
        """Affiche le résumé final du déploiement"""
        print("\n" + "=" * 60)
        print("🏆 RÉSULTATS DU DÉPLOIEMENT:")

        passed_tests = sum(1 for result in self.test_results.values() if result)
        total_tests = len(self.test_results)

        for test_name, result in self.test_results.items():
            status = "✅ DÉPLOYÉ" if result else "❌ ÉCHEC"
            print(f"   {test_name.upper():<15} {status}")

        success_rate = (passed_tests / total_tests) * 100
        print(f"\n📊 TAUX DE RÉUSSITE: {passed_tests}/{total_tests} ({success_rate:.1f}%)")

        if success_rate >= 90:
            print("\n🎉 DÉPLOIEMENT HYPERION v2.9 + v3.0 RÉUSSI!")
            print("\n📋 SERVICES DÉPLOYÉS:")
            print("   🚀 v3.0 Enterprise:")
            print("      • Monitoring (Performance, Health, Logs)")
            print("      • Cache Distribué (Multi-niveaux)")
            print("      • Sécurité (Auth, MFA, Sessions)")
            print("      • API Gateway (Rate limiting)")
            print("\n   ⚡ v2.9 Enhanced:")
            print("      • RAG Pipeline (Reranking, Contexte)")
            print("      • ML Ensemble (Modèles adaptatifs)")
            print("      • Analytics (Intelligence, Insights)")
            print("\n🎯 STATUT: ARCHITECTURE PRÊTE POUR PRODUCTION")

        elif success_rate >= 75:
            print("\n✅ DÉPLOIEMENT FONCTIONNEL")
            print("   Quelques services peuvent nécessiter des ajustements")

        else:
            print("\n❌ PROBLÈMES DE DÉPLOIEMENT DÉTECTÉS")
            print("   Révision nécessaire avant mise en production")

        print("\n🔧 COMMANDES DE VÉRIFICATION:")
        print("   python test_simple.py                    # Test rapide")
        print("   python test_architecture_validation.py   # Validation complète")
        print("   python test_hyperion_architecture.py     # Test avancé")


async def main():
    """Fonction principale"""
    tester = SimpleDeploymentTest()
    await tester.test_full_deployment()

    # Retourner code de sortie approprié
    success_rate = (
        sum(1 for result in tester.test_results.values() if result) / len(tester.test_results) * 100
    )
    return success_rate >= 75


if __name__ == "__main__":
    try:
        success = asyncio.run(main())
        sys.exit(0 if success else 1)
    except KeyboardInterrupt:
        print("\n⏹️  Déploiement interrompu")
        sys.exit(1)
    except Exception as e:
        print(f"\n💥 Erreur critique déploiement: {e}")
        sys.exit(1)
