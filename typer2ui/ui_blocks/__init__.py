"""UI Blocks - Components for building command line and GUI interfaces.

This module provides a collection of UI components that work in both CLI
(via Rich) and GUI (via Flet) modes automatically.
"""

# Base classes and utilities
from .base import (
    UiBlock,
    Container,
    get_current_runner,
    set_current_runner,
    to_component,
)

# Simple components
from .text import Text
from .md import Md

# Data display
from .table import Table
from .data_table import DataTable

# Layout
from .layout import Row, Column

# Interactive
from .interactive import Button, Link, TextInput, Alert, Confirm

# Tabs
from .tabs import Tab, Tabs

# Export all public APIs
__all__ = [
    # Base
    "UiBlock",
    "Container",
    "get_current_runner",
    "set_current_runner",
    "to_component",
    # Simple
    "Text",
    "Md",
    # Data
    "Table",
    "DataTable",
    # Layout
    "Row",
    "Column",
    # Interactive
    "Button",
    "Link",
    "TextInput",
    "Alert",
    "Confirm",
    # Tabs
    "Tab",
    "Tabs",
]
