# Typer2UI

Automatically generate desktop GUIs for existing [Typer](https://typer.tiangolo.com/) CLI applications using [Flet](https://flet.dev/).

## Overview

**Typer2UI** is a Python library that bridges the gap between command-line interfaces and graphical user interfaces. If you have a Typer-based CLI application, you can instantly create a desktop GUI for it with just a few lines of code.

### Key Features

- **Zero or minimal code changes** to your existing Typer app
- **Automatic GUI generation** from Typer commands and parameters
- **Simple, elegant API** - `ui(component)` for all output
- **Auto-update components** - modify components and see changes instantly
- **Progressive rendering** - update UI in real-time with context managers
- **Rich UI components** - Tables, Markdown, Buttons, Rows, Columns, and more
- **Type-aware controls** - text fields, dropdowns, checkboxes based on parameter types
- **Real-time output streaming** - see output as it's produced for long-running commands
- **Clean, modern interface** powered by Flet

## Installation

### Using pip

```bash
pip install typer2ui
```

This will automatically install `typer` and `flet` as dependencies if they're not already present.

### For development

```bash
# Clone the repository
git clone https://github.com/rados4y/typer2ui.git
cd typer2ui

# Create a virtual environment
python -m venv .venv
source .venv/bin/activate  # On Windows: .venv\Scripts\activate

# Install in development mode
pip install -e .
```

## Quick Start

Here's a minimal example to get you started:

```python
# my_app.py
import typer
import typer2ui as tu

# Create the Typer app
app = typer.Typer()

# Create the UI wrapper
ui = tu.Ui(
    app,
    title="My App",
    description="A graphical interface for my CLI app"
)

@app.command()
def greet(name: str, excited: bool = False):
    """Greet someone with a friendly message."""
    punctuation = "!" if excited else "."

    # Use ui() to output components
    ui(tu.Md(f"# Hello {name}{punctuation}"))
    ui(tu.Text("Thanks for using Typer2UI!"))

@app.command()
def add(a: int, b: int):
    """Add two numbers together."""
    result = a + b

    # You can also use print()
    print(f"{a} + {b} = {result}")

if __name__ == "__main__":
    # Launch the GUI
    ui.app()
```

**Run it:**
```bash
# Launch GUI
python my_app.py

# Or run CLI directly with --cli flag
python my_app.py --cli greet "World" --excited
python my_app.py --cli add 5 10
```

That's it! Your CLI app now has a fully functional GUI.

## The Simple API

### Universal Output: `ui(component)`

Instead of multiple output methods, Typer2UI has one simple pattern:

```python
# Output any component
ui(tu.Text("Hello"))
ui(tu.Md("# Header"))
ui(tu.Table(cols=["Name"], data=[["Alice"]]))

# Or return a component (auto-displayed)
@app.command()
def get_data():
    return tu.Table(cols=["Name"], data=[["Bob"]])
```

### Available Components

#### Text & Markdown
```python
ui(tu.Text("Plain text"))
ui(tu.Md("**Bold** and *italic* with markdown"))
ui(tu.Md("""
# Report
- Item 1
- Item 2
"""))
```

#### Tables
```python
ui(tu.Table(
    cols=["Name", "Age", "City"],
    data=[
        ["Alice", 30, "NYC"],
        ["Bob", 25, "LA"],
    ],
    title="Users"
))
```

#### Layout Components
```python
# Horizontal layout
ui(tu.Row([
    tu.Button("Save", on_click=save_data),
    tu.Button("Cancel", on_click=cancel),
]))

# Vertical layout
ui(tu.Column([
    tu.Md("# Dashboard"),
    tu.Table(cols=["Metric", "Value"], data=get_metrics()),
]))
```

#### Interactive Components
```python
# Buttons (GUI only)
ui(tu.Button("Click me", on_click=lambda: print("Clicked!")))

# Links (GUI only)
ui(tu.Link("Learn more", on_click=open_docs))

# Text input (GUI only)
ui(tu.TextInput(
    label="Name",
    value="",
    on_change=lambda text: print(f"Changed to: {text}")
))
```

### Auto-Update Components

One of Typer2UI's most powerful features: **components automatically update when modified**!

```python
@app.command()
def process_items():
    # Create and present a table
    table = tu.Table(cols=["Item", "Status"], data=[])
    ui(table)  # Present it

    # Add rows - table auto-updates in real-time!
    for i in range(10):
        table.add_row([f"Item {i}", "Processing..."])
        time.sleep(0.5)

    ui(tu.Md("✓ Complete!"))
```

### Progressive Rendering with Context Managers

For even cleaner code, use context managers:

```python
@app.command()
@ui.command(is_long=True)
def analyze_data():
    # Present and update in one flow
    with ui(tu.Table(cols=["Step", "Progress"], data=[])) as table:
        table.add_row(["Loading", "0%"])
        time.sleep(1)

        table.add_row(["Processing", "50%"])
        time.sleep(1)

        table.add_row(["Complete", "100%"])
```

## GUI Customization

Use the `@ui.command()` decorator to customize command behavior:

```python
@app.command()
@ui.command(is_button=True, is_long=True)
def process():
    """Long-running process with button styling."""
    with ui(tu.Table(cols=["Step", "Status"], data=[])) as t:
        for i in range(10):
            t.add_row([f"Step {i+1}", "Running..."])
            time.sleep(1)
```

**Available options:**

- **`is_button`** (bool): Display command as a highlighted button
- **`is_long`** (bool): Enable real-time output streaming
- **`is_auto_exec`** (bool): Execute automatically when selected

## Comprehensive Example

```python
import typer
import typer2ui as tu
import time

app = typer.Typer()
ui = tu.Ui(app, title="Data Processor", description="Process and analyze data")

@app.command()
def show_report():
    """Display a formatted report."""
    ui(tu.Md("""
# System Report

## Summary
All systems operational.
    """))

    ui(tu.Table(
        cols=["Component", "Status", "Usage"],
        data=[
            ["CPU", "✓", "45%"],
            ["Memory", "✓", "60%"],
            ["Disk", "✓", "70%"],
        ],
        title="System Metrics"
    ))

@app.command()
@ui.command(is_button=True, is_long=True)
def process_files(count: int = 5):
    """Process multiple files with progress updates."""
    ui(tu.Md(f"# Processing {count} files"))

    with ui(tu.Table(cols=["File", "Status"], data=[])) as table:
        for i in range(count):
            table.add_row([f"file_{i}.txt", "Processing..."])
            time.sleep(0.5)

    ui(tu.Md("✓ **All files processed!**"))

@app.command()
def dashboard():
    """Show interactive dashboard."""
    ui(tu.Column([
        tu.Md("# Dashboard"),
        tu.Row([
            tu.Button("Refresh", on_click=lambda: print("Refreshing...")),
            tu.Button("Export", on_click=lambda: print("Exporting...")),
        ]),
        tu.Table(
            cols=["Metric", "Value"],
            data=[
                ["Users", "1,234"],
                ["Revenue", "$56,789"],
                ["Growth", "+12%"],
            ]
        ),
    ]))

@app.command()
def analyze():
    """Return data for automatic display."""
    return tu.Table(
        cols=["Analysis", "Result"],
        data=[
            ["Mean", "42.5"],
            ["Median", "40.0"],
            ["Std Dev", "5.2"],
        ]
    )

if __name__ == "__main__":
    ui.app()
```

## Supported Parameter Types

Typer2UI automatically maps Python types to appropriate GUI controls:

| Python Type | GUI Control | Notes |
|-------------|-------------|-------|
| `str` | Text field | For string input |
| `int` | Text field | Numeric keyboard, validates integers |
| `float` | Text field | Numeric keyboard, validates floats |
| `bool` | Checkbox | For boolean flags |
| `Enum` | Dropdown | Shows all enum values as options |

### Example with Enums

```python
from enum import Enum

class LogLevel(str, Enum):
    DEBUG = "debug"
    INFO = "info"
    WARNING = "warning"
    ERROR = "error"

@app.command()
def configure(level: LogLevel = LogLevel.INFO):
    """Configure logging level."""
    print(f"Log level set to: {level.value}")
```

In the GUI, the `level` parameter will appear as a dropdown with all enum values.

## API Reference

### `Ui` Class

The main entry point for Typer2UI.

**Constructor:**
```python
Ui(app, *, title=None, description=None)
```

**Parameters:**
- `app` (typer.Typer): The Typer application instance
- `title` (str, optional): Window title for the GUI
- `description` (str, optional): Description text shown at the top

**Methods:**

#### `ui(component)` - Universal Output

Output any UI component. Returns the component for chaining/context managers.

```python
# Simple output
ui(tu.Text("Hello"))

# Store reference for updates
table = tu.Table(cols=["Name"], data=[])
ui(table)
table.add_row(["Alice"])  # Auto-updates!

# Context manager
with ui(tu.Table(cols=["Name"], data=[])) as t:
    t.add_row(["Bob"])
```

#### `ui.command(*, is_button=False, is_long=False, is_auto_exec=False)`

Decorator to customize command appearance and behavior.

```python
@app.command()
@ui.command(is_button=True, is_long=True)
def process():
    print("Processing...")
```

#### `ui.app()`

Launch the GUI or run in CLI mode with `--cli` flag.

```bash
python my_app.py              # Launch GUI
python my_app.py --cli hello  # Run CLI
```

### UI Components

All components are in the `typer2ui` module:

```python
import typer2ui as tu

# Simple components
tu.Text("content")           # Plain text
tu.Md("# markdown")          # Markdown

# Data display
tu.Table(
    cols=["A", "B"],         # Column headers
    data=[["1", "2"]],       # Row data
    title="Table Title"      # Optional title
)

# Layout
tu.Row([comp1, comp2])       # Horizontal
tu.Column([comp1, comp2])    # Vertical

# Interactive (GUI only)
tu.Button("text", on_click=callback)
tu.Link("text", on_click=callback)
tu.TextInput("label", value="", on_change=callback)
```

## Examples

Check out the `examples/` directory for working examples:

- **`01_basic_typer_to_gui.py`** - Minimal example showing basic usage
- **`02_arguments_and_output.py`** - Parameters and UI components
- **`03_ui_blocks.py`** - Tables, layout, and composition
- **`04_customizations.py`** - Buttons, streaming, and advanced features

**Run examples:**
```bash
# GUI mode
python examples/01_basic_typer_to_gui.py

# CLI mode
python examples/01_basic_typer_to_gui.py --cli add 5 3
```

## Features

### Current Features

- ✅ Simple, unified API with `ui(component)`
- ✅ Auto-update components when modified
- ✅ Progressive rendering with context managers
- ✅ Rich UI components (Text, Markdown, Table, Row, Column, Button, Link)
- ✅ Automatic GUI generation from Typer commands
- ✅ Type-aware form controls
- ✅ Real-time output streaming (`is_long=True`)
- ✅ Command customization (`is_button`, `is_auto_exec`)
- ✅ Both GUI and CLI modes from single entry point
- ✅ Cross-platform (Windows, macOS, Linux)

### Planned Features

- Path/file selection widgets
- Progress bars and spinners
- Date/time pickers
- Custom themes
- Nested/grouped commands
- Command history
- Tabs and panels

## How It Works

1. **Reflection**: Analyzes your Typer app using Python's introspection
2. **GUI Generation**: Creates Flet-based UI with appropriate controls
3. **Direct Execution**: Calls your command functions directly (not via subprocess)
4. **Component System**: Simple `show_cli()` and `show_gui()` methods for each component
5. **Auto-Update**: Components track when they're presented and update automatically

## Contributing

Contributions are welcome! Please feel free to submit issues or pull requests.

## License

MIT License - see LICENSE file for details.

## Credits

Built with:
- [Typer](https://typer.tiangolo.com/) - CLI framework by Sebastián Ramírez
- [Flet](https://flet.dev/) - GUI framework based on Flutter

---

Made with ❤️ for the Python CLI community
