from __future__ import annotations

import heapq
from typing import TYPE_CHECKING

from models.path import Path
from utils.exceptions import AlgorithmError

if TYPE_CHECKING:
    from models.graph import Graph
    from models.zone import Zone
    from models.connection import Connection


def dijkstra(graph: Graph, start: Zone, end: Zone) -> Path:
    """Find shortest path from start to end using Dijkstra's algorithm."""
    counter = 0
    pq: list[
        tuple[float, int, int, int, str, list[Zone], list[Connection]]
        ] = [
        (0.0, 0, 0, counter, start.name, [start], [])
    ]
    visited: set[str] = set()

    while pq:
        (
            cost,
            neg_prio,
            steps,
            _cnt,
            current_name,
            zones,
            connections,
            ) = heapq.heappop(pq)

        if current_name in visited:
            continue
        visited.add(current_name)

        current = graph.get_zone(current_name)
        if current is end:
            return Path(zones, connections)

        for neighbor, connection in graph.neighbors(current):
            if neighbor.is_blocked():
                continue
            if neighbor.name in visited:
                continue

            move_cost = neighbor.movement_cost()
            if neighbor.zone_type.value == "priority":
                effective_cost = cost + 0.99
                new_neg_prio = neg_prio - 1
            else:
                effective_cost = cost + float(move_cost)
                new_neg_prio = neg_prio

            counter += 1
            new_zones = zones + [neighbor]
            new_connections = connections + [connection]
            heapq.heappush(
                pq,
                (
                    effective_cost,
                    new_neg_prio,
                    steps + 1,
                    counter,
                    neighbor.name,
                    new_zones,
                    new_connections,
                ),
            )

    raise AlgorithmError(f"No path from {start.name} to {end.name}.")
