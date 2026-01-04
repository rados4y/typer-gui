"""CLI runner for command-line execution."""

import asyncio
import inspect
import sys
from io import StringIO
from contextlib import redirect_stdout, redirect_stderr
from typing import Any, Optional, Callable

from .base import Runner
from .cli_context import CLIRunnerCtx
from ..specs import AppSpec, CommandSpec
from ..ui_blocks import Text, set_current_runner


class _PassThroughWriter(StringIO):
    """Custom writer that both captures and immediately displays output."""

    def __init__(self, display_callback: Callable[[str], None]):
        """Initialize the writer.

        Args:
            display_callback: Function to call with each line to display it
        """
        super().__init__()
        self.display_callback = display_callback
        self._buffer = ""

    def write(self, text: str) -> int:
        """Write text, capturing it and displaying complete lines immediately.

        Args:
            text: Text to write

        Returns:
            Number of characters written
        """
        # Capture in buffer for later retrieval
        result = super().write(text)

        # Also display immediately (line by line)
        self._buffer += text

        # Process complete lines
        while '\n' in self._buffer:
            line, self._buffer = self._buffer.split('\n', 1)
            self.display_callback(line)

        return result

    def flush(self):
        """Flush any remaining buffer."""
        super().flush()
        # Display any remaining partial line
        if self._buffer:
            self.display_callback(self._buffer)
            self._buffer = ""


class CLIRunner(Runner):
    """Runner for CLI environment.

    Executes commands directly from command line and prints output.
    """

    def __init__(self, app_spec: AppSpec, ui: Optional[Any] = None):
        super().__init__(app_spec)
        self._verbose = False
        self.channel = "cli"
        self.ui = ui

        # New architecture: CLIRunnerCtx instance
        self.ctx = CLIRunnerCtx()
        from ..context import UIRunnerCtx
        UIRunnerCtx._current_instance = self.ctx  # Set as global instance

        # Reactive components (for compatibility with GUI runner)
        self._reactive_components = {}

    def start(self) -> None:
        """Start CLI runner (no-op for CLI, execution is synchronous)."""
        pass

    def update_reactive_component(self, component_id: int, new_component) -> None:
        """Update a reactive component (no-op in CLI mode).

        In CLI mode, reactive updates aren't displayed since output is static.
        This method exists for compatibility with the reactive state system.

        Args:
            component_id: Unique ID of the component
            new_component: New component instance
        """
        # No-op for CLI - reactive updates only make sense in GUI
        pass

    def is_reactive_mode(self) -> bool:
        """Check if in reactive mode (always False for CLI).

        Returns:
            False - CLI doesn't support reactive containers
        """
        return False

    def execute_command(
        self,
        command_name: str,
        params: dict[str, Any]
    ) -> tuple[Any, Optional[Exception], str]:
        """Execute command callback with stdout/stderr capture.

        Args:
            command_name: Name of command to execute
            params: Parameter values

        Returns:
            Tuple of (result, exception, output_text)
        """
        # Find command spec
        command_spec: Optional[CommandSpec] = None
        for cmd in self.app_spec.commands:
            if cmd.name == command_name:
                command_spec = cmd
                break

        if not command_spec:
            error = ValueError(f"Command not found: {command_name}")
            return None, error, ""

        # Save current runner for nested execution support
        from ..ui_blocks import get_current_runner
        saved_runner = get_current_runner()

        # Set this runner as current so ui() works
        set_current_runner(self)

        # Set current command in Ui
        if self.ui:
            self.ui.current_command = command_spec

        # Set context as current instance
        from ..context import UIRunnerCtx
        UIRunnerCtx._current_instance = self.ctx

        # Create root component for build_child() hierarchy
        from ..ui_blocks import Column
        root = Column([])

        # Capture output lines for cmd.output property
        output_lines = []  # Capture rendered text output

        # Create pass-through writer for print() statements
        # This displays print() output immediately while also capturing it
        def display_print_line(line: str):
            """Display a line from print() and capture it."""
            output_lines.append(line)
            # Print directly to avoid recursion (don't go through runner.show)
            print(line, file=sys.__stdout__)

        stdout_writer = _PassThroughWriter(display_print_line)
        stderr_capture = StringIO()

        result = None
        exception = None

        try:
            # Execute command with UI stack context
            with self.ctx._new_ui_stack() as ui_stack:
                with redirect_stdout(stdout_writer), redirect_stderr(stderr_capture):
                    # Call the command callback directly
                    # Async commands are already wrapped by def_command decorator
                    result = command_spec.callback(**params)

                    # Flush any remaining buffered output
                    stdout_writer.flush()

                # If command returns a value, add it to stack
                if result is not None:
                    ui_stack.append(result)

            # Process UI stack - build and print each item
            for item in ui_stack:
                # Capture the rendered output
                text_capture = StringIO()
                with redirect_stdout(text_capture):
                    # Build renderable from item
                    renderable = self.ctx.build_child(root, item)
                    # Print using Rich console
                    self.ctx.console.print(renderable)

                captured = text_capture.getvalue()
                if captured:
                    output_lines.append(captured.rstrip('\n'))
                    # Also print to stdout
                    print(captured.rstrip('\n'), file=sys.__stdout__)

        except Exception as e:
            exception = e

        stderr_text = stderr_capture.getvalue()
        if stderr_text:
            print(stderr_text, file=sys.stderr, end='')

        # Restore previous runner (for nested execution support)
        set_current_runner(saved_runner)

        # Join all output lines
        output_text = '\n'.join(output_lines)

        return result, exception, output_text

    def set_verbose(self, verbose: bool) -> None:
        """Enable/disable verbose output.

        Args:
            verbose: Whether to show verbose messages
        """
        self._verbose = verbose
