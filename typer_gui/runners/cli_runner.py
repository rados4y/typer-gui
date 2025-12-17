"""CLI runner for command-line execution."""

import asyncio
import sys
from io import StringIO
from contextlib import redirect_stdout, redirect_stderr
from typing import Any, Optional

from .base import Runner
from ..specs import AppSpec, CommandSpec
from ..events import (
    Event,
    CommandStarted,
    CommandFinished,
    TextEmitted,
    BlockEmitted,
    ErrorRaised,
)


class CLIRunner(Runner):
    """Runner for CLI environment.

    Executes commands directly from command line and prints output.
    """

    def __init__(self, app_spec: AppSpec):
        super().__init__(app_spec)
        self._verbose = False

    async def start(self) -> None:
        """Start CLI runner (no-op for CLI, execution is synchronous)."""
        # CLI doesn't need async start loop
        pass

    async def handle_event(self, event: Event) -> None:
        """Handle event by printing to stdout.

        Args:
            event: Event to handle
        """
        if isinstance(event, TextEmitted):
            # Print text directly
            stream = sys.stderr if event.stream == "stderr" else sys.stdout
            print(event.text, file=stream, end="")
        elif isinstance(event, BlockEmitted):
            # In CLI, blocks are just printed as text
            print(str(event.block))
        elif isinstance(event, CommandStarted):
            if self._verbose:
                print(f"Running command: {event.command_name}", file=sys.stderr)
        elif isinstance(event, CommandFinished):
            if event.error and self._verbose:
                print(f"Command failed: {event.error}", file=sys.stderr)
        elif isinstance(event, ErrorRaised):
            print(f"Error: {event.exception}", file=sys.stderr)

    async def execute_command(
        self,
        command_name: str,
        params: dict[str, Any]
    ) -> tuple[Any, Optional[Exception]]:
        """Execute command callback with stdout/stderr capture.

        Args:
            command_name: Name of command to execute
            params: Parameter values

        Returns:
            Tuple of (result, exception)
        """
        # Find command spec
        command_spec: Optional[CommandSpec] = None
        for cmd in self.app_spec.commands:
            if cmd.name == command_name:
                command_spec = cmd
                break

        if not command_spec:
            error = ValueError(f"Command not found: {command_name}")
            return None, error

        # Capture stdout/stderr
        stdout_capture = StringIO()
        stderr_capture = StringIO()

        result = None
        exception = None

        try:
            with redirect_stdout(stdout_capture), redirect_stderr(stderr_capture):
                # Call the command callback directly
                result = command_spec.callback(**params)

                # If result is awaitable, await it
                if asyncio.iscoroutine(result):
                    result = await result

        except Exception as e:
            exception = e

        # Emit captured output as events
        if self.ui_app:
            stdout_text = stdout_capture.getvalue()
            if stdout_text:
                await self.ui_app.emit_event(
                    TextEmitted(text=stdout_text, stream="stdout")
                )

            stderr_text = stderr_capture.getvalue()
            if stderr_text:
                await self.ui_app.emit_event(
                    TextEmitted(text=stderr_text, stream="stderr")
                )

        return result, exception

    def set_verbose(self, verbose: bool) -> None:
        """Enable/disable verbose output.

        Args:
            verbose: Whether to show verbose messages
        """
        self._verbose = verbose
