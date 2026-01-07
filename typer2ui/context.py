"""
UIRunnerCtx - Context for UI rendering with stack-based architecture.

This module provides the abstract base class for UI runner contexts,
implementing stack-based lazy evaluation for UI components.
"""

from abc import ABC, abstractmethod
from contextlib import contextmanager
from contextvars import ContextVar
from typing import TYPE_CHECKING, Any, Callable, List, Optional, Union

if TYPE_CHECKING:
    from .ui_blocks import UiBlock

# Type alias for all possible UI content types
UIBlockType = Union[str, Callable[[], Any], "UiBlock"]

# Context variable for current UI stack (shared across execution context)
_current_stack_var: ContextVar[Optional["UiStack"]] = ContextVar('current_stack', default=None)


class UiStack(list):
    """UI stack with observer pattern for append notifications.

    This is a list subclass that notifies registered observers whenever
    an item is appended. This enables real-time rendering for long-running
    and async tasks.
    """

    def __init__(self):
        """Initialize empty stack with empty observer list."""
        super().__init__()
        self._observers: List[Callable[[Any], None]] = []

    def register_observer(self, callback: Callable[[Any], None]) -> None:
        """Register an observer to be notified on append.

        Args:
            callback: Function to call when items are appended.
                     Receives the appended item as argument.
        """
        self._observers.append(callback)

    def append(self, item: Any) -> None:
        """Append item to stack and notify all observers.

        Args:
            item: UIBlockType to append
        """
        super().append(item)
        # Notify all observers immediately
        for observer in self._observers:
            observer(item)


class UIRunnerCtx(ABC):
    """Abstract base class for UI runner contexts.

    Implements stack-based architecture where ui() calls simply append to a stack,
    and build_child() handles all the complexity of rendering different content types.
    """

    # Global current instance (set by subclass)
    _current_instance: Optional["UIRunnerCtx"] = None

    def __init__(self):
        """Initialize the context."""
        # Note: _current_stack is now a context variable, not instance variable
        pass

    @staticmethod
    def instance() -> Optional["UIRunnerCtx"]:
        """Get the current runner context.

        Returns:
            The current UIRunnerCtx instance, or None if no context is active.
        """
        return UIRunnerCtx._current_instance

    def ui(self, component: UIBlockType) -> None:
        """Simply append UIBlockType to current stack.

        This is the core of the new architecture - ui() is trivial,
        just appending to a stack. All complexity is in build_child().

        Args:
            component: A string (markdown), callable, or UIBlock instance.

        Raises:
            RuntimeError: If called outside an active UI stack context.
        """
        # Get current stack from context variable
        current_stack = _current_stack_var.get()

        if current_stack is None:
            # No active stack - handle based on runner type
            self._handle_immediate_output(component)
        else:
            # Just append, don't build yet! (lazy evaluation)
            current_stack.append(component)

    def _handle_immediate_output(self, component: UIBlockType) -> None:
        """Handle output when there's no active stack context.

        This is used in CLI mode when commands are executed directly by Typer
        without going through execute_command().

        Args:
            component: Component or value to output immediately.
        """
        # Default implementation for subclasses to override
        raise RuntimeError(
            "No active UI stack - ui() called outside command context"
        )

    @contextmanager
    def new_ui_stack(self):
        """Context manager for stack management using context variables.

        Creates a new UI stack and sets it in the context variable.
        When the context exits, automatically restores the previous value.

        This supports nested callables - each callable gets its own stack,
        and when it completes (or raises an error), the previous stack is restored.

        Public API for extensibility - use this when creating custom components
        that need to capture UI output in isolation.

        Yields:
            UiStack: The new UI stack for capturing ui() calls.
        """
        # Create new stack
        ui_stack = UiStack()

        # Set in context variable and get token for restoration
        token = _current_stack_var.set(ui_stack)

        try:
            yield ui_stack
        finally:
            # Restore previous stack using token (even if error occurred)
            _current_stack_var.reset(token)

    @abstractmethod
    def build_child(self, parent: "UiBlock", child: UIBlockType) -> Any:
        """Build child component and establish parent-child relationship.

        This method handles all the complexity of rendering different content types:
        - str → Markdown component
        - UIBlock → Build and set parent relationship
        - Callable (dynamic) → ListView with on_append callback
        - Callable (regular) → Capture stack and build controls
        - Other → Convert to Text

        Args:
            parent: The parent UIBlock that will contain this child.
            child: The child content to build (string, callable, or UIBlock).

        Returns:
            For GUI: ft.Control
            For CLI: RenderableType (Rich renderable)
        """
        pass
