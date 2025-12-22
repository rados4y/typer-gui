"""CLI runner for command-line execution."""

import sys
from io import StringIO
from contextlib import redirect_stdout, redirect_stderr
from typing import Any, Optional

from .base import Runner
from ..specs import AppSpec, CommandSpec
from ..ui_blocks import Text, set_current_runner
from ..ui_app import UIApp


class CLIRunner(Runner):
    """Runner for CLI environment.

    Executes commands directly from command line and prints output.
    """

    def __init__(self, app_spec: AppSpec, ui_app: Optional[UIApp] = None):
        super().__init__(app_spec)
        self._verbose = False
        self.channel = "cli"
        self.ui_app = ui_app or UIApp(app_spec, self)

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

        # Set current command in UIApp
        self.ui_app.current_command = command_spec

        # Capture stdout/stderr and UI components
        stdout_capture = StringIO()
        stderr_capture = StringIO()
        output_lines = []  # Capture rendered text output

        # Temporarily replace show method to capture output
        original_show = self.show

        def capturing_show(component):
            """Capture text representation while showing."""
            # Capture the text output by temporarily redirecting stdout
            text_capture = StringIO()
            with redirect_stdout(text_capture):
                # Call the component's show_cli directly
                component.show_cli(self)
            captured = text_capture.getvalue()
            if captured:
                output_lines.append(captured.rstrip('\n'))

        self.show = capturing_show

        result = None
        exception = None

        try:
            with redirect_stdout(stdout_capture), redirect_stderr(stderr_capture):
                # Call the command callback directly
                result = command_spec.callback(**params)

        except Exception as e:
            exception = e
        finally:
            # Restore original show method AFTER capturing output
            self.show = original_show

        # Capture print statements as output lines
        stdout_text = stdout_capture.getvalue()
        if stdout_text:
            # Add print statements to output
            for line in stdout_text.rstrip('\n').split('\n'):
                if line:
                    output_lines.append(line)

        # Print everything for display (using restored show method)
        if stdout_text:
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
                # Capture output from returned UiBlock
                text_capture = StringIO()
                with redirect_stdout(text_capture):
                    result.show_cli(self)
                captured = text_capture.getvalue()
                if captured:
                    output_lines.append(captured.rstrip('\n'))

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
