"""CLI runner for command-line execution."""

import sys
from io import StringIO
from contextlib import redirect_stdout, redirect_stderr
from typing import Any, Optional

from .base import Runner
from ..specs import AppSpec, CommandSpec
from ..ui_blocks import Text, set_current_runner


class CLIRunner(Runner):
    """Runner for CLI environment.

    Executes commands directly from command line and prints output.
    """

    def __init__(self, app_spec: AppSpec):
        super().__init__(app_spec)
        self._verbose = False
        self.channel = "cli"

    def start(self) -> None:
        """Start CLI runner (no-op for CLI, execution is synchronous)."""
        pass

    def show(self, component) -> None:
        """Show component in CLI by calling its show_cli method.

        Args:
            component: UiBlock component to display
        """
        component.show_cli(self)

    def update(self, component) -> None:
        """Update component (for progressive rendering in context managers).

        Args:
            component: UiBlock component to update
        """
        # In CLI, we can't really update in place, so just clear and re-show
        # Could use terminal control codes for better UX in the future
        print()  # Add newline for separation
        component.show_cli(self)

    def execute_command(
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

        # Set this runner as current so ui.out() works
        set_current_runner(self)

        # Capture stdout/stderr
        stdout_capture = StringIO()
        stderr_capture = StringIO()

        result = None
        exception = None

        try:
            with redirect_stdout(stdout_capture), redirect_stderr(stderr_capture):
                # Call the command callback directly
                result = command_spec.callback(**params)

        except Exception as e:
            exception = e

        # Print captured output
        stdout_text = stdout_capture.getvalue()
        if stdout_text:
            # Convert print statements to Text components
            for line in stdout_text.rstrip('\n').split('\n'):
                if line:
                    Text(line).show_cli(self)

        stderr_text = stderr_capture.getvalue()
        if stderr_text:
            print(stderr_text, file=sys.stderr, end='')

        # Handle return value - auto-display if it's a UiBlock
        if result is not None:
            from ..ui_blocks import UiBlock
            if isinstance(result, UiBlock):
                self.show(result)

        # Clear runner reference
        set_current_runner(None)

        return result, exception

    def set_verbose(self, verbose: bool) -> None:
        """Enable/disable verbose output.

        Args:
            verbose: Whether to show verbose messages
        """
        self._verbose = verbose
