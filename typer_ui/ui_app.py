"""UIApp - Simple synchronous application controller."""

from typing import Any, Optional
from .specs import AppSpec, CommandSpec


class UICommand:
    """Wrapper for command operations."""

    def __init__(self, app: 'UIApp', command_spec: CommandSpec):
        """Initialize UICommand.

        Args:
            app: Parent UIApp instance
            command_spec: Command specification
        """
        self.app = app
        self.command_spec = command_spec
        self.name = command_spec.name

    def select(self) -> None:
        """Select this command (sets it as current)."""
        self.app.current_command = self.command_spec

    def run(self, **kwargs) -> Any:
        """Execute this command with parameters.

        Captures output separately from current context.

        Args:
            **kwargs: Parameter values

        Returns:
            Command result
        """
        # Execute via runner if available
        if self.app.runner:
            result, error = self.app.runner.execute_command(
                self.command_spec.name, kwargs
            )
            if error:
                raise error
            return result
        else:
            # Direct execution fallback
            return self.command_spec.callback(**kwargs)

    def include(self, **kwargs) -> Any:
        """Execute this command inline within current context.

        Output appears in the current command's output area.

        Args:
            **kwargs: Parameter values

        Returns:
            Command result
        """
        # Save current command
        saved_command = self.app.current_command

        try:
            # Temporarily set this as current
            self.app.current_command = self.command_spec

            # Execute directly (output goes to current context)
            if self.command_spec.callback:
                return self.command_spec.callback(**kwargs)
        finally:
            # Restore previous command
            self.app.current_command = saved_command


class UIApp:
    """Central controller for UI applications.

    Provides simple API for command selection and execution.
    """

    def __init__(self, app_spec: AppSpec, runner: Optional[Any] = None):
        """Initialize UIApp.

        Args:
            app_spec: Immutable application specification
            runner: Optional runner instance (CLIRunner, GUIRunner, etc.)
        """
        self.app_spec = app_spec
        self.runner = runner
        self.current_command: Optional[CommandSpec] = None

    def command(self, name: Optional[str] = None) -> Optional[UICommand]:
        """Get a command by name or return the current command.

        Args:
            name: Command name (optional). If None, returns current command.

        Returns:
            UICommand instance or None

        Examples:
            >>> # Get command by name
            >>> app.command("fetch-data").run(source="api")

            >>> # Get current command
            >>> current = app.command()
        """
        if name is None:
            # Return current command
            if self.current_command:
                return UICommand(self, self.current_command)
            return None

        # Find command by name
        command_spec = self._find_command(name)
        if command_spec:
            return UICommand(self, command_spec)
        return None

    def _find_command(self, command_name: str) -> Optional[CommandSpec]:
        """Find command spec by name.

        Args:
            command_name: Command name

        Returns:
            CommandSpec or None
        """
        for cmd in self.app_spec.commands:
            if cmd.name == command_name:
                return cmd
        return None

    @property
    def commands(self) -> list[UICommand]:
        """Get all commands as UICommand wrappers.

        Returns:
            List of UICommand instances
        """
        return [UICommand(self, cmd) for cmd in self.app_spec.commands]
