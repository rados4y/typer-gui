"""Typer-UI: Automatically generate desktop GUIs for Typer CLI applications."""

from .spec_builder import build_app_spec
from .ui import Ui
from .ui_blocks import (
    UiBlock,
    Container,
    Text,
    Md,
    Table,
    Row,
    Column,
    Button,
    Link,
    TextInput,
)
from .ui_app import UICommand

__version__ = "0.2.0"
__all__ = [
    "build_app_spec",
    "Ui",
    "UiBlock",
    "Container",
    "Text",
    "Md",
    "Table",
    "Row",
    "Column",
    "Button",
    "Link",
    "TextInput",
    "UICommand",
]
