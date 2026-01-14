"""Core reflection logic for introspecting Typer applications."""

import inspect
from enum import Enum as PyEnum
from typing import Any, Callable, Optional, get_args, get_origin

import typer
from typer.models import CommandInfo, ParameterInfo

from .specs import AppSpec, CommandSpec, ParamSpec, CommandUiSpec, ParamType


# Attribute name for storing GUI options on functions
_GUI_OPTIONS_ATTR = "__typer_ui_options__"


def _get_param_type(annotation: Any) -> tuple[ParamType, Optional[type], Optional[tuple[str, ...]]]:
    """Determine the ParamType from a Python type annotation.

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
        choices = tuple([e.value for e in annotation])
        return ParamType.ENUM, annotation, choices

    # Handle list types
    if origin is list:
        # Get the item type from list[X]
        args = get_args(annotation)
        item_type = args[0] if args else str

        # Check if it's list[EnumType]
        if inspect.isclass(item_type) and issubclass(item_type, PyEnum):
            choices = tuple([e.value for e in item_type])
            return ParamType.ENUM_LIST, item_type, choices

        return ParamType.LIST, item_type, None

    # Unsupported type
    return ParamType.UNSUPPORTED, annotation, None


def _extract_param_info(param_name: str, param: inspect.Parameter) -> ParamSpec:
    """Extract parameter information from an inspect.Parameter."""
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
    cli_flags = ()
    if typer_info and hasattr(typer_info, "param_decls") and typer_info.param_decls:
        cli_flags = tuple(typer_info.param_decls)

    # Get help text
    help_text = None
    if typer_info and hasattr(typer_info, "help") and typer_info.help:
        help_text = typer_info.help

    return ParamSpec(
        name=param_name,
        param_type=param_type,
        required=required,
        default=default_value,
        help_text=help_text,
        cli_flags=cli_flags,
        enum_choices=enum_choices,
        python_type=python_type,
    )


def _extract_command_info(command_name: str, command_info: CommandInfo) -> CommandSpec:
    """Extract command information from Typer's CommandInfo."""
    callback = command_info.callback

    # Get help text from docstring or callback help
    help_text = None
    if hasattr(command_info, "help") and command_info.help:
        help_text = command_info.help
    elif callback and callback.__doc__:
        help_text = callback.__doc__.strip()

    # Extract parameters from callback signature
    params: list[ParamSpec] = []
    if callback:
        sig = inspect.signature(callback)
        for param_name, param in sig.parameters.items():
            param_spec = _extract_param_info(param_name, param)
            params.append(param_spec)

    # Extract GUI options if present
    ui_spec = CommandUiSpec()
    if callback and hasattr(callback, _GUI_OPTIONS_ATTR):
        # Get the stored CommandUiSpec directly (it's already the right type)
        ui_spec = getattr(callback, _GUI_OPTIONS_ATTR)

    return CommandSpec(
        name=command_name,
        callback=callback,
        help_text=help_text,
        params=tuple(params),
        ui_spec=ui_spec,
    )


def _build_sub_app_spec(typer_info) -> 'SubAppSpec':
    """Build SubAppSpec from a Typer TyperInfo object.

    Args:
        typer_info: TyperInfo object from app.registered_groups

    Returns:
        SubAppSpec: Immutable sub-application specification
    """
    from .specs import SubAppSpec

    commands: list[CommandSpec] = []

    # Access the registered commands from the sub-app's Typer instance
    if hasattr(typer_info.typer_instance, "registered_commands"):
        for command_info in typer_info.typer_instance.registered_commands:
            # Get command name
            command_name = command_info.name or (
                command_info.callback.__name__ if command_info.callback else "unnamed"
            )

            # Convert underscores to dashes to match Typer's CLI convention
            command_name = command_name.replace("_", "-")

            command_spec = _extract_command_info(command_name, command_info)
            commands.append(command_spec)

    return SubAppSpec(
        name=typer_info.name,
        commands=tuple(commands),
        description=typer_info.help
    )


def build_app_spec(
    app: typer.Typer,
    *,
    title: Optional[str] = None,
    description: Optional[str] = None,
    main_label: str = "main"
) -> AppSpec:
    """Build an application specification from a Typer app.

    Args:
        app: A Typer application instance
        title: Optional title for the application
        description: Optional description for the application
        main_label: Label for main/root commands tab (default: "main")

    Returns:
        AppSpec: Immutable application specification
    """
    commands: list[CommandSpec] = []

    # Access the registered commands from Typer (root-level commands)
    if hasattr(app, "registered_commands"):
        for command_info in app.registered_commands:
            # Get command name
            command_name = command_info.name or (
                command_info.callback.__name__ if command_info.callback else "unnamed"
            )

            # Convert underscores to dashes to match Typer's CLI convention
            command_name = command_name.replace("_", "-")

            command_spec = _extract_command_info(command_name, command_info)
            commands.append(command_spec)

    # Handle the case where there's a single callback (no explicit commands)
    if not commands and hasattr(app, "registered_callback") and app.registered_callback:
        callback_info = app.registered_callback
        command_spec = _extract_command_info("main", callback_info)
        commands.append(command_spec)

    # Process sub-applications (registered via add_typer)
    sub_apps: list['SubAppSpec'] = []
    if hasattr(app, "registered_groups"):
        for group in app.registered_groups:
            sub_app_spec = _build_sub_app_spec(group)
            sub_apps.append(sub_app_spec)

    return AppSpec(
        commands=tuple(commands),
        sub_apps=tuple(sub_apps),
        title=title,
        description=description,
        main_label=main_label,
    )
