"""Main UI class for typer-ui - integrated API."""

from typing import Callable, Optional
import sys
import typer
import flet as ft

from .spec_builder import build_app_spec, _GUI_OPTIONS_ATTR
from .specs import CommandUiSpec, AppSpec, CommandSpec
from .runners.gui_runner import create_flet_app
from .runners.cli_runner import CLIRunner
from .ui_blocks import get_current_runner


class Ui:
    """Main entry point for typer-ui - extension API for Typer apps.

    This class provides GUI-specific configuration on top of existing Typer applications.
    It works alongside Typer's decorators, not as a replacement.

    Example:
        >>> import typer
        >>> import typer_ui as tg
        >>>
        >>> app = typer.Typer()
        >>> ui = tg.Ui(
        >>>     app,
        >>>     title="My Application",
        >>>     description="A demo app"
        >>> )
        >>>
        >>> @app.command()
        >>> @ui.command(is_button=True)
        >>> def greet(name: str):
        >>>     ui(tg.Md("# Hello!"))
        >>>     print(f"Hello {name}!")
        >>>
        >>> if __name__ == "__main__":
        >>>     ui.app()
    """

    def __init__(
        self,
        app: typer.Typer,
        *,
        title: Optional[str] = None,
        description: Optional[str] = None,
    ):
        """Initialize the UI wrapper for a Typer app.

        Args:
            app: The Typer application instance to extend
            title: Window title for the GUI
            description: Description text shown at the top of the GUI
        """
        self.title = title
        self.description = description
        self._typer_app = app
        self._cli_mode = False

        # Runtime attributes (initialized when app starts)
        self.app_spec: Optional[AppSpec] = None
        self.runner: Optional[Any] = None
        self.current_command: Optional[CommandSpec] = None

    def _to_component(self, value):
        """Convert value to a UiBlock component.

        Args:
            value: Value to convert (None, str, UiBlock, or any object)

        Returns:
            UiBlock component
        """
        from .ui_blocks import to_component
        return to_component(value)

    def __call__(self, component_or_renderer=None, *dependencies):
        """Present a component and return it for further use.

        Supports multiple patterns:
        1. Normal: ui(component) - Display a component
        2. Reactive: ui(renderer, state1, state2, ...) - Display and auto-update
        3. Shortcut: ui() - Display empty line (like print())
        4. Shortcut: ui(str) - Display string as Markdown
        5. Shortcut: ui(obj) - Display object as text

        Args:
            component_or_renderer: Component to display OR callable returning component.
                Can be None (empty line), str (markdown), or any object (converted to text)
            *dependencies: State objects this component depends on (reactive mode)

        Returns:
            The component (for chaining or context manager usage)

        Examples:
            >>> # Normal pattern
            >>> ui(tg.Text("Hello"))
            >>>
            >>> # Shortcuts
            >>> ui()  # Empty line
            >>> ui("# Hello")  # Markdown
            >>> ui(42)  # Prints "42"
            >>>
            >>> # Reactive pattern with state
            >>> counter = ui.state(0)
            >>> ui(lambda: f"Count: {counter.value}", counter)  # Returns string → Markdown
            >>> counter.set(1)  # Automatically re-renders
            >>>
            >>> # Context manager
            >>> with ui(tg.Table(cols=["Name"], data=[])) as t:
            >>>     t.add_row(["Alice"])

        Raises:
            RuntimeError: If called outside of command execution context
        """
        runner = get_current_runner()
        if not runner:
            raise RuntimeError(
                "ui() can only be called during command execution. "
                "Ensure you're calling it from within a command function."
            )

        # Auto-convert input to UiBlock if needed (unless it's a callable with dependencies)
        if not (callable(component_or_renderer) and dependencies):
            component_or_renderer = self._to_component(component_or_renderer)

        # Check if this is reactive pattern: ui(renderer, state1, state2, ...)
        if callable(component_or_renderer) and dependencies:
            # Reactive mode: renderer function with state dependencies
            renderer = component_or_renderer

            # Create a reactive container to capture all ui() calls
            from .ui_blocks import Column
            container = Column(children=[])

            # Execute renderer in reactive mode
            # This captures all ui() calls into the container
            container, flet_control = runner.execute_in_reactive_mode(container, renderer)

            # Store the container's flet control for updates (if we have one)
            if flet_control is not None:
                runner._reactive_components[id(container)] = flet_control
                # Show the container (GUI mode)
                runner.add_to_output(flet_control, component=container)
            # In CLI mode, flet_control is None and renderer already printed output

            # Create observer callback that handles re-rendering
            def on_state_change():
                """Observer callback invoked when any dependency changes.

                Re-executes the renderer and updates the container.
                """
                # Update the reactive container
                runner.update_reactive_container(container, renderer)

            # Register the observer callback with all state dependencies
            from .state import State
            for dep in dependencies:
                if isinstance(dep, State):
                    dep.add_observer(on_state_change)

            return container

        else:
            # Normal mode: just a component
            component = component_or_renderer

            # Check if in reactive mode
            if runner.is_reactive_mode():
                # Add to reactive container instead of main output
                runner.add_to_reactive_container(component)
            else:
                # Normal show to main output
                runner.show(component)

            # Mark component as presented for auto-updates
            if hasattr(component, '_mark_presented'):
                component._mark_presented(runner)

            # Return component for chaining/context manager
            return component

    def out(self, component) -> None:
        """Legacy output method. Use ui(component) instead.

        Args:
            component: UiBlock component to display
        """
        self(component)

    def clipboard(self, text: str) -> None:
        """Copy text to clipboard.

        Works in both GUI and CLI modes.
        In GUI mode, copies to system clipboard.
        In CLI mode, prints the text with a copy indicator.

        Args:
            text: Text to copy

        Example:
            >>> ui(tg.Button("Copy Result",
            ...     on_click=lambda: ui.clipboard(str(result))))
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
            >>> counter = ui.state(0)
            >>> ui(lambda: tg.Text(f"Count: {counter.value}"), counter)
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
        # Deprecated parameters (for backward compatibility)
        is_button: Optional[bool] = None,
        is_long: Optional[bool] = None,
        is_auto_exec: Optional[bool] = None,
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
            is_button: Deprecated, use 'button' instead
            is_long: Deprecated, use 'long' instead
            is_auto_exec: Deprecated, use 'auto' instead

        Example:
            >>> @app.command()
            >>> @ui.def_command(button=True, long=True)
            >>> def process():
            >>>     for i in range(10):
            >>>         print(f"Step {i}")
            >>>         time.sleep(1)
            >>>
            >>> @app.command()
            >>> @ui.def_command(auto=True, header=False)
            >>> def dashboard():
            >>>     ui("# Dashboard")  # Only output shown, no command header
        """

        def decorator(func: Callable) -> Callable:
            import asyncio
            import inspect

            # Handle backward compatibility
            final_button = is_button if is_button is not None else button
            final_long = is_long if is_long is not None else long
            final_auto = is_auto_exec if is_auto_exec is not None else auto

            # Store GUI options on the function
            setattr(
                func,
                _GUI_OPTIONS_ATTR,
                CommandUiSpec(
                    button=final_button,
                    long=final_long,
                    auto=final_auto,
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
            >>> ui.command("fetch-data").run(source="api")
            >>>
            >>> # Get current command
            >>> current = ui.command()
        """
        # Import here to avoid circular dependency
        from .ui_app import UICommand

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
        # Import here to avoid circular dependency
        from .ui_app import UICommand

        if not self.app_spec:
            return []

        return [UICommand(self, cmd) for cmd in self.app_spec.commands]

    def app(self):
        """Launch the GUI application or CLI based on --cli flag.

        This should be called at the end of your script to start the GUI.
        If --cli flag is present in command line arguments, the GUI is bypassed
        and the Typer CLI is executed directly.

        Example:
            >>> if __name__ == "__main__":
            >>>     ui.app()  # Launches GUI
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
