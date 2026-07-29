from __future__ import annotations

from typing import TYPE_CHECKING

from visualization.colors import colorize, RESET, BOLD

if TYPE_CHECKING:
    from simulation.turn import Turn
    from models.simulation_config import SimulationConfig
    from models.graph import Graph



def print_simulation_header(config: SimulationConfig) -> None:
    """Print a colorful header before simulation starts."""
    print()
    print("=" * 50)
    print(colorize(" FLY-IN DRONE SIMULATION", "cyan"))
    print(f" Drones: {config.nb_drones}")
    print(f" Start:  {config.graph.start.name}")
    print(f" End:    {config.graph.end.name}")
    print("=" * 50)
    print()
    

def print_turn(turn_number: int, turn: Turn, graph: Graph) -> None:
    """Print a single simulation turn with colored output."""
    if not turn.moves:
        print(f"Turn {turn_number:3d}: (no moves)")
        return

    parts: list[str] = []
    for move in turn.moves:
        drone_str = colorize(str(move.drone), "cyan")
        if hasattr(move.destination, "name"):
            zone = move.destination
            color = getattr(zone, "color", None)
            dest_str = colorize(zone.name, color)
        else:
            dest_str = colorize(str(move.destination), "yellow")
        parts.append(f"{drone_str}-{dest_str}")

    joined = " ".join(parts)
    print(f"Turn {turn_number:3d}: {joined}")


def print_simulation_summary(total_turns: int, config: SimulationConfig) -> None:
    """Print final summary after simulation completes."""
    print()
    print("=" * 50)
    print(colorize("  SIMULATION COMPLETE", "green"))
    print(f"  Total turns: {total_turns}")
    print(f"  Drones delivered: {config.nb_drones}/{config.nb_drones}")
    print("=" * 50)
    print()


def print_zone_status(graph: Graph) -> None:
    """Debug helper: print current occupancy of each zone."""
    print("\n--- Zone Status ---")
    for zone in graph.zones():
        occupant_str = ", ".join(str(d) for d in zone.occupants) or "empty"
        color = zone.color or "white"
        print(
            f"  {colorize(zone.name, color):20s} [{len(zone.occupants)}/{zone.max_drones}] {occupant_str}"
        )
    print()