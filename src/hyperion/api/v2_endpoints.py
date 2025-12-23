"""Endpoints API v2 pour les 8 moteurs d'intelligence Hyperion."""

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel

from hyperion.modules.integrations.neo4j_code_ingester import Neo4jCodeIngester

router = APIRouter(prefix="/api/v2", tags=["Hyperion v2"])

# ============================================================================
# Models Pydantic
# ============================================================================


class ImpactAnalysisRequest(BaseModel):
    repo: str
    file: str
    changes: list[str]
    depth: int | None = 3


class CodeSearchRequest(BaseModel):
    query: str
    repo: str
    type: str | None = None  # function, class, file


class AnomalyRequest(BaseModel):
    repo: str
    types: list[str] | None = ["complexity", "size", "duplicates"]


# ============================================================================
# Neo4j v2 Endpoints (Code Understanding)
# ============================================================================


@router.get("/repos/{repo_name}/functions")
async def get_repo_functions(repo_name: str, limit: int = 50):
    """Liste les fonctions d'un repo avec Neo4j v2."""
    try:
        ingester = Neo4jCodeIngester()

        with ingester.driver.session(database=ingester.database) as session:
            result = session.run(
                """
                MATCH (f:Function {repo: $repo})
                RETURN f.name as name, f.file as file, f.line_start as line,
                       f.signature as signature, f.docstring as docstring,
                       f.is_method as is_method, f.is_private as is_private
                ORDER BY f.file, f.line_start
                LIMIT $limit
            """,
                repo=repo_name,
                limit=limit,
            )

            functions = []
            for record in result:
                functions.append(
                    {
                        "name": record["name"],
                        "file": record["file"],
                        "line": record["line"],
                        "signature": record["signature"],
                        "docstring": record["docstring"][:200] if record["docstring"] else "",
                        "is_method": record["is_method"],
                        "is_private": record["is_private"],
                    }
                )

        ingester.close()

        return {"repo": repo_name, "functions": functions, "count": len(functions)}

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Erreur Neo4j: {str(e)}")


@router.get("/repos/{repo_name}/classes")
async def get_repo_classes(repo_name: str, limit: int = 30):
    """Liste les classes d'un repo avec Neo4j v2."""
    try:
        ingester = Neo4jCodeIngester()

        with ingester.driver.session(database=ingester.database) as session:
            result = session.run(
                """
                MATCH (c:Class {repo: $repo})
                RETURN c.name as name, c.file as file, c.line_start as line,
                       c.docstring as docstring, c.methods as methods,
                       c.bases as bases, c.is_private as is_private
                ORDER BY c.file, c.line_start
                LIMIT $limit
            """,
                repo=repo_name,
                limit=limit,
            )

            classes = []
            for record in result:
                classes.append(
                    {
                        "name": record["name"],
                        "file": record["file"],
                        "line": record["line"],
                        "docstring": record["docstring"][:200] if record["docstring"] else "",
                        "methods": record["methods"] or [],
                        "bases": record["bases"] or [],
                        "is_private": record["is_private"],
                    }
                )

        ingester.close()

        return {"repo": repo_name, "classes": classes, "count": len(classes)}

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Erreur Neo4j: {str(e)}")


@router.get("/repos/{repo_name}/stats")
async def get_repo_code_stats(repo_name: str):
    """Statistiques code d'un repo (Neo4j v2)."""
    try:
        ingester = Neo4jCodeIngester()
        stats = ingester.get_repo_stats(repo_name)
        ingester.close()

        if stats["functions"] == 0 and stats["classes"] == 0:
            raise HTTPException(
                status_code=404, detail=f"Repo '{repo_name}' non trouvé dans Neo4j v2"
            )

        return {"repo": repo_name, **stats}

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Erreur Neo4j: {str(e)}")


# ============================================================================
# Code Understanding Engine
# ============================================================================


