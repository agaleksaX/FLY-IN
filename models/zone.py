from dataclasses import dataclass, field
from enum import Enum
from models.connection import Connection
from models.drone import Drone


class ZoneType(Enum):
    NORMAL = "normal"
    BLOCKED = "blocked"
    PRIORITY = "priority"
    RESTRICTED = "restricted"


@dataclass
class Zone:
    name: str
    x: int
    y: int
    zone_type: ZoneType = ZoneType.NORMAL
    color: str | None = None
    max_drones: int = 1

    connections: list[Connection] = field(default_factory=list)
    occupants: list[Drone] = field(default_factory=list)

    def add_connection(self, connection: Connection) -> None:
        """Add a connection to this zone."""
        if connection not in self.connections:
            self.connections.append(connection)

    def add_drone(self, drone: Drone) -> None:
        """Place a drone into the zone."""
        if self.is_full():
            raise ValueError(f"Zone '{self.name}' is full.")
        self.occupants.append(drone)

    def remove_drone(self, drone: Drone) -> None:
        """Remove a drone from the zone."""
        if drone not in self.occupants:
            raise ValueError("")
        self.occupants.remove(drone)

    def is_full(self) -> bool:
        """Return True if the zone has reached its capacity."""
        return len(self.occupants) >= self.max_drones

    def is_blocked(self) -> bool:
        """Return True if the zone cannot be entered."""
        return self.zone_type == ZoneType.BLOCKED

    def movement_cost(self) -> int:
        """Return the movement cost of entering this zone."""
        if self.zone_type == ZoneType.NORMAL or self.zone_type == ZoneType.PRIORITY:
            return 1
        elif self.zone_type == ZoneType.RESTRICTED:
            return 2
        elif self.zone_type == ZoneType.BLOCKED:
            raise ValueError("Blocked zones cannot be entered.")

    def degree(self) -> int:
        """Return the number of connected edges."""
        return len(self.connections)

    def __str__(self) -> str:
        return self.name
