from dataclasses import dataclass, field
from typing import TYPE_CHECKING

from models.zone import Zone
from models.drone import Drone

@dataclass
class Connection:
    zone_a: Zone
    zone_b: Zone
    max_link_capacity: int = 1
    
    drone_in_transit: list[Drone] = field(default_factory=list, repr=False)
    
    def get_other(self, zone: Zone) -> Zone:
        """Return the zone on the other end of this connection."""
        if zone == self.zone_a:
            return self.zone_b
        elif zone == self.zone_b:
            return self.zone_a
        else:
            raise ValueError(f"Zone '{zone.name}' is not part of connection '{self}'.")
    
    def connects(self, zone: Zone) -> bool:
        """Check if this connection connects to the given zone."""
        return zone == self.zone_a or zone == self.zone_b
    
    def is_full(self) -> bool:
        """Return True if connection has reached its transit capacity."""
        return len(self.drone_in_transit) >= self.max_link_capacity
    
    def enter(self, drone: Drone) -> None:
        """Register a drone as correctly traversing this connection."""
        if self.is_full():
            raise ValueError(f"Connection '{self}' is at full capacity.")
        self.drone_in_transit.append(drone)

    def leave(self, drone: Drone) -> None:
        """Remove a drone that has finished traversing this connection."""
        if drone not in self.drone_in_transit:
            raise ValueError(f"Drone '{drone.id}' is not transit on connection '{self}'.")
        self.drone_in_transit.remove(drone)
        
    def _key(self) -> frozenset[str]:
        return frozenset({self.zone_a.name, self.zone_b.name})
    
    def __eq__(self, other: object) -> bool:
        if not isinstance(other, Connection):
            return NotImplemented
        return self._key() == other._key()
    
    def __hash__(self) -> int:
        return hash(self._key())
    
    def __str__(self) -> str:
        return f"{self.zone_a.name}-{self.zone_b.name}"