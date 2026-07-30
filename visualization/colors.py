"""ANSI color utilities for terminal output."""

from typing import Final

COLOR_MAP: Final[dict[str, str]] = {
    "red": "\033[91m",
    "green": "\033[92m",
    "yellow": "\033[93m",
    "blue": "\033[94m",
    "magenta": "\033[95m",
    "cyan": "\033[96m",
    "white": "\033[97m",
    "black": "\033[90m",
    "orange": "\033[38;5;208m",
    "purple": "\033[38;5;129m",
    "brown": "\033[38;5;130m",
    "maroon": "\033[38;5;88m",
    "gold": "\033[38;5;220m",
    "darkred": "\033[38;5;124m",
    "violet": "\033[38;5;177m",
    "crimson": "\033[38;5;161m",
    "rainbow": "\033[95m",
    "lime": "\033[38;5;118m",
    "darkgreen": "\033[38;5;28m",
    "gray": "\033[90m",
    "grey": "\033[90m",
}

RESET: Final[str] = "\033[0m"
BOLD: Final[str] = "\033[1m"


def colorize(text: str, color: str | None) -> str:
    """Wrap text in ANSI color codes if color is recognized."""
    if not color:
        return text
    code = COLOR_MAP.get(color.lower(), "")
    if not code:
        return text
    return f"{code}{text}{RESET}"


def print_colored(text: str, color: str | None = None) -> None:
    """Print text with optional color."""
    print(colorize(text, color))
