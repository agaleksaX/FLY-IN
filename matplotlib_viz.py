from __future__ import annotations

from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from models.graph import Graph
    from models.zone import Zone
    from models.drone import Drone
    from simulation.turn import Turn


_COLOR_MAP: dict[str, str] = {
    "green": "#2ecc71", "red": "#e74c3c", "blue": "#3498db",
    "yellow": "#f1c40f", "orange": "#e67e22", "purple": "#9b59b6",
    "cyan": "#1abc9c", "magenta": "#ff00ff", "brown": "#8b4513",
    "maroon": "#800000", "gold": "#ffd700", "darkred": "#8b0000",
    "violet": "#ee82ee", "crimson": "#dc143c", "rainbow": "#ff69b4",
    "lime": "#32cd32", "black": "#2c3e50", "gray": "#7f8c8d",
    "grey": "#7f8c8d", "white": "#ecf0f1",
}


def _to_mpl_color(color: str | None, default: str = "#95a5a6") -> str:
    if not color:
        return default
    return _COLOR_MAP.get(color.lower(), default)


def _compute_figsize(graph: Graph) -> tuple[float, float]:
    zones = graph.zones()
    if not zones:
        return (10, 8)
    xs = [z.x for z in zones]
    ys = [z.y for z in zones]
    x_span = max(xs) - min(xs)
    y_span = max(ys) - min(ys)
    width = max(10, x_span * 0.9 + 4)
    height = max(6, y_span * 1.1 + 3)
    return (width, height)


def _compute_marker_size(graph: Graph) -> int:
    n = len(graph.zones())
    if n > 30:
        return 250
    if n > 15:
        return 450
    return 700


def _compute_fontsize(graph: Graph) -> int:
    n = len(graph.zones())
    if n > 30:
        return 6
    if n > 15:
        return 7
    return 9


def _draw_static_background(ax, graph: Graph) -> None:
    """Draw zones and connections on the given axes."""
    marker_size = _compute_marker_size(graph)
    fontsize = _compute_fontsize(graph)

    # Connections
    drawn: set[frozenset[str]] = set()
    for zone in graph.zones():
        for neighbor, connection in graph.neighbors(zone):
            key = frozenset({zone.name, neighbor.name})
            if key in drawn:
                continue
            drawn.add(key)
            ax.plot(
                [zone.x, neighbor.x], [zone.y, neighbor.y],
                "k-", linewidth=1.2, alpha=0.45, zorder=1,
            )
            if connection.max_link_capacity != 1:
                mid_x = (zone.x + neighbor.x) / 2
                mid_y = (zone.y + neighbor.y) / 2
                ax.text(
                    mid_x, mid_y,
                    f"c={connection.max_link_capacity}",
                    fontsize=max(5, fontsize - 2),
                    color="#7f8c8d", ha="center", va="center",
                    bbox=dict(boxstyle="round,pad=0.15", facecolor="white", alpha=0.7),
                    zorder=2,
                )

    # Zones
    for zone in graph.zones():
        color = _to_mpl_color(zone.color)
        shape = "s" if zone.is_start else ("*" if zone.is_end else "o")
        size = marker_size * (1.4 if zone.is_start or zone.is_end else 1.0)

        ax.scatter(
            zone.x, zone.y,
            c=color, marker=shape, s=size,
            edgecolors="black", linewidths=1.5, zorder=3,
        )

        label = zone.name
        if zone.max_drones != 1 and not zone.is_start and not zone.is_end:
            label += f" [{zone.max_drones}]"
        if zone.zone_type.value == "restricted":
            label += " (R)"
        elif zone.zone_type.value == "priority":
            label += " (P)"

        offset = -0.4 if len(graph.zones()) < 20 else -0.28
        ax.text(
            zone.x, zone.y + offset,
            label,
            fontsize=fontsize,
            ha="center", va="top",
            fontweight="bold" if zone.is_start or zone.is_end else "normal",
            bbox=dict(
                boxstyle="round,pad=0.25",
                facecolor="white",
                alpha=0.9,
                edgecolor="none",
            ),
            zorder=4,
        )

    ax.set_aspect("equal")
    ax.grid(True, alpha=0.25, linestyle="--", linewidth=0.5)
    ax.margins(0.12)

    # Legend
    from matplotlib.lines import Line2D
    legend_elements = [
        Line2D([0], [0], marker="s", color="w", markerfacecolor="#2ecc71",
               markersize=10, label="Start", markeredgecolor="black"),
        Line2D([0], [0], marker="*", color="w", markerfacecolor="#e74c3c",
               markersize=12, label="End", markeredgecolor="black"),
        Line2D([0], [0], marker="o", color="w", markerfacecolor="#95a5a6",
               markersize=8, label="Zone", markeredgecolor="black"),
    ]
    ax.legend(handles=legend_elements, loc="upper right", fontsize=9, framealpha=0.9)


def draw_graph(graph: Graph, title: str = "Fly-In Map") -> None:
    """Draw the static graph layout using matplotlib."""
    import matplotlib.pyplot as plt

    figsize = _compute_figsize(graph)
    fig, ax = plt.subplots(figsize=figsize)
    _draw_static_background(ax, graph)
    ax.set_title(title, fontsize=14, fontweight="bold", pad=15)
    ax.set_xlabel("X", fontsize=10)
    ax.set_ylabel("Y", fontsize=10)
    plt.tight_layout(pad=2.0)
    plt.show()


