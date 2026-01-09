"""Text component - Display plain text."""

from dataclasses import dataclass
from typing import Any

from .base import UiBlock


@dataclass
class Text(UiBlock):
    """Display plain text."""

    content: str

    def __post_init__(self):
        """Initialize parent class after dataclass fields."""
        UiBlock.__init__(self)

    def to_dict(self) -> dict:
        return {"type": "text", "content": self.content}

    def build_cli(self, ctx) -> Any:
        """Build Text for CLI (returns Rich Text).

        Args:
            ctx: CLI runner context

        Returns:
            Rich Text renderable
        """
        from rich.text import Text as RichText

        return RichText(self.content)

    def build_gui(self, ctx) -> Any:
        """Build Text for GUI (returns Flet Text).

        Args:
            ctx: GUI runner context

        Returns:
            Flet Text control
        """
        import flet as ft

        return ft.Text(self.content, selectable=True)
