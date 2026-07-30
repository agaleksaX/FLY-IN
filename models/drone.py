from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from models.connection import Connection
    from models.zone import Zone


class DroneState(Enum):
    """Possible states for a drone during simulation."""

    WAITING = "waiting"
    IN_TRANSIT = "in_transit"
    DELIVERED = "delivered"


@dataclass(eq=False)
class Drone:
    """Represents a single drone in the simulation."""

    id: int
    current_zone: Zone | None

    path: list[Zone] = field(default_factory=list)
    path_index: int = 0

    state: DroneState = DroneState.WAITING
    transit_connection: Connection | None = None
    transit_turns_remaining: int = 0

    def next_zone(self) -> Zone | None:
        """Return the next zone on the cached path, or None if at the end."""
        if self.path_index + 1 >= len(self.path):
            return None
        return self.path[self.path_index + 1]

    def advance(self, zone: Zone) -> None:
        """Move the drone's path pointer onto an adjacent zone (1 turn)."""
        self.current_zone = zone
        self.path_index += 1

    def start_transit(self, connection: Connection, turns: int) -> None:
        """Begin a multi-turn transit across a restricted connection."""
        self.current_zone = None
        self.state = DroneState.IN_TRANSIT
        self.transit_connection = connection
        self.transit_turns_remaining = turns

    def tick_transit(self) -> None:
        """Advance the transit countdown by one turn."""
        if self.transit_turns_remaining > 0:
            self.transit_turns_remaining -= 1

    def finish_transit(self, zone: Zone) -> None:
        """Complete a multi-turn transit, arriving at the destination zone."""
        self.current_zone = zone
        self.path_index += 1
        self.state = DroneState.WAITING
        self.transit_connection = None
        self.transit_turns_remaining = 0

    def deliver(self) -> None:
        """Mark the drone as delivered at the end zone."""
        self.state = DroneState.DELIVERED

    def is_delivered(self) -> bool:
        """Return True if the drone has reached the end zone."""
        return self.state == DroneState.DELIVERED

    def remaining_path_cost(self) -> int:
        """Calculate the sum of movement costs for the remaining path."""
        if self.path_index >= len(self.path):
            return 0
        return sum(zone.movement_cost() for zone in self.path[self.path_index + 1 :])

    def __eq__(self, other: object) -> bool:
        if not isinstance(other, Drone):
            return NotImplemented
        return self.id == other.id

    def __hash__(self) -> int:
        return hash(self.id)

    def __str__(self) -> str:
        return f"D{self.id}"