@router.post("/understanding/search")
async def search_code(request: CodeSearchRequest):
    """Recherche sémantique dans le code (RAG + Neo4j)."""
    try:
        # Utiliser l'engine RAG existant
        from hyperion.modules.rag.query import RAGQueryEngine

        engine = RAGQueryEngine()

        # Query RAG avec focus sur le code
        question = f"Dans {request.repo}, trouve {request.query}"
        if request.type:
            question += f" (type: {request.type})"

        result = engine.chat(question=question, repo=request.repo, history=None)

        return {
            "query": request.query,
            "repo": request.repo,
            "answer": result["answer"],
            "sources": result["sources"],
            "type": "semantic_search",
        }

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Erreur recherche: {str(e)}")


@router.get("/understanding/{repo_name}/explore")
async def explore_codebase(repo_name: str, pattern: str = ""):
    """Exploration guidée du codebase."""
    try:
        ingester = Neo4jCodeIngester()

        with ingester.driver.session(database=ingester.database) as session:
            # Exploration adaptée au pattern
            if "session" in pattern.lower():
                query = """
                MATCH (f:Function {repo: $repo})
                WHERE toLower(f.name) CONTAINS 'session'
                   OR toLower(f.file) CONTAINS 'session'
                RETURN f.name, f.file, f.signature, f.docstring
                LIMIT 10
                """
            elif "auth" in pattern.lower():
                query = """
                MATCH (f:Function {repo: $repo})
                WHERE toLower(f.name) CONTAINS 'auth'
                   OR toLower(f.file) CONTAINS 'auth'
                RETURN f.name, f.file, f.signature, f.docstring
                LIMIT 10
                """
            else:
                # Exploration générale : top functions
                query = """
                MATCH (f:Function {repo: $repo})
                WHERE NOT f.is_private
                RETURN f.name, f.file, f.signature, f.docstring
                ORDER BY size(f.docstring) DESC
                LIMIT 10
                """

            result = session.run(query, repo=repo_name)

            exploration = []
            for record in result:
                exploration.append(
                    {
                        "name": record["f.name"],
                        "file": record["f.file"],
                        "signature": record["f.signature"],
                        "docstring": record["f.docstring"][:150] if record["f.docstring"] else "",
                    }
                )

        ingester.close()

        return {
            "repo": repo_name,
            "pattern": pattern,
            "results": exploration,
            "type": "code_exploration",
        }

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Erreur exploration: {str(e)}")


# ============================================================================
# Impact Analysis Engine (simplifié)
# ============================================================================


@router.post("/impact/analyze")
async def analyze_impact(request: ImpactAnalysisRequest):
    """Analyse d'impact des modifications (version simplifiée)."""
    try:
        ingester = Neo4jCodeIngester()

        with ingester.driver.session(database=ingester.database) as session:
            # Trouver les fonctions dans le fichier modifié
            result = session.run(
                """
                MATCH (f:Function {repo: $repo, file: $file})
                RETURN f.name, f.signature
            """,
                repo=request.repo,
                file=request.file,
            )

            affected_functions = []
            for record in result:
                affected_functions.append(
                    {
                        "name": record["f.name"],
                        "signature": record["f.signature"],
                        "impact": "DIRECT",
                    }
                )

            # Trouver les classes dans le même fichier
            result = session.run(
                """
                MATCH (c:Class {repo: $repo, file: $file})
                RETURN c.name, c.methods
            """,
                repo=request.repo,
                file=request.file,
            )

            affected_classes = []
            for record in result:
                affected_classes.append(
                    {"name": record["c.name"], "methods": record["c.methods"], "impact": "DIRECT"}
                )

            # Impact potentiel : fichiers qui importent ce module
            result = session.run(
                """
                MATCH (file:File {repo: $repo})-[:IMPORTS]->(m:Module)
                WHERE $file CONTAINS m.name OR m.name CONTAINS $file
                RETURN DISTINCT file.path
                LIMIT 5
            """,
                repo=request.repo,
                file=request.file.replace(".py", ""),
            )

            potentially_affected_files = []
            for record in result:
                potentially_affected_files.append(
                    {
                        "file": record["file.path"],
                        "impact": "INDIRECT",
                        "reason": "imports_modified_module",
                    }
                )

        ingester.close()

        return {
            "repo": request.repo,
            "modified_file": request.file,
            "changes": request.changes,
            "affected_functions": affected_functions,
            "affected_classes": affected_classes,
            "potentially_affected_files": potentially_affected_files,
            "risk_level": "MEDIUM" if len(affected_functions) > 3 else "LOW",
            "impact_summary": f"{len(affected_functions)} functions, {len(affected_classes)} classes",
        }

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Erreur impact analysis: {str(e)}")


