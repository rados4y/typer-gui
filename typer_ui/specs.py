"""Immutable specification models for application definition."""

from dataclasses import dataclass
from enum import Enum
from typing import Any, Callable, Optional


class ParamType(Enum):
    """Supported parameter types for GUI controls."""
    STRING = "string"
    INTEGER = "integer"
    FLOAT = "float"
    BOOLEAN = "boolean"
    ENUM = "enum"
    UNSUPPORTED = "unsupported"


@dataclass(frozen=True)
class ParamSpec:
    """Immutable specification for a command parameter."""

    name: str
    """Parameter name as shown in CLI (e.g., 'name', 'verbose')"""

    param_type: ParamType
    """Type of the parameter"""

    required: bool
    """Whether this parameter is required"""

    default: Any = None
    """Default value if any"""

    help_text: Optional[str] = None
    """Help text / description"""

    cli_flags: tuple[str, ...] = ()
    """CLI flags like ('--name', '-n')"""

    enum_choices: Optional[tuple[str, ...]] = None
    """For Enum types, the list of valid choices"""

    python_type: Optional[type] = None
    """Original Python type annotation"""


@dataclass(frozen=True)
class CommandUiSpec:
    """GUI-specific options for a command."""

    button: bool = False
    """Display as a button in the left panel instead of a text link"""

    long: bool = False
    """Command is long-running, enable real-time output streaming"""

    auto: bool = False
    """Execute command automatically when selected, hide submit button"""

    header: bool = True
    """Show command name and description. If False, only show output"""

    submit_name: str = "Run Command"
    """Text for the submit button that executes the command"""

    on_select: Optional[Callable] = None
    """Callback function called when command is selected in GUI"""

    auto_scroll: bool = True
    """Automatically scroll to the end of output after command execution"""


@dataclass(frozen=True)
class CommandSpec:
    """Immutable specification for a command."""

    name: str
    """Command name (CLI name)"""

    callback: Callable
    """The actual Python function to call"""

    help_text: Optional[str] = None
    """Command help text / description"""

    params: tuple[ParamSpec, ...] = ()
    """Tuple of parameters for this command"""

    ui_spec: CommandUiSpec = CommandUiSpec()
    """GUI-specific display and behavior options"""


@dataclass(frozen=True)
class AppSpec:
    """Immutable specification for the entire application."""

    commands: tuple[CommandSpec, ...]
    """Tuple of all commands in the app"""

    title: Optional[str] = None
    """Optional app title"""

    description: Optional[str] = None
    """Optional app description"""


# Legacy type alias for backward compatibility during transition
Markdown = str  # Will be replaced with proper type
