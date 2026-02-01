"""Hold - Provides access to GUI internals for advanced customization."""

from typing import Optional, Any, TYPE_CHECKING

if TYPE_CHECKING:
    import flet as ft


class Hold:
    """Provides access to GUI internals for advanced customization.

    Available as `ui.hold` on the Typer2Ui instance.

    Attributes:
        page: Access to Flet Page object (GUI mode only)
        result: Dict-like access to command output controls

    Example:
        >>> # Access Flet page for customization
        >>> if ui.hold.page:
        >>>     ui.hold.page.theme_mode = ft.ThemeMode.DARK
        >>>     ui.hold.page.update()
        >>>
        >>> # Access command output control
        >>> output_control = ui.hold.result['my-command']
    """

    def __init__(self, ui_app: Any):
        """Initialize Hold with reference to Typer2Ui.

        Args:
            ui_app: Parent Typer2Ui instance
        """
        self._ui_app = ui_app

    @property
    def page(self) -> Optional["ft.Page"]:
        """Get Flet Page object (GUI mode only).

        Returns:
            Flet Page if in GUI mode, None otherwise
        """
        if self._ui_app.runner and hasattr(self._ui_app.runner, 'page'):
            return self._ui_app.runner.page
        return None

    @property
    def result(self) -> "ResultAccessor":
        """Get dict-like accessor for command output controls.

        Returns:
            ResultAccessor that provides access to command outputs
        """
        return ResultAccessor(self._ui_app)


class ResultAccessor:
    """Dict-like accessor for command output controls."""

    def __init__(self, ui_app: Any):
        """Initialize with reference to Typer2Ui.

        Args:
            ui_app: Parent Typer2Ui instance
        """
        self._ui_app = ui_app

    def __getitem__(self, command_name: str) -> Optional[Any]:
        """Get output control for a command.

        Args:
            command_name: Name of the command (e.g., 'my-command')

        Returns:
            Flet ListView control for command output, or None if not found
        """
        if not self._ui_app.runner or not hasattr(self._ui_app.runner, 'command_views'):
            return None

        # Get command view for this command
        command_views = self._ui_app.runner.command_views
        if command_name in command_views:
            view = command_views[command_name]
            # Return the output ListView where results are displayed
            return view.output_view

        return None

    def get(self, command_name: str, default: Any = None) -> Optional[Any]:
        """Get output control with default fallback.

        Args:
            command_name: Name of the command
            default: Value to return if command not found

        Returns:
            Output control or default value
        """
        try:
            result = self[command_name]
            return result if result is not None else default
        except (KeyError, AttributeError):
            return default
