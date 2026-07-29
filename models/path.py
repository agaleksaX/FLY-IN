from __future__ import annotations

from dataclasses import dataclass, field
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from models.connection import Connection
    from models.zone import Zone


@dataclass
class Path:
    """A sequence of zones and the connetions between them."""
    
    zones: list[Zone] = field(default_factory=list)
    connections: list[Connection] = field(default_factory=list)

    def __post_init__(self) -> None:
        expected = max(len(self.zones) - 1, 0)
        if len(self.connections) != expected:
            raise ValueError(
                f"Path has {len(self.zones)} zones but "
                f"{len(self.connections)} connections (expected {expected})."
            )

    def total_cost(self) -> int:
        """Return the total movement cost, excluding the start zone."""
        return sum(zone.movement_cost() for zone in self.zones[1:])
    
    def priority_count(self) -> int:
        """Return the number of priority zones in the path."""
        from models.zone import ZoneType
        
        return sum(1 for zone in self.zones[1:] if zone.zone_type == ZoneType.PRIORITY)

    def connection_after(self, index: int) -> Connection:
        """Return the connection from zones[index] to zones[index + 1]."""
        return self.connections[index]

    def __len__(self) -> int:
        return len(self.zones)

    def __str__(self) -> str:
        return " -> ".join(zone.name for zone in self.zones)
