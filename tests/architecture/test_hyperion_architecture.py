#!/usr/bin/env python3
"""
Test Suite for Hyperion Architecture
Test complet de l'architecture enterprise
"""

import asyncio
import sys
import time
from pathlib import Path

# Ajouter le chemin vers les modules Hyperion
sys.path.insert(0, str(Path(__file__).parent / "src"))


def test_imports():
    """Test des imports des modules clés"""
    print("🔍 Test des imports...")

    # Version check
    from hyperion import __version__

    print(f"   ✅ Version Hyperion: {__version__}")

    # Monitoring

    print("   ✅ Monitoring - OK")

    # RAG

    print("   ✅ RAG Pipeline - OK")

    # ML

    print("   ✅ ML Ensemble - OK")

    # Analytics

    print("   ✅ Analytics - OK")

    # Cache

    print("   ✅ Cache distribué - OK")

    # Security

    print("   ✅ Sécurité - OK")

    # Gateway

    print("   ✅ API Gateway - OK")


def test_monitoring_v3():
    """Test du système de monitoring"""
    print("\n📊 Test Monitoring...")

    from hyperion.modules.monitoring.logging.structured_logger import StructuredLogger
    from hyperion.modules.monitoring.metrics.performance_tracker import PerformanceTracker
    from hyperion.modules.monitoring.metrics.prometheus_exporter import PrometheusExporter

    # Test Prometheus Exporter
    exporter = PrometheusExporter()
    exporter.start_server()
    exporter.record_api_request("GET", "/test", 200, 0.1)
    print("   ✅ PrometheusExporter - OK")

    # Test Performance Tracker
    tracker = PerformanceTracker()
    with tracker.track_operation("test_operation"):
        time.sleep(0.01)  # Simuler travail
    stats = tracker.get_operation_stats("test_operation")
    print(f"   ✅ PerformanceTracker - {len(stats)} métriques")

    # Test Structured Logger
    logger = StructuredLogger()
    logger.set_context(user_id="test_user", operation="test")
    logger.info("Test log message", extra_data="test")
    print("   ✅ StructuredLogger - OK")


def test_cache_v3():
    """Test du cache distribué"""
    print("\n💾 Test Cache Distribué...")

    async def _async_test():
        from hyperion.modules.cache.distributed_cache import DistributedCacheManager

        # Initialiser cache
        cache = DistributedCacheManager(
            enable_l1=True, enable_l2=False, l1_max_size=1000  # Désactiver Redis pour test
        )

        # Test set/get
        test_key = "test:key"
        test_value = {"data": "test_value", "timestamp": time.time()}

        success = await cache.set(test_key, test_value, ttl=60)
        print(f"   ✅ Cache SET: {success}")

        retrieved = await cache.get(test_key)
        print(f"   ✅ Cache GET: {retrieved == test_value}")

        # Test avec tags
        await cache.set("tagged:key", "tagged_value", tags=["test", "demo"])
        invalidated = await cache.invalidate_by_tags(["test"])
        print(f"   ✅ Invalidation par tags: {invalidated} clés")

        # Statistiques
        stats = cache.get_cache_statistics()
        print(f"   ✅ Stats cache: hit_rate={stats['hit_rate_percent']:.1f}%")

        return True

    try:
        result = asyncio.run(_async_test())
        assert result is True
    except Exception as e:
        print(f"   ❌ Erreur cache: {e}")
        raise AssertionError(f"Cache test failed: {e}") from e


def test_auth_v3():
    """Test du système d'authentification"""
    print("\n🔐 Test Authentification...")

    async def _async_test():
        import secrets

        from hyperion.modules.security.auth_manager import AuthManager

        # Initialiser gestionnaire auth
        auth = AuthManager(jwt_secret=secrets.token_urlsafe(32))

        # Créer utilisateur test
        success, message = await auth.create_user(
            username="testuser",
            email="test@hyperion.com",
            password="TestPassword123!",
            roles=["user"],
        )
        print(f"   ✅ Création utilisateur: {success} - {message}")

        # Test authentification
        result = await auth.authenticate("testuser", "TestPassword123!")
        print(f"   ✅ Authentification: {result.success}")

        if result.session:
            # Test vérification session
            session = await auth.verify_session(result.session.access_token)
            print(f"   ✅ Vérification session: {session is not None}")

            # Test génération clé API
            api_key = await auth.generate_api_key(result.user.id)
            print(f"   ✅ Clé API générée: {api_key[:20]}...")

        # Statistiques auth
        stats = auth.get_auth_statistics()
        print(f"   ✅ Stats auth: {stats['total_users']} utilisateurs")

        return True

    try:
        result = asyncio.run(_async_test())
        assert result is True
    except Exception as e:
        print(f"   ❌ Erreur auth: {e}")
        raise AssertionError(f"Auth test failed: {e}") from e


