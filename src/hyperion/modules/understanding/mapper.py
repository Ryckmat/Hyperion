"""
Mapper feature business → code.

Auteur: Ryckman Matthieu
Projet: Hyperion (projet personnel)
Version: 2.0.0
"""

from typing import Any


class FeatureMapper:
    """
    Mappe les features business vers le code source.

    Utilise embeddings sémantiques pour recherche.
    """

    def __init__(self, code_index: dict[str, dict[str, Any]]):
        """
        Initialise le mapper.

        Args:
            code_index: Index de code généré par CodeIndexer
        """
        self.code_index = code_index
        self.feature_mappings: dict[str, list[str]] = {}

    def map_feature_to_code(self, feature_description: str) -> list[dict[str, Any]]:
        """
        Trouve le code correspondant à une feature business.

        Args:
            feature_description: Description textuelle de la feature

        Returns:
            Liste de localisations code avec scores
        """
        # TODO: Implémenter recherche sémantique via embeddings
        results = []

        # Recherche simple par mots-clés (à remplacer par embeddings)
        keywords = set(feature_description.lower().split())

        for file_path, metadata in self.code_index.items():
            score = self._calculate_relevance(keywords, metadata)
            if score > 0.3:  # Seuil de pertinence
                results.append(
                    {
                        "file": file_path,
                        "score": score,
                        "matches": self._find_matches(keywords, metadata),
                    }
                )

        # Trier par score décroissant
        results.sort(key=lambda x: x["score"], reverse=True)
        return results

    def _calculate_relevance(
        self, keywords: set[str], metadata: dict[str, Any]
    ) -> float:
        """Calcule un score de pertinence."""
        # TODO: Implémenter scoring avancé
        score = 0.0
        total_text = ""

        # Docstrings
        for docstring in metadata.get("docstrings", {}).values():
            total_text += " " + docstring.lower()

        # Commentaires
        total_text += " " + " ".join(metadata.get("comments", []))

        # Noms de fonctions/classes
        for func in metadata.get("functions", []):
            total_text += " " + func.get("name", "")

        # Compter matches
        matches = sum(1 for kw in keywords if kw in total_text)
        score = matches / len(keywords) if keywords else 0.0

        return score

    def _find_matches(self, keywords: set[str], metadata: dict[str, Any]) -> list[str]:
        """Trouve les localisations exactes des matches."""
        # TODO: Implémenter localisation précise
        matches = []

        # Docstrings
        for name, docstring in metadata.get("docstrings", {}).items():
            if any(kw in docstring.lower() for kw in keywords):
                matches.append(f"docstring:{name}")

        # Fonctions
        for func in metadata.get("functions", []):
            if any(kw in func.get("name", "").lower() for kw in keywords):
                matches.append(f"function:{func.get('name')}")

        return matches

    def add_manual_mapping(self, feature_name: str, code_locations: list[str]):
        """
        Ajoute un mapping manuel feature → code.

        Args:
            feature_name: Nom de la feature
            code_locations: Liste de localisations code
        """
        self.feature_mappings[feature_name] = code_locations

    def get_all_features(self) -> list[str]:
        """Retourne toutes les features mappées."""
        return list(self.feature_mappings.keys())
