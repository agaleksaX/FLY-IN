from __future__ import annotations

from parser.tokenizer import Token, TokenType
from models.graph import Graph
from models.simulation_config import SimulationConfig
from models.zone import Zone, ZoneType
from utils.exceptions import ParserError
from models.connection import Connection


class Parser:
    """Build a Graph from tokens."""

    def __init__(self) -> None:
        self._zones: dict[str, Zone] = {}
        self._connections: list[Token] = []
        self._start: Zone | None = None
        self._end: Zone | None = None
        self._nb_drones: int = 0

    def parse(self, tokens: list[Token]) -> SimulationConfig:
        """Build a graph from tokens."""
        for token in tokens:
            if token.type is TokenType.HUB:
                self._parse_zone(token)
            elif token.type is TokenType.CONNECTION:
                self._parse_connection(token)
            elif token.type is TokenType.START_HUB:
                self._parse_start(token)
            elif token.type is TokenType.END_HUB:
                self._parse_end(token)
            elif token.type is TokenType.NB_DRONES:
                self._parse_nb_drones(token)
            else:
                raise ParserError(f"Unknown token type '{token.type}'.")

        self._build_connections()

        if self._start is None:
            raise ParserError("Start hub is missing.")
        if self._end is None:
            raise ParserError("End hub is missing.")
        if self._nb_drones <= 0:
            raise ParserError("Number of drones is missing or invalid.")

        graph = Graph(zones=self._zones, start=self._start, end=self._end)
        graph.validate_connectivity()

        return SimulationConfig(graph=graph, nb_drones=self._nb_drones)

    def _create_zone(
        self, token: Token, is_start: bool = False, is_end: bool = False
    ) -> Zone:
        """Create a Zone from a token."""
        if len(token.values) != 3:
            raise ParserError(f"Line {token.line}: Invalid zone definition.")

        try:
            x = int(token.values[1])
            y = int(token.values[2])
        except ValueError:
            raise ParserError(
                f"Line {token.line}: Zone coordinates must be integers."
            ) from None

        zone_type_str = token.metadata.get("zone", "normal")
        try:
            zone_type = ZoneType(zone_type_str)
        except ValueError:
            raise ParserError(
                f"Line {token.line}: Unknown zone type '{zone_type_str}'."
            ) from None

        try:
            max_drones = int(token.metadata.get("max_drones", "1"))
        except ValueError:
            raise ParserError(
                f"Line {token.line}: Invalid max_drones value."
                ) from None

        if is_start or is_end:
            max_drones = 999_999

        return Zone(
            name=token.values[0],
            x=x,
            y=y,
            zone_type=zone_type,
            color=token.metadata.get("color"),
            max_drones=max_drones,
            is_start=is_start,
            is_end=is_end,
        )

    def _parse_zone(self, token: Token) -> None:
        """Parse a normal zone."""
        zone = self._create_zone(token)
        if zone.name in self._zones:
            raise ParserError(
                f"Line {token.line}: "
                f"Duplicate zone '{zone.name}'."
            )
        self._zones[zone.name] = zone

    def _parse_start(self, token: Token) -> None:
        """Parse the start hub."""
        if self._start is not None:
            raise ParserError(
                f"Line {token.line}: "
                "Multiple start hubs defined."
            )
        zone = self._create_zone(token, is_start=True)
        if zone.name in self._zones:
            raise ParserError(
                f"Line {token.line}: "
                f"Duplicate zone '{zone.name}'."
            )
        self._zones[zone.name] = zone
        self._start = zone

    def _parse_end(self, token: Token) -> None:
        """Parse the end hub."""
        if self._end is not None:
            raise ParserError(f"Line {token.line}: Multiple end hubs defined.")
        zone = self._create_zone(token, is_end=True)
        if zone.name in self._zones:
            raise ParserError(
                f"Line {token.line}: "
                f"Duplicate zone '{zone.name}'."
            )
        self._zones[zone.name] = zone
        self._end = zone

    def _parse_connection(self, token: Token) -> None:
        """Store a connection for later processing."""
        if len(token.values) != 1:
            raise ParserError(
                f"Line {token.line}: "
                "Invalid connection definition."
            )
        if "-" not in token.values[0]:
            raise ParserError(f"Line {token.line}: Invalid connection format.")
        self._connections.append(token)

    def _parse_nb_drones(self, token: Token) -> None:
        """Parse the number of drones."""
        if self._nb_drones != 0:
            raise ParserError(
                f"Line {token.line}: "
                "Duplicate nb_drones definition."
            )
        if len(token.values) != 1:
            raise ParserError(
                f"Line {token.line}: "
                "Invalid nb_drones definition."
            )
        try:
            nb_drones = int(token.values[0])
        except ValueError:
            raise ParserError(
                f"Line {token.line}: Number of drones must be an integer."
            ) from None
        if nb_drones <= 0:
            raise ParserError(
                f"Line {token.line}: "
                "Number of drones must be positive."
            )
        self._nb_drones = nb_drones

    def _build_connections(self) -> None:
        """Create Connection objects between parsed zones."""
        created: set[Connection] = set()

        for token in self._connections:
            zone1_name, zone2_name = token.values[0].split("-", 1)

            if zone1_name not in self._zones:
                raise ParserError(
                    f"Line {token.line}: "
                    f"Unknown zone '{zone1_name}'."
                )
            if zone2_name not in self._zones:
                raise ParserError(
                    f"Line {token.line}: "
                    f"Unknown zone '{zone2_name}'."
                )

            try:
                max_capacity = int(
                    token.metadata.get("max_link_capacity", "1")
                )
            except ValueError:
                raise ParserError(
                    f"Line {token.line}: Invalid max_link_capacity."
                ) from None

            if max_capacity <= 0:
                raise ParserError(
                    f"Line {token.line}: max_link_capacity must be positive."
                )

            zone1 = self._zones[zone1_name]
            zone2 = self._zones[zone2_name]

            connection = Connection(
                zone_a=zone1,
                zone_b=zone2,
                max_link_capacity=max_capacity,
            )

            if connection in created:
                raise ParserError(
                    f"Line {token.line}: Duplicate connection '{connection}'."
                )

            created.add(connection)
            zone1.add_connection(connection)
            zone2.add_connection(connection)
