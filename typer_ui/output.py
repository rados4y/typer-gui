"""Standalone output functions for Typer-UI.

This module provides the primary API for displaying UI components:
- ui() - Universal output function (str input is treated as markdown)
- text() - Plain text shortcut
- dx() - Dynamic/reactive content
"""

from typing import Any, Callable, Optional
from dataclasses import dataclass

from .ui_blocks import UiBlock, Text, Md, Column, get_current_runner, set_current_runner


class DynamicBlock(UiBlock):
    """Wrapper for dynamic/reactive UI content.

    Created by dx() function. When passed to ui(), renders
    content that auto-updates when dependencies change.
    """

    def __init__(self, renderer: Callable, dependencies: tuple):
        """Initialize DynamicBlock.

        Args:
            renderer: Function that builds the UI content
            dependencies: State objects to observe for changes
        """
        super().__init__()
        self.renderer = renderer
        self.dependencies = dependencies
        self._container = None

    def __repr__(self):
        deps = ', '.join(str(d) for d in self.dependencies)
        renderer_name = getattr(self.renderer, '__name__', repr(self.renderer))
        return f"DynamicBlock(renderer={renderer_name}, deps=[{deps}])"

    def build_cli(self, ctx) -> Any:
        """Build DynamicBlock for CLI (returns Rich Group).

        Args:
            ctx: CLI runner context

        Returns:
            Rich Group renderable
        """
        from rich.console import Group

        # Execute renderer with new UI stack context
        with ctx._new_ui_stack() as ui_stack:
            result = self.renderer()
            if result is not None:
                ui_stack.append(result)

        # Build renderables from stack
        renderables = [ctx.build_child(self, item) for item in ui_stack]

        # Set up observers for re-rendering
        def on_state_change():
            # Re-render with new stack context
            with ctx._new_ui_stack() as new_stack:
                result = self.renderer()
                if result is not None:
                    new_stack.append(result)

            # Print new output
            for item in new_stack:
                renderable = ctx.build_child(self, item)
                ctx.console.print(renderable)

        from .state import State
        for dep in self.dependencies:
            if isinstance(dep, State):
                dep.add_observer(on_state_change)

        return Group(*renderables) if renderables else ""

    def build_gui(self, ctx) -> Any:
        """Build DynamicBlock for GUI (returns Flet Column).

        Args:
            ctx: GUI runner context

        Returns:
            Flet Column control
        """
        import flet as ft

        # Create container for dynamic content
        self._container = ft.Column(controls=[], spacing=10)
        self._flet_control = self._container

        def render():
            """Re-render on state change."""
            # Clear container
            self._container.controls.clear()

            # Execute renderer with new UI stack context
            with ctx._new_ui_stack() as ui_stack:
                result = self.renderer()
                if result is not None:
                    ui_stack.append(result)

            # Build controls from stack
            controls = [ctx.build_child(self, item) for item in ui_stack]

            # Add to container
            self._container.controls.extend(controls)

            # Update display
            if ctx.page:
                ctx.page.update()

        # Initial render
        render()

        # Register observers
        from .state import State
        for dep in self.dependencies:
            if isinstance(dep, State):
                dep.add_observer(render)

        return self._container


def dx(renderer: Callable, *dependencies) -> DynamicBlock:
    """Create a dynamic UI block that re-renders when dependencies change.

    The renderer can:
    - Return a UiBlock component
    - Return a string (converted to Markdown)
    - Return None (empty)
    - Call ui() internally to build content

    Args:
        renderer: Function that builds the UI content
        *dependencies: State objects to observe for changes

    Returns:
        DynamicBlock that can be passed to ui()

    Examples:
        >>> state = app.state(0)
        >>> ui(dx(lambda: f"Count: {state.value}", state))
        >>>
        >>> # Or return a component
        >>> ui(dx(lambda: tu.Table(...), state1, state2))
        >>>
        >>> # Or use ui() inside renderer
        >>> def render():
        ...     ui("### Dynamic Section")
        ...     ui(tu.Table(...))
        >>> ui(dx(render, state))
    """
    return DynamicBlock(renderer=renderer, dependencies=dependencies)


def ui(component_or_value: Any = None) -> Any:
    """Present a UI component or value.

    Uses the new stack-based architecture. Simply appends the value to the
    current UI stack. Conversion from strings/values to UI components happens
    later in build_child().

    Automatic conversions (handled by build_child):
    - None → Text("") (empty line)
    - str → Md(str) (markdown - default behavior)
    - int/float/etc → Text(str(value))
    - UiBlock → unchanged
    - DynamicBlock → setup reactive rendering
    - Callable → captured and rendered

    Args:
        component_or_value: Component, string, callable, or value to display

    Returns:
        The input value (for chaining/context manager support)

    Raises:
        RuntimeError: If called outside command execution context

    Examples:
        >>> ui("# Hello")  # Markdown (default for strings)
        >>> ui("**Bold**")  # Markdown
        >>> ui()  # Empty line
        >>> ui(tu.Table(...))  # Component
        >>> ui(dx(lambda: "...", state))  # Dynamic content
        >>> print("plain text")  # Use print() for plain text
    """
    from .context import UIRunnerCtx

    # Get current context
    ctx = UIRunnerCtx.instance()
    if ctx is None:
        raise RuntimeError("ui() can only be called during command execution.")

    # Simply append to stack - all conversion logic is in build_child()
    ctx.ui(component_or_value)

    # Return the component for context manager support
    return component_or_value


def text(value: Any = "") -> Text:
    """Present plain text content.

    Shortcut for ui(tu.Text(...)). Unlike ui() which treats strings
    as markdown, this displays plain text without markdown rendering.

    Args:
        value: Value to display as plain text (converted to string)

    Returns:
        The Text component

    Examples:
        >>> text("Plain text output")
        >>> text(42)
        >>> text()  # Empty line
    """
    component = Text(str(value))
    return ui(component)
