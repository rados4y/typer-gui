# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

**Typer-UI** is a Python library that automatically generates desktop GUIs for existing Typer CLI applications using Flet. It allows developers to write CLI applications once and run them in both CLI and GUI modes without code duplication.

**Key principle**: Commands call `ui(component)` for output, and the library handles rendering in both CLI (via print) and GUI (via Flet controls) transparently.

## Development Commands

### Setup
```bash
# Create virtual environment
python -m venv .venv

# Activate (Windows)
.venv\Scripts\activate

# Activate (Linux/Mac)
source .venv/bin/activate

# Install in development mode
pip install -e .
```

### Running Examples
```bash
# GUI mode
python examples/01_basic_typer_to_gui.py

# CLI mode (add --cli flag)
python examples/01_basic_typer_to_gui.py --cli add 5 3

# Specific command in CLI mode
python examples/03_ui_blocks.py --cli show-table
```

### Testing
```bash
# Run all tests
python -m pytest tests/ -v

# Run specific test file
python -m pytest tests/test_core.py -v
```

### Type Checking
```bash
mypy typer_ui/
```

## Architecture Overview

### Core Execution Flow

```
User calls app() (UiApp instance)
    ↓
Checks for --cli flag in sys.argv
    ↓
┌─────────────────┬─────────────────┐
│   CLI Mode      │   GUI Mode      │
│   CLIRunner     │   GUIRunner     │
└─────────────────┴─────────────────┘
    ↓                   ↓
Typer handles args   Flet app builds UI
    ↓                   ↓
Command executed     User fills form
    ↓                   ↓
ui(component) called (standalone function)
    ↓
get_current_runner().show(component)
    ↓
component.show_cli(runner) OR component.show_gui(runner)
```

### Three-Stage Pipeline

1. **Reflection** (`spec_builder.py`): Introspects Typer app to extract commands, parameters, and types
2. **Specification** (`specs.py`): Immutable data models (AppSpec, CommandSpec, ParamSpec)
3. **Execution** (`runners/`): CLI or GUI runner executes commands and renders output

### Dual-Channel Architecture

Every UI component implements TWO rendering methods:
- `show_cli(runner)`: Terminal output (uses print)
- `show_gui(runner)`: GUI output (creates Flet controls)

This allows the same `ui(tu.Text("Hello"))` call to work in both modes.

## Key Components

### Entry Point: `UiApp` class (`typer_ui/ui_app.py`)
- Main API wrapper around Typer app
- `app()`: Launches GUI or CLI mode based on --cli flag (callable pattern)
- `app.command(name)`: Returns UICommand wrapper for programmatic control
- `app.state(value)`: Creates reactive state objects
- `app.def_command()`: Decorator for GUI-specific options
  - `button=True`: Display as button in left panel
  - `long=True`: Enable real-time output streaming for long-running commands
  - `auto=True`: Execute automatically when selected, hide submit button
  - `header=True`: Show command name and description (default: True)
  - `auto_scroll=True`: Automatically scroll to end of output after execution (default: True)
  - `view=True`: Convenience flag - sets `auto=True, auto_scroll=False, header=False` (useful for dashboards)

### Standalone Functions (`typer_ui/output.py`)
- `ui(component_or_value)`: Universal output function for displaying components. **When passed a string, it renders as markdown** (e.g., `ui("# Hello")` renders markdown, not plain text)
- `text(value)`: Shortcut for displaying plain text (equivalent to `ui(tu.Text(...))`)
- `dx(renderer, *dependencies)`: Creates dynamic/reactive UI blocks

### Runners (`typer_ui/runners/`)
- **base.py**: Abstract Runner interface
- **cli_runner.py**: CLI execution with stdout/stderr capture
- **gui_runner.py**: Flet-based GUI with form generation and real-time updates

**Important**: Runner context is managed via global `_current_runner` variable set during command execution. This enables `ui()` calls within commands to work without passing runner as parameter.

### UI Components (`typer_ui/ui_blocks.py`)
All components inherit from `UiBlock` abstract base:
- **Simple**: Text, Md (Markdown)
- **Containers**: Table (with auto-update), Row, Column
- **Interactive** (GUI-only): Button, Link, TextInput

**Auto-update mechanism**: Container components track when they're presented and automatically re-render when modified (e.g., `table.add_row()` triggers update).

### Command Control (`typer_ui/ui_app.py`)
`UICommand` provides programmatic command execution:
- `.run(**kwargs)`: Execute and capture output separately
- `.include(**kwargs)`: Execute inline in current context
- `.select()`: Set as current command in GUI
- `.out`: Property to get captured output
- `.result`: Property to get return value

### Specifications (`typer_ui/specs.py`)
Immutable dataclasses that model the app structure:
- `AppSpec`: Complete application model
- `CommandSpec`: Individual command definition
- `ParamSpec`: Parameter with type, default, required flag
- `CommandUiSpec`: GUI options (is_button, is_long, is_auto_exec)
- `ParamType`: Enum mapping Python types to GUI controls

### Spec Builder (`typer_ui/spec_builder.py`)
- `build_app_spec()`: Main entry point for reflection
- Extracts commands from Typer app's `registered_commands`
- Uses `inspect.signature()` to analyze parameters
- Maps Python types to ParamType enum (str→STRING, int→INTEGER, bool→BOOLEAN, Enum→ENUM)