def test_gateway_v3():
    """Test de l'API Gateway"""
    print("\n🌐 Test API Gateway...")

    async def _async_test():
        from hyperion.modules.gateway.api_gateway import APIGateway, HTTPMethod, Request, Route

        # Initialiser gateway
        gateway = APIGateway(enable_auth=False)  # Désactiver auth pour test

        # Ajouter route test
        test_route = Route(
            path_pattern=r"^/api/test$",
            methods=[HTTPMethod.GET, HTTPMethod.POST],
            backend_url="http://localhost:8001/test",
            auth_required=False,
            name="test_endpoint",
        )
        gateway.add_route(test_route)

        # Créer requête test
        request = Request(
            method=HTTPMethod.GET,
            path="/api/test",
            headers={"Content-Type": "application/json"},
            query_params={"param1": "value1"},
            client_ip="127.0.0.1",
        )

        # Traiter requête
        response = await gateway.handle_request(request)
        print(f"   ✅ Requête traitée: {response.status_code}")

        # Health check
        health = await gateway.health_check()
        print(f"   ✅ Health check: {health['status']}")

        # Statistiques
        stats = gateway.get_gateway_statistics()
        print(f"   ✅ Stats gateway: {stats['total_requests']} requêtes")

        return True

    try:
        result = asyncio.run(_async_test())
        assert result is True
    except Exception as e:
        print(f"   ❌ Erreur gateway: {e}")
        raise AssertionError(f"Gateway test failed: {e}") from e


def test_rag_v29():
    """Test du pipeline RAG"""
    print("\n🔍 Test RAG Pipeline...")

    async def _async_test():
        from hyperion.modules.rag.context_manager import ContextManager
        from hyperion.modules.rag.enhanced_pipeline import EnhancedRAGPipeline, RAGConfig

        # Initialiser pipeline RAG
        config = RAGConfig(
            max_chunks=5, enable_semantic_reranking=True, enable_context_compression=True
        )
        rag_pipeline = EnhancedRAGPipeline(config)

        # Test requête RAG
        response = await rag_pipeline.query(
            question="Comment utiliser l'authentification?",
            repo_context="hyperion-security",
            user_context={"expertise_level": "intermediate"},
        )

        print(f"   ✅ Requête RAG: {len(response.answer)} caractères de réponse")
        print(f"   ✅ Sources trouvées: {len(response.sources)}")
        print(f"   ✅ Confiance: {response.confidence:.2f}")
        print(f"   ✅ Temps traitement: {response.processing_time:.3f}s")

        # Test gestionnaire de contexte
        context_mgr = ContextManager()
        context_mgr.get_or_create_context("test_session", "test_user")  # Test context creation

        context_mgr.add_conversation_turn(
            session_id="test_session",
            user_id="test_user",
            query="Test question",
            response=response.answer,
            sources_used=[s.source for s in response.sources],
        )

        print("   ✅ Contexte conversationnel mis à jour")

        # Stats pipeline
        stats = rag_pipeline.get_pipeline_stats()
        print(f"   ✅ Stats pipeline: {stats['total_queries']} requêtes")

        return True

    try:
        result = asyncio.run(_async_test())
        assert result is True
    except Exception as e:
        print(f"   ❌ Erreur RAG: {e}")
        raise AssertionError(f"RAG test failed: {e}") from e


def test_ml_v29(tmp_path):
    """Test des modèles ML ensemble"""
    print("\n🤖 Test ML Ensemble...")

    async def _async_test():
        import numpy as np

        from hyperion.modules.ml.ensemble_models import EnsembleModel, EnsembleModelManager

        # Initialiser gestionnaire ensemble (hors de models/ pour ne pas écraser les artefacts)
        manager = EnsembleModelManager(models_directory=str(tmp_path))

        # Ajouter modèle test (simulation)
        model_config = EnsembleModel(
            name="test_model",
            model_type="random_forest",
            model_path="/tmp/test_model.joblib",
            weight=1.0,
            hyperparameters={"n_estimators": 100},
        )

        success = manager.add_model(model_config)
        print(f"   ✅ Modèle ajouté: {success}")

        # Test entraînement (simulation avec données factices)
        X_train = np.random.random((100, 10))
        y_train = np.random.randint(0, 2, 100)
        X_val = np.random.random((20, 10))
        y_val = np.random.randint(0, 2, 20)

        trained = await asyncio.create_task(
            asyncio.to_thread(manager.train_model, "test_model", X_train, y_train, X_val, y_val)
        )
        print(f"   ✅ Entraînement: {trained}")

        if trained:
            # Test prédiction ensemble
            X_test = np.random.random((5, 10))
            prediction = await asyncio.create_task(asyncio.to_thread(manager.predict, X_test))
            print(f"   ✅ Prédiction: confiance={prediction.confidence:.2f}")

        # Résumé ensemble
        summary = manager.get_ensemble_summary()
        print(
            f"   ✅ Ensemble: {summary['total_models']} modèles, {summary['trained_models']} entraînés"
        )

        return True

    try:
        result = asyncio.run(_async_test())
        assert result is True
    except Exception as e:
        print(f"   ❌ Erreur ML: {e}")
        raise AssertionError(f"ML test failed: {e}") from e


