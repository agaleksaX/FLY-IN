from dataclasses import dataclass, field
from models.drone import Drone
from models.graph import Graph

@dataclass(slots=True)
class SimulationState:
    graph: Graph
    drones: list[Drone] = field(default_factory=list)
    
    current_turn: int = 0
    ddelivered: int = 0