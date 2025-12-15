"""UIApp and UICommand classes for advanced UI operations and extensions."""

import io
from contextlib import redirect_stdout, redirect_stderr
from typing import Any, Optional, List, TYPE_CHECKING
from .types import GuiCommand, GuiApp
from .ui_blocks import UiOutput

if TYPE_CHECKING:
    import flet as ft
    from .flet_ui import TyperGUI


class UICommandBlocks:
    """Container for command-specific UI block references.

    Provides direct access to the Flet controls that make up a command's UI.
    """

    def __init__(self):
        self.arguments: Optional['ft.Container'] = None
        """Container with command arguments/parameters"""

        self.title: Optional['ft.Container'] = None
        """Container with command title and description"""

        self.actions: Optional['ft.Container'] = None
        """Container with 'Run Command' button"""

        self.result: Optional['ft.Container'] = None
        """Container with command execution result"""


class UICommand:
    """Command-level UI context and operations.

    Provides access to command execution, selection, and UI blocks.
    Each command in the application has a corresponding UICommand instance.
    """

    def __init__(self, gui_command: GuiCommand, gui_instance: 'TyperGUI', ui_app: 'UIApp'):
        """Initialize UICommand.

        Args:
            gui_command: The underlying GuiCommand model
            gui_instance: Reference to the TyperGUI instance
            ui_app: Reference to the parent UIApp
        """
        self._gui_command = gui_command
        self._gui = gui_instance
        self._ui_app = ui_app
        self.blocks = UICommandBlocks()

    @property
    def name(self) -> str:
        """Get command name."""
        return self._gui_command.name

    def select(self) -> None:
        """Select this command in the UI.

        This updates the form to show this command's parameters and prepares it for execution.
        """
        if self._gui:
            self._gui.select_command(self._gui_command)

    def run(self, **kwargs):
        """Select and execute this command with given parameters.

        This method:
        - Selects the command in the GUI
        - Populates form fields with provided parameters (if any)
        - Executes the command normally (output appears in the selected command)

        Args:
            **kwargs: Parameter values to pass to the command (optional)

        Example:
            >>> ui.command("calculate").run(x=10, y=5)  # Selects, populates x=10, y=5, and executes
            >>> ui.command("show-table").run()  # Selects and executes (no params)
        """
        # Select the command first
        self.select()

        # Populate form fields with provided parameters
        if self._gui and kwargs:
            for param_name, param_value in kwargs.items():
                control = self._gui.form_controls.get(param_name)
                if control:
                    # Set the value based on control type
                    if hasattr(control, 'value'):
                        control.value = str(param_value) if not isinstance(control.value, bool) else bool(param_value)

            # Update the page to show the populated values
            if self._gui.page:
                self._gui.page.update()

        # Execute the command normally (output appears in GUI)
        if self._gui:
            self._gui.run_command()
        else:
            # CLI mode - just execute directly
            self._gui_command.callback(**kwargs)

    def include(self, **kwargs) -> Any:
        """Execute this command and present output in currently selected command.

        Unlike run(), this method:
        - Doesn't select the command
        - Executes inline (output appears in current command's context)
        - Useful for composing commands inline

        Args:
            **kwargs: Parameter values to pass to the command

        Returns:
            The command's return value

        Example:
            >>> # Inside a command, include another command's output
            >>> result = ui.command("helper").include(x=5)
        """
        from .ui_blocks import UiContext, set_context, get_context

        # Check if we're in GUI mode
        if self._gui and self._gui.output_view:
            # Capture output from the included command
            stdout_capture = io.StringIO()
            stderr_capture = io.StringIO()

            # Get or create context for output rendering
            existing_context = get_context()
            if not existing_context:
                # Create temporary context for include execution
                context = UiContext(
                    mode="gui",
                    page=self._gui.page,
                    output_view=self._gui.output_view,
                    gui_app=self._gui,
                    ui_app=self._ui_app
                )
                set_context(context)
                try:
                    with redirect_stdout(stdout_capture), redirect_stderr(stderr_capture):
                        result = self._gui_command.callback(**kwargs)

                    # Append captured output to current view
                    stdout_text = stdout_capture.getvalue()
                    stderr_text = stderr_capture.getvalue()

                    if stdout_text:
                        self._gui._append_output(stdout_text)
                    if stderr_text:
                        self._gui._append_output(f"[STDERR]\n{stderr_text}")

                    # Update page to show the included output
                    if self._gui.page:
                        self._gui.page.update()

                    return result
                finally:
                    set_context(None)
            else:
                # Context already exists - execute with stdout capture
                with redirect_stdout(stdout_capture), redirect_stderr(stderr_capture):
                    result = self._gui_command.callback(**kwargs)

                # Append captured output to current view
                stdout_text = stdout_capture.getvalue()
                stderr_text = stderr_capture.getvalue()

                if stdout_text:
                    self._gui._append_output(stdout_text)
                if stderr_text:
                    self._gui._append_output(f"[STDERR]\n{stderr_text}")

                # Update page to show the included output
                if self._gui.page:
                    self._gui.page.update()

                return result
        else:
            # CLI mode - just execute
            return self._gui_command.callback(**kwargs)

    def clear(self) -> None:
        """Clear the current command's output.

        This clears the output view for the currently selected command.
        If the command has is_auto_exec=True, it will re-execute after clearing.
        Only works in GUI mode.

        Example:
            >>> ui.command("my-command").clear()
        """
        if self._gui and self._gui.output_view:
            self._gui.output_view.controls.clear()
            if self._gui.page:
                self._gui.page.update()

            # Re-execute if command is auto-exec
            if self._gui_command.gui_options.is_auto_exec:
                self._gui.run_command()


class UIAppBlocks:
    """Container for application-level UI block references.

    Provides direct access to the main Flet controls that make up the application layout.
    """

    def __init__(self):
        self.header: Optional['ft.Container'] = None
        """Header container for custom header content"""

        self.body: Optional['ft.Container'] = None
        """Main body container for the application"""


class UIApp:
    """Application-level UI context and operations.

    Provides access to commands, UI blocks, and application state.
    Available as ui.app in command execution context.
    """

    def __init__(self, gui_instance: 'TyperGUI', gui_model: GuiApp):
        """Initialize UIApp.

        Args:
            gui_instance: Reference to the TyperGUI instance
            gui_model: The GuiApp model with all commands
        """
        self._gui = gui_instance
        self._gui_model = gui_model
        self.blocks = UIAppBlocks()
        self.out = UiOutput()

        # Create UICommand instances for each GuiCommand
        self._commands: List[UICommand] = []
        self._command_map: dict[str, UICommand] = {}
        for gui_cmd in gui_model.commands:
            ui_cmd = UICommand(gui_cmd, gui_instance, self)
            self._commands.append(ui_cmd)
            self._command_map[gui_cmd.name] = ui_cmd

    @property
    def cmd(self) -> Optional[UICommand]:
        """Get the currently selected or executing command.

        Returns:
            UICommand instance for the current command, or None if no command is selected.
        """
        if self._gui and self._gui.current_command:
            return self._command_map.get(self._gui.current_command.name)
        return None

    @property
    def commands(self) -> List[UICommand]:
        """Get list of all available commands.

        Returns:
            List of UICommand instances for all commands in the application.
        """
        return self._commands

    def get_command(self, name: str) -> Optional[UICommand]:
        """Get a command by name.

        Args:
            name: The command name

        Returns:
            UICommand instance if found, None otherwise.
        """
        return self._command_map.get(name)
