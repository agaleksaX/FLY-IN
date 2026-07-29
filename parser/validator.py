from __future__ import annotations

from parser.tokenizer import Token, TokenType
from utils.exceptions import ValidationError


class Validator:
    """Performs semantic validation on a sequence of tokens."""

    def validate(self, tokens: list[Token]) -> None:
        """Validate token sequence and raise on errors."""
        self._validate_nb_drones(tokens)
        self._validate_unique_zones(tokens)
        self._validate_connection_references(tokens)

    def _validate_nb_drones(self, tokens: list[Token]) -> None:
        """Ensure exactly one nb_drones definition exists."""
        nb_tokens = [t for t in tokens if t.type is TokenType.NB_DRONES]
        if len(nb_tokens) != 1:
            raise ValidationError(
                f"Expected exactly one nb_drones definition, found {len(nb_tokens)}."
            )
        if len(nb_tokens[0].values) != 1:
            raise ValidationError("nb_drones must have exactly one value.")
        try:
            val = int(nb_tokens[0].values[0])
        except ValueError:
            raise ValidationError("nb_drones must be a positive integer.") from None
        if val <= 0:
            raise ValidationError("nb_drones must be positive.")

    def _validate_unique_zones(self, tokens: list[Token]) -> None:
        """Ensure zone names are unique."""
        seen: set[str] = set()
        for token in tokens:
            if token.type in (TokenType.START_HUB, TokenType.END_HUB, TokenType.HUB):
                if not token.values:
                    raise ValidationError(
                        f"Line {token.line}: Zone definition missing name."
                    )
                name = token.values[0]
                if name in seen:
                    raise ValidationError(
                        f"Line {token.line}: Duplicate zone name '{name}'."
                    )
                seen.add(name)

    def _validate_connection_references(self, tokens: list[Token]) -> None:
        """Ensure connections reference defined zones."""
        zones: set[str] = set()
        for token in tokens:
            if token.type in (TokenType.START_HUB, TokenType.END_HUB, TokenType.HUB):
                zones.add(token.values[0])

        for token in tokens:
            if token.type is TokenType.CONNECTION:
                if len(token.values) != 1 or "-" not in token.values[0]:
                    raise ValidationError(
                        f"Line {token.line}: Invalid connection format."
                    )
                a, b = token.values[0].split("-", 1)
                if a not in zones:
                    raise ValidationError(
                        f"Line {token.line}: Unknown zone '{a}' in connection."
                    )
                if b not in zones:
                    raise ValidationError(
                        f"Line {token.line}: Unknown zone '{b}' in connection."
                    )
