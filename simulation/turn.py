from dataclasses import dataclass, field
from models.drone import Drone
from models.zone import Zone
from models.connection import Connection

@dataclass(slots=True)
class Move:
    """A single drone movement performed during one simulation turn."""
    
    drone: Drone
    destination: Zone | Connection

@dataclass(slots=True)
class Turn:
    """All drone movements executed during a simulation turn."""
    
    moves: list[Move] = field(default_factory=list)