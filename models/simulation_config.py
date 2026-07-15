from dataclasses import dataclass

from models.graph import Graph


@dataclass(slots=True)
class SimulationConfig:
    """Configuration required to start a simulation."""

    graph: Graph
    nb_drones: int