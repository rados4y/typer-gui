"""Core reflection logic for introspecting Typer applications."""

import inspect
from enum import Enum as PyEnum
from typing import Any, Callable, Optional, get_args, get_origin
from functools import wraps

import typer
from typer.models import CommandInfo, ParameterInfo

from .types import GuiApp, GuiCommand, GuiParam, ParamType, GuiCommandOptions


# Attribute name for storing GUI options on functions
_GUI_OPTIONS_ATTR = "__typer_gui_options__"


def gui_command(*, is_button: bool = False, is_long: bool = False, is_markdown: bool = False, is_auto_exec: bool = False):
    """Decorator to add GUI-specific options to a Typer command.

    This decorator can be used alongside @app.command() to customize
    how the command appears and behaves in the GUI.

    Args:
        is_button: If True, display the command as a button in the left panel
                   instead of a text link. Useful for important or frequently
                   used commands.
        is_long: If True, the command is marked as long-running and the GUI
                 will stream output in real-time as it's produced, instead of
                 waiting for the command to complete.
        is_markdown: If True, the command's return value will be treated as
                     markdown-formatted text and rendered with formatting.
        is_auto_exec: If True, the command is executed automatically when selected,
                      and the 'Run Command' button is hidden.

    Example:
        >>> from typer_gui import gui_command
        >>> import typer
        >>>
        >>> app = typer.Typer()
        >>>
        >>> @app.command()
        >>> @gui_command(is_button=True, is_long=True)
        >>> def process_data():
        >>>     for i in range(10):
        >>>         print(f"Processing {i}...")
        >>>         time.sleep(1)
        >>>
        >>> @app.command()
        >>> @gui_command(is_markdown=True)
        >>> def info() -> str:
        >>>     return "# Hello **World**!"
    """
    def decorator(func: Callable) -> Callable:
        # Store GUI options as function attribute
        setattr(func, _GUI_OPTIONS_ATTR, GuiCommandOptions(
            is_button=is_button,
            is_long=is_long,
            is_markdown=is_markdown,
            is_auto_exec=is_auto_exec,
        ))
        return func
    return decorator


def _get_param_type(annotation: Any) -> tuple[ParamType, Optional[type], Optional[list[str]]]:
    """
    Determine the ParamType from a Python type annotation.

    Returns:
        Tuple of (ParamType, original_type, enum_choices)
    """
    # Handle Optional types
    origin = get_origin(annotation)
    if origin is type(None) or annotation is type(None):
        return ParamType.UNSUPPORTED, annotation, None

    # Unwrap Optional[X] to X
    if origin is type(None) or (hasattr(annotation, "__args__") and type(None) in get_args(annotation)):
        args = get_args(annotation)
        if args:
            annotation = args[0] if args[0] is not type(None) else args[1]
            origin = get_origin(annotation)

    # Handle basic types
    if annotation is str or annotation == str:
        return ParamType.STRING, str, None
    elif annotation is int or annotation == int:
        return ParamType.INTEGER, int, None
    elif annotation is float or annotation == float:
        return ParamType.FLOAT, float, None
    elif annotation is bool or annotation == bool:
        return ParamType.BOOLEAN, bool, None

    # Handle Enum types
    if inspect.isclass(annotation) and issubclass(annotation, PyEnum):
        choices = [e.value for e in annotation]
        return ParamType.ENUM, annotation, choices

    # Unsupported type
    return ParamType.UNSUPPORTED, annotation, None


def _extract_param_info(param_name: str, param: inspect.Parameter) -> GuiParam:
    """Extract GUI parameter information from an inspect.Parameter."""
    from typer.models import ArgumentInfo, OptionInfo

    # Get the annotation
    annotation = param.annotation if param.annotation != inspect.Parameter.empty else str

    # Determine the parameter type
    param_type, python_type, enum_choices = _get_param_type(annotation)

    # Check if default is ArgumentInfo or OptionInfo
    typer_info = None
    if isinstance(param.default, (ArgumentInfo, OptionInfo)):
        typer_info = param.default

    # Determine if required
    # ArgumentInfo with no default means required
    # OptionInfo always has a default (False for flags, or explicit value)
    required = False
    default_value = None

    if typer_info:
        if isinstance(typer_info, ArgumentInfo):
            # Arguments are required unless they have a default
            required = typer_info.default is ... or typer_info.default is None
            if typer_info.default is not ... and typer_info.default is not None:
                default_value = typer_info.default
                required = False
        else:  # OptionInfo
            required = False
            default_value = typer_info.default if typer_info.default is not ... else None
    elif param.default == inspect.Parameter.empty:
        required = True
    else:
        default_value = param.default

    # Build CLI flags
    cli_flags = []
    if typer_info and hasattr(typer_info, "param_decls") and typer_info.param_decls:
        cli_flags = list(typer_info.param_decls)

    # Get help text
    help_text = None
    if typer_info and hasattr(typer_info, "help") and typer_info.help:
        help_text = typer_info.help

    return GuiParam(
        name=param_name,
        param_type=param_type,
        required=required,
        default=default_value,
        help_text=help_text,
        cli_flags=cli_flags,
        enum_choices=enum_choices,
        python_type=python_type,
    )


def _extract_command_info(command_name: str, command_info: CommandInfo) -> GuiCommand:
    """Extract GUI command information from Typer's CommandInfo."""
    callback = command_info.callback

    # Get help text from docstring or callback help
    help_text = None
    if hasattr(command_info, "help") and command_info.help:
        help_text = command_info.help
    elif callback and callback.__doc__:
        help_text = callback.__doc__.strip()

    # Extract parameters from callback signature
    params: list[GuiParam] = []
    if callback:
        sig = inspect.signature(callback)
        for param_name, param in sig.parameters.items():
            gui_param = _extract_param_info(param_name, param)
            params.append(gui_param)

    # Extract GUI options if present
    gui_options = GuiCommandOptions()
    if callback and hasattr(callback, _GUI_OPTIONS_ATTR):
        gui_options = getattr(callback, _GUI_OPTIONS_ATTR)

    return GuiCommand(
        name=command_name,
        callback=callback,
        help_text=help_text,
        params=params,
        gui_options=gui_options,
    )


def build_gui_model(app: typer.Typer, *, title: Optional[str] = None, description: Optional[str] = None) -> GuiApp:
    """
    Build a GUI model from a Typer application.

    Args:
        app: A Typer application instance
        title: Optional title for the GUI
        description: Optional description for the GUI

    Returns:
        GuiApp: A structured representation of the Typer app
    """
    commands: list[GuiCommand] = []

    # Access the registered commands from Typer
    # Typer stores commands in app.registered_commands
    if hasattr(app, "registered_commands"):
        for command_info in app.registered_commands:
            # Get command name
            command_name = command_info.name or (
                command_info.callback.__name__ if command_info.callback else "unnamed"
            )

            gui_command = _extract_command_info(command_name, command_info)
            commands.append(gui_command)

    # Handle the case where there's a single callback (no explicit commands)
    if not commands and hasattr(app, "registered_callback") and app.registered_callback:
        callback_info = app.registered_callback
        gui_command = _extract_command_info("main", callback_info)
        commands.append(gui_command)

    return GuiApp(commands=commands, title=title, description=description)
