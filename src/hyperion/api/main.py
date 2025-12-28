"""API REST Hyperion - Backend FastAPI avec monitoring qualité v2.8."""

import yaml
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel

from hyperion.__version__ import __version__
from hyperion.config import DATA_DIR

try:
    from hyperion.modules.integrations.neo4j_ingester import Neo4jIngester
except ModuleNotFoundError:
    Neo4jIngester = None

# Import système de monitoring qualité v2.8
try:
    from hyperion.modules.rag.monitoring.quality_metrics import QualityMetricsTracker

    QUALITY_MONITORING_AVAILABLE = True
except ImportError as e:
    print(f"⚠️ Monitoring qualité non disponible: {e}")
    QUALITY_MONITORING_AVAILABLE = False


# ============================================================================
# Pydantic Models
# ============================================================================


class ChatRequest(BaseModel):
    """Requête chat RAG."""

    question: str
    repo: str | None = None
    history: list[dict] | None = None


# ============================================================================
# Configuration FastAPI
# ============================================================================

app = FastAPI(
    title="Hyperion API",
    description="API REST pour le profiler Git Hyperion + RAG",
    version=__version__,
    docs_url="/docs",
    redoc_url="/redoc",
)

# CORS (pour React)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000", "http://localhost:5173"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# ============================================================================
# RAG & Quality Monitoring Global (lazy loading)
# ============================================================================

_query_engine = None
_quality_tracker = None


def get_query_engine():
    """Get or create RAG query engine."""
    global _query_engine
    if _query_engine is None:
        from hyperion.modules.rag.query import RAGQueryEngine

        _query_engine = RAGQueryEngine()
    return _query_engine


def get_quality_tracker():
    """Get or create quality metrics tracker."""
    global _quality_tracker
    if _quality_tracker is None and QUALITY_MONITORING_AVAILABLE:
        _quality_tracker = QualityMetricsTracker()
    return _quality_tracker


# ============================================================================
# Routes
# ============================================================================


@app.get("/")
def read_root():
    """Endpoint racine."""
    return {
        "name": "Hyperion API",
        "version": __version__,
        "status": "running",
        "features": ["repos", "neo4j", "rag", "quality_monitoring"],
        "endpoints": {
            "docs": "/docs",
            "repos": "/api/repos",
            "chat": "/api/chat",
            "health": "/api/health",
            # endpoints OpenAI-compat (pour Open WebUI sans Pipe)
            "openai_models": "/v1/models",
            "openai_chat": "/v1/chat/completions",
            # endpoints Quality Monitoring v2.8
            "quality_metrics": "/api/quality/metrics",
            "quality_trends": "/api/quality/trends",
            "quality_alerts": "/api/quality/alerts",
            "quality_stats": "/api/quality/stats",
        },
    }


@app.get("/api/health")
def health_check():
    """Health check API + Neo4j + RAG optimisé."""
    status = {
        "status": "healthy",
        "api": "ok",
        "neo4j": "unknown",
        "rag": "unknown",
        "details": {},
    }

    # Test Neo4j (tolérant)
    if Neo4jIngester is None:
        status["neo4j"] = "warning: dependency not installed"
        status["details"]["neo4j"] = "Neo4j optional, API fonctionnel sans"
    else:
        try:
            # Test rapide avec timeout
            ingester = Neo4jIngester()
            # Test simple sans verify_connectivity (plus rapide)
            with ingester.driver.session() as session:
                result = session.run("RETURN 1 as test")
                result.single()
            ingester.close()
            status["neo4j"] = "ok"
        except Exception as e:
            status["neo4j"] = "warning: connection failed"
            status["details"]["neo4j"] = f"Neo4j indisponible mais API fonctionnel: {str(e)[:50]}"

    # Test RAG (optimisé)
    try:
        # Test simple sans initialiser complètement si déjà fait
        if _query_engine is None:
            # Premier chargement - peut prendre du temps
            _ = get_query_engine()
            status["rag"] = "ok"
            status["details"]["rag"] = "RAG initialisé avec succès"
        else:
            # Déjà initialisé - test rapide
            status["rag"] = "ok"
            status["details"]["rag"] = "RAG prêt et en cache"
    except Exception as e:
        # RAG échec ne dégrade pas le service complet
        status["rag"] = "warning: initialization failed"
        status["details"]["rag"] = f"RAG indisponible mais API core fonctionnel: {str(e)[:50]}"

    # Status global: healthy sauf si API core échoue
    # Neo4j et RAG sont des features optionnelles
    api_critical_failed = False

    if not api_critical_failed:
        status["status"] = "healthy"

    return status


