"""Typer-GUI: Automatically generate desktop GUIs for Typer CLI applications."""

from .core import build_gui_model
from .types import Markdown, GuiCommandOptions
from .ui import Ui
from .ui_blocks import UiBlock, Table, Markdown as MarkdownBlock, Link, Button, Row, UiOutput
from .ui_app import UIApp, UICommand

__version__ = "0.2.0"
__all__ = [
    "build_gui_model",
    "Markdown",
    "Ui",
    "GuiCommandOptions",
    "UiBlock",
    "Table",
    "MarkdownBlock",
    "Link",
    "Button",
    "Row",
    "UiOutput",
    "UIApp",
    "UICommand",
]
