from __future__ import annotations

from collections import deque
from typing import TYPE_CHECKING

from utils.exceptions import AlgorithmError

if TYPE_CHECKING:
    from models.graph import Graph
    from models.zone import Zone
    from models.path import Path
    from models.connection import Connection


def bfs(graph: Graph, start: Zone, end: Zone) -> Path:
    """Find shortest path (by hop count) using Breadth-First Search."""
    from models.path import Path

    queue: deque[tuple[Zone, list[Zone], list[Connection]]] = deque()
    queue.append((start, [start], []))
    visited: set[str] = {start.name}

    while queue:
        current, zones, connections = queue.popleft()
        if current is end:
            return Path(zones, connections)

        for neighbor, connection in graph.neighbors(current):
            if neighbor.is_blocked():
                continue
            if neighbor.name in visited:
                continue
            visited.add(neighbor.name)
            queue.append((neighbor, zones + [neighbor], connections + [connection]))

    raise AlgorithmError(f"No path from {start.name} to {end.name}.")
