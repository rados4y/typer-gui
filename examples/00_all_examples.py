"""Example 0: All Examples Combined

This example demonstrates how to combine multiple Typer applications
into a single application with tab-based navigation.

Each tab contains all commands from the corresponding example:
- basic: Basic Typer to GUI conversion (01)
- params: Parameters, outputs, and async (02)
- ui: UI components demonstration (03)
- control: Application control with upp.command() API (04)
- state: State management (05)
- datatable: DataTable with dynamic data loading (06)
- subapps: Sub-applications with tab navigation (07)
"""

import importlib.util
import sys
from pathlib import Path

import typer
import typer2ui as tu
from typer2ui import ui


def import_example(filename: str) -> object:
    """Import an example module by filename (handles numeric prefixes)."""
    examples_dir = Path(__file__).parent
    module_path = examples_dir / filename

    # Create a valid module name (replace invalid characters)
    module_name = f"examples.{filename.replace('.py', '').replace('-', '_')}"

    spec = importlib.util.spec_from_file_location(module_name, module_path)
    if spec is None or spec.loader is None:
        raise ImportError(f"Cannot load module from {module_path}")

    module = importlib.util.module_from_spec(spec)
    sys.modules[module_name] = module
    spec.loader.exec_module(module)
    return module


# Create main app
main_app = typer.Typer()

# Create UiApp wrapper for the main app
upp = tu.UiApp(
    main_app,
    title="Typer2UI Examples Gallery",
    description="Browse all examples in a single application",
)


# Add a welcome command at the main level (defined before imports to be first)
@main_app.command()
@upp.def_command(view=True)
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
| **control** | Programmatic command control with `upp.command()` API |
| **state** | Reactive state management with `upp.state()` and `dx()` |
| **datatable** | DataTable with pagination, sorting, and filtering |
| **subapps** | Nested sub-applications with qualified command names |

## How to Navigate

- Click on tabs above to switch between example categories
- Each tab contains multiple commands demonstrating different features
- Commands marked with `view=True` execute automatically when selected

## Running Examples

```bash
# GUI mode (this view)
python examples/00_all_examples.py

# CLI mode
python examples/00_all_examples.py --cli welcome
python examples/00_all_examples.py --cli basic add 5 3
python examples/00_all_examples.py --cli params basic-parameters Alice
python examples/00_all_examples.py --cli ui ui-table
```
"""
    )


# Import example modules dynamically
ex01 = import_example("01_basic_typer_to_gui.py")
ex02 = import_example("02_arguments_and_output.py")
ex03 = import_example("03_ui_blocks.py")
ex04 = import_example("04_app_control.py")
ex05 = import_example("05_state.py")
ex06 = import_example("06_data_table.py")
ex07 = import_example("07_sub_applications.py")

# Add each example as a sub-application with tabs
main_app.add_typer(ex01.tapp, name="basic", help="01: Basic Typer to GUI")
main_app.add_typer(ex02.tapp, name="params", help="02: Parameters & Outputs")
main_app.add_typer(ex03.tapp, name="ui", help="03: UI Components")
main_app.add_typer(ex04.tapp, name="control", help="04: App Control API")
main_app.add_typer(ex05.tapp, name="state", help="05: State Management")
main_app.add_typer(ex06.tapp, name="datatable", help="06: DataTable")
main_app.add_typer(ex07.app, name="subapps", help="07: Sub-Applications")


if __name__ == "__main__":
    upp()
