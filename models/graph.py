from __future__ import annotations

from typing import TYPE_CHECKING

from utils.exceptions import GraphError

if TYPE_CHECKING:
    from models.connection import Connection
    from models.zone import Zone


class Graph:
    """Static network of zones and connections between them."""

    def __init__(self, zones: dict[str, Zone], start: Zone, end: Zone) -> None:
        self._zones: dict[str, Zone] = zones
        self.start: Zone = start
        self.end: Zone = end

    def get_zone(self, name: str) -> Zone:
        """Return the zone with the given name, or raise if unknown."""
        try:
            return self._zones[name]
        except KeyError:
            raise GraphError(f"Unknown zone '{name}'.") from None

    def zones(self) -> list[Zone]:
        """Return all zones in the graph."""
        return list(self._zones.values())

    def connections(self) -> list[Connection]:
        """Return all unique connections in the graph."""
        seen: set[Connection] = set()
        for zone in self._zones.values():
            for connection in zone.connections:
                seen.add(connection)
        return list(seen)

    def neighbors(self, zone: Zone) -> list[tuple[Zone, Connection]]:
        """Return (neighbor_zone, connection) pairs for a given zone."""
        result: list[tuple[Zone, Connection]] = []
        for connection in zone.connections:
            other = connection.get_other(zone)
            result.append((other, connection))
        return result

    def validate_connectivity(self) -> None:
        """Ensure end is reachable from start, ignoring blocked zones.

        Raises:
            GraphError: if no path exists between start and end.
        """
        if self.start.is_blocked() or self.end.is_blocked():
            raise GraphError("Start or end zone cannot be blocked.")

        visited: set[Zone] = {self.start}
        queue: list[Zone] = [self.start]

        while queue:
            current = queue.pop(0)
            if current is self.end:
                return
            for neighbor, _connection in self.neighbors(current):
                if neighbor.is_blocked() or neighbor in visited:
                    continue
                visited.add(neighbor)
                queue.append(neighbor)

        raise GraphError(
            f"No path exists between start zone '{self.start.name}' "
            f"and end zone '{self.end.name}'."
        )

    def __len__(self) -> int:
        return len(self._zones)

    def __str__(self) -> str:
        return f"Graph({len(self._zones)} zones, {len(self.connections())} connections)"