"""
Graphe de code pour analyse des relations et dépendances.

Module pour construire et analyser un graphe des relations entre éléments de code.
"""

from __future__ import annotations

import json
from collections import deque
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

import networkx as nx

from hyperion.modules.monitoring.logging.json_logger import get_logger
from hyperion.modules.understanding.ast_parser import FileAnalysis

logger = get_logger("hyperion.code_graph")


@dataclass
class CodeNode:
    """Nœud dans le graphe de code."""

    id: str
    type: str  # file, class, function, method, variable
    name: str
    file_path: str
    lineno: int = 0
    attributes: dict[str, Any] = field(default_factory=dict)


@dataclass
class CodeEdge:
    """Arête dans le graphe de code."""

    source: str
    target: str
    type: str  # imports, calls, inherits, contains, uses
    attributes: dict[str, Any] = field(default_factory=dict)


@dataclass
class GraphMetrics:
    """Métriques du graphe de code."""

    total_nodes: int
    total_edges: int
    connected_components: int
    avg_clustering: float
    max_depth: int
    cyclomatic_complexity: int
    coupling_metrics: dict[str, float]
    cohesion_metrics: dict[str, float]


class CodeGraph:
    """
    Graphe de code pour analyse des relations et dépendances.

    Fonctionnalités :
    - Construction du graphe depuis AST
    - Analyse des dépendances
    - Détection de cycles
    - Métriques de couplage/cohésion
    - Export pour visualisation
    - Recherche de chemins
    """

    def __init__(self):
        self.graph = nx.DiGraph()
        self.nodes: dict[str, CodeNode] = {}
        self.edges: dict[tuple[str, str], CodeEdge] = {}
        self.logger = get_logger("hyperion.code_graph")

    def build_from_analyses(self, analyses: dict[str, FileAnalysis]) -> None:
        """
        Construit le graphe depuis les analyses AST.

        Args:
            analyses: Résultats d'analyse AST par fichier
        """
        self.logger.info("Construction du graphe de code", files=len(analyses))

        # Phase 1 : Créer tous les nœuds
        self._create_nodes(analyses)

        # Phase 2 : Créer les arêtes
        self._create_edges(analyses)

        self.logger.info(
            "Graphe construit",
            nodes=len(self.nodes),
            edges=len(self.edges),
            components=nx.number_connected_components(self.graph.to_undirected()),
        )

    def _create_nodes(self, analyses: dict[str, FileAnalysis]) -> None:
        """Crée tous les nœuds du graphe."""
        for file_path, analysis in analyses.items():
            # Nœud fichier
            file_node_id = f"file:{file_path}"
            self._add_node(
                CodeNode(
                    id=file_node_id,
                    type="file",
                    name=Path(file_path).name,
                    file_path=file_path,
                    attributes={
                        "lines_of_code": analysis.lines_of_code,
                        "complexity": analysis.complexity_total,
                        "imports_count": len(analysis.imports),
                        "encoding": analysis.encoding,
                    },
                )
            )

            # Nœuds classes
            for class_info in analysis.classes:
                class_node_id = f"class:{file_path}:{class_info.name}"
                self._add_node(
                    CodeNode(
                        id=class_node_id,
                        type="class",
                        name=class_info.name,
                        file_path=file_path,
                        lineno=class_info.lineno,
                        attributes={
                            "bases": class_info.bases,
                            "decorators": class_info.decorators,
                            "is_abstract": class_info.is_abstract,
                            "visibility": class_info.visibility,
                            "methods_count": len(class_info.methods),
                            "attributes_count": len(class_info.attributes),
                        },
                    )
                )

                # Relation containment fichier -> classe
                self._add_edge(CodeEdge(source=file_node_id, target=class_node_id, type="contains"))

                # Nœuds méthodes
                for method_info in class_info.methods:
                    method_node_id = f"method:{file_path}:{class_info.name}:{method_info.name}"
                    self._add_node(
                        CodeNode(
                            id=method_node_id,
                            type="method",
                            name=method_info.name,
                            file_path=file_path,
                            lineno=method_info.lineno,
                            attributes={
                                "args": method_info.args,
                                "complexity": method_info.complexity,
                                "is_async": method_info.is_async,
                                "visibility": method_info.visibility,
                                "decorators": method_info.decorators,
                                "calls_count": len(method_info.calls),
                            },
                        )
                    )

                    # Relation containment classe -> méthode
                    self._add_edge(
                        CodeEdge(source=class_node_id, target=method_node_id, type="contains")
                    )

            # Nœuds fonctions (hors classes)
            for func_info in analysis.functions:
                func_node_id = f"function:{file_path}:{func_info.name}"
                self._add_node(
                    CodeNode(
                        id=func_node_id,
                        type="function",
                        name=func_info.name,
                        file_path=file_path,
                        lineno=func_info.lineno,
                        attributes={
                            "args": func_info.args,
                            "complexity": func_info.complexity,
                            "is_async": func_info.is_async,
                            "visibility": func_info.visibility,
                            "decorators": func_info.decorators,
                            "calls_count": len(func_info.calls),
                        },
                    )
                )

                # Relation containment fichier -> fonction
                self._add_edge(CodeEdge(source=file_node_id, target=func_node_id, type="contains"))

    def _create_edges(self, analyses: dict[str, FileAnalysis]) -> None:
        """Crée toutes les arêtes du graphe."""
        for file_path, analysis in analyses.items():
            # Arêtes d'imports
            self._create_import_edges(file_path, analysis)

            # Arêtes d'héritage
            self._create_inheritance_edges(file_path, analysis)

            # Arêtes d'appels de fonctions
            self._create_call_edges(file_path, analysis)

    def _create_import_edges(self, file_path: str, analysis: FileAnalysis) -> None:
        """Crée les arêtes d'imports."""
        file_node_id = f"file:{file_path}"

        for import_info in analysis.imports:
            # Essayer de trouver le fichier correspondant
            target_file = self._resolve_import(import_info.module, file_path)
            if target_file and f"file:{target_file}" in self.nodes:
                self._add_edge(
                    CodeEdge(
                        source=file_node_id,
                        target=f"file:{target_file}",
                        type="imports",
                        attributes={
                            "module": import_info.module,
                            "name": import_info.name,
                            "alias": import_info.alias,
                            "is_relative": import_info.is_relative,
                        },
                    )
                )

    def _create_inheritance_edges(self, file_path: str, analysis: FileAnalysis) -> None:
        """Crée les arêtes d'héritage."""
        for class_info in analysis.classes:
            class_node_id = f"class:{file_path}:{class_info.name}"

            for base_name in class_info.bases:
                # Rechercher la classe de base
                base_node_id = self._find_class_node(base_name, file_path)
                if base_node_id:
                    self._add_edge(
                        CodeEdge(
                            source=class_node_id,
                            target=base_node_id,
                            type="inherits",
                            attributes={"base_name": base_name},
                        )
                    )

    def _create_call_edges(self, file_path: str, analysis: FileAnalysis) -> None:
        """Crée les arêtes d'appels de fonctions."""
        # Calls depuis les fonctions
        for func_info in analysis.functions:
            func_node_id = f"function:{file_path}:{func_info.name}"
            for call_name in func_info.calls:
                target_node_id = self._find_callable_node(call_name, file_path)
                if target_node_id:
                    self._add_edge(
                        CodeEdge(
                            source=func_node_id,
                            target=target_node_id,
                            type="calls",
                            attributes={"function_name": call_name},
                        )
                    )

        # Calls depuis les méthodes
        for class_info in analysis.classes:
            for method_info in class_info.methods:
                method_node_id = f"method:{file_path}:{class_info.name}:{method_info.name}"
                for call_name in method_info.calls:
                    target_node_id = self._find_callable_node(call_name, file_path)
                    if target_node_id:
                        self._add_edge(
                            CodeEdge(
                                source=method_node_id,
                                target=target_node_id,
                                type="calls",
                                attributes={"function_name": call_name},
                            )
                        )

    def _add_node(self, node: CodeNode) -> None:
        """Ajoute un nœud au graphe."""
        self.nodes[node.id] = node
        self.graph.add_node(node.id, **node.attributes, name=node.name, type=node.type)

    def _add_edge(self, edge: CodeEdge) -> None:
        """Ajoute une arête au graphe."""
        if edge.source in self.nodes and edge.target in self.nodes:
            key = (edge.source, edge.target)
            self.edges[key] = edge
            self.graph.add_edge(edge.source, edge.target, type=edge.type, **edge.attributes)

    def _resolve_import(self, module_name: str, current_file: str) -> str | None:
        """Résout un nom de module vers un fichier."""
        # Heuristique simple pour résolution d'imports
        if module_name.startswith("."):
            # Import relatif
            current_dir = str(Path(current_file).parent)
            module_path = module_name.lstrip(".").replace(".", "/") + ".py"
            return str(Path(current_dir) / module_path)

        # Import absolu - chercher dans les fichiers connus
        module_path = module_name.replace(".", "/") + ".py"
        for _node_id, node in self.nodes.items():
            if node.type == "file" and node.file_path.endswith(module_path):
                return node.file_path

        return None

    def _find_class_node(self, class_name: str, current_file: str) -> str | None:
        """Trouve un nœud de classe par nom."""
        # Chercher dans le fichier actuel d'abord
        local_class_id = f"class:{current_file}:{class_name}"
        if local_class_id in self.nodes:
            return local_class_id

        # Chercher dans tous les fichiers
        for node_id, node in self.nodes.items():
            if node.type == "class" and node.name == class_name:
                return node_id

        return None

    def _find_callable_node(self, callable_name: str, current_file: str) -> str | None:
        """Trouve un nœud callable (fonction/méthode) par nom."""
        # Chercher fonction dans le fichier actuel
        func_id = f"function:{current_file}:{callable_name}"
        if func_id in self.nodes:
            return func_id

        # Chercher méthode dans les classes du fichier actuel
        for node_id, node in self.nodes.items():
            if (
                node.type == "method"
                and node.name == callable_name
                and node.file_path == current_file
            ):
                return node_id

        # Chercher dans tous les fichiers
        for node_id, node in self.nodes.items():
            if (node.type == "function" or node.type == "method") and node.name == callable_name:
                return node_id

        return None

    def find_cycles(self) -> list[list[str]]:
        """
        Trouve les cycles dans le graphe.

        Returns:
            Liste des cycles trouvés
        """
        try:
            cycles = list(nx.simple_cycles(self.graph))
            self.logger.info(f"Cycles détectés : {len(cycles)}")
            return cycles
        except nx.NetworkXError:
            return []

    def get_strongly_connected_components(self) -> list[set[str]]:
        """
        Trouve les composantes fortement connexes.

        Returns:
            Liste des composantes fortement connexes
        """
        return list(nx.strongly_connected_components(self.graph))

    def calculate_metrics(self) -> GraphMetrics:
        """
        Calcule les métriques du graphe.

        Returns:
            Métriques complètes du graphe
        """
        # Métriques de base
        total_nodes = len(self.nodes)
        total_edges = len(self.edges)
        connected_components = nx.number_connected_components(self.graph.to_undirected())

        # Clustering coefficient
        try:
            avg_clustering = nx.average_clustering(self.graph.to_undirected())
        except Exception:
            avg_clustering = 0.0

        # Profondeur maximale
        max_depth = self._calculate_max_depth()

        # Complexité cyclomatique totale
        cyclomatic_complexity = sum(
            node.attributes.get("complexity", 0) for node in self.nodes.values()
        )

        # Métriques de couplage
        coupling_metrics = self._calculate_coupling_metrics()

        # Métriques de cohésion
        cohesion_metrics = self._calculate_cohesion_metrics()

        return GraphMetrics(
            total_nodes=total_nodes,
            total_edges=total_edges,
            connected_components=connected_components,
            avg_clustering=avg_clustering,
            max_depth=max_depth,
            cyclomatic_complexity=cyclomatic_complexity,
            coupling_metrics=coupling_metrics,
            cohesion_metrics=cohesion_metrics,
        )

    def _calculate_max_depth(self) -> int:
        """Calcule la profondeur maximale du graphe."""
        max_depth = 0

        # Trouver tous les nœuds racines (sans prédécesseurs)
        roots = [n for n in self.graph.nodes() if self.graph.in_degree(n) == 0]

        for root in roots:
            try:
                paths = nx.single_source_shortest_path_length(self.graph, root)
                if paths:
                    max_depth = max(max_depth, max(paths.values()))
            except Exception:
                continue

        return max_depth

    def _calculate_coupling_metrics(self) -> dict[str, float]:
        """Calcule les métriques de couplage."""
        metrics = {}

        # Afferent coupling (Ca) - nombre de classes qui dépendent de cette classe
        # Efferent coupling (Ce) - nombre de classes dont cette classe dépend

        class_nodes = {nid: node for nid, node in self.nodes.items() if node.type == "class"}

        for class_id, class_node in class_nodes.items():
            # Ca - classes qui pointent vers cette classe
            ca = len(
                [
                    e
                    for e in self.edges.values()
                    if e.target == class_id and e.type in ["inherits", "uses", "calls"]
                ]
            )

            # Ce - classes vers lesquelles cette classe pointe
            ce = len(
                [
                    e
                    for e in self.edges.values()
                    if e.source == class_id and e.type in ["inherits", "uses", "calls"]
                ]
            )

            # Instability = Ce / (Ca + Ce)
            instability = ce / (ca + ce) if (ca + ce) > 0 else 0

            metrics[class_node.name] = {
                "afferent_coupling": ca,
                "efferent_coupling": ce,
                "instability": instability,
            }

        return metrics

    def _calculate_cohesion_metrics(self) -> dict[str, float]:
        """Calcule les métriques de cohésion."""
        metrics = {}

        class_nodes = {nid: node for nid, node in self.nodes.items() if node.type == "class"}

        for _class_id, class_node in class_nodes.items():
            # LCOM (Lack of Cohesion of Methods)
            # Simplifié : méthodes qui partagent des attributs

            class_methods = [
                nid
                for nid, node in self.nodes.items()
                if node.type == "method"
                and nid.startswith(f"method:{class_node.file_path}:{class_node.name}:")
            ]

            # Calculer les connections internes
            internal_connections = 0
            total_possible = len(class_methods) * (len(class_methods) - 1) / 2

            for i, method1_id in enumerate(class_methods):
                for method2_id in class_methods[i + 1 :]:
                    # Vérifier s'il y a une connexion directe ou indirecte
                    if (method1_id, method2_id) in self.edges or (
                        method2_id,
                        method1_id,
                    ) in self.edges:
                        internal_connections += 1

            cohesion = internal_connections / total_possible if total_possible > 0 else 1.0

            metrics[class_node.name] = {
                "cohesion_ratio": cohesion,
                "methods_count": len(class_methods),
                "internal_connections": internal_connections,
            }

        return metrics

    def find_shortest_path(self, source: str, target: str) -> list[str] | None:
        """
        Trouve le chemin le plus court entre deux nœuds.

        Args:
            source: Nœud source
            target: Nœud cible

        Returns:
            Chemin le plus court ou None si pas de chemin
        """
        try:
            return nx.shortest_path(self.graph, source, target)
        except nx.NetworkXNoPath:
            return None

    def get_node_dependencies(self, node_id: str, max_depth: int = None) -> set[str]:
        """
        Obtient toutes les dépendances d'un nœud.

        Args:
            node_id: ID du nœud
            max_depth: Profondeur maximale de recherche

        Returns:
            Ensemble des dépendances
        """
        dependencies = set()

        if node_id not in self.graph:
            return dependencies

        # BFS pour trouver les dépendances
        queue = deque([(node_id, 0)])
        visited = {node_id}

        while queue:
            current_node, depth = queue.popleft()

            if max_depth is not None and depth >= max_depth:
                continue

            for successor in self.graph.successors(current_node):
                if successor not in visited:
                    dependencies.add(successor)
                    visited.add(successor)
                    queue.append((successor, depth + 1))

        return dependencies

    def export_to_dot(self, output_path: str | Path, include_types: set[str] = None) -> None:
        """
        Exporte le graphe en format DOT pour Graphviz.

        Args:
            output_path: Chemin de sortie
            include_types: Types de nœuds à inclure
        """
        if include_types is None:
            include_types = {"file", "class", "function", "method"}

        subgraph = self.graph.subgraph(
            [nid for nid, node in self.nodes.items() if node.type in include_types]
        )

        nx.drawing.nx_pydot.write_dot(subgraph, output_path)
        self.logger.info(f"Graphe exporté vers {output_path}")

    def export_to_json(self, output_path: str | Path) -> None:
        """
        Exporte le graphe en format JSON.

        Args:
            output_path: Chemin de sortie
        """
        data = {
            "nodes": [
                {
                    "id": node.id,
                    "type": node.type,
                    "name": node.name,
                    "file_path": node.file_path,
                    "lineno": node.lineno,
                    "attributes": node.attributes,
                }
                for node in self.nodes.values()
            ],
            "edges": [
                {
                    "source": edge.source,
                    "target": edge.target,
                    "type": edge.type,
                    "attributes": edge.attributes,
                }
                for edge in self.edges.values()
            ],
        }

        with open(output_path, "w", encoding="utf-8") as f:
            json.dump(data, f, ensure_ascii=False, indent=2)

        self.logger.info(f"Graphe exporté vers {output_path}")

    def get_hotspots(self, metric: str = "complexity", top_n: int = 10) -> list[tuple[str, Any]]:
        """
        Identifie les hotspots selon une métrique.

        Args:
            metric: Métrique à utiliser (complexity, calls_count, etc.)
            top_n: Nombre de résultats à retourner

        Returns:
            Liste des hotspots triés par métrique décroissante
        """
        candidates = []

        for node_id, node in self.nodes.items():
            if metric in node.attributes:
                value = node.attributes[metric]
                candidates.append((node_id, value))

        candidates.sort(key=lambda x: x[1], reverse=True)
        return candidates[:top_n]
