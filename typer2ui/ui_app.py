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

    def __init__(self, ui_app: 'UiApp', command_spec: CommandSpec, tab_name: Optional[str] = None):
        """Initialize UICommand.

        Args:
            ui_app: Parent UiApp instance
            command_spec: Command specification
            tab_name: Optional tab/sub-app name for context
        """
        self.ui_app = ui_app
        self.command_spec = command_spec
        self.name = command_spec.name
        self.tab_name = tab_name  # Track which tab this command belongs to
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

            # Set tab context if this command has a tab
            if self.tab_name is not None and hasattr(runner, 'current_tab'):
                runner.current_tab = self.tab_name

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
        import asyncio
        import inspect

        # Select command first (in GUI mode, this updates the form)
        self.select()

        # Execute via runner if available
        if self.ui_app.runner:
            # Check if execute_command is async (GUI mode) or sync (CLI mode)
            exec_result = self.ui_app.runner.execute_command(
                self.command_spec.name, kwargs
            )

            # Handle async execution (GUI mode)
            if inspect.iscoroutine(exec_result):
                # In GUI mode, schedule async execution
                runner = self.ui_app.runner
                if hasattr(runner, 'page') and runner.page:
                    async def do_run():
                        result, error, output = await exec_result
                        self.result = result
                        self._output = output
                        if error:
                            raise error
                    runner.page.run_task(do_run)
                else:
                    # Fallback: run async in new event loop (shouldn't happen)
                    result, error, output = asyncio.run(exec_result)
                    self.result = result
                    self._output = output
                    if error:
                        raise error
            else:
                # Sync execution (CLI mode)
                result, error, output = exec_result
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
        # Execute via runner if available (ensures proper stack context)
        if self.ui_app.runner:
            # Use runner's execution mechanism with stack context
            from .context import _current_stack_var

            # Get the runner's context
            if hasattr(self.ui_app.runner, 'ctx'):
                ctx = self.ui_app.runner.ctx

                # Execute with new stack context
                with ctx.new_ui_stack() as ui_stack:
                    # Execute callback - ui() calls will append to this stack
                    if self.command_spec.callback:
                        result = self.command_spec.callback(**kwargs)
                        self.result = result
                        if result is not None:
                            ui_stack.append(result)

                # Build and display output inline
                from .ui_blocks import Column
                root = Column([])
                for item in ui_stack:
                    control = ctx.build_child(root, item)
                    self.ui_app.runner.add_to_output(control)

                # Update display
                if hasattr(ctx, 'page') and ctx.page:
                    ctx.page.update()
            else:
                # Fallback: direct execution
                result = self.command_spec.callback(**kwargs)
                self.result = result
        else:
            # No runner available - direct execution fallback
            if self.command_spec.callback:
                result = self.command_spec.callback(**kwargs)
                self.result = result

        return self  # Return self for chaining


