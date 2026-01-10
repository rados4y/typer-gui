"""Print component - Handles print() output with automatic accumulation."""

from dataclasses import dataclass
from typing import Any, Optional

from .base import UiBlock


@dataclass
class Print(UiBlock):
    """Display print() output with automatic text accumulation.

    This component handles the accumulation logic for consecutive print() calls.
    In GUI mode, it uses the runner's text_buffer to accumulate consecutive
    print() statements into a single Text control, maintaining the same behavior
    as before but encapsulated in a UI block.
    """

    content: str

    def __post_init__(self):
        """Initialize parent class after dataclass fields."""
        UiBlock.__init__(self)

    def to_dict(self) -> dict:
        return {"type": "print", "content": self.content}

    def build_cli(self, ctx) -> Any:
        """Build Print for CLI (returns Rich Text).

        Args:
            ctx: CLI runner context

        Returns:
            Rich Text renderable
        """
        from rich.text import Text as RichText

        return RichText(self.content)

    def build_gui(self, ctx) -> Any:
        """Build Print for GUI using text buffer accumulation.

        This uses the runner's text_buffer mechanism to accumulate consecutive
        print() calls. The actual Text control is created when the buffer is flushed.

        Args:
            ctx: GUI runner context

        Returns:
            Empty invisible container (placeholder - actual text added via buffer flush)
        """
        import flet as ft

        # Try to get runner from ctx
        runner = getattr(ctx, "runner", None)
        if runner and hasattr(runner, '_append_text'):
            # Call the runner's _append_text method to add to buffer
            # This maintains the existing accumulation behavior
            runner._append_text(self.content)

        # Return an empty invisible container as placeholder
        # The actual text will be rendered when the buffer is flushed
        return ft.Container(visible=False, width=0, height=0)
