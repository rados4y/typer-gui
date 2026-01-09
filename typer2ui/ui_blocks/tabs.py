"""Tabs components - Tabbed interface."""

from dataclasses import dataclass
from typing import Any, Callable, Union

from .base import UiBlock, to_component


@dataclass
class Tab:
    """A single tab with label and content.

    Args:
        label: Tab label/title
        content: Either a UiBlock component, a callable that builds content using ui(), or a string (converted to markdown)
    """

    label: str
    content: Union[UiBlock, Callable, str, Any]

    def __post_init__(self):
        """Validate and convert tab content."""
        if not callable(self.content):
            # Convert non-callable content to a UiBlock component
            # This handles strings (→ Md), None (→ Text("")), and other values
            if not isinstance(self.content, UiBlock):
                self.content = to_component(self.content)


@dataclass
class Tabs(UiBlock):
    """Tabbed interface container.

    Args:
        tabs: List of Tab objects
    """

    tabs: list[Tab]

    def __post_init__(self):
        """Validate tabs configuration."""
        UiBlock.__init__(self)
        if not self.tabs:
            raise ValueError("Tabs must contain at least one tab")
        if not all(isinstance(tab, Tab) for tab in self.tabs):
            raise ValueError("All items must be Tab objects")

    def to_dict(self) -> dict:
        return {
            "type": "tabs",
            "tabs": [
                {
                    "label": tab.label,
                    "content": (
                        tab.content.to_dict()
                        if isinstance(tab.content, UiBlock)
                        else "<callable>"
                    ),
                }
                for tab in self.tabs
            ],
        }

    def build_cli(self, ctx) -> Any:
        """Build Tabs for CLI (returns Rich Group - sequential rendering).

        Args:
            ctx: CLI runner context

        Returns:
            Rich Group renderable
        """
        from rich.console import Group
        from rich.text import Text as RichText
        from rich.rule import Rule

        renderables = []
        for i, tab in enumerate(self.tabs):
            # Add spacing between tabs
            if i > 0:
                renderables.append(RichText(""))

            # Tab header
            renderables.append(Rule(tab.label))

            # Tab content - use ctx.build_child to handle all content types
            content = ctx.build_child(self, tab.content)
            renderables.append(content)

        return Group(*renderables)

    def build_gui(self, ctx) -> Any:
        """Build Tabs for GUI (returns Flet Tabs with TabBar + TabBarView).

        Args:
            ctx: GUI runner context

        Returns:
            Flet Tabs control containing TabBar and TabBarView
        """
        import flet as ft

        # Create tab labels (for TabBar)
        tab_controls = [ft.Tab(tab.label) for tab in self.tabs]

        # Create tab content (for TabBarView)
        content_controls = []
        for tab in self.tabs:
            # Use ctx.build_child to handle all content types (string/callable/UIBlock)
            tab_content = ctx.build_child(self, tab.content)

            # Wrap in Container for padding
            wrapped_content = ft.Container(
                content=tab_content,
                padding=10,
            )
            content_controls.append(wrapped_content)

        # Create TabBar and TabBarView (Flet 0.80+ API)
        tab_bar = ft.TabBar(tabs=tab_controls)
        tab_view = ft.TabBarView(
            controls=content_controls,
            expand=True,  # Required: TabBarView needs bounded height
        )

        # Wrap in Tabs control (required coordinator in Flet 0.80+)
        return ft.Tabs(
            content=ft.Column(
                controls=[tab_bar, tab_view],
                spacing=0,
            ),
            length=len(self.tabs),
        )
