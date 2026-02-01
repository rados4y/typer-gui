"""Typer-UI: Automatically generate desktop GUIs for Typer CLI applications."""

from .spec_builder import build_app_spec
from .state import State
from .ui_app import Typer2Ui, UICommand
from .output import ui, text, dx
from .data_source import DataSource
from .ui_blocks import (
    UiBlock,
    Container,
    Text,
    Md,
    Print,
    Table,
    Row,
    Column,
    Button,
    Link,
    TextInput,
    Alert,
    Confirm,
    Tab,
    Tabs,
    DataTable,
)

# Backwards compatibility
UiApp = Typer2Ui

__version__ = "0.16.0"
__all__ = [
    "build_app_spec",
    "State",
    "Typer2Ui",
    "UiApp",
    "UICommand",
    "ui",
    "text",
    "dx",
    "DataSource",
    "UiBlock",
    "Container",
    "Text",
    "Md",
    "Print",
    "Table",
    "DataTable",
    "Row",
    "Column",
    "Button",
    "Link",
    "TextInput",
    "Alert",
    "Confirm",
    "Tab",
    "Tabs",
]
