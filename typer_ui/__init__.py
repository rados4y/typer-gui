"""Typer-UI: Automatically generate desktop GUIs for Typer CLI applications."""

from .spec_builder import build_app_spec
from .state import State
from .ui_app import UiApp, UICommand
from .output import ui, text, dx
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
    Tab,
    Tabs,
)

__version__ = "0.2.0"
__all__ = [
    "build_app_spec",
    "State",
    "UiApp",
    "UICommand",
    "ui",
    "text",
    "dx",
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
    "Tab",
    "Tabs",
]
