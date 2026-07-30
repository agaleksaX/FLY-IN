from __future__ import annotations

from typing import TYPE_CHECKING

from algorithms.dijkstra import dijkstra
from algorithms.bfs import bfs
from utils.exceptions import AlgorithmError

if TYPE_CHECKING:
    from models.graph import Graph
    from models.zone import Zone
    from models.path import Path


class PathSelector:
    """Selects the best path between zones using available algorithms."""

    def __init__(self, graph: Graph) -> None:
        self._graph = graph
        self._cache: dict[tuple[str, str], Path] = {}

    def find_path(self, start: Zone, end: Zone) -> Path:
        """Find a path from start to end, using cache if available."""
        key = (start.name, end.name)
        if key in self._cache:
            return self._cache[key]

        try:
            path = dijkstra(self._graph, start, end)
        except AlgorithmError:
            path = bfs(self._graph, start, end)

        self._cache[key] = path
        return path

    def clear_cache(self) -> None:
        """Clear the path cache."""
        self._cache.clear()
