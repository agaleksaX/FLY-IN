from __future__ import annotations

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

    def __init__(
        self,
        config: SimulationConfig,
        scheduler: Scheduler | None = None,
    ) -> None:
        self._config = config
        self._scheduler = scheduler or Scheduler(config.graph)
        self._state: SimulationState | None = None

    def run(self) -> list[Turn]:
        """Run the full simulation and return all turns."""
        self._state = self._initialize()
        turns: list[Turn] = []
        max_turns = 10_000

        while not self._is_finished():
            if (
                self._state is not None
                and self._state.current_turn > max_turns
            ):
                raise SimulationError(
                    f"Simulation exceeded {max_turns}"
                    " turns — possible deadlock."
                )
            turn = self._simulate_turn()
            self._apply_turn(turn)
            turns.append(turn)
            if self._state is not None:
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
                    if drone.transit_connection is not None:
                        if drone.transit_connection.drone_in_transit:
                            drone.transit_connection.leave(drone)
                    drone.finish_transit(destination)
                else:
                    source_zone = drone.current_zone
                    if (
                        source_zone is not None
                        and source_zone is not destination
                        and drone in source_zone.occupants
                    ):
                        source_zone.remove_drone(drone)
                    drone.advance(destination)

                try:
                    if drone not in destination.occupants:
                        destination.add_drone(drone)
                except ValueError as exc:
                    raise SimulationError(
                        f"Turn {self._state.current_turn}: Drone {drone.id} "
                        f"cannot enter zone '{destination.name}' — {exc}"
                    ) from exc

                if (
                    destination is self._config.graph.end
                    and not drone.is_delivered()
                ):
                    drone.deliver()
                    self._state.delivered += 1

            elif isinstance(destination, Connection):
                source_zone = drone.current_zone
                if source_zone is not None and drone in source_zone.occupants:
                    source_zone.remove_drone(drone)
                drone.start_transit(destination, 1)
                destination.enter(drone)

    def _is_finished(self) -> bool:
        if self._state is None:
            return False
        return self._state.delivered >= self._config.nb_drones

    @property
    def state(self) -> SimulationState | None:
        return self._state
