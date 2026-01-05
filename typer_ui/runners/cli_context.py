"""
CLIRunnerCtx - CLI-specific context implementation with Rich integration.

This module implements the UIRunnerCtx for CLI rendering using Rich,
providing the build_child() method that handles all content type complexity.
"""

from typing import Any, Optional
from rich.console import Console, Group, RenderableType
from rich.markdown import Markdown
from rich.text import Text as RichText

from ..context import UIRunnerCtx, UIBlockType
from ..ui_blocks import UiBlock


class CLIRunnerCtx(UIRunnerCtx):
    """CLI-specific runner context using Rich.

    Implements stack-based architecture where ui() just appends to a stack,
    and build_child() handles all the complexity of building different content types.
    """

    def __init__(self):
        """Initialize CLI context with Rich console."""
        super().__init__()
        self.console = Console()

    def _handle_immediate_output(self, component: UIBlockType) -> None:
        """Handle output when there's no active stack context.

        In CLI mode, when commands are executed directly by Typer, we just build
        and print the component immediately.

        Args:
            component: Component or value to output immediately.
        """
        from ..ui_blocks import Text
        # Create a simple dummy root for build_child
        root = Text("")
        # Build and print immediately
        renderable = self.build_child(root, component)
        self.console.print(renderable)

    def build_child(self, parent: UiBlock, child: UIBlockType) -> RenderableType:
        """Build child component - handles all types.

        This is where all the complexity lives. Handles:
        - String → Markdown renderable
        - UIBlock → Build and set parent relationship
        - Callable (dynamic) → Print immediately, set up on_append
        - Callable (regular) → Capture stack and build renderables
        - Other → Convert to Text

        Args:
            parent: Parent UIBlock that will contain this child
            child: Child content (string, callable, or UIBlock)

        Returns:
            Rich renderable ready to print
        """
        # Case 1: String → Markdown
        if isinstance(child, str):
            return Markdown(child)

        # Case 2: UIBlock → Build and set parent relationship
        if isinstance(child, UiBlock):
            parent.add_child(child)
            child._ctx = self
            return child.build_cli(self)

        # Case 3: Dynamic callable (can receive ui() calls after execution)
        if callable(child) and getattr(child, '__typer_ui_is_dynamic__', False):
            # Capture initial UI
            with self.new_ui_stack() as ui_stack:
                child()

            # Print captured output immediately
            for item in ui_stack:
                renderable = self.build_child(parent, item)
                self.console.print(renderable)

            # Set up callback for future ui() calls
            def on_append(item: UIBlockType):
                renderable = self.build_child(parent, item)
                self.console.print(renderable)  # Print immediately

            ui_stack.on_append = on_append  # type: ignore
            return ""  # Already printed

        # Case 4: Regular callable → Capture ui() calls
        if callable(child):
            with self.new_ui_stack() as ui_stack:
                result = child()

                # If callable returns a value, add it to stack
                if result is not None:
                    ui_stack.append(result)

            # Build renderables from captured stack
            renderables = [self.build_child(parent, item) for item in ui_stack]

            # Return single or grouped
            if len(renderables) == 0:
                return ""
            elif len(renderables) == 1:
                return renderables[0]
            else:
                return Group(*renderables)

        # Fallback: Convert to string
        return RichText(str(child))
