"""Standalone output functions for Typer-UI.

This module provides the primary API for displaying UI components:
- ui() - Universal output function (str input is treated as markdown)
- text() - Plain text shortcut
- dx() - Dynamic/reactive content
"""

from typing import Any, Callable, Optional
from dataclasses import dataclass

from .ui_blocks import UiBlock, Text, Md, Column, get_current_runner, set_current_runner


@dataclass
class DynamicBlock:
    """Wrapper for dynamic/reactive UI content.

    Created by dx() function. When passed to ui(), renders
    content that auto-updates when dependencies change.
    """
    renderer: Callable
    dependencies: tuple

    def __repr__(self):
        deps = ', '.join(str(d) for d in self.dependencies)
        renderer_name = getattr(self.renderer, '__name__', repr(self.renderer))
        return f"DynamicBlock(renderer={renderer_name}, deps=[{deps}])"


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


def _render_dynamic_block(dyn_block: DynamicBlock, runner) -> Column:
    """Internal: Render a dynamic block with reactive updates."""
    from .state import State

    container = Column([])

    # Execute renderer in reactive mode
    _, flet_control = runner.execute_in_reactive_mode(container, dyn_block.renderer)

    # Store control for updates (GUI mode)
    if flet_control is not None:
        runner._reactive_components[id(container)] = flet_control
        runner.add_to_output(flet_control, component=container)

    # Register observer callbacks
    def on_state_change():
        runner.update_reactive_container(container, dyn_block.renderer)

    for dep in dyn_block.dependencies:
        if isinstance(dep, State):
            dep.add_observer(on_state_change)

    return container


def ui(component_or_value: Any = None) -> UiBlock:
    """Present a UI component or value.

    Automatic conversions:
    - None → Text("") (empty line)
    - str → Md(str) (markdown - default behavior)
    - int/float/etc → Text(str(value))
    - UiBlock → unchanged
    - DynamicBlock → setup reactive rendering

    Args:
        component_or_value: Component or value to display

    Returns:
        The displayed component (for chaining/context manager)

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
    runner = get_current_runner()
    if not runner:
        raise RuntimeError("ui() can only be called during command execution.")

    # Handle None (empty line)
    if component_or_value is None:
        component = Text("")

    # Handle DynamicBlock (reactive content)
    elif isinstance(component_or_value, DynamicBlock):
        return _render_dynamic_block(component_or_value, runner)

    # Handle strings (convert to Markdown)
    elif isinstance(component_or_value, str):
        component = Md(component_or_value)

    # Handle other values (convert to Text)
    elif not isinstance(component_or_value, UiBlock):
        component = Text(str(component_or_value))

    # Already a UiBlock
    else:
        component = component_or_value

    # Check if in reactive mode
    if runner.is_reactive_mode():
        runner.add_to_reactive_container(component)
    else:
        runner.show(component)

    # Mark component as presented for auto-updates
    if hasattr(component, '_mark_presented'):
        component._mark_presented(runner)

    return component


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
