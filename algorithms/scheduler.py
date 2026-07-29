from __future__ import annotations

from typing import TYPE_CHECKING

from algorithms.path_selector import PathSelector
from models.drone import Drone, DroneState
from models.turn import Move, Turn
from utils.exceptions import AlgorithmError

if TYPE_CHECKING:
    from models.connection import Connection
    from models.graph import Graph
    from models.zone import Zone
    from simulation.state import SimulationState


class Scheduler:
    """Decides drone movements for each simulation turn."""

    def __init__(self, graph: Graph, path_selector: PathSelector | None = None) -> None:
        self._graph = graph
        self._path_selector = path_selector or PathSelector(graph)

    def schedule(self, state: SimulationState) -> Turn:
        """Produce the next Turn based on current state."""
        turn = Turn()

        # First: advance in-transit drones
        for drone in state.drones:
            if drone.state is DroneState.IN_TRANSIT:
                drone.tick_transit()
                if drone.transit_turns_remaining == 0:
                    # Plan arrival
                    destination = self._transit_destination(drone)
                    turn.moves.append(Move(drone=drone, destination=destination))

        # Then: plan movements for waiting drones
        self._assign_paths(state)
        self._plan_moves(state, turn)

        return turn

    def _transit_destination(self, drone: Drone) -> Zone:
        """Determine where a drone in transit will arrive."""
        if not drone.transit_connection:
            raise ValueError("Drone has no transit connection")
        # Source is the zone at path_index
        if drone.path and drone.path_index < len(drone.path):
            source = drone.path[drone.path_index]
            return drone.transit_connection.get_other(source)
        # Fallback
        return drone.transit_connection.zone_b

    def _assign_paths(self, state: SimulationState) -> None:
        """Ensure every waiting drone has a cached path to the end."""
        for drone in state.drones:
            if drone.state is not DroneState.WAITING:
                continue
            if drone.current_zone is None:
                continue
            if not drone.path or drone.path_index >= len(drone.path) - 1:
                try:
                    path = self._path_selector.find_path(
                        drone.current_zone, state.graph.end
                    )
                    drone.path = list(path.zones)
                    drone.path_index = drone.path.index(drone.current_zone)
                except AlgorithmError:
                    pass  # No path — drone will wait

    def _plan_moves(self, state: SimulationState, turn: Turn) -> None:
        """Plan moves for waiting drones, respecting capacities."""
        zone_incoming: dict[Zone, int] = {}
        zone_outgoing: dict[Zone, int] = {}
        connection_usage: dict[Connection, int] = {}

        for zone in state.graph.zones():
            zone_incoming[zone] = 0
            zone_outgoing[zone] = 0

        for conn in state.graph.connections():
            connection_usage[conn] = len(conn.drone_in_transit)

        # Drones already planned to arrive this turn (from transit)
        for move in turn.moves:
            if hasattr(move.destination, "occupants"):
                zone_incoming[move.destination] += 1

        waiting = [
            d
            for d in state.drones
            if d.state is DroneState.WAITING and d.current_zone is not None
        ]
        waiting.sort(key=lambda d: (len(d.path) - d.path_index, d.id))

        for drone in waiting:
            current = drone.current_zone
            if current is state.graph.end:
                continue  # Will be marked delivered by engine

            next_zone = drone.next_zone()
            if next_zone is None:
                continue

            connection = self._find_connection(current, next_zone, state.graph)
            if connection is None:
                continue

            # Check capacities
            is_end = next_zone is state.graph.end
            dest_available = (
                float("inf")
                if is_end
                else (
                    next_zone.max_drones
                    - len(next_zone.occupants)
                    - zone_incoming.get(next_zone, 0)
                    + zone_outgoing.get(next_zone, 0)
                )
            )

            conn_available = connection.max_link_capacity - connection_usage.get(
                connection, 0
            )

            if next_zone.is_blocked():
                continue

            if dest_available > 0 and conn_available > 0:
                if next_zone.movement_cost() == 2:
                    turn.moves.append(Move(drone=drone, destination=connection))
                    connection_usage[connection] += 1
                    zone_outgoing[current] += 1
                else:
                    turn.moves.append(Move(drone=drone, destination=next_zone))
                    zone_incoming[next_zone] += 1
                    zone_outgoing[current] += 1

    def _find_connection(self, zone_a: Zone, zone_b: Zone, graph) -> Connection | None:
        for neighbor, connection in graph.neighbors(zone_a):
            if neighbor is zone_b:
                return connection
        return None