class UiApp:
    """Main entry point for typer-ui - extension API for Typer apps.

    This class provides GUI-specific configuration on top of existing Typer applications.
    It works alongside Typer's decorators, not as a replacement.

    Example:
        >>> import typer
        >>> import typer2ui as tu
        >>> from typer2ui import ui, md, dx
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
        runner: str = "gui",
        print2ui: bool = True,
        main_label: str = "main",
    ):
        """Initialize the UI wrapper for a Typer app.

        Args:
            typer_app: The Typer application instance to extend
            title: Window title for the GUI
            description: Description text shown at the top of the GUI
            runner: Default runner mode - "gui" (default, use --cli to switch) or "cli" (use --gui to switch)
            print2ui: If True (default), print() statements are captured and displayed in UI.
                      If False, print() goes directly to stdout (regular behavior)
            main_label: Label for the main/root commands tab when app has both main and sub-app commands (default: "main")
        """
        if runner not in ("gui", "cli"):
            raise ValueError(f"runner must be 'gui' or 'cli', got: {runner}")

        self.title = title
        self.description = description
        self._typer_app = typer_app
        self._runner_mode = runner
        self.print2ui = print2ui
        self.main_label = main_label
        self._cli_mode = False

        # Runtime attributes (initialized when app starts)
        self.app_spec: Optional[AppSpec] = None
        self.runner: Optional[Any] = None
        self.current_command: Optional[CommandSpec] = None

        # Hold object for accessing GUI internals
        from .hold import Hold
        self.hold = Hold(self)

        # Init callback (called when GUI starts)
        self._init_callback: Optional[Callable] = None

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
                # Show feedback using new architecture
                if hasattr(runner, 'ctx') and runner.ctx:
                    from .ui_blocks import Text
                    root = Text("")  # Dummy root
                    control = runner.ctx.build_child(root, "✓ Copied to clipboard")
                    runner.add_to_output(control)
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

    def init(self, func: Optional[Callable] = None):
        """Decorator to register a function that runs when GUI starts.

        The decorated function is called after the GUI page is initialized
        but before any commands are displayed. This is useful for:
        - Showing welcome dialogs
        - Initializing state
        - Setting up page-level customizations

        The function receives no arguments but can access:
        - upp.hold.page - The Flet Page object
        - All UiApp methods and state

        Example:
            >>> @upp.init()
            >>> def on_startup():
            >>>     import flet as ft
            >>>     # Show welcome dialog
            >>>     dlg = ft.AlertDialog(
            >>>         title=ft.Text("Welcome!"),
            >>>         content=ft.Text("Thanks for using our app")
            >>>     )
            >>>     upp.hold.page.dialog = dlg
            >>>     dlg.open = True
            >>>     upp.hold.page.update()

        Args:
            func: Function to call on GUI startup

        Returns:
            The decorated function
        """
        def decorator(f: Callable) -> Callable:
            self._init_callback = f
            return f

        if func is None:
            # Called with parentheses: @upp.init()
            return decorator
        else:
            # Called without parentheses: @upp.init
            return decorator(func)

    def def_command(
        self,
        *,
        button: bool = False,
        threaded: bool = True,
        auto: bool = False,
        header: bool = True,
        submit_name: str = "Run Command",
        on_select: Optional[Callable] = None,
        auto_scroll: bool = True,
        view: bool = False,
        modal: bool = False,
    ):
        """Decorator to add GUI-specific options to a Typer command.

        This decorator should be used alongside @app.command(), not instead of it.
        It only stores GUI metadata and doesn't affect Typer's behavior.

        Args:
            button: Display as a button in the left panel
            threaded: Run in background thread with real-time output streaming (default: True)
            auto: Execute automatically when selected, hide submit button
            header: Show command name and description (default: True)
            submit_name: Text for the submit button (default: "Run Command")
            on_select: Callback function called when command is selected
            auto_scroll: Automatically scroll to end of output (default: True)
            view: Convenience flag - sets auto=True, auto_scroll=False, header=False
                  (useful for dashboard/info screens)
            modal: Display parameters and results in a modal dialog (GUI only)

        Example:
            >>> @typer_app.command()
            >>> @app.def_command(button=True, threaded=True)
            >>> def process():
            >>>     for i in range(10):
            >>>         print(f"Step {i}")
            >>>         time.sleep(1)
            >>>
            >>> @typer_app.command()
            >>> @app.def_command(view=True)
            >>> def dashboard():
            >>>     ui("# Dashboard")  # Auto-executes, no header, no auto-scroll
            >>>
            >>> @typer_app.command()
            >>> @app.def_command(auto=True, header=False, auto_scroll=False)
            >>> def status():
            >>>     ui("# Status")  # Equivalent to view=True
        """

        def decorator(func: Callable) -> Callable:
            import asyncio
            import inspect

            # Handle view flag - overrides auto, header, and auto_scroll
            final_auto = auto
            final_header = header
            final_auto_scroll = auto_scroll

            if view:
                final_auto = True
                final_header = False
                final_auto_scroll = False

            # Store GUI options on the function
            setattr(
                func,
                _GUI_OPTIONS_ATTR,
                CommandUiSpec(
                    button=button,
                    threaded=threaded,
                    auto=final_auto,
                    header=final_header,
                    submit_name=submit_name,
                    on_select=on_select,
                    auto_scroll=final_auto_scroll,
                    modal=modal,
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

        Supports qualified names to specify sub-app (e.g., "users:create").
        If no qualifier, uses current tab context.

        Args:
            name: Command name or qualified name ("tab:command").
                  If None, returns current command.

        Returns:
            UICommand instance or None

        Examples:
            >>> # Get command by name (uses current tab)
            >>> app.command("fetch-data").run(source="api")
            >>>
            >>> # Get command with qualified name
            >>> app.command("users:create").run(name="John")
            >>>
            >>> # Get current command
            >>> current = app.command()
        """
        if name is None:
            # Return current command
            if self.current_command:
                # Determine tab for current command
                tab_name = None
                if self.runner and hasattr(self.runner, 'current_tab'):
                    tab_name = self.runner.current_tab
                return UICommand(self, self.current_command, tab_name)
            return None

        # Determine tab_name from qualified name
        tab_name = None
        if ":" in name:
            tab_name, _ = name.split(":", 1)

        # Find command by name
        command_spec = self._find_command(name)
        if command_spec:
            # If tab_name not specified in qualified name, get from runner
            if tab_name is None and self.runner and hasattr(self.runner, 'current_tab'):
                tab_name = self.runner.current_tab
            return UICommand(self, command_spec, tab_name)
        return None

    def _find_command(self, command_name: str) -> Optional[CommandSpec]:
        """Find command spec by name.

        Supports qualified names (e.g., "users:create") to specify sub-app.
        If no qualifier, uses current tab context from runner.

        Args:
            command_name: Command name or qualified name ("tab:command")

        Returns:
            CommandSpec or None
        """
        if not self.app_spec:
            return None

        # Check if qualified name (e.g., "users:create")
        if ":" in command_name:
            tab_name, cmd_name = command_name.split(":", 1)

            # Search in specified sub-app
            for sub_app in self.app_spec.sub_apps:
                if sub_app.name == tab_name:
                    for cmd in sub_app.commands:
                        if cmd.name == cmd_name:
                            return cmd
            return None

        # Unqualified name - determine context from runner
        current_tab = None
        if self.runner and hasattr(self.runner, 'current_tab'):
            current_tab = self.runner.current_tab

        # Search in current tab/sub-app if applicable
        if current_tab is not None:
            for sub_app in self.app_spec.sub_apps:
                if sub_app.name == current_tab:
                    for cmd in sub_app.commands:
                        if cmd.name == command_name:
                            return cmd

        # Fallback: search in root commands
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
        """Launch the application in GUI or CLI mode based on runner setting and flags.

        Behavior depends on the runner parameter set in __init__:
        - runner="gui" (default): Launches GUI by default, use --cli to run CLI mode
        - runner="cli": Launches CLI by default, use --gui to run GUI mode

        Example:
            >>> # Default GUI mode
            >>> app = tu.UiApp(tapp, runner="gui")
            >>> app()  # Launches GUI
            >>> # Or use: python script.py --cli command arg1 arg2
            >>>
            >>> # Default CLI mode
            >>> app = tu.UiApp(tapp, runner="cli")
            >>> app()  # Launches CLI
            >>> # Or use: python script.py --gui
        """
        # Determine which mode to run based on runner setting and flags
        if self._runner_mode == "gui":
            # Default is GUI, check for --cli flag
            run_cli = "--cli" in sys.argv
            flag_to_remove = "--cli" if run_cli else None
        else:  # runner_mode == "cli"
            # Default is CLI, check for --gui flag
            run_cli = "--gui" not in sys.argv
            flag_to_remove = "--gui" if not run_cli else None

        # Remove the flag from argv if present
        if flag_to_remove and flag_to_remove in sys.argv:
            sys.argv.remove(flag_to_remove)

        if run_cli:
            # Run CLI mode
            self._cli_mode = True

            # Build app spec
            self.app_spec = build_app_spec(
                self._typer_app,
                title=self.title,
                description=self.description,
                main_label=self.main_label
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
            description=self.description,
            main_label=self.main_label
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
