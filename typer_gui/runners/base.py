"""Base runner abstract class."""

from abc import ABC, abstractmethod
from typing import Any, Callable, Optional
from ..specs import AppSpec
from ..events import Event


class Runner(ABC):
    """Abstract base class for all runners.

    Runners host the application in specific environments (CLI, GUI, REST)
    and handle event presentation/rendering.
    """

    def __init__(self, app_spec: AppSpec):
        """Initialize runner with application specification.

        Args:
            app_spec: Immutable application specification
        """
        self.app_spec = app_spec
        self.ui_app: Optional[Any] = None  # Will be UIApp instance
        self._event_handlers: list[Callable[[Event], None]] = []

    @abstractmethod
    async def start(self) -> None:
        """Boot the environment and start the runner.

        This method should:
        - Initialize the environment (CLI process, Flet app, REST server)
        - Create UIApp instance
        - Subscribe to UIApp events
        - Start the main loop
        """
        pass

    @abstractmethod
    async def handle_event(self, event: Event) -> None:
        """Handle an event emitted by UIApp.

        Args:
            event: The event to handle
        """
        pass

    @abstractmethod
    async def execute_command(
        self,
        command_name: str,
        params: dict[str, Any]
    ) -> tuple[Any, Optional[Exception]]:
        """Execute a command callback with stdout/stderr capture.

        Args:
            command_name: Name of the command to execute
            params: Parameter values for the command

        Returns:
            Tuple of (result, exception). Exception is None if successful.
        """
        pass

    def subscribe(self, handler: Callable[[Event], None]) -> None:
        """Subscribe to events.

        Args:
            handler: Callback function to handle events
        """
        self._event_handlers.append(handler)

    def unsubscribe(self, handler: Callable[[Event], None]) -> None:
        """Unsubscribe from events.

        Args:
            handler: Callback function to remove
        """
        if handler in self._event_handlers:
            self._event_handlers.remove(handler)

    async def _emit_to_handlers(self, event: Event) -> None:
        """Emit event to all registered handlers.

        Args:
            event: Event to emit
        """
        for handler in self._event_handlers:
            try:
                if asyncio.iscoroutinefunction(handler):
                    await handler(event)
                else:
                    handler(event)
            except Exception as e:
                # Log error but don't let handler failures stop event emission
                print(f"Error in event handler: {e}")


import asyncio