## Important Patterns

### Output Capture in CLI Mode
Uses `io.StringIO` with `redirect_stdout()` and `redirect_stderr()` to capture both:
- Traditional `print()` calls
- Output from `ui(component)` via show_cli()

Returns tuple: `(result, exception, output_text)`

### Real-Time Streaming in GUI Mode
For commands marked `long=True`, uses custom `_RealTimeWriter` that:
- Buffers partial output
- Emits complete lines immediately to GUI
- Allows progressive rendering for long-running commands

### Progressive Rendering
Container components support context managers:
```python
with ui(tu.Table(cols=["Name"], data=[])) as table:
    table.add_row(["Alice"])  # Auto-updates in real-time
```

Implementation:
- `__enter__` sets runner context
- Modifications call `_update()` which triggers `runner.update(component)`
- `__exit__` clears context

### Type-to-Control Mapping
`_get_param_type()` in spec_builder.py maps:
- `str` → TextField
- `int`, `float` → TextField with numeric validation
- `bool` → Checkbox
- `Enum` → Dropdown with enum values
- Unsupported types → UNSUPPORTED (error in GUI)

## Critical Implementation Details

### Runner Lifecycle
```python
# In app() (UiApp.__call__):
runner = CLIRunner() or GUIRunner()
set_current_runner(runner)
# Execute command
set_current_runner(None)
```

### Component Presentation Tracking
Components track if they've been presented:
- `_mark_presented(runner)`: Called when `ui(component)` is invoked
- `_presented`: Boolean flag
- `_presentation_runner`: Reference to runner that presented it
- Used to enable auto-update when component is modified

### GUI Layout Structure
```
Flet Page
├── Header (title + description)
└── Content Row
    ├── Left Panel (command list)
    └── Right Panel
        ├── Form (parameter inputs)
        ├── Run button
        └── Output view
```

## File Organization

```
typer_ui/
├── __init__.py          # Public API exports
├── ui_app.py            # Main UiApp class and UICommand controller
├── output.py            # Standalone functions: ui(), text(), dx()
├── ui_blocks.py         # UI component definitions
├── state.py             # Reactive state management
├── specs.py             # Immutable data models
├── spec_builder.py      # Reflection/introspection
└── runners/
    ├── base.py          # Abstract Runner
    ├── cli_runner.py    # CLI execution
    └── gui_runner.py    # Flet/GUI execution
```

## Common Development Tasks

### Adding a New UI Component

1. Create class in `ui_blocks.py` inheriting from `UiBlock`
2. Implement `show_cli(runner)` for terminal output
3. Implement `show_gui(runner)` for Flet control creation
4. Export in `__init__.py`

Example:
```python
class MyComponent(UiBlock):
    def show_cli(self, runner):
        print(self.content)

    def show_gui(self, runner):
        import flet as ft
        runner.add_to_output(ft.Text(self.content))
```

### Adding a New Parameter Type

1. Add enum value to `ParamType` in `specs.py`
2. Update `_get_param_type()` in `spec_builder.py`
3. Update `_create_input_control()` in `gui_runner.py`

### Testing Commands Programmatically

Commands can be tested in both CLI and GUI modes:
```bash
# CLI mode - output goes to stdout
python examples/03_ui_blocks.py --cli calc --x 10 --y 5

# GUI mode - visual inspection
python examples/03_ui_blocks.py
```

## Package Notes

- Python 3.10+ required
- Dependencies: `typer>=0.9.0`, `flet>=0.20.0`
- Package name: `typer-ui` (note: hyphen in package name, underscore in import)
- Import pattern (dual import):
  ```python
  import typer_ui as tu              # For components: tu.Table, tu.Row, etc.
  from typer_ui import ui, text, dx  # For standalone functions
  ```

## API Pattern

```python
import typer
import typer_ui as tu
from typer_ui import ui, text, dx

# Create Typer app
typer_app = typer.Typer()

# Create UiApp instance
app = tu.UiApp(
    typer_app,
    title="My Application",
    description="Description here"
)

# Define commands
@typer_app.command()
@app.def_command(button=True)
def my_command():
    # ui(str) renders as markdown
    ui("# Hello World")
    ui("This is **bold** text")

    # For plain text, use text()
    text("This is plain text, not markdown")

    # Components via tu prefix
    ui(tu.Table(...))

    # Reactive UI with dx()
    counter = app.state(0)
    ui(dx(lambda: f"Count: {counter.value}", counter))

# Dashboard/view command (auto-executes, no header, no scroll)
@typer_app.command()
@app.def_command(view=True)
def dashboard():
    ui("# Dashboard")
    ui(tu.Table(cols=["Metric", "Value"], data=[...]))

# Launch app
if __name__ == "__main__":
    app()  # Callable pattern
```

## Examples Structure

Examples are numbered progressively:
- **01**: Basic conversion (minimal example)
- **02**: Parameters and output types
- **03**: UI blocks and components
- **04**: Application control (app.command() API)
- **05**: State management and reactive UI

Each example is self-contained and runnable in both CLI and GUI modes.
