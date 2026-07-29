"""ANSI color utilities for terminal output."""

from typing import Final

COLOR_MAP: Final[dict[str, str]] = {
    "red": "[91m",
    "green": "[92m",
    "yellow": "[93m",
    "blue": "[94m",
    "magenta": "[95m",
    "cyan": "[96m",
    "white": "[97m",
    "black": "[90m",
    "orange": "[38;5;208m",
    "purple": "[38;5;129m",
    "brown": "[38;5;130m",
    "maroon": "[38;5;88m",
    "gold": "[38;5;220m",
    "darkred": "[38;5;124m",
    "violet": "[38;5;177m",
    "crimson": "[38;5;161m",
    "rainbow": "[95m",
    "lime": "[38;5;118m",
    "darkgreen": "[38;5;28m",
    "gray": "[90m",
    "grey": "[90m",
}

RESET: Final[str] = "[0m"
BOLD: Final[str] = "[1m"


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