def animate_simulation(
    graph: Graph,
    turns: list["Turn"],
    config: "SimulationConfig",
    subframes: int = 10,
) -> None:
    """Animate the simulation with smooth drone movement between zones.

    Args:
        subframes: Number of interpolation steps per turn (higher = smoother).
    """
    import numpy as np
    import matplotlib.pyplot as plt
    from matplotlib.animation import FuncAnimation

    figsize = _compute_figsize(graph)
    fig, ax = plt.subplots(figsize=figsize)
    _draw_static_background(ax, graph)

    ax.set_xlabel("X", fontsize=10)
    ax.set_ylabel("Y", fontsize=10)

    # Drone markers (dynamic) - initialize with empty data but correct shape
    drone_scatter = ax.scatter(
        [], [], c="black", marker="^", s=180,
        edgecolors="white", linewidths=0.8, zorder=5,
    )
    drone_labels: list = []

    # Build per-drone position timeline
    drone_positions: dict[int, tuple[float, float]] = {}
    for i in range(1, config.nb_drones + 1):
        drone_positions[i] = (config.graph.start.x, config.graph.start.y)

    # Timeline: list of (turn_number, frame_positions dict)
    timeline: list[dict[int, tuple[float, float]]] = []
    # Frame 0: initial positions
    timeline.append({k: v for k, v in drone_positions.items()})

    for turn_idx, turn in enumerate(turns):
        # Determine target position for each drone this turn
        targets: dict[int, tuple[float, float]] = {}
        for drone_id, pos in drone_positions.items():
            targets[drone_id] = pos  # default: stay

        for move in turn.moves:
            drone = move.drone
            dest = move.destination
            if hasattr(dest, "x") and hasattr(dest, "y"):
                targets[drone.id] = (dest.x, dest.y)
            elif hasattr(dest, "zone_a"):
                # In transit — place midway on the connection
                mid_x = (dest.zone_a.x + dest.zone_b.x) / 2
                mid_y = (dest.zone_a.y + dest.zone_b.y) / 2
                targets[drone.id] = (mid_x, mid_y)

        # Generate subframes with linear interpolation
        for step in range(1, subframes + 1):
            t = step / subframes
            frame_pos: dict[int, tuple[float, float]] = {}
            for drone_id in drone_positions:
                x0, y0 = drone_positions[drone_id]
                x1, y1 = targets[drone_id]
                frame_pos[drone_id] = (x0 + (x1 - x0) * t, y0 + (y1 - y0) * t)
            timeline.append(frame_pos)

        # Update positions for next turn
        drone_positions = {k: v for k, v in targets.items()}

    def init():
        drone_scatter.set_offsets(np.empty((0, 2)))
        for txt in drone_labels:
            txt.remove()
        drone_labels.clear()
        return (drone_scatter,)

    def update(frame_idx: int):
        positions = timeline[frame_idx]
        
        # Update scatter positions - MUST be numpy array shape (N, 2)
        if positions:
            pos_array = np.array(list(positions.values()))
            drone_scatter.set_offsets(pos_array)
        else:
            drone_scatter.set_offsets(np.empty((0, 2)))

        # Clear old labels
        for txt in drone_labels:
            txt.remove()
        drone_labels.clear()

        # Add new labels
        for drone_id, (x, y) in positions.items():
            txt = ax.text(
                x + 0.15, y + 0.15,
                f"D{drone_id}",
                fontsize=8,
                color="black",
                fontweight="bold",
                zorder=6,
                bbox=dict(boxstyle="round,pad=0.15", facecolor="white", 
                         alpha=0.8, edgecolor="none"),
            )
            drone_labels.append(txt)

        # Calculate which turn we are in
        turn_display = min(frame_idx // subframes, len(turns))
        delivered = sum(
            1 for d in config.graph.end.occupants if d.is_delivered()
        )
        ax.set_title(
            f"Turn {turn_display}/{len(turns)}  |  "
            f"Delivered: {delivered}/{config.nb_drones}",
            fontsize=12, fontweight="bold",
        )
        
        # Force redraw
        fig.canvas.draw_idle()
        
        return (drone_scatter,)

    anim = FuncAnimation(
        fig, update,
        frames=len(timeline),
        init_func=init,
        interval=200,  # 200ms per subframe
        repeat=True,
        repeat_delay=2000,
        blit=False,
    )

    plt.tight_layout(pad=2.0)
    plt.show()


def draw_turn_snapshot(
    graph: Graph,
    turn: "Turn",
    turn_number: int,
    config: "SimulationConfig",
) -> None:
    """Draw a single turn snapshot showing drone positions."""
    import matplotlib.pyplot as plt

    figsize = _compute_figsize(graph)
    fig, ax = plt.subplots(figsize=figsize)
    _draw_static_background(ax, graph)

    # Draw drones at their destination positions for this turn
    for move in turn.moves:
        drone = move.drone
        dest = move.destination
        if hasattr(dest, "x") and hasattr(dest, "y"):
            x, y = dest.x, dest.y
        elif hasattr(dest, "zone_a"):
            x = (dest.zone_a.x + dest.zone_b.x) / 2
            y = (dest.zone_a.y + dest.zone_b.y) / 2
        else:
            continue

        ax.scatter(x, y, c="black", marker="^", s=150,
                   edgecolors="white", linewidths=0.8, zorder=5)
        ax.text(
            x + 0.15, y + 0.15,
            str(drone),
            fontsize=8,
            color="black", fontweight="bold", zorder=6,
            bbox=dict(boxstyle="round,pad=0.15", facecolor="white",
                     alpha=0.8, edgecolor="none"),
        )

    delivered = sum(1 for d in config.graph.end.occupants if d.is_delivered())
    ax.set_title(
        f"Turn {turn_number}  |  Delivered: {delivered}/{config.nb_drones}",
        fontsize=12, fontweight="bold",
    )
    plt.tight_layout(pad=2.0)
    plt.show()