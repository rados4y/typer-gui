"""UIApp - Simple synchronous application controller."""

from typing import Any, Optional
from .specs import AppSpec, CommandSpec


class UICommand:
    """Wrapper for command operations.

    Supports method chaining for convenient access to output:
        ui.runtime.command("fetch").run(x=10).out  # Execute and get output

    Attributes:
        name: Command name
        result: Return value from last run() or include()
        out: Property - captured text output (chainable)
    """

    def __init__(self, app: 'UIApp', command_spec: CommandSpec):
        """Initialize UICommand.

        Args:
            app: Parent UIApp instance
            command_spec: Command specification
        """
        self.app = app
        self.command_spec = command_spec
        self.name = command_spec.name
        self._output: Optional[str] = None  # Internal captured output
        self.result: Any = None  # Return value from last run()

    @property
    def out(self) -> str:
        """Get captured output from last run().

        Returns empty string if no output captured yet.

        Example:
            >>> # Get current command output
            >>> output = ui.runtime.command().out
            >>>
            >>> # Chain after run()
            >>> output = ui.runtime.command("fetch").run(x=10).out
        """
        return self._output or ""

    def select(self) -> 'UICommand':
        """Select this command (sets it as current).

        In GUI mode, this changes the displayed command form.
        In CLI mode, this has no visible effect.

        Returns:
            Self for chaining
        """
        self.app.current_command = self.command_spec
        return self

    def clear(self) -> 'UICommand':
        """Clear output for this command.

        Returns:
            Self for chaining
        """
        self._output = None
        self.result = None
        return self

    def run(self, **kwargs) -> 'UICommand':
        """Execute this command with parameters.

        Captures output separately from current context.
        Returns self for method chaining.

        Args:
            **kwargs: Parameter values

        Returns:
            Self (for chaining .out, .result, etc.)

        Example:
            >>> # Chain to get output
            >>> output = ui.runtime.command("fetch").run(source="api").out
            >>>
            >>> # Chain to get result
            >>> result = ui.runtime.command("fetch").run(source="api").result
            >>>
            >>> # Use in button lambda
            >>> ui(tg.Button("Copy",
            ...     on_click=lambda: ui.clipboard(
            ...         ui.runtime.command("fetch").run(source="api").out
            ...     )))
        """
        # Execute via runner if available
        if self.app.runner:
            result, error, output = self.app.runner.execute_command(
                self.command_spec.name, kwargs
            )
            self.result = result
            self._output = output
            if error:
                raise error
        else:
            # Direct execution fallback
            result = self.command_spec.callback(**kwargs)
            self.result = result
            self._output = ""  # No output capture without runner

        return self  # Return self for chaining

    def include(self, **kwargs) -> 'UICommand':
        """Execute this command inline within current context.

        Output appears in the current command's output area.
        Returns self for method chaining.

        Args:
            **kwargs: Parameter values

        Returns:
            Self (for chaining .result, etc.)

        Example:
            >>> # Execute inline and get result
            >>> result = ui.runtime.command("process").include().result
        """
        # Save current command
        saved_command = self.app.current_command

        try:
            # Temporarily set this as current
            self.app.current_command = self.command_spec

            # Execute directly (output goes to current context)
            if self.command_spec.callback:
                result = self.command_spec.callback(**kwargs)
                self.result = result
                # Note: output is shown inline, not captured separately
        finally:
            # Restore previous command
            self.app.current_command = saved_command

        return self  # Return self for chaining


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
