"""Data types for GUI model representation."""

from dataclasses import dataclass, field
from enum import Enum
from typing import Any, Callable, Optional


@dataclass
class Markdown:
    """Markdown formatted output for GUI display.

    Use this as a return type in your Typer commands to render
    formatted markdown in the GUI instead of plain text.

    Example:
        >>> from typer_gui import Markdown
        >>>
        >>> @app.command()
        >>> def info() -> Markdown:
        >>>     return Markdown('''
        >>>     # Hello World
        >>>     This is **bold** and *italic* text.
        >>>     ''')
    """
    content: str
    """The markdown content to display"""


class ParamType(Enum):
    """Supported parameter types for GUI controls."""

    STRING = "string"
    INTEGER = "integer"
    FLOAT = "float"
    BOOLEAN = "boolean"
    ENUM = "enum"
    UNSUPPORTED = "unsupported"


@dataclass
class GuiParam:
    """Represents a single parameter/option in a command."""

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

    cli_flags: list[str] = field(default_factory=list)
    """CLI flags like ['--name', '-n']"""

    enum_choices: Optional[list[str]] = None
    """For Enum types, the list of valid choices"""

    python_type: Optional[type] = None
    """Original Python type annotation"""


@dataclass
class GuiCommandOptions:
    """GUI-specific options for a command."""

    is_button: bool = False
    """Display as a button in the left panel instead of a text link"""

    is_long: bool = False
    """Command is long-running, enable real-time output streaming"""

    is_markdown: bool = False
    """Command returns markdown-formatted string that should be rendered as Markdown"""

    is_auto_exec: bool = False
    """Execute command automatically when selected, hide 'Run Command' button"""


@dataclass
class GuiCommand:
    """Represents a single command in the Typer app."""

    name: str
    """Command name (CLI name)"""

    callback: Callable
    """The actual Python function to call"""

    help_text: Optional[str] = None
    """Command help text / description"""

    params: list[GuiParam] = field(default_factory=list)
    """List of parameters for this command"""

    gui_options: GuiCommandOptions = field(default_factory=GuiCommandOptions)
    """GUI-specific display and behavior options"""


@dataclass
class GuiApp:
    """Represents the entire Typer application in GUI form."""

    commands: list[GuiCommand]
    """List of all commands in the app"""

    title: Optional[str] = None
    """Optional app title"""

    description: Optional[str] = None
    """Optional app description"""
