from __future__ import annotations

from typing import TYPE_CHECKING

from algorithms.scheduler import Scheduler
from models.drone import Drone, DroneState
from models.simulation_config import SimulationConfig
from simulation.turn import Turn
from models.zone import Zone
from models.connection import Connection
from simulation.state import SimulationState
from utils.exceptions import SimulationError


class Engine:
    """Orchestrates the drone simulation."""

    def __init__(self, config: SimulationConfig, scheduler: Scheduler | None = None) -> None:
        self._config = config
        self._scheduler = scheduler or Scheduler(config.graph)
        self._state: SimulationState | None = None

    def run(self) -> list[Turn]:
        """Run the full simulation and return all turns."""
        self._state = self._initialize()
        turns: list[Turn] = []

        while not self._is_finished():
            turn = self._simulate_turn()
            self._apply_turn(turn)
            turns.append(turn)
            self._state.current_turn += 1

        return turns

    def _initialize(self) -> SimulationState:
        """Create initial simulation state."""
        drones: list[Drone] = []
        for i in range(1, self._config.nb_drones + 1):
            drone = Drone(id=i, current_zone=self._config.graph.start)
            self._config.graph.start.add_drone(drone)
            drones.append(drone)

        return SimulationState(
            graph=self._config.graph,
            drones=drones,
            current_turn=0,
            delivered=0,
        )

    def _simulate_turn(self) -> Turn:
        if self._state is None:
            raise SimulationError("Simulation not initialized.")
        return self._scheduler.schedule(self._state)

    def _apply_turn(self, turn: Turn) -> None:
        """Apply a turn's moves to the simulation state."""
        if self._state is None:
            return

        for move in turn.moves:
            drone = move.drone
            destination = move.destination

            if isinstance(destination, Zone):
                if drone.state is DroneState.IN_TRANSIT:
                    source_zone = self._get_transit_source(drone)
                    if source_zone is not None:
                        pass
                    drone.finish_transit(destination)
                else:
                    source_zone = drone.current_zone
                    if source_zone is not None and source_zone is not destination:
                        source_zone.remove_drone(drone)
                    drone.advance(destination)

                if drone not in destination.occupants:
                    destination.add_drone(drone)

                if destination is self._config.graph.end and not drone.is_delivered():
                    drone.deliver()
                    self._state.delivered += 1

            elif isinstance(destination, Connection):
                source_zone = drone.current_zone
                if source_zone is not None and drone in source_zone.occupants:
                    source_zone.remove_drone(drone)
                drone.start_transit(destination, 2)
                destination.enter(drone)

    def _get_transit_source(self, drone: Drone) -> Zone | None:
        """Determine source zone for a drone in transit."""
        if not drone.transit_connection or not drone.path:
            return None
        if drone.path_index < len(drone.path):
            return drone.path[drone.path_index]
        return None

    def _is_finished(self) -> bool:
        if self._state is None:
            return False
        return self._state.delivered >= self._config.nb_drones

    @property
    def state(self) -> SimulationState | None:
        return self._state