"""Async event-emitting UIApp controller."""

import asyncio
import time
from typing import Any, Optional, Callable
from dataclasses import dataclass, field

from .specs import AppSpec, CommandSpec
from .events import (
    Event,
    CommandSelected,
    CommandStarted,
    CommandFinished,
    TextEmitted,
    BlockEmitted,
    ContainerStarted,
    ContainerEnded,
    ErrorRaised,
)


@dataclass
class ExecutionRecord:
    """Record of command execution."""
    command_name: str
    params: dict[str, Any]
    result: Any
    success: bool
    duration: float
    timestamp: float = field(default_factory=time.time)
    error: Optional[Exception] = None


class UIApp:
    """Central controller for UI applications.

    UIApp is presentation-agnostic and coordinates command selection
    and execution without knowing how results are displayed.
    """

    def __init__(self, app_spec: AppSpec, runner: Optional[Any] = None):
        """Initialize UIApp.

        Args:
            app_spec: Immutable application specification
            runner: Optional runner instance (CLIRunner, GUIRunner, etc.)
        """
        self.app_spec = app_spec
        self.runner = runner

        # Session state
        self.current_command: Optional[CommandSpec] = None
        self.execution_history: list[ExecutionRecord] = []

        # Event subscribers
        self._event_handlers: list[Callable[[Event], None]] = []
        self._event_queue: asyncio.Queue = asyncio.Queue()
        self._event_loop_task: Optional[asyncio.Task] = None

    async def start(self) -> None:
        """Start the UIApp event loop."""
        self._event_loop_task = asyncio.create_task(self._event_loop())

    async def stop(self) -> None:
        """Stop the UIApp event loop."""
        if self._event_loop_task:
            self._event_loop_task.cancel()
            try:
                await self._event_loop_task
            except asyncio.CancelledError:
                pass

    async def _event_loop(self) -> None:
        """Event processing loop."""
        while True:
            try:
                event = await self._event_queue.get()
                await self._process_event(event)
            except asyncio.CancelledError:
                break
            except Exception as e:
                print(f"Error processing event: {e}")

    async def _process_event(self, event: Event) -> None:
        """Process a single event.

        Args:
            event: Event to process
        """
        for handler in self._event_handlers:
            try:
                if asyncio.iscoroutinefunction(handler):
                    await handler(event)
                else:
                    handler(event)
            except Exception as e:
                print(f"Error in event handler: {e}")

    async def emit_event(self, event: Event) -> None:
        """Emit an event to all subscribers.

        Args:
            event: Event to emit
        """
        await self._event_queue.put(event)

    def subscribe(self, handler: Callable[[Event], None]) -> None:
        """Subscribe to events.

        Args:
            handler: Callback function (sync or async)
        """
        self._event_handlers.append(handler)

    def unsubscribe(self, handler: Callable[[Event], None]) -> None:
        """Unsubscribe from events.

        Args:
            handler: Callback function to remove
        """
        if handler in self._event_handlers:
            self._event_handlers.remove(handler)

    async def select_command(self, command_name: str) -> None:
        """Select a command.

        Args:
            command_name: Name of command to select
        """
        command_spec = self._find_command(command_name)
        if not command_spec:
            await self.emit_event(
                ErrorRaised(
                    exception=ValueError(f"Command not found: {command_name}"),
                    traceback="",
                    context="command_selection",
                    severity="error",
                )
            )
            return

        self.current_command = command_spec
        await self.emit_event(CommandSelected(command_name=command_name))

    async def run_command(self, **kwargs) -> Any:
        """Execute the currently selected command.

        Args:
            **kwargs: Parameter values

        Returns:
            Command result
        """
        if not self.current_command:
            await self.emit_event(
                ErrorRaised(
                    exception=ValueError("No command selected"),
                    traceback="",
                    context="execution",
                    severity="error",
                )
            )
            return None

        start_time = time.time()

        # Emit start event
        await self.emit_event(
            CommandStarted(
                command_name=self.current_command.name,
                params=kwargs,
            )
        )

        result = None
        exception = None
        success = False

        try:
            # Execute via runner if available
            if self.runner:
                result, exception = await self.runner.execute_command(
                    self.current_command.name, kwargs
                )
                success = exception is None
            else:
                # Direct execution fallback
                result = self.current_command.callback(**kwargs)
                if asyncio.iscoroutine(result):
                    result = await result
                success = True

        except Exception as e:
            exception = e
            success = False
            await self.emit_event(
                ErrorRaised(
                    exception=e,
                    traceback="",
                    context="execution",
                    severity="error",
                )
            )

        duration = time.time() - start_time

        # Record execution
        record = ExecutionRecord(
            command_name=self.current_command.name,
            params=kwargs,
            result=result,
            success=success,
            duration=duration,
            error=exception,
        )
        self.execution_history.append(record)

        # Emit finish event
        await self.emit_event(
            CommandFinished(
                command_name=self.current_command.name,
                result=result,
                success=success,
                duration=duration,
                error=exception,
            )
        )

        return result

    async def include_command(self, command_name: str, **kwargs) -> Any:
        """Execute a command inline without changing selection.

        Args:
            command_name: Name of command to execute
            **kwargs: Parameter values

        Returns:
            Command result
        """
        command_spec = self._find_command(command_name)
        if not command_spec:
            await self.emit_event(
                ErrorRaised(
                    exception=ValueError(f"Command not found: {command_name}"),
                    traceback="",
                    context="execution",
                    severity="error",
                )
            )
            return None

        # Temporarily save current command
        saved_command = self.current_command
        self.current_command = command_spec

        try:
            result = await self.run_command(**kwargs)
            return result
        finally:
            # Restore previous command
            self.current_command = saved_command

    async def clear(self) -> None:
        """Clear output for current command."""
        # This is now handled by the runner via events
        # UIApp just emits an intent
        pass

    def _find_command(self, command_name: str) -> Optional[CommandSpec]:
        """Find command by name.

        Args:
            command_name: Command name

        Returns:
            CommandSpec or None
        """
        for cmd in self.app_spec.commands:
            if cmd.name == command_name:
                return cmd
        return None

    def get_command(self, command_name: str) -> Optional['UICommand']:
        """Get UICommand wrapper by name.

        Args:
            command_name: Command name

        Returns:
            UICommand instance or None
        """
        command_spec = self._find_command(command_name)
        if command_spec:
            return UICommand(self, command_spec)
        return None

    @property
    def commands(self) -> list['UICommand']:
        """Get all commands as UICommand wrappers.

        Returns:
            List of UICommand instances
        """
        return [UICommand(self, cmd) for cmd in self.app_spec.commands]


class UICommand:
    """Wrapper for command operations."""

    def __init__(self, ui_app: UIApp, command_spec: CommandSpec):
        """Initialize UICommand.

        Args:
            ui_app: Parent UIApp instance
            command_spec: Command specification
        """
        self.ui_app = ui_app
        self.command_spec = command_spec

    @property
    def name(self) -> str:
        """Get command name."""
        return self.command_spec.name

    async def select(self) -> None:
        """Select this command."""
        await self.ui_app.select_command(self.command_spec.name)

    async def run(self, **kwargs) -> Any:
        """Select and execute this command.

        Args:
            **kwargs: Parameter values

        Returns:
            Command result
        """
        await self.select()
        return await self.ui_app.run_command(**kwargs)

    async def include(self, **kwargs) -> Any:
        """Execute this command inline.

        Args:
            **kwargs: Parameter values

        Returns:
            Command result
        """
        return await self.ui_app.include_command(self.command_spec.name, **kwargs)

    async def clear(self) -> None:
        """Clear output for this command."""
        await self.ui_app.clear()