# ============================================================================
# Anomaly Detection Engine (simplifié)
# ============================================================================


@router.post("/anomaly/scan")
async def scan_anomalies(request: AnomalyRequest):
    """Détection d'anomalies dans le code."""
    try:
        ingester = Neo4jCodeIngester()

        anomalies = []

        with ingester.driver.session(database=ingester.database) as session:
            # Anomalie : Fonctions avec beaucoup d'arguments
            if "complexity" in request.types:
                result = session.run(
                    """
                    MATCH (f:Function {repo: $repo})
                    WHERE size(f.args) > 5
                    RETURN f.name, f.file, f.signature, size(f.args) as arg_count
                    ORDER BY arg_count DESC
                    LIMIT 10
                """,
                    repo=request.repo,
                )

                for record in result:
                    anomalies.append(
                        {
                            "type": "high_complexity",
                            "severity": "MEDIUM",
                            "function": record["f.name"],
                            "file": record["f.file"],
                            "signature": record["f.signature"],
                            "metric": f"{record['arg_count']} arguments",
                            "suggestion": "Consider breaking into smaller functions",
                        }
                    )

            # Anomalie : Fichiers avec beaucoup de fonctions
            if "size" in request.types:
                result = session.run(
                    """
                    MATCH (file:File {repo: $repo})-[:CONTAINS]->(f:Function)
                    WITH file, count(f) as function_count
                    WHERE function_count > 15
                    RETURN file.path, function_count
                    ORDER BY function_count DESC
                    LIMIT 5
                """,
                    repo=request.repo,
                )

                for record in result:
                    anomalies.append(
                        {
                            "type": "large_file",
                            "severity": "LOW",
                            "file": record["file.path"],
                            "metric": f"{record['function_count']} functions",
                            "suggestion": "Consider splitting into multiple modules",
                        }
                    )

            # Anomalie : Classes sans docstring
            result = session.run(
                """
                MATCH (c:Class {repo: $repo})
                WHERE c.docstring IS NULL OR c.docstring = ""
                RETURN c.name, c.file
                LIMIT 5
            """,
                repo=request.repo,
            )

            for record in result:
                anomalies.append(
                    {
                        "type": "missing_documentation",
                        "severity": "LOW",
                        "class": record["c.name"],
                        "file": record["c.file"],
                        "suggestion": "Add class docstring",
                    }
                )

        ingester.close()

        return {
            "repo": request.repo,
            "anomaly_types": request.types,
            "anomalies": anomalies,
            "total_found": len(anomalies),
            "severity_summary": {
                "HIGH": len([a for a in anomalies if a["severity"] == "HIGH"]),
                "MEDIUM": len([a for a in anomalies if a["severity"] == "MEDIUM"]),
                "LOW": len([a for a in anomalies if a["severity"] == "LOW"]),
            },
        }

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Erreur anomaly detection: {str(e)}")


# ============================================================================
# Health Check v2
# ============================================================================


@router.get("/health")
async def health_check_v2():
    """Health check des moteurs v2."""
    status = {"status": "healthy", "neo4j_code": "unknown", "rag": "unknown", "modules": []}

    # Test Neo4j Code
    try:
        ingester = Neo4jCodeIngester()
        stats = ingester.get_repo_stats("requests")
        ingester.close()
        if stats["functions"] > 0:
            status["neo4j_code"] = f"ok ({stats['functions']} functions)"
        else:
            status["neo4j_code"] = "no data"
    except Exception as e:
        status["neo4j_code"] = f"error: {str(e)}"
        status["status"] = "degraded"

    # Test RAG
    try:
        from hyperion.modules.rag.query import RAGQueryEngine

        _ = RAGQueryEngine()
        status["rag"] = "ok"
    except Exception as e:
        status["rag"] = f"error: {str(e)}"
        status["status"] = "degraded"

    # Status modules
    status["modules"] = ["code_understanding", "impact_analysis", "anomaly_detection", "neo4j_v2"]

    return status
