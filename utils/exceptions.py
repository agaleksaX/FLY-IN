class FlyInError(Exception):
    """Base class for all project-specific exceptions."""


class ParserError(FlyInError):
    """Raised when parsing the input file fails."""


class ValidationError(FlyInError):
    """Raised when parsed data is semantically invalid."""


class GraphError(FlyInError):
    """Raised when graph operations fail."""


class AlgorithmError(FlyInError):
    """Raised when a pathfinding or scheduling algorithm fails."""


class SimulationError(FlyInError):
    """Raised when simulation rules are violated."""
