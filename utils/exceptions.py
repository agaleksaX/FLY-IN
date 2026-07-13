class FlyInError(Exception):
    """Base exception for Fly-in."""


class ParserError(FlyInError):
    """Input parsing error."""


class ValidationError(FlyInError):
    """Input validation error."""


class GraphError(FlyInError):
    """Graph integrity error."""


class SimulationError(FlyInError):
    """Simulation error."""