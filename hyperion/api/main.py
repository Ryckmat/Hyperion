"""API REST Hyperion - Backend FastAPI."""

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from pathlib import Path
from typing import Optional, List
import yaml

from hyperion.integrations.neo4j_ingester import Neo4jIngester
from hyperion.config import DATA_DIR
from hyperion.__version__ import __version__


# ============================================================================
# Pydantic Models
# ============================================================================

class ChatRequest(BaseModel):
    """Requête chat RAG."""
    question: str
    repo: Optional[str] = None
    history: Optional[List[dict]] = None


# ============================================================================
# Configuration FastAPI
# ============================================================================

app = FastAPI(
    title="Hyperion API",
    description="API REST pour le profiler Git Hyperion + RAG",
    version=__version__,
    docs_url="/docs",
    redoc_url="/redoc"
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
# RAG Global (lazy loading)
# ============================================================================

_query_engine = None

def get_query_engine():
    """Get or create RAG query engine."""
    global _query_engine
    if _query_engine is None:
        from hyperion.rag.query import RAGQueryEngine
        _query_engine = RAGQueryEngine()
    return _query_engine


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
        "features": ["repos", "neo4j", "rag"],
        "endpoints": {
            "docs": "/docs",
            "repos": "/api/repos",
            "chat": "/api/chat",
            "health": "/api/health"
        }
    }


@app.get("/api/health")
def health_check():
    """Health check API + Neo4j + RAG."""
    status = {
        "status": "healthy",
        "api": "ok",
        "neo4j": "unknown",
        "rag": "unknown"
    }
    
    # Test Neo4j
    try:
        ingester = Neo4jIngester()
        ingester.driver.verify_connectivity()
        ingester.close()
        status["neo4j"] = "ok"
    except Exception as e:
        status["neo4j"] = f"error: {str(e)}"
        status["status"] = "degraded"
    
    # Test RAG
    try:
        engine = get_query_engine()
        status["rag"] = "ok"
    except Exception as e:
        status["rag"] = f"error: {str(e)}"
        status["status"] = "degraded"
    
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
            with open(profile_file, "r") as f:
                profile = yaml.safe_load(f)
            
            repos.append({
                "name": profile["service"],
                "language": profile["repositories"][0]["main_language"],
                "commits": profile["git_summary"]["commits"],
                "contributors": profile["git_summary"]["contributors"],
                "first_commit": profile["git_summary"]["first_commit"],
                "last_commit": profile["git_summary"]["last_commit"],
                "license": profile["repositories"][0]["license"],
            })
        except Exception as e:
            continue
    
    return {"repos": repos, "count": len(repos)}


@app.get("/api/repos/{repo_name}")
def get_repo(repo_name: str):
    """Détails complets d'un repo."""
    profile_file = DATA_DIR / "repositories" / repo_name / "profile.yaml"
    
    if not profile_file.exists():
        raise HTTPException(status_code=404, detail=f"Repo '{repo_name}' non trouvé")
    
    with open(profile_file, "r") as f:
        profile = yaml.safe_load(f)
    
    return profile


@app.get("/api/repos/{repo_name}/contributors")
def get_contributors(repo_name: str, limit: Optional[int] = 10):
    """Top contributeurs d'un repo."""
    profile_file = DATA_DIR / "repositories" / repo_name / "profile.yaml"
    
    if not profile_file.exists():
        raise HTTPException(status_code=404, detail=f"Repo '{repo_name}' non trouvé")
    
    with open(profile_file, "r") as f:
        profile = yaml.safe_load(f)
    
    contributors = profile["git_summary"]["contributors_top10"][:limit]
    
    return {
        "repo": repo_name,
        "contributors": contributors,
        "count": len(contributors)
    }


@app.get("/api/repos/{repo_name}/hotspots")
def get_hotspots(repo_name: str, limit: Optional[int] = 10):
    """Top hotspots d'un repo."""
    profile_file = DATA_DIR / "repositories" / repo_name / "profile.yaml"
    
    if not profile_file.exists():
        raise HTTPException(status_code=404, detail=f"Repo '{repo_name}' non trouvé")
    
    with open(profile_file, "r") as f:
        profile = yaml.safe_load(f)
    
    hotspots = profile["git_summary"]["hotspots_top10"][:limit]
    
    return {
        "repo": repo_name,
        "hotspots": hotspots,
        "count": len(hotspots)
    }


@app.get("/api/repos/{repo_name}/metrics")
def get_metrics(repo_name: str):
    """Métriques qualité d'un repo."""
    profile_file = DATA_DIR / "repositories" / repo_name / "profile.yaml"
    
    if not profile_file.exists():
        raise HTTPException(status_code=404, detail=f"Repo '{repo_name}' non trouvé")
    
    with open(profile_file, "r") as f:
        profile = yaml.safe_load(f)
    
    return {
        "repo": repo_name,
        "metrics": profile["metrics"]
    }


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
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


# ============================================================================
# RAG Endpoints
# ============================================================================

@app.post("/api/chat")
def chat(request: ChatRequest):
    """
    Chat RAG avec les repos.
    
    Body:
        {
            "question": "Qui est le contributeur principal ?",
            "repo": "requests",  // optionnel
            "history": []        // optionnel
        }
    """
    try:
        engine = get_query_engine()
        
        result = engine.chat(
            question=request.question,
            repo=request.repo,
            history=request.history
        )
        
        return result
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


# ============================================================================
# Main
# ============================================================================

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
