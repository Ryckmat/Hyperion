"""Ingestion des données dans Qdrant."""

from pathlib import Path
from typing import List, Dict, Optional
import yaml
from qdrant_client import QdrantClient
from qdrant_client.models import Distance, VectorParams, PointStruct
from sentence_transformers import SentenceTransformer
import hashlib

from hyperion.rag.config import (
    QDRANT_HOST,
    QDRANT_PORT,
    QDRANT_COLLECTION,
    EMBEDDING_MODEL,
    EMBEDDING_DEVICE,
    EMBEDDING_DIM,
    CHUNK_SIZE,
    REPOS_DIR
)


class RAGIngester:
    """
    Ingestion des profils Hyperion dans Qdrant.
    
    Process :
    1. Charge les profils YAML
    2. Découpe en chunks sémantiques
    3. Génère embeddings (BGE-large GPU)
    4. Stocke dans Qdrant avec métadonnées
    """
    
    def __init__(
        self,
        qdrant_host: str = QDRANT_HOST,
        qdrant_port: int = QDRANT_PORT,
        collection_name: str = QDRANT_COLLECTION
    ):
        """Initialise l'ingester."""
        self.qdrant_client = QdrantClient(host=qdrant_host, port=qdrant_port)
        self.collection_name = collection_name
        
        # Modèle d'embeddings (GPU)
        print(f"📥 Chargement modèle embeddings : {EMBEDDING_MODEL}")
        self.embedding_model = SentenceTransformer(
            EMBEDDING_MODEL,
            device=EMBEDDING_DEVICE
        )
        print(f"✅ Modèle chargé sur {EMBEDDING_DEVICE}")
        
        # Créer collection si nécessaire
        self._ensure_collection()
    
    def _ensure_collection(self):
        """Crée la collection Qdrant si elle n'existe pas."""
        collections = self.qdrant_client.get_collections().collections
        collection_names = [c.name for c in collections]
        
        if self.collection_name not in collection_names:
            print(f"📦 Création collection : {self.collection_name}")
            self.qdrant_client.create_collection(
                collection_name=self.collection_name,
                vectors_config=VectorParams(
                    size=EMBEDDING_DIM,
                    distance=Distance.COSINE
                )
            )
            print("✅ Collection créée")
        else:
            print(f"✅ Collection existante : {self.collection_name}")
    
    def ingest_repo(self, repo_name: str) -> int:
        """
        Ingère un repo dans Qdrant.
        
        Args:
            repo_name: Nom du repo (ex: "requests")
            
        Returns:
            Nombre de chunks ingérés
        """
        profile_path = REPOS_DIR / repo_name / "profile.yaml"
        
        if not profile_path.exists():
            raise FileNotFoundError(f"Profil introuvable : {profile_path}")
        
        print(f"\n📊 Ingestion repo : {repo_name}")
        
        # Charger profil
        with open(profile_path, "r") as f:
            profile = yaml.safe_load(f)
        
        # Découper en chunks
        chunks = self._create_chunks(profile, repo_name)
        print(f"   • {len(chunks)} chunks créés")
        
        # Générer embeddings
        texts = [c["text"] for c in chunks]
        print(f"   • Génération embeddings...")
        embeddings = self.embedding_model.encode(
            texts,
            batch_size=32,
            show_progress_bar=True,
            convert_to_numpy=True
        )
        
        # Créer points Qdrant
        points = []
        for i, (chunk, embedding) in enumerate(zip(chunks, embeddings)):
            point_id = self._generate_id(repo_name, i)
            
            points.append(PointStruct(
                id=point_id,
                vector=embedding.tolist(),
                payload={
                    "repo": repo_name,
                    "text": chunk["text"],
                    "section": chunk["section"],
                    "metadata": chunk["metadata"]
                }
            ))
        
        # Uploader vers Qdrant
        print(f"   • Upload vers Qdrant...")
        self.qdrant_client.upsert(
            collection_name=self.collection_name,
            points=points
        )
        
        print(f"✅ {len(points)} chunks ingérés")
        return len(points)
    
    def ingest_all_repos(self) -> Dict[str, int]:
        """
        Ingère tous les repos disponibles.
        
        Returns:
            Dict {repo_name: nb_chunks}
        """
        if not REPOS_DIR.exists():
            raise FileNotFoundError(f"Dossier repos introuvable : {REPOS_DIR}")
        
        results = {}
        
        for repo_dir in REPOS_DIR.iterdir():
            if not repo_dir.is_dir():
                continue
            
            profile_file = repo_dir / "profile.yaml"
            if not profile_file.exists():
                continue
            
            repo_name = repo_dir.name
            
            try:
                count = self.ingest_repo(repo_name)
                results[repo_name] = count
            except Exception as e:
                print(f"❌ Erreur {repo_name} : {e}")
                results[repo_name] = 0
        
        return results
    
    def _create_chunks(self, profile: dict, repo_name: str) -> List[Dict]:
        """Découpe le profil en chunks sémantiques."""
        chunks = []
        
        # 1. Overview
        overview_text = self._format_overview(profile)
        chunks.append({
            "text": overview_text,
            "section": "overview",
            "metadata": {"type": "summary"}
        })
        
        # 2. Métriques
        metrics_text = self._format_metrics(profile)
        chunks.append({
            "text": metrics_text,
            "section": "metrics",
            "metadata": {"type": "quality"}
        })
        
        # 3. Contributeurs (par batch de 5)
        contributors = profile.get("git_summary", {}).get("contributors_top10", [])
        for i in range(0, len(contributors), 5):
            batch = contributors[i:i+5]
            contrib_text = self._format_contributors(batch, repo_name)
            chunks.append({
                "text": contrib_text,
                "section": "contributors",
                "metadata": {"type": "people", "batch": i//5}
            })
        
        # 4. Hotspots (par batch de 5)
        hotspots = profile.get("git_summary", {}).get("hotspots_top10", [])
        for i in range(0, len(hotspots), 5):
            batch = hotspots[i:i+5]
            hotspot_text = self._format_hotspots(batch, repo_name)
            chunks.append({
                "text": hotspot_text,
                "section": "hotspots",
                "metadata": {"type": "files", "batch": i//5}
            })
        
        # 5. Extensions
        extensions = profile.get("git_summary", {}).get("by_extension", [])[:10]
        ext_text = self._format_extensions(extensions, repo_name)
        chunks.append({
            "text": ext_text,
            "section": "extensions",
            "metadata": {"type": "tech"}
        })
        
        return chunks
    
    def _format_overview(self, profile: dict) -> str:
        """Formate l'overview du repo."""
        git = profile.get("git_summary", {})
        repo_info = profile.get("repositories", [{}])[0]
        metrics = profile.get("metrics", {})
        
        return f"""Repository: {profile.get('service')}
Language: {repo_info.get('main_language')}
License: {repo_info.get('license')}
Total commits: {git.get('commits')}
Contributors: {git.get('contributors')}
First commit: {git.get('first_commit')}
Last commit: {git.get('last_commit')}
Recent activity (90 days): {git.get('recent_commits_90d')} commits
Evolution years: {metrics.get('evolution_years')}
Average commits per year: {metrics.get('avg_commits_per_year')}
"""
    
    def _format_metrics(self, profile: dict) -> str:
        """Formate les métriques qualité."""
        metrics = profile.get("metrics", {})
        ratio = metrics.get("changes_ratio", {})
        
        return f"""Repository: {profile.get('service')}
Quality Metrics:
- Code Python: {ratio.get('code_py')}%
- Tests: {ratio.get('tests')}%
- Documentation: {ratio.get('docs')}%
- Average changes per hotspot: {metrics.get('avg_changes_per_hotspot')}
- Python changes per file: {metrics.get('py_changes_per_file_avg')}
"""
    
    def _format_contributors(self, contributors: list, repo_name: str) -> str:
        """Formate les contributeurs."""
        lines = [f"Repository: {repo_name}", "Top Contributors:"]
        
        for c in contributors:
            lines.append(f"- {c['name']} ({c['email']}): {c['commits']} commits")
        
        return "\n".join(lines)
    
    def _format_hotspots(self, hotspots: list, repo_name: str) -> str:
        """Formate les hotspots."""
        lines = [f"Repository: {repo_name}", "Most Changed Files (Hotspots):"]
        
        for h in hotspots:
            lines.append(f"- {h['path']}: {h['changes']} changes")
        
        return "\n".join(lines)
    
    def _format_extensions(self, extensions: list, repo_name: str) -> str:
        """Formate les extensions."""
        lines = [f"Repository: {repo_name}", "File Types:"]
        
        for e in extensions:
            lines.append(f"- {e['ext']}: {e['files']} files, {e['changes']} changes")
        
        return "\n".join(lines)
    
    def _generate_id(self, repo_name: str, index: int) -> int:
        """Génère un ID unique pour un point."""
        # Hash repo_name + index
        text = f"{repo_name}_{index}"
        hash_value = hashlib.md5(text.encode()).hexdigest()
        # Convertir en int (premiers 8 bytes)
        return int(hash_value[:16], 16) % (2**63)
    
    def clear_repo(self, repo_name: str):
        """Supprime les données d'un repo."""
        self.qdrant_client.delete(
            collection_name=self.collection_name,
            points_selector={
                "filter": {
                    "must": [
                        {"key": "repo", "match": {"value": repo_name}}
                    ]
                }
            }
        )
        print(f"🧹 Repo {repo_name} supprimé de Qdrant")
    
    def get_stats(self) -> dict:
        """Statistiques de la collection."""
        info = self.qdrant_client.get_collection(self.collection_name)
        return {
            "total_points": info.points_count,
            "vectors_count": info.vectors_count,
            "indexed_vectors_count": info.indexed_vectors_count
        }
