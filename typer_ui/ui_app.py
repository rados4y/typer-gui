"""UiApp and UICommand - Main UI classes for typer-ui."""

from typing import Any, Callable, Optional, TYPE_CHECKING
import sys
import typer
import flet as ft

from .spec_builder import build_app_spec, _GUI_OPTIONS_ATTR
from .specs import CommandUiSpec, AppSpec, CommandSpec
from .runners.gui_runner import create_flet_app
from .runners.cli_runner import CLIRunner
from .ui_blocks import get_current_runner

if TYPE_CHECKING:
    pass


class UICommand:
    """Wrapper for command operations.

    Supports method chaining for convenient access to output:
        app.command("fetch").run(x=10).out  # Execute and get output

    Attributes:
        name: Command name
        result: Return value from last run() or include()
        out: Property - captured text output (chainable)
    """

    def __init__(self, ui_app: 'UiApp', command_spec: CommandSpec):
        """Initialize UICommand.

        Args:
            ui_app: Parent UiApp instance
            command_spec: Command specification
        """
        self.ui_app = ui_app
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
            >>> output = app.command().out
            >>>
            >>> # Chain after run()
            >>> output = app.command("fetch").run(x=10).out
        """
        return self._output or ""

    def select(self) -> 'UICommand':
        """Select this command (sets it as current).

        In GUI mode, this changes the displayed command form.
        In CLI mode, this has no visible effect.

        Returns:
            Self for chaining
        """
        self.ui_app.current_command = self.command_spec

        # Trigger GUI update if in GUI mode
        if self.ui_app.runner and hasattr(self.ui_app.runner, '_select_command'):
            runner = self.ui_app.runner
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
        if self.ui_app.runner and hasattr(self.ui_app.runner, 'output_view'):
            runner = self.ui_app.runner
            if runner.output_view:
                runner.output_view.controls.clear()
                if hasattr(runner, 'page') and runner.page:
                    runner.page.update()

        # Re-execute if auto-exec
        if self.command_spec.ui_spec.auto:
            # Execute the command again
            if self.ui_app.runner and hasattr(self.ui_app.runner, 'page') and self.ui_app.runner.page:
                # In GUI mode, use async execution
                async def re_execute():
                    await self.ui_app.runner._run_command()

                self.ui_app.runner.page.run_task(re_execute)
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
            >>> output = app.command("fetch").run(source="api").out
            >>>
            >>> # Chain to get result
            >>> result = app.command("fetch").run(source="api").result
            >>>
            >>> # Use in button lambda
            >>> ui(tu.Button("Copy",
            ...     on_click=lambda: app.clipboard(
            ...         app.command("fetch").run(source="api").out
            ...     )))
        """
        # Select command first (in GUI mode, this updates the form)
        self.select()

        # Execute via runner if available
        if self.ui_app.runner:
            result, error, output = self.ui_app.runner.execute_command(
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
            >>> result = app.command("process").include().result
        """
        # Save current command
        saved_command = self.ui_app.current_command

        try:
            # Temporarily set this as current
            self.ui_app.current_command = self.command_spec

            # Execute directly (output goes to current context)
            if self.command_spec.callback:
                result = self.command_spec.callback(**kwargs)
                self.result = result
                # Note: output is shown inline, not captured separately
        finally:
            # Restore previous command
            self.ui_app.current_command = saved_command

        return self  # Return self for chaining


class UiApp:
    """Main entry point for typer-ui - extension API for Typer apps.

    This class provides GUI-specific configuration on top of existing Typer applications.
    It works alongside Typer's decorators, not as a replacement.

    Example:
        >>> import typer
        >>> import typer_ui as tu
        >>> from typer_ui import ui, md, dx
        >>>
        >>> typer_app = typer.Typer()
        >>> app = tu.UiApp(
        >>>     typer_app,
        >>>     title="My Application",
        >>>     description="A demo app"
        >>> )
        >>>
        >>> @typer_app.command()
        >>> @app.def_command(button=True)
        >>> def greet(name: str):
        >>>     ui("# Hello!")
        >>>     print(f"Hello {name}!")
        >>>
        >>> if __name__ == "__main__":
        >>>     app()  # Callable pattern
    """

    def __init__(
        self,
        typer_app: typer.Typer,
        *,
        title: Optional[str] = None,
        description: Optional[str] = None,
    ):
        """Initialize the UI wrapper for a Typer app.

        Args:
            typer_app: The Typer application instance to extend
            title: Window title for the GUI
            description: Description text shown at the top of the GUI
        """
        self.title = title
        self.description = description
        self._typer_app = typer_app
        self._cli_mode = False

        # Runtime attributes (initialized when app starts)
        self.app_spec: Optional[AppSpec] = None
        self.runner: Optional[Any] = None
        self.current_command: Optional[CommandSpec] = None

    def clipboard(self, text: str) -> None:
        """Copy text to clipboard.

        Works in both GUI and CLI modes.
        In GUI mode, copies to system clipboard.
        In CLI mode, prints the text with a copy indicator.

        Args:
            text: Text to copy

        Example:
            >>> ui(tu.Button("Copy Result",
            ...     on_click=lambda: app.clipboard(str(result))))
        """
        runner = get_current_runner()
        if not runner:
            # Fallback if no runner available
            print(f"[CLIPBOARD] {text}")
            return

        if runner.channel == "gui":
            # GUI mode - copy to clipboard via Flet
            if hasattr(runner, 'page') and runner.page:
                runner.page.set_clipboard(text)
                # Show feedback
                from .ui_blocks import Text
                Text(f"✓ Copied to clipboard").show_gui(runner)
        else:
            # CLI mode - print with indicator
            print(f"[CLIPBOARD] {text}")

    def state(self, initial_value):
        """Create a reactive state object.

        State objects trigger automatic re-rendering of dependent UI components
        when their value changes via set().

        Args:
            initial_value: Initial state value

        Returns:
            State object that can be read (.value) and updated (.set())

        Example:
            >>> counter = app.state(0)
            >>> ui(dx(lambda: tu.Text(f"Count: {counter.value}"), counter))
            >>> counter.set(counter.value + 1)  # Triggers re-render

        Note:
            State is independent of the execution context and can be created
            outside of command functions if needed.
        """
        from .state import State

        return State(initial_value)

    def def_command(
        self,
        *,
        button: bool = False,
        long: bool = False,
        auto: bool = False,
        header: bool = True,
        submit_name: str = "Run Command",
        on_select: Optional[Callable] = None,
    ):
        """Decorator to add GUI-specific options to a Typer command.

        This decorator should be used alongside @app.command(), not instead of it.
        It only stores GUI metadata and doesn't affect Typer's behavior.

        Args:
            button: Display as a button in the left panel
            long: Enable real-time output streaming for long-running commands
            auto: Execute automatically when selected, hide submit button
            header: Show command name and description (default: True)
            submit_name: Text for the submit button (default: "Run Command")
            on_select: Callback function called when command is selected

        Example:
            >>> @typer_app.command()
            >>> @app.def_command(button=True, long=True)
            >>> def process():
            >>>     for i in range(10):
            >>>         print(f"Step {i}")
            >>>         time.sleep(1)
            >>>
            >>> @typer_app.command()
            >>> @app.def_command(auto=True, header=False)
            >>> def dashboard():
            >>>     ui("# Dashboard")  # Only output shown, no command header
        """

        def decorator(func: Callable) -> Callable:
            import asyncio
            import inspect

            # Store GUI options on the function
            setattr(
                func,
                _GUI_OPTIONS_ATTR,
                CommandUiSpec(
                    button=button,
                    long=long,
                    auto=auto,
                    header=header,
                    submit_name=submit_name,
                    on_select=on_select,
                ),
            )

            # If the function is async, wrap it for Typer compatibility
            # Typer will call it synchronously, so we need to handle async execution
            if inspect.iscoroutinefunction(func):
                def sync_wrapper(*args, **kwargs):
                    return asyncio.run(func(*args, **kwargs))

                # Copy over the GUI options to the wrapper
                setattr(sync_wrapper, _GUI_OPTIONS_ATTR, getattr(func, _GUI_OPTIONS_ATTR))

                # Store reference to original async function
                setattr(sync_wrapper, '_original_async_func', func)

                # Copy function metadata
                sync_wrapper.__name__ = func.__name__
                sync_wrapper.__doc__ = func.__doc__
                sync_wrapper.__annotations__ = func.__annotations__
                sync_wrapper.__signature__ = inspect.signature(func)

                return sync_wrapper

            return func

        return decorator

    def command(self, name: Optional[str] = None):
        """Get a command by name or return the current command.

        Args:
            name: Command name (optional). If None, returns current command.

        Returns:
            UICommand instance or None

        Examples:
            >>> # Get command by name
            >>> app.command("fetch-data").run(source="api")
            >>>
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
        if not self.app_spec:
            return None

        for cmd in self.app_spec.commands:
            if cmd.name == command_name:
                return cmd
        return None

    @property
    def commands(self):
        """Get all commands as UICommand wrappers.

        Returns:
            List of UICommand instances
        """
        if not self.app_spec:
            return []

        return [UICommand(self, cmd) for cmd in self.app_spec.commands]

    def __call__(self):
        """Launch the GUI application or CLI based on --cli flag.

        This should be called at the end of your script to start the GUI.
        If --cli flag is present in command line arguments, the GUI is bypassed
        and the Typer CLI is executed directly.

        Example:
            >>> if __name__ == "__main__":
            >>>     app()  # Launches GUI
            >>>     # Or use: python script.py --cli command arg1 arg2
        """
        # Check if --cli flag is present
        if "--cli" in sys.argv:
            self._cli_mode = True

            # Remove --cli flag from arguments
            sys.argv.remove("--cli")

            # Build app spec
            self.app_spec = build_app_spec(
                self._typer_app,
                title=self.title,
                description=self.description
            )

            # Create CLI runner and set as current
            from .ui_blocks import set_current_runner
            cli_runner = CLIRunner(self.app_spec, self)

            # Set the runner
            self.runner = cli_runner

            set_current_runner(cli_runner)

            try:
                # Run the Typer CLI directly
                self._typer_app()
            finally:
                # Clear runner reference
                set_current_runner(None)
        else:
            # Launch the GUI
            self._run_gui()

    def _run_gui(self):
        """Internal method to launch the GUI."""
        # Build the GUI model from the Typer app
        self.app_spec = build_app_spec(
            self._typer_app,
            title=self.title,
            description=self.description
        )

        # Create the Flet app function
        flet_main = create_flet_app(self.app_spec, self)

        # Run the Flet app
        ft.app(target=flet_main)

    @property
    def is_cli_mode(self) -> bool:
        """Check if running in CLI mode.

        Returns:
            True if in CLI mode, False if in GUI mode.
        """
        return self._cli_mode

    @property
    def typer_app(self) -> typer.Typer:
        """Access the underlying Typer application.

        This allows advanced usage if you need direct access to the Typer app.
        """
        return self._typer_app