@app.get("/api/repos")
def list_repos():
    """Liste tous les repos analysés."""
    repos_dir = DATA_DIR / "repositories"

    if not repos_dir.exists():
        return {"repos": []}

    repos = []

    for repo_dir in repos_dir.iterdir():
        if not repo_dir.is_dir():
            continue

        profile_file = repo_dir / "profile.yaml"
        if not profile_file.exists():
            continue

        try:
            with open(profile_file) as f:
                profile = yaml.safe_load(f)

            repos.append(
                {
                    "name": profile["service"],
                    "language": profile["repositories"][0]["main_language"],
                    "commits": profile["git_summary"]["commits"],
                    "contributors": profile["git_summary"]["contributors"],
                    "first_commit": profile["git_summary"]["first_commit"],
                    "last_commit": profile["git_summary"]["last_commit"],
                    "license": profile["repositories"][0]["license"],
                }
            )
        except Exception:
            continue

    return {"repos": repos, "count": len(repos)}


@app.get("/api/repos/{repo_name}")
def get_repo(repo_name: str):
    """Détails complets d'un repo."""
    profile_file = DATA_DIR / "repositories" / repo_name / "profile.yaml"

    if not profile_file.exists():
        raise HTTPException(status_code=404, detail=f"Repo '{repo_name}' non trouvé")

    with open(profile_file) as f:
        profile = yaml.safe_load(f)

    return profile


@app.get("/api/repos/{repo_name}/contributors")
def get_contributors(repo_name: str, limit: int | None = 10):
    """Top contributeurs d'un repo."""
    profile_file = DATA_DIR / "repositories" / repo_name / "profile.yaml"

    if not profile_file.exists():
        raise HTTPException(status_code=404, detail=f"Repo '{repo_name}' non trouvé")

    with open(profile_file) as f:
        profile = yaml.safe_load(f)

    contributors = profile["git_summary"]["contributors_top10"][:limit]

    return {"repo": repo_name, "contributors": contributors, "count": len(contributors)}


@app.get("/api/repos/{repo_name}/hotspots")
def get_hotspots(repo_name: str, limit: int | None = 10):
    """Top hotspots d'un repo."""
    profile_file = DATA_DIR / "repositories" / repo_name / "profile.yaml"

    if not profile_file.exists():
        raise HTTPException(status_code=404, detail=f"Repo '{repo_name}' non trouvé")

    with open(profile_file) as f:
        profile = yaml.safe_load(f)

    hotspots = profile["git_summary"]["hotspots_top10"][:limit]

    return {"repo": repo_name, "hotspots": hotspots, "count": len(hotspots)}


@app.get("/api/repos/{repo_name}/metrics")
def get_metrics(repo_name: str):
    """Métriques qualité d'un repo."""
    profile_file = DATA_DIR / "repositories" / repo_name / "profile.yaml"

    if not profile_file.exists():
        raise HTTPException(status_code=404, detail=f"Repo '{repo_name}' non trouvé")

    with open(profile_file) as f:
        profile = yaml.safe_load(f)

    return {"repo": repo_name, "metrics": profile["metrics"]}


@app.get("/api/neo4j/repos/{repo_name}")
def get_neo4j_repo(repo_name: str):
    """Stats Neo4j d'un repo."""
    try:
        ingester = Neo4jIngester()
        stats = ingester.get_repo_stats(repo_name)
        ingester.close()

        if not stats:
            raise HTTPException(status_code=404, detail=f"Repo '{repo_name}' non trouvé dans Neo4j")

        return stats
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e)) from e


# ============================================================================
# RAG Endpoints
# ============================================================================


