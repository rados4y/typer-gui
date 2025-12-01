# Typer-GUI

Automatically generate desktop GUIs for existing [Typer](https://typer.tiangolo.com/) CLI applications using [Flet](https://flet.dev/).

## Overview

**Typer-GUI** is a Python library that bridges the gap between command-line interfaces and graphical user interfaces. If you have a Typer-based CLI application, you can instantly create a desktop GUI for it with just a few lines of code.

Key features:

- **Zero or minimal code changes** to your existing Typer app
- **Automatic GUI generation** from Typer commands and parameters
- **Type-aware controls** - text fields, dropdowns, checkboxes based on parameter types
- **Real-time output streaming** - see output as it's produced for long-running commands
- **Markdown rendering** - rich formatted output with headings, lists, code blocks, and more
- **Auto-execution** - commands that run immediately when selected
- **Custom styling** - highlight important commands as buttons
- **Clean, modern interface** powered by Flet

## Installation

### Using pip

```bash
pip install typer-gui
```

This will automatically install `typer` and `flet` as dependencies if they're not already present.

### For development

If you're contributing to typer-gui or want to try it locally, you can use `uv` (optional but recommended for faster dependency management):

```bash
# Clone the repository
git clone https://github.com/yourusername/typer-gui.git
cd typer-gui

# Create a virtual environment with uv (optional)
uv venv
source .venv/bin/activate  # On Windows: .venv\Scripts\activate

# Install in development mode
uv pip install -e .

# Or with standard pip
pip install -e .
```

## Quick Start

Here's a minimal example to get you started:

### Option 1: Integrated API (Recommended)

```python
# my_app.py
import typer
import typer_gui

# Create the Typer app
app = typer.Typer()

# Create the UI wrapper
ui = typer_gui.Ui(
    app,
    title="My App GUI",
    description="A graphical interface for my CLI app"
)

@app.command()
def greet(name: str, excited: bool = False):
    """Greet someone with a friendly message."""
    punctuation = "!" if excited else "."
    print(f"Hello {name}{punctuation}")

@app.command()
def add(a: int, b: int):
    """Add two numbers together."""
    result = a + b
    print(f"{a} + {b} = {result}")

if __name__ == "__main__":
    # Launch the GUI
    ui.app()
```

Run it:
```bash
# Launch GUI
python my_app.py

# Or run CLI directly with --cli flag
python my_app.py --cli greet "World" --excited
python my_app.py --cli add 5 10
```

### Option 2: Separate GUI Runner

If you prefer to keep your CLI and GUI code separate:

```python
# my_app.py
import typer

app = typer.Typer()

@app.command()
def greet(name: str, excited: bool = False):
    """Greet someone with a friendly message."""
    punctuation = "!" if excited else "."
    print(f"Hello {name}{punctuation}")

if __name__ == "__main__":
    app()
```

```python
# my_app_gui.py
import typer_gui
from my_app import app

if __name__ == "__main__":
    ui = typer_gui.Ui(
        app,
        title="My App GUI",
        description="A graphical interface for my CLI app"
    )
    ui.app()
```

Run it:
```bash
python my_app_gui.py
```

That's it! Your CLI app now has a fully functional GUI.

## GUI Layout

The generated GUI has three main areas:

```
┌─────────────────────────────────────────┐
│  Title and Description (if provided)    │
├──────────┬──────────────────────────────┤
│          │                              │
│ Commands │  Parameter Form              │
│  List    │  - Input fields              │
│          │  - Dropdowns                 │
│          │  - Checkboxes                │
│          │  - [Run Command] button      │
│          │                              │
│          ├──────────────────────────────┤
│          │  Output Console              │
│          │  (stdout/stderr)             │
└──────────┴──────────────────────────────┘
```

## GUI Customization

Typer-GUI provides decorators to customize how commands appear and behave in the GUI. These work alongside your Typer decorators.

### Using `@ui.command()`

The `@ui.command()` decorator adds GUI-specific options to your commands:

```python
import typer
import typer_gui

app = typer.Typer()
ui = typer_gui.Ui(app, title="My App")

@app.command()
@ui.command(is_button=True, is_long=True)
def process():
    """Long-running process with real-time output."""
    for i in range(10):
        print(f"Processing step {i}...")
        time.sleep(1)
```

**Available options:**

- **`is_button`** (bool): Display command as a highlighted button instead of a text link
  ```python
  @ui.command(is_button=True)
  ```

- **`is_long`** (bool): Enable real-time output streaming for long-running commands
  ```python
  @ui.command(is_long=True)
  ```

- **`is_markdown`** (bool): Render the command's return value as Markdown
  ```python
  @app.command()
  @ui.command(is_markdown=True)
  def info() -> str:
      return "# Hello\n\nThis is **bold** text!"
  ```

- **`is_auto_exec`** (bool): Execute automatically when selected (hides "Run Command" button)
  ```python
  @app.command()
  @ui.command(is_auto_exec=True)
  def status():
      print(f"Current time: {datetime.now()}")
  ```

### Using `@gui_command()` (Alternative)

If you're using the separate runner approach, use `@gui_command()` instead:

```python
from typer_gui import gui_command
import typer

app = typer.Typer()

@app.command()
@gui_command(is_button=True, is_long=True)
def process():
    """Long-running process."""
    for i in range(10):
        print(f"Step {i}")
        time.sleep(1)
```

The options are identical to `@ui.command()`.

### Markdown Output Example

```python
@app.command()
@ui.command(is_markdown=True)
def report() -> str:
    """Generate a formatted report."""
    return """
# System Report

## Status
- **CPU**: OK
- **Memory**: OK
- **Disk**: OK

## Details

| Component | Status | Usage |
|-----------|--------|-------|
| CPU       | ✓      | 45%   |
| Memory    | ✓      | 60%   |
| Disk      | ✓      | 70%   |

```python
# Example code block
print("Hello World")
```
"""
```

## Supported Parameter Types

Typer-GUI automatically maps Python types to appropriate GUI controls:

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
import typer

class Color(str, Enum):
    RED = "red"
    GREEN = "green"
    BLUE = "blue"

app = typer.Typer()

@app.command()
def paint(color: Color):
    """Paint with a color."""
    print(f"Painting with {color.value}!")
```

In the GUI, the `color` parameter will appear as a dropdown with "red", "green", and "blue" as options.

## API Reference

### `Ui` Class

The main entry point for typer-gui's integrated API.

**Constructor:**
```python
Ui(app, *, title=None, description=None)
```

**Parameters:**
- `app` (typer.Typer): The Typer application instance to extend
- `title` (str, optional): Window title for the GUI
- `description` (str, optional): Description text shown at the top of the GUI

**Methods:**

#### `ui.command(*, is_button=False, is_long=False, is_markdown=False, is_auto_exec=False)`

Decorator to add GUI-specific options to a Typer command.

**Parameters:**
- `is_button` (bool): Display as a button in the left panel
- `is_long` (bool): Enable real-time output streaming for long-running commands
- `is_markdown` (bool): Render return value as Markdown
- `is_auto_exec` (bool): Execute automatically when selected, hide 'Run Command' button

**Example:**
```python
import typer
import typer_gui

app = typer.Typer()
ui = typer_gui.Ui(app, title="My App")

@app.command()
@ui.command(is_button=True, is_long=True)
def process():
    for i in range(10):
        print(f"Step {i}")
        time.sleep(1)

if __name__ == "__main__":
    ui.app()
```

#### `ui.app()`

Launch the GUI application or run in CLI mode with `--cli` flag.

By default, `ui.app()` launches the GUI. However, you can bypass the GUI and run the CLI directly by passing the `--cli` flag.

**GUI Mode (default):**
```python
if __name__ == "__main__":
    ui.app()
```

**CLI Mode:**
```bash
# Run with GUI (default)
python my_app.py

# Run with CLI (bypasses GUI)
python my_app.py --cli greet "Alice" --excited
python my_app.py --cli add 5 3
python my_app.py --cli --help  # Show all commands
```

This allows you to have a single entry point that supports both GUI and CLI modes, giving your users flexibility in how they interact with your application.

---

### `gui_command(*, is_button=False, is_long=False, is_markdown=False, is_auto_exec=False)`

Decorator to add GUI-specific options to a Typer command (standalone decorator).

**Parameters:**
- `is_button` (bool): Display as a button in the left panel
- `is_long` (bool): Enable real-time output streaming
- `is_markdown` (bool): Render return value as Markdown
- `is_auto_exec` (bool): Execute automatically when selected

**Example:**
```python
from typer_gui import gui_command
import typer

app = typer.Typer()

@app.command()
@gui_command(is_button=True, is_markdown=True)
def info() -> str:
    return "# Hello **World**!"
```

---

### `build_gui_model(app, *, title=None, description=None)`

Build a structured representation of a Typer app (useful for testing or custom implementations).

**Parameters:**
- `app` (typer.Typer): A Typer application instance
- `title` (str, optional): App title
- `description` (str, optional): App description

**Returns:**
- `GuiApp`: A structured model containing commands and parameters

**Example:**
```python
from typer_gui import build_gui_model

gui_model = build_gui_model(app)
for command in gui_model.commands:
    print(f"Command: {command.name}")
    for param in command.params:
        print(f"  - {param.name}: {param.param_type}")
```

---

### `Markdown` Class

A return type for commands that produce Markdown output (alternative to `is_markdown=True`).

**Example:**
```python
from typer_gui import Markdown

@app.command()
def info() -> Markdown:
    return Markdown("# Hello\n\nThis is **bold** text!")
```

**Note:** Using `is_markdown=True` and returning a string is the preferred approach.

## Examples

Check out the `examples/` directory for comprehensive working examples:

- **`examples/basic_typer_app.py`** - A complete demonstration featuring:
  - Multiple command types (greet, add, calculate, paint)
  - Enum parameters with dropdown selection
  - Button-styled commands (`is_button=True`)
  - Long-running commands with real-time output (`is_long=True`)
  - Markdown-formatted output (`is_markdown=True`)
  - Auto-executing commands (`is_auto_exec=True`)
  - Combination features (e.g., button + long-running)

- **`examples/basic_gui_runner.py`** - Alternative approach showing separate GUI runner

**To run the main example:**

```bash
# Using the integrated approach
python examples/basic_typer_app.py

# Or using the separate runner
python examples/basic_gui_runner.py
```

**For development with auto-reload:**

```bash
uv run flet run examples/basic_typer_app.py --reload
```

## Running Tests

The library includes unit tests for the core reflection logic:

```bash
# Install dev dependencies
pip install -e ".[dev]"

# Run tests
pytest
```

## Features & Limitations

### Current Features

- ✅ Automatic reflection of Typer commands and parameters
- ✅ Support for str, int, float, bool, and Enum types
- ✅ Required and optional parameters with validation
- ✅ Default values
- ✅ Help text and descriptions
- ✅ Live output capture (stdout/stderr)
- ✅ **Real-time output streaming** for long-running commands (`is_long=True`)
- ✅ **Markdown rendering** for rich formatted output (`is_markdown=True`)
- ✅ **Auto-execution** - commands that run on selection (`is_auto_exec=True`)
- ✅ **Button styling** for important commands (`is_button=True`)
- ✅ **Integrated API** with `Ui` class for cleaner code
- ✅ Output clearing when switching between commands
- ✅ Clean, modern UI powered by Flet
- ✅ Cross-platform (Windows, macOS, Linux)

### Planned Features

- Path/file selection widgets
- Support for list/multiple value parameters
- Date/time pickers
- Custom themes and color schemes
- Nested/grouped commands
- Command history
- Progress bars and status indicators
- Command search/filtering

### Known Limitations

- Unsupported parameter types fall back to text input
- Long-running commands without `is_long=True` will block the UI
- No built-in progress bars (commands must print their own progress)

## How It Works

1. **Reflection**: Typer-GUI uses Python's introspection (`inspect` module) to analyze your Typer app, extracting command names, parameter types, defaults, and help text from function signatures.

2. **Decorator Metadata**: The `@ui.command()` or `@gui_command()` decorators attach GUI-specific metadata (button styling, streaming, markdown, auto-exec) to your functions without affecting Typer's CLI behavior.

3. **GUI Generation**: Based on the reflection data and decorator metadata, it generates a Flet-based GUI with appropriate controls for each parameter type (text fields, dropdowns, checkboxes).

4. **Direct Execution**: When you click "Run" (or when auto-exec triggers), the GUI calls your command function directly (not via subprocess), passing the parsed and validated parameters.

5. **Output Capture**:
   - **Regular commands**: stdout and stderr are buffered and displayed when the command completes
   - **Long-running commands** (`is_long=True`): Output is streamed in real-time as it's produced using custom IO writers
   - **Markdown commands** (`is_markdown=True`): Return values are rendered with GitHub-flavored markdown formatting

## Publishing Releases

For maintainers: To publish a new version to PyPI:

1. **Update the version** in `pyproject.toml`:
   ```toml
   version = "0.2.0"  # Increment as appropriate
   ```

2. **Commit the version change**:
   ```bash
   git add pyproject.toml
   git commit -m "Bump version to 0.2.0"
   git push
   ```

3. **Run the release script**:
   ```bash
   # Cross-platform (recommended)
   python release.py

   # Or on Windows
   release.bat

   # Or on Linux/Mac
   ./release.sh
   ```

The script will:
- Clean previous builds
- Build the package (source distribution + wheel)
- Upload to PyPI (you'll be prompted for your API token)

**Note**: You need a PyPI API token stored in `~/.pypirc` or will be prompted to enter it.

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
