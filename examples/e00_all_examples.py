"""Example 0: All Examples Combined

This example demonstrates how to combine multiple Typer2Ui applications
into a single application with tab-based navigation using add_typer().

Each tab contains all commands from the corresponding example:
- basic: Basic Typer to GUI conversion (01)
- params: Parameters, outputs, and async (02)
- ui: UI components demonstration (03)
- control: Application control with app.get_command() API (04)
- state: State management (05)
- datatable: DataTable with dynamic data loading (06)
- subapps: Sub-applications with tab navigation (07)
"""

import sys
from pathlib import Path

# Add parent directory to path for imports to work when running directly
sys.path.insert(0, str(Path(__file__).parent.parent))

import typer2ui
from typer2ui import ui

# Static imports of example modules
from examples import e01_basic_typer_to_gui as ex01
from examples import e02_arguments_and_output as ex02
from examples import e03_ui_blocks as ex03
from examples import e04_app_control as ex04
from examples import e05_state as ex05
from examples import e06_data_table as ex06
from examples import e07_sub_applications as ex07

# Create main app
app = typer2ui.Typer2Ui(
    title="Typer2UI Examples Gallery",
    description="Browse all examples in a single application",
)


# Add a welcome command at the main level (defined before adding sub-apps to be first)
@app.command(view=True)
def welcome():
    """Welcome screen with overview of all examples."""
    ui(
        """
# Welcome to Typer2UI Examples Gallery

This application demonstrates all features of the **typer2ui** library.

## Available Examples

| Tab | Description |
|-----|-------------|
| **basic** | Minimal example showing how to convert a Typer CLI to GUI |
| **params** | Parameter types, output methods, modals, and async commands |
| **ui** | All UI components: Text, Table, Row, Column, Button, Tabs, etc. |
| **control** | Programmatic command control with `app.get_command()` API |
| **state** | Reactive state management with `app.state()` and `ui.dx()` |
| **datatable** | DataTable with pagination, sorting, and filtering |
| **subapps** | Nested sub-applications with qualified command names |

## How to Navigate

- Click on tabs above to switch between example categories
- Each tab contains multiple commands demonstrating different features
- Commands marked with `view=True` execute automatically when selected

## Running Examples

```bash
# GUI mode (this view)
python examples/e00_all_examples.py

# CLI mode
python examples/e00_all_examples.py --cli welcome
python examples/e00_all_examples.py --cli basic add 5 3
python examples/e00_all_examples.py --cli params basic-parameters Alice
python examples/e00_all_examples.py --cli ui ui-table
```
"""
    )


# Add each example as a sub-application using add_typer()
app.add_typer(ex01.typer_app, name="basic", help="01: Basic Typer to GUI")
app.add_typer(ex02.app, name="params", help="02: Parameters & Outputs")
app.add_typer(ex03.app, name="ui", help="03: UI Components")
app.add_typer(ex04.app, name="control", help="04: App Control API")
app.add_typer(ex05.app, name="state", help="05: State Management")
app.add_typer(ex06.app, name="datatable", help="06: DataTable")
app.add_typer(ex07.app, name="subapps", help="07: Sub-Applications")


if __name__ == "__main__":
    app()