@app.post("/api/chat")
def chat(request: ChatRequest):
    """
    Chat RAG avec les repos et monitoring qualité v2.8.

    Body:
        {
            "question": "Qui est le contributeur principal ?",
            "repo": "requests",  // optionnel
            "history": []        // optionnel
        }

    Response:
        {
            "answer": "...",
            "sources": [...],
            "processing_time": 1.23,
            "quality": {...}  // si validation activée
        }
    """
    try:
        engine = get_query_engine()

        result = engine.chat(
            question=request.question,
            repo=request.repo,
            history=request.history,
        )

        # Track métriques qualité si validation activée et disponible
        if "quality" in result:
            quality_tracker = get_quality_tracker()
            if quality_tracker:
                try:
                    # Construire résultat de validation pour tracking
                    validation_result = {
                        "confidence": result["quality"]["confidence"],
                        "quality_grade": result["quality"]["grade"],
                        "action": result["quality"]["action"],
                        "should_flag": result["quality"]["should_flag"],
                        "hallucination_analysis": {
                            "is_hallucination": result["quality"]["hallucination_detected"],
                            "severity": result["quality"]["hallucination_severity"],
                        },
                        "confidence_factors": {
                            "primary_weakness": "unknown"  # Non disponible dans API response simplifiée
                        },
                        "validation_metadata": {
                            "validation_time": result["quality"]["validation_time"],
                            "num_sources": len(result["sources"]),
                            "avg_source_score": (
                                sum(s["score"] for s in result["sources"]) / len(result["sources"])
                                if result["sources"]
                                else 0.0
                            ),
                            "answer_length": len(result["answer"]),
                            "question_length": len(request.question),
                            "validator_version": "2.8.0",
                        },
                        "answer_modified": result["quality"].get("answer_modified", False),
                    }

                    quality_tracker.track_response(
                        validation_result=validation_result,
                        processing_time=result["processing_time"],
                        question=request.question,
                        repo=request.repo,
                    )

                except Exception as tracking_error:
                    # Ne pas faire échouer la requête si tracking échoue
                    print(f"⚠️ Erreur tracking qualité: {tracking_error}")

        return result

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e)) from e


# ============================================================================
# OpenAI-compatible routes (pour Open WebUI sans Pipe)
# ============================================================================
# NOTE: On l'importe ICI, après que get_query_engine existe, pour éviter les cycles.
from hyperion.api.openai_compat import router as openai_router  # noqa: E402
from hyperion.api.v2_endpoints import router as v2_router  # noqa: E402

app.include_router(openai_router)
app.include_router(v2_router)


# ============================================================================
# Quality Monitoring Endpoints v2.8
# ============================================================================


@app.get("/api/quality/metrics")
def get_quality_metrics(hours: int = 24, repo: str = None):
    """
    Obtenir métriques qualité des réponses sur une période.

    Args:
        hours: Période en heures (défaut 24h)
        repo: Filtrer sur un repository (optionnel)

    Returns:
        Métriques agrégées (acceptance rate, confidence, etc.)
    """
    try:
        quality_tracker = get_quality_tracker()
        if not quality_tracker:
            raise HTTPException(status_code=503, detail="Monitoring qualité non disponible")

        # Valider paramètres
        if hours <= 0 or hours > 7 * 24:  # Max 7 jours
            raise HTTPException(
                status_code=400, detail="Période doit être entre 1h et 168h (7 jours)"
            )

        metrics = quality_tracker.get_metrics_summary(hours=hours, repo=repo)
        return metrics

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e)) from e


@app.get("/api/quality/trends")
def get_quality_trends(days: int = 7, repo: str = None):
    """
    Obtenir tendances qualité pour graphiques.

    Args:
        days: Nombre de jours (défaut 7, max 30)
        repo: Repository à filtrer (optionnel)

    Returns:
        Liste de points de données par jour
    """
    try:
        quality_tracker = get_quality_tracker()
        if not quality_tracker:
            raise HTTPException(status_code=503, detail="Monitoring qualité non disponible")

        # Valider paramètres
        if days <= 0 or days > 30:
            raise HTTPException(status_code=400, detail="Période doit être entre 1 et 30 jours")

        trends = quality_tracker.get_trend_data(days=days, repo=repo)
        return {"trends": trends, "period_days": days, "repository": repo or "all"}

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e)) from e


@app.get("/api/quality/alerts")
def get_quality_alerts(resolved: bool = False):
    """
    Obtenir alertes qualité actives ou résolues.

    Args:
        resolved: Inclure alertes résolues (défaut False)

    Returns:
        Liste d'alertes avec détails
    """
    try:
        quality_tracker = get_quality_tracker()
        if not quality_tracker:
            raise HTTPException(status_code=503, detail="Monitoring qualité non disponible")

        alerts = quality_tracker.get_quality_alerts(resolved=resolved)
        return {
            "alerts": alerts,
            "total": len(alerts),
            "resolved": resolved,
            "timestamp": "2024-12-28T00:00:00",  # API timestamp
        }

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e)) from e


@app.get("/api/quality/stats")
def get_quality_database_stats():
    """
    Obtenir statistiques de la base de données qualité.

    Returns:
        Informations sur la base de données (taille, records, etc.)
    """
    try:
        quality_tracker = get_quality_tracker()
        if not quality_tracker:
            raise HTTPException(status_code=503, detail="Monitoring qualité non disponible")

        stats = quality_tracker.get_database_stats()
        return stats

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e)) from e


# ============================================================================
# Main
# ============================================================================

if __name__ == "__main__":
    import uvicorn

    uvicorn.run(app, host="0.0.0.0", port=8000)
