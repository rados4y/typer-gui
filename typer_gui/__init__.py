"""Typer-GUI: Automatically generate desktop GUIs for Typer CLI applications."""

from .core import build_gui_model, gui_command
from .types import Markdown, GuiCommandOptions
from .ui import Ui
from .ui_blocks import UiBlock, Table, Markdown as MarkdownBlock, Link, Button

__version__ = "0.2.0"
__all__ = [
    "build_gui_model",
    "Markdown",
    "gui_command",
    "Ui",
    "GuiCommandOptions",
    "UiBlock",
    "Table",
    "MarkdownBlock",
    "Link",
    "Button",
]
