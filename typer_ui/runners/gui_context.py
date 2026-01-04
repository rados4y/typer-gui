"""
GUIRunnerCtx - GUI-specific context implementation with Flet integration.

This module implements the UIRunnerCtx for GUI rendering using Flet,
providing the build_child() method that handles all content type complexity.
"""

from typing import Any, Optional
import flet as ft

from ..context import UIRunnerCtx, UIBlockType
from ..ui_blocks import UiBlock


class ListView(UiBlock):
    """Container that supports dynamic appending for progressive updates.

    Used for regular callables (multiple ui() calls) and dynamic callables
    (can receive ui() calls after execution).
    """

    def __init__(self, controls: Optional[list] = None):
        """Initialize ListView with optional pre-built controls.

        Args:
            controls: List of Flet controls to initialize with
        """
        super().__init__()
        self.controls = controls or []
        self._column: Optional[ft.Column] = None

    def append(self, control: ft.Control) -> None:
        """Append control dynamically.

        Args:
            control: Flet control to append
        """
        if self._column:
            self._column.controls.append(control)

    def update(self) -> None:
        """Refresh display."""
        if self._ctx and hasattr(self._ctx, 'page'):
            self._ctx.page.update()

    def build_cli(self, ctx: 'UIRunnerCtx') -> Any:
        """Build ListView for CLI (returns Rich Group).

        Args:
            ctx: The CLI runner context

        Returns:
            Rich Group containing all renderables
        """
        from rich.console import Group
        # Not typically used, but provided for completeness
        return Group(*["ListView (GUI only)"])

    def build_gui(self, ctx: 'GUIRunnerCtx') -> ft.Control:
        """Build ListView for GUI.

        Args:
            ctx: The GUI runner context

        Returns:
            Flet Column control containing all child controls
        """
        self._column = ft.Column(controls=self.controls, spacing=10)
        self._flet_control = self._column
        self._ctx = ctx
        return self._column


class GUIRunnerCtx(UIRunnerCtx):
    """GUI-specific runner context using Flet.

    Implements stack-based architecture where ui() just appends to a stack,
    and build_child() handles all the complexity of building different content types.
    """

    # Global instance for context retrieval
    _instance: Optional['GUIRunnerCtx'] = None

    def __init__(self, page: ft.Page):
        """Initialize GUI context.

        Args:
            page: Flet page instance for rendering
        """
        super().__init__()
        self.page = page

    @staticmethod
    def instance() -> Optional['GUIRunnerCtx']:
        """Get current runner context.

        Returns:
            Current GUIRunnerCtx instance, or None if no context active
        """
        return GUIRunnerCtx._instance

    def build_child(self, parent: UiBlock, child: UIBlockType) -> ft.Control:
        """Build child component - handles all types.

        This is where all the complexity lives. Handles:
        - String → Markdown
        - UIBlock → Build and set parent relationship
        - Callable (dynamic) → ListView with on_append callback
        - Callable (regular) → Capture stack and build controls
        - Other → Convert to Text

        Args:
            parent: Parent UIBlock that will contain this child
            child: Child content (string, callable, or UIBlock)

        Returns:
            Flet control ready to add to the page
        """
        # Case 1: String → Markdown
        if isinstance(child, str):
            from ..ui_blocks import Md
            md = Md(child)
            md._ctx = self
            control = md.build_gui(self)
            md._flet_control = control
            return control

        # Case 2: UIBlock → Build and set parent relationship
        if isinstance(child, UiBlock):
            parent.add_child(child)
            child._ctx = self
            control = child.build_gui(self)
            child._flet_control = control
            return control

        # Case 3: Dynamic callable (can receive ui() calls after execution)
        if callable(child) and getattr(child, '__typer_ui_is_dynamic__', False):
            # Capture initial UI
            with self._new_ui_stack() as ui_stack:
                child()

            # Build ListView from captured stack
            controls = [self.build_child(parent, item) for item in ui_stack]
            lv = ListView(controls=controls)
            lv._ctx = self
            lv_control = lv.build_gui(self)
            lv._flet_control = lv_control

            # Set up callback for future ui() calls
            def on_append(item: UIBlockType):
                control = self.build_child(parent, item)
                lv.append(control)
                lv.update()

            # Register observer on stack (for async/threaded ui() calls)
            ui_stack.register_observer(on_append)
            return lv_control

        # Case 4: Regular callable → Capture ui() calls
        if callable(child):
            with self._new_ui_stack() as ui_stack:
                result = child()

                # If callable returns a value, add it to stack
                if result is not None:
                    ui_stack.append(result)

            # Build controls from captured stack
            controls = [self.build_child(parent, item) for item in ui_stack]

            # Unwrap single element
            if len(controls) == 1:
                return controls[0]

            # Wrap multiple in ListView
            lv = ListView(controls=controls)
            lv._ctx = self
            lv_control = lv.build_gui(self)
            lv._flet_control = lv_control
            return lv_control

        # Fallback: Convert to string and create Text
        from ..ui_blocks import Text
        text = Text(str(child))
        text._ctx = self
        control = text.build_gui(self)
        text._flet_control = control
        return control
