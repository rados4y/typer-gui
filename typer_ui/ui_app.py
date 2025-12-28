"""UICommand - Command wrapper for execution control."""

from typing import Any, Optional, TYPE_CHECKING
from .specs import CommandSpec

if TYPE_CHECKING:
    from .ui import Ui


class UICommand:
    """Wrapper for command operations.

    Supports method chaining for convenient access to output:
        ui.command("fetch").run(x=10).out  # Execute and get output

    Attributes:
        name: Command name
        result: Return value from last run() or include()
        out: Property - captured text output (chainable)
    """

    def __init__(self, ui: 'Ui', command_spec: CommandSpec):
        """Initialize UICommand.

        Args:
            ui: Parent Ui instance
            command_spec: Command specification
        """
        self.ui = ui
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
            >>> output = ui.command().out
            >>>
            >>> # Chain after run()
            >>> output = ui.command("fetch").run(x=10).out
        """
        return self._output or ""

    def select(self) -> 'UICommand':
        """Select this command (sets it as current).

        In GUI mode, this changes the displayed command form.
        In CLI mode, this has no visible effect.

        Returns:
            Self for chaining
        """
        self.ui.current_command = self.command_spec

        # Trigger GUI update if in GUI mode
        if self.ui.runner and hasattr(self.ui.runner, '_select_command'):
            runner = self.ui.runner
            # Use page.run_task if available (Flet GUI mode)
            if hasattr(runner, 'page') and runner.page:
                async def do_select():
                    await runner._select_command(self.command_spec)
                runner.page.run_task(do_select)

        return self

    def clear(self) -> 'UICommand':
        """Clear output for this command.

        If command is auto-exec, re-executes it after clearing.

        Returns:
            Self for chaining
        """
        # Clear internal state
        self._output = None
        self.result = None

        # Clear GUI output if in GUI mode
        if self.ui.runner and hasattr(self.ui.runner, 'output_view'):
            runner = self.ui.runner
            if runner.output_view:
                runner.output_view.controls.clear()
                if hasattr(runner, 'page') and runner.page:
                    runner.page.update()

        # Re-execute if auto-exec
        if self.command_spec.ui_spec.is_auto_exec:
            # Execute the command again
            if self.ui.runner and hasattr(self.ui.runner, 'page') and self.ui.runner.page:
                # In GUI mode, use async execution
                async def re_execute():
                    await self.ui.runner._run_command()

                self.ui.runner.page.run_task(re_execute)
            else:
                # In CLI mode or no runner, direct execution
                if self.command_spec.callback:
                    self.result = self.command_spec.callback()

        return self

    def run(self, **kwargs) -> 'UICommand':
        """Execute this command with parameters.

        In GUI mode, selects the command first (changes form), then executes.
        Captures output separately from current context.
        Returns self for method chaining.

        Args:
            **kwargs: Parameter values

        Returns:
            Self (for chaining .out, .result, etc.)

        Example:
            >>> # Chain to get output
            >>> output = ui.command("fetch").run(source="api").out
            >>>
            >>> # Chain to get result
            >>> result = ui.command("fetch").run(source="api").result
            >>>
            >>> # Use in button lambda
            >>> ui(tg.Button("Copy",
            ...     on_click=lambda: ui.clipboard(
            ...         ui.command("fetch").run(source="api").out
            ...     )))
        """
        # Select command first (in GUI mode, this updates the form)
        self.select()

        # Execute via runner if available
        if self.ui.runner:
            result, error, output = self.ui.runner.execute_command(
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
            >>> result = ui.command("process").include().result
        """
        # Save current command
        saved_command = self.ui.current_command

        try:
            # Temporarily set this as current
            self.ui.current_command = self.command_spec

            # Execute directly (output goes to current context)
            if self.command_spec.callback:
                result = self.command_spec.callback(**kwargs)
                self.result = result
                # Note: output is shown inline, not captured separately
        finally:
            # Restore previous command
            self.ui.current_command = saved_command

        return self  # Return self for chaining