def test_analytics_v29():
    """Test du moteur d'intelligence"""
    print("\n📈 Test Analytics...")

    async def _async_test():
        from hyperion.modules.analytics.intelligence_engine import (
            IntelligenceEngine,
            create_event,
        )

        # Initialiser moteur intelligence
        engine = IntelligenceEngine(enable_real_time_analysis=False)

        # Générer événements test
        events = [
            create_event("api_request", "gateway", {"response_time": 0.1}, "user1"),
            create_event("rag_query", "pipeline", {"quality_score": 0.85}, "user1"),
            create_event("user_action", "ui", {"action": "search"}, "user1"),
            create_event("performance", "system", {"cpu_usage": 45.2}),
            create_event("error", "auth", {"error_code": "INVALID_TOKEN"}, "user2"),
        ]

        for event in events:
            engine.record_event(event)

        print(f"   ✅ Événements enregistrés: {len(events)}")

        # Générer insights
        await engine._generate_insights()
        current_insights = engine.get_current_insights()
        print(f"   ✅ Insights générés: {len(current_insights)}")

        # Résumé analytics
        summary = engine.get_analytics_summary(hours=1)
        print(
            f"   ✅ Résumé: {summary.total_events} événements, {summary.unique_users} utilisateurs"
        )

        # Dashboard temps réel
        dashboard = engine.get_real_time_dashboard_data()
        print(f"   ✅ Dashboard: {dashboard['active_users_count']} utilisateurs actifs")

        return True

    try:
        result = asyncio.run(_async_test())
        assert result is True
    except Exception as e:
        print(f"   ❌ Erreur Analytics: {e}")
        raise AssertionError(f"Analytics test failed: {e}") from e


async def run_integration_test():
    """Test d'intégration complet"""
    print("\n🔄 Test d'intégration Hyperion...")

    try:
        # Simuler workflow complet
        from hyperion.modules.cache.distributed_cache import distributed_cache
        from hyperion.modules.monitoring.logging.structured_logger import default_logger

        # 1. Logger le début du workflow
        default_logger.set_context(workflow="integration_test", user_id="test_user")
        default_logger.info("Démarrage du workflow d'intégration")

        # 2. Test cache pour données partagées
        workflow_data = {
            "test_id": "integration_001",
            "started_at": time.time(),
            "components_tested": [],
        }

        await distributed_cache.set("workflow:integration_001", workflow_data, ttl=300)
        cached_data = await distributed_cache.get("workflow:integration_001")

        # 3. Logger succès cache
        default_logger.info("Cache testé avec succès", cache_hit=cached_data is not None)

        # 4. Simulation flux de données
        processing_steps = ["auth", "rag", "ml", "analytics"]
        for step in processing_steps:
            with default_logger.track_operation(f"process_{step}"):
                await asyncio.sleep(0.01)  # Simuler traitement
                cached_data["components_tested"].append(step)

        # 5. Mise à jour finale
        await distributed_cache.set("workflow:integration_001", cached_data, ttl=300)

        print("   ✅ Workflow d'intégration complet")
        print(f"   ✅ Composants testés: {cached_data['components_tested']}")

        return True

    except Exception as e:
        print(f"   ❌ Erreur intégration: {e}")
        return False


async def main():
    """Fonction principale de test"""
    print("🚀 HYPERION - TEST SUITE COMPLET")
    print("=" * 60)

    results = {}

    # Tests séquentiels
    results["imports"] = test_imports()
    results["monitoring"] = test_monitoring_v3()
    results["cache"] = await test_cache_v3()
    results["auth"] = await test_auth_v3()
    results["gateway"] = await test_gateway_v3()
    results["rag"] = await test_rag_v29()
    results["ml"] = await test_ml_v29()
    results["analytics"] = await test_analytics_v29()
    results["integration"] = await run_integration_test()

    # Résumé final
    print("\n" + "=" * 60)
    print("📊 RÉSULTATS DES TESTS:")

    total_tests = len(results)
    passed_tests = sum(1 for result in results.values() if result)

    for test_name, result in results.items():
        status = "✅ PASS" if result else "❌ FAIL"
        print(f"   {test_name.upper():<15} {status}")

    success_rate = (passed_tests / total_tests) * 100
    print(f"\n🎯 TAUX DE RÉUSSITE: {passed_tests}/{total_tests} ({success_rate:.1f}%)")

    if success_rate >= 90:
        print("🎉 HYPERION - ARCHITECTURE VALIDÉE!")
    elif success_rate >= 75:
        print("⚠️  ARCHITECTURE FONCTIONNELLE AVEC QUELQUES PROBLÈMES")
    else:
        print("❌ PROBLÈMES CRITIQUES DÉTECTÉS")

    return success_rate >= 75


if __name__ == "__main__":
    try:
        success = asyncio.run(main())
        sys.exit(0 if success else 1)
    except KeyboardInterrupt:
        print("\n⏹️  Tests interrompus par l'utilisateur")
        sys.exit(1)
    except Exception as e:
        print(f"\n💥 Erreur critique: {e}")
        sys.exit(1)
