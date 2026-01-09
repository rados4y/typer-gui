"""Layout components - Row and Column for arranging components."""

from dataclasses import dataclass, field
from typing import Any

from .base import Container, UiBlock


@dataclass
class Row(Container):
    """Display components horizontally."""

    children: list[Any] = field(default_factory=list)

    def __post_init__(self):
        """Initialize Container attributes after dataclass init."""
        # Store the children list from dataclass field before calling super().__init__()
        # because dataclass sets self.children directly, bypassing the property setter
        children_from_dataclass = self.children if hasattr(self, "children") else []

        # Only call super().__init__() if not already initialized
        if not hasattr(self, "_context_active"):
            super().__init__()

        # Now set children properly through the property setter
        # This ensures self._children gets populated
        if children_from_dataclass:
            self.children = children_from_dataclass

    def add(self, child: UiBlock) -> None:
        """Add a child component to the row."""
        self.children.append(child)
        self._update()

    def to_dict(self) -> dict:
        return {
            "type": "row",
            "children": [
                child.to_dict() if isinstance(child, UiBlock) else str(child)
                for child in self.children
            ],
        }

    def build_cli(self, ctx) -> Any:
        """Build Row for CLI (returns Rich Group - vertical in CLI).

        Args:
            ctx: CLI runner context

        Returns:
            Rich Group renderable
        """
        from rich.console import Group

        # CLI shows children vertically (no horizontal layout in terminal)
        renderables = []
        for child in self.children:
            if isinstance(child, UiBlock) and not child.is_gui_only():
                renderable = ctx.build_child(self, child)
                renderables.append(renderable)
            elif not isinstance(child, UiBlock):
                from rich.text import Text as RichText

                renderables.append(RichText(str(child)))

        return Group(*renderables) if renderables else ""

    def build_gui(self, ctx) -> Any:
        """Build Row for GUI (returns Flet Row).

        Args:
            ctx: GUI runner context

        Returns:
            Flet Row control
        """
        import flet as ft

        controls = [ctx.build_child(self, child) for child in self.children]
        return ft.Row(controls=controls, spacing=10, wrap=True)


@dataclass
class Column(Container):
    """Display components vertically."""

    children: list[UiBlock] = field(default_factory=list)

    def __post_init__(self):
        """Initialize Container attributes after dataclass init."""
        # Store the children list from dataclass field before calling super().__init__()
        # because dataclass sets self.children directly, bypassing the property setter
        children_from_dataclass = self.children if hasattr(self, "children") else []

        # Only call super().__init__() if not already initialized
        if not hasattr(self, "_context_active"):
            super().__init__()

        # Now set children properly through the property setter
        # This ensures self._children gets populated
        if children_from_dataclass:
            self.children = children_from_dataclass

    def add(self, child: UiBlock) -> None:
        """Add a child component to the column."""
        self.children.append(child)
        self._update()

    def to_dict(self) -> dict:
        return {
            "type": "column",
            "children": [child.to_dict() for child in self.children],
        }

    def build_cli(self, ctx) -> Any:
        """Build Column for CLI (returns Rich Group - vertical layout).

        Args:
            ctx: CLI runner context

        Returns:
            Rich Group renderable
        """
        from rich.console import Group

        renderables = [ctx.build_child(self, child) for child in self.children]
        return Group(*renderables) if renderables else ""

    def build_gui(self, ctx) -> Any:
        """Build Column for GUI (returns Flet Column).

        Args:
            ctx: GUI runner context

        Returns:
            Flet Column control
        """
        import flet as ft

        controls = [ctx.build_child(self, child) for child in self.children]
        return ft.Column(controls=controls, spacing=10)
