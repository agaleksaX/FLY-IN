from dataclasses import dataclass, field

from models.drone import Drone
from models.graph import Graph


@dataclass(slots=True)
class SimulationState:
    """Current state of an ongoing simulation."""

    graph: Graph
    drones: list[Drone] = field(default_factory=list)
    current_turn: int = 0
    delivered: int = 0
