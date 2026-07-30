from __future__ import annotations

from typing import TYPE_CHECKING

from algorithms.path_selector import PathSelector
from models.drone import Drone, DroneState
from models.zone import Zone
from models.path import Path
from simulation.turn import Move, Turn
from utils.exceptions import AlgorithmError

if TYPE_CHECKING:
    from models.connection import Connection
    from models.graph import Graph
    from simulation.state import SimulationState


class Scheduler:
    """Decides drone movements for each simulation turn."""

    def __init__(
        self,
        graph: Graph,
        path_selector: PathSelector | None = None,
    ) -> None:
        self._graph = graph
        self._path_selector = path_selector or PathSelector(graph)
        self._zone_reserved: dict[Zone, int] = {}
        self._stuck_turns: dict[int, int] = {}

    def schedule(self, state: SimulationState) -> Turn:
        """Produce the next Turn based on current state."""
        turn = Turn()
        arriving: list[tuple[Drone, Zone]] = []

        for drone in state.drones:
            if drone.state is DroneState.IN_TRANSIT:
                drone.tick_transit()
                if drone.transit_turns_remaining == 0:
                    destination = self._transit_destination(drone)
                    arriving.append((drone, destination))

        zone_incoming: dict[Zone, int] = {}
        for zone in state.graph.zones():
            zone_incoming[zone] = 0

        for drone, destination in arriving:
            zone_incoming[destination] += 1
            turn.moves.append(Move(drone, destination))

        self._assign_paths(state)
        self._plan_moves(state, turn, zone_incoming)
        self._zone_reserved.clear()

        return turn

    def _transit_destination(self, drone: Drone) -> Zone:
        """Determine where a drone in transit will arrive."""
        if not drone.transit_connection:
            raise ValueError("Drone has no transit connection")
        if drone.path and drone.path_index < len(drone.path):
            source = drone.path[drone.path_index]
            return drone.transit_connection.get_other(source)
        return drone.transit_connection.zone_b

    def _count_outgoing(self, zone: Zone, state: SimulationState) -> int:
        """Count drones currently in zone that are waiting and have a next zone."""
        count = 0
        for drone in zone.occupants:
            if drone.state is DroneState.WAITING and drone.next_zone() is not None:
                count += 1
        return count

    def _assign_paths(self, state: SimulationState) -> None:
        """Ensure every waiting drone has a path to the end."""
        for drone in state.drones:
            if drone.state is not DroneState.WAITING:
                continue
            if drone.current_zone is None:
                continue
            if drone.is_delivered():
                continue
            if drone.current_zone is state.graph.end:
                continue

            needs_new_path = (
                not drone.path
                or drone.path_index >= len(drone.path) - 1
                or self._stuck_turns.get(drone.id, 0) > 2
            )

            if needs_new_path:
                try:
                    avoid: set[str] = set()
                    if self._stuck_turns.get(drone.id, 0) > 2 and drone.next_zone():
                        avoid.add(drone.next_zone().name)

                    path = self._find_path_avoiding(
                        drone.current_zone, state.graph.end, avoid
                    )
                    drone.path = list(path.zones)
                    drone.path_index = drone.path.index(drone.current_zone)
                    self._stuck_turns[drone.id] = 0
                except AlgorithmError:
                    pass
            else:
                if drone.path_index < len(drone.path):
                    if drone.path[drone.path_index] is not drone.current_zone:
                        try:
                            drone.path_index = drone.path.index(drone.current_zone)
                        except ValueError:
                            try:
                                path = self._path_selector.find_path(
                                    drone.current_zone, state.graph.end
                                )
                                drone.path = list(path.zones)
                                drone.path_index = 0
                            except AlgorithmError:
                                pass

    def _find_path_avoiding(self, start: Zone, end: Zone, avoid: set[str]) -> Path:
        """Find path avoiding certain zone names."""
        from algorithms.dijkstra import dijkstra
        from algorithms.bfs import bfs
        from utils.exceptions import AlgorithmError

        try:
            return dijkstra(self._graph, start, end)
        except AlgorithmError:
            pass

        try:
            return bfs(self._graph, start, end)
        except AlgorithmError:
            pass

        raise AlgorithmError(f"No path from {start.name} to {end.name}")

    def _plan_moves(
        self,
        state: SimulationState,
        turn: Turn,
        zone_incoming: dict[Zone, int],
    ) -> None:
        """Plan moves for waiting drones, respecting capacities."""
        zone_outgoing: dict[Zone, int] = {}
        connection_usage: dict[Connection, int] = {}
        zone_reserved: dict[Zone, int] = {}

        for zone in state.graph.zones():
            zone_outgoing[zone] = 0
            zone_reserved[zone] = 0

        for conn in state.graph.connections():
            connection_usage[conn] = len(conn.drone_in_transit)

        waiting = [
            d
            for d in state.drones
            if d.state is DroneState.WAITING
            and d.current_zone is not None
            and not d.is_delivered()
            and d.current_zone is not state.graph.end
        ]

        waiting.sort(key=lambda d: (d.remaining_path_cost(), d.id))

        moved_this_turn: set[int] = set()

        for drone in waiting:
            current = drone.current_zone
            if current is None:
                continue

            next_zone = drone.next_zone()
            if next_zone is None:
                self._stuck_turns[drone.id] = self._stuck_turns.get(drone.id, 0) + 1
                continue

            connection = self._find_connection(current, next_zone, state.graph)
            if connection is None:
                self._stuck_turns[drone.id] = self._stuck_turns.get(drone.id, 0) + 1
                continue

            if next_zone.is_blocked():
                self._stuck_turns[drone.id] = self._stuck_turns.get(drone.id, 0) + 1
                continue

            is_end = next_zone is state.graph.end

            if is_end or next_zone.is_start:
                dest_available = float("inf")
            else:
                if next_zone.movement_cost() == 2:
                    future_occ = (
                        len(next_zone.occupants)
                        - zone_outgoing.get(next_zone, 0)
                        + zone_incoming.get(next_zone, 0)
                        + zone_reserved.get(next_zone, 0)
                    )
                    dest_available = next_zone.max_drones - future_occ
                else:
                    cur_occ = (
                        len(next_zone.occupants)
                        - zone_outgoing.get(next_zone, 0)
                        + zone_incoming.get(next_zone, 0)
                    )
                    dest_available = next_zone.max_drones - cur_occ

            conn_available = connection.max_link_capacity - connection_usage.get(
                connection, 0
            )

            if dest_available <= 0 or conn_available <= 0:
                self._stuck_turns[drone.id] = self._stuck_turns.get(drone.id, 0) + 1
                continue

            if next_zone.movement_cost() == 2:
                turn.moves.append(Move(drone=drone, destination=connection))
                connection_usage[connection] += 1
                zone_outgoing[current] += 1
                zone_reserved[next_zone] += 1
            else:
                turn.moves.append(Move(drone=drone, destination=next_zone))
                zone_incoming[next_zone] += 1
                zone_outgoing[current] += 1

            moved_this_turn.add(drone.id)
            self._stuck_turns[drone.id] = 0

        for drone in waiting:
            if drone.id not in moved_this_turn:
                self._stuck_turns[drone.id] = self._stuck_turns.get(drone.id, 0) + 1

    def _find_connection(
        self, zone_a: Zone, zone_b: Zone, graph: Graph
    ) -> Connection | None:
        """Find the connection linking two adjacent zones."""
        for neighbor, connection in graph.neighbors(zone_a):
            if neighbor is zone_b:
                return connection
        return None
