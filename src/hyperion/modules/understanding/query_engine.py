"""
Moteur de requêtes pour compréhension de code.

Auteur: Ryckman Matthieu
Projet: Hyperion (projet personnel)
Version: 2.0.0
"""

from pathlib import Path
from typing import Any

from hyperion.modules.understanding.indexer import CodeIndexer
from hyperion.modules.understanding.mapper import FeatureMapper


class UnderstandingQueryEngine:
    """
    Interface unifiée pour requêtes de compréhension code.

    Combine indexation + mapping + RAG.
    """

    def __init__(self, repo_path: Path):
        """
        Initialise le query engine.

        Args:
            repo_path: Chemin du repository
        """
        self.repo_path = Path(repo_path)
        self.indexer = CodeIndexer(repo_path)
        self.code_index = self.indexer.index_repository()
        self.mapper = FeatureMapper(self.code_index)

    def query(self, question: str) -> dict[str, Any]:
        """
        Répond à une question sur le code.

        Args:
            question: Question en langage naturel

        Returns:
            Réponse structurée avec sources
        """
        # TODO: Implémenter RAG multi-sources
        results = self.mapper.map_feature_to_code(question)

        return {
            "question": question,
            "answer": self._generate_answer(question, results),
            "sources": results[:5],  # Top 5 sources
            "confidence": self._calculate_confidence(results),
        }

    def _generate_answer(self, question: str, results: list[dict[str, Any]]) -> str:
        """Génère une réponse textuelle."""
        # TODO: Implémenter génération via LLM
        if not results:
            return "Aucune localisation code trouvée pour cette question."

        top_result = results[0]
        return f"La fonctionnalité est implémentée dans {top_result['file']} (score: {top_result['score']:.2f})"

    def _calculate_confidence(self, results: list[dict[str, Any]]) -> float:
        """Calcule la confiance de la réponse."""
        if not results:
            return 0.0
        return min(results[0]["score"], 1.0)

    def find_implementation(self, feature_name: str) -> list[str]:
        """
        Trouve où une feature est implémentée.

        Args:
            feature_name: Nom de la feature

        Returns:
            Liste de fichiers/fonctions
        """
        results = self.mapper.map_feature_to_code(feature_name)
        return [r["file"] for r in results[:10]]

    def find_tests(self, code_location: str) -> list[str]:
        """
        Trouve les tests associés à un code.

        Args:
            code_location: Chemin du fichier/fonction

        Returns:
            Liste de fichiers de tests
        """
        # TODO: Implémenter recherche tests
        # Stratégie: chercher test_*.py ou *_test.py contenant le nom
        test_files = []
        test_paths = list(self.repo_path.rglob("test_*.py")) + list(self.repo_path.rglob("*_test.py"))

        for test_file in test_paths:
            # Vérifier si le nom du fichier est mentionné
            if Path(code_location).stem in test_file.read_text():
                test_files.append(str(test_file))

        return test_files

    def get_related_files(self, file_path: str, max_results: int = 10) -> list[dict[str, Any]]:
        """
        Trouve les fichiers liés sémantiquement.

        Args:
            file_path: Fichier de référence
            max_results: Nombre max de résultats

        Returns:
            Fichiers similaires avec scores
        """
        # TODO: Implémenter similarité sémantique via embeddings
        return []
