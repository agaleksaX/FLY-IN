from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from models.connection import Connection
    from models.drone import Drone


class ZoneType(Enum):
    """Supported zone types with their movment characteristics."""
    
    NORMAL = "normal"
    BLOCKED = "blocked"
    PRIORITY = "priority"
    RESTRICTED = "restricted"


@dataclass(eq=False)
class Zone:
    """A node inn the drone navigation graph."""
    
    name: str
    x: int
    y: int
    zone_type: ZoneType = ZoneType.NORMAL
    color: str | None = None
    max_drones: int = 1
    is_start: bool = False
    is_end: bool = False

    connections: list[Connection] = field(default_factory=list)
    occupants: list[Drone] = field(default_factory=list)

    def add_connection(self, connection: Connection) -> None:
        """Add a connection to this zone."""
        if connection not in self.connections:
            self.connections.append(connection)

    def add_drone(self, drone: Drone) -> None:
        """Place a drone into the zone."""
        if drone in self.occupants:
            return
        if self.is_full():
            raise ValueError(f"Zone '{self.name}' is full.")
        self.occupants.append(drone)

    def remove_drone(self, drone: Drone) -> None:
        """Remove a drone from the zone."""
        if drone not in self.occupants:
            raise ValueError(f"Drone {drone.id} is not in zone '{self.name}'.")
        self.occupants.remove(drone)

    def is_full(self) -> bool:
        """Return True if the zone has reached its capacity."""
        if self.is_start or self.is_end:
            return False
        return len(self.occupants) >= self.max_drones

    def is_blocked(self) -> bool:
        """Return True if the zone cannot be entered."""
        return self.zone_type == ZoneType.BLOCKED

    def movement_cost(self) -> int:
        """Return the movement cost of entering this zone."""
        if self.zone_type in (ZoneType.NORMAL, ZoneType.PRIORITY):
            return 1
        if self.zone_type == ZoneType.RESTRICTED:
            return 2
        raise ValueError("Blocked zones cannot be entered.")

    def degree(self) -> int:
        """Return the number of connected edges."""
        return len(self.connections)

    def __eq__(self, other: object) -> bool:
        if not isinstance(other, Zone):
            return NotImplemented
        return self.name == other.name

    def __hash__(self) -> int:
        return hash(self.name)

    def __str__(self) -> str:
        return self.name
