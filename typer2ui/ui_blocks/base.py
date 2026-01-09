"""Base classes and utilities for UI blocks."""

from abc import ABC, abstractmethod
from typing import Any, Optional, TYPE_CHECKING

if TYPE_CHECKING:
    import flet as ft

# Global reference to current runner (set by runner during command execution)
_current_runner = None


def get_current_runner() -> Optional[Any]:
    """Get the current active runner."""
    return _current_runner


def set_current_runner(runner: Optional[Any]) -> None:
    """Set the current active runner."""
    global _current_runner
    _current_runner = runner


def to_component(value: Any) -> 'UiBlock':
    """Convert a value to a UiBlock component.

    Handles automatic conversion:
    - None → Text("") (empty line)
    - str → Md(str) (markdown)
    - UiBlock → unchanged
    - any other object → Text(str(obj))

    Args:
        value: Value to convert

    Returns:
        UiBlock component
    """
    # Import here to avoid circular dependency
    from .text import Text
    from .md import Md

    # Already a component - return as-is
    if isinstance(value, UiBlock):
        return value

    # None → empty line
    if value is None:
        return Text("")

    # String → Markdown
    if isinstance(value, str):
        return Md(value)

    # Anything else → convert to string
    return Text(str(value))


class UiBlock(ABC):
    """Base class for all UI components.

    Each component contains all presentation logic for every channel in a single class.
    """

    def __init__(self):
        """Initialize the UI block with hierarchy support."""
        # Parent-child hierarchy (for new architecture)
        self._parent: Optional["UiBlock"] = None
        self._children: list["UiBlock"] = []

        # Context and control references (for new architecture)
        self._ctx: Optional[Any] = None  # UIRunnerCtx instance
        self._flet_control: Optional[Any] = None  # ft.Control for GUI

    @abstractmethod
    def build_cli(self, ctx) -> Any:
        """Build component for CLI (returns Rich renderable).

        Args:
            ctx: CLI runner context
        """
        pass

    @abstractmethod
    def build_gui(self, ctx) -> Any:
        """Build component for GUI (returns Flet control).

        Args:
            ctx: GUI runner context
        """
        pass

    def show_rest(self, runner) -> None:
        """Render the component for REST API output.

        Args:
            runner: RESTRunner instance
        """
        runner.add_element(self.to_dict())

    def to_dict(self) -> dict:
        """Serialize component to dict for REST API."""
        return {"type": self.__class__.__name__.lower()}

    def to_text(self) -> str:
        """Convert component to plain text representation.

        This method reuses the component's show_cli() logic by capturing
        its stdout output. Components can override this for better performance
        or different text representation.

        Returns:
            Plain text representation of the component
        """
        import io
        from contextlib import redirect_stdout
        from rich.console import Console

        buffer = io.StringIO()
        console = Console(file=buffer, force_terminal=False)

        # Use CLIRunnerCtx to build the component
        from ..runners.cli_context import CLIRunnerCtx

        ctx = CLIRunnerCtx()
        ctx.console = console

        # Build and render
        renderable = self.build_cli(ctx)
        console.print(renderable)

        return buffer.getvalue().rstrip("\n")

    def is_gui_only(self) -> bool:
        """Whether this component should only appear in GUI mode."""
        return False

    # Hierarchy management methods (for new architecture)
    @property
    def parent(self) -> Optional["UiBlock"]:
        """Get parent component."""
        return self._parent

    @property
    def children(self) -> list["UiBlock"]:
        """Get child components."""
        return self._children

    @children.setter
    def children(self, value: list["UiBlock"]) -> None:
        """Set child components."""
        self._children = value

    def add_child(self, child: "UiBlock") -> None:
        """Add child and establish parent-child relationship.

        Args:
            child: The child component to add
        """
        child._parent = self
        if child not in self._children:
            self._children.append(child)

    def get_root(self) -> "UiBlock":
        """Get root component by walking up the hierarchy.

        Returns:
            The root component (has no parent)
        """
        current = self
        while current._parent:
            current = current._parent
        return current


class Container(UiBlock, ABC):
    """Base class for components that can contain children.

    Supports context manager pattern for progressive rendering.
    Also supports auto-update when presented via ui(component).
    """

    def __init__(self):
        # Initialize parent class
        super().__init__()

        # Only initialize children if not already set by dataclass
        if not hasattr(self, "children"):
            self.children: list[UiBlock] = []
        self._context_active = False
        self._runner = None
        self._presentation_runner = None
        self._presented = False

    def _mark_presented(self, runner) -> None:
        """Mark this container as presented for auto-updates.

        Called by ui() when component is first displayed.

        Args:
            runner: The runner that presented this component
        """
        self._presented = True
        self._presentation_runner = runner

    def __enter__(self) -> 'Container':
        """Enter context manager - start progressive rendering."""
        self._context_active = True
        self._runner = get_current_runner()

        # Mark as presented for update tracking
        # Note: The container is already in the ui_stack via ui() call
        # It will be built and displayed when stack is processed
        if not self._presented and self._runner:
            self._mark_presented(self._runner)

        return self

    def __exit__(self, exc_type: Optional[type], exc_val: Optional[BaseException], exc_tb: Optional[Any]) -> bool:
        """Exit context manager - finalize rendering."""
        self._context_active = False
        self._runner = None
        return False

    def _update(self) -> None:
        """Update display if presented or in context manager.

        In the new architecture, components update by calling page.update()
        on their context's page. The Flet control is already in the page,
        so we just need to refresh it.
        """
        # New architecture: use _ctx if available
        if self._ctx and hasattr(self._ctx, "page"):
            # Component's Flet control is already in the page
            # Use runner's thread-safe update for Flet 0.80+
            if hasattr(self._ctx, "runner") and self._ctx.runner:
                self._ctx.runner._safe_page_update()
            elif self._ctx.page:
                # Fallback to direct update if runner not available
                self._ctx.page.update()
