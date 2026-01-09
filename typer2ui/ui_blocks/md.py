"""Markdown component - Display markdown content."""

from dataclasses import dataclass
from typing import Any

from .base import UiBlock


@dataclass
class Md(UiBlock):
    """Display Markdown content."""

    content: str

    def __post_init__(self):
        """Initialize parent class after dataclass fields."""
        UiBlock.__init__(self)

    def to_dict(self) -> dict:
        return {"type": "markdown", "content": self.content}

    def build_cli(self, ctx) -> Any:
        """Build Markdown for CLI (returns Rich Markdown).

        Args:
            ctx: CLI runner context

        Returns:
            Rich Markdown renderable
        """
        from rich.markdown import Markdown

        return Markdown(self.content)

    def build_gui(self, ctx) -> Any:
        """Build Markdown for GUI (returns Flet Markdown).

        Args:
            ctx: GUI runner context

        Returns:
            Flet Markdown control
        """
        import flet as ft

        return ft.Markdown(
            self.content,
            selectable=True,
            extension_set=ft.MarkdownExtensionSet.GITHUB_WEB,
            on_tap_link=lambda e: print(f"Link tapped: {e.data}"),
        )
