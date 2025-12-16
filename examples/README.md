# Typer-GUI Examples

This directory contains progressive examples demonstrating how to use Typer-GUI.

## Getting Started

Each example is numbered and builds upon previous concepts. Start with example 01 and work your way through.

## Examples Overview

### 01. Basic Typer to GUI
**File:** `01_basic_typer_to_gui.py`

The simplest way to add a GUI to your Typer application. Shows the minimal code changes needed.

**Key Concepts:**
- Creating a `Ui` instance
- Wrapping existing Typer commands
- Running in both GUI and CLI modes

**Run:**
```bash
# GUI mode
python 01_basic_typer_to_gui.py

# CLI mode
python 01_basic_typer_to_gui.py --cli add 5 3
```

---

### 02. Parameters and Command Options
**File:** `02_arguments_and_output.py`

Demonstrates parameter types and command options.

**Key Concepts:**
- Parameter types: str, int, bool, enum
- Markdown output: `ui.out.md()`
- Command options: `is_button`, `is_long`, `is_auto_exec`

**Commands:**
- `greet` - Parameter types (str, int, bool)
- `create-task` - Enum parameter (dropdown)
- `markdown-demo` - Markdown formatting
- `long-process` - Real-time output streaming
- `welcome` - Auto-execute demo

**Run:**
```bash
# GUI mode
python 02_arguments_and_output.py

# CLI mode
python 02_arguments_and_output.py --cli greet --name Alice
python 02_arguments_and_output.py --cli create-task "Fix bug" --priority urgent
python 02_arguments_and_output.py --cli long-process --steps 3
```

---

### 03. UI Blocks and UICommand Methods
**File:** `03_ui_blocks.py`

Demonstrates UI Blocks, UICommand methods, auto-executed vs manual commands, and passing parameters.

**Key Concepts:**
- `ui.out.table()` - Display tabular data
- `ui.out.md()` - Markdown formatting
- `ui.out.link()` - Interactive navigation links (GUI only)
- `ui.command(name).select()` - Navigate to command
- `ui.command(name).run(**params)` - Execute with params, capture output/result
- `ui.command(name).include(**params)` - Execute with params inline
- `ui.command(name).clear()` - Clear output (auto-exec re-runs after clear)
- Auto-exec commands run automatically when selected or after clear()

**Commands:**
- `show-table` - Display random user data (auto-exec)
- `show-markdown` - Display random stats (auto-exec)
- `calc` - Simple calculator with parameters (manual, NOT auto-exec)
- `command-methods` - Interactive demo of all UICommand methods (auto-exec)

**Run:**
```bash
# GUI mode
python 03_ui_blocks.py

# CLI mode
python 03_ui_blocks.py --cli show-table
python 03_ui_blocks.py --cli show-markdown
python 03_ui_blocks.py --cli calc --x 100 --y 25
```

---

### 04. Advanced Customizations
**File:** `04_customizations.py`

Advanced customizations with command options and UIApp features.

**Key Concepts:**
- `@ui.options(is_button=True)` - Display as prominent button
- `@ui.options(is_long=True)` - Real-time output streaming
- `@ui.options(is_auto_exec=True)` - Auto-execute when selected
- `ui.runtime` - Access UIApp instance
- `ui.command(name)` - Get command by name
- `cmd.run()` - Command composition
- `ui.out.button()` - Interactive buttons with icons

**Commands:**
- `quick-action` - Button-styled command demo
- `long-process` - Real-time streaming demo
- `welcome-screen` - Auto-execute demo
- `app-info` - UIApp access demo
- `composed-calculation` - Command composition demo
- `button-menu` - Interactive button menu

**Run:**
```bash
# GUI mode
python 04_customizations.py

# CLI mode
python 04_customizations.py --cli quick-action
python 04_customizations.py --cli long-process --steps 3
python 04_customizations.py --cli composed-calculation --x 10 --y 5
```

---

## Running Examples

### GUI Mode
Simply run the example without any arguments:
```bash
python 01_basic_typer_to_gui.py
```

### CLI Mode
Add `--cli` flag followed by the command and its arguments:
```bash
python 01_basic_typer_to_gui.py --cli add 5 3
```

### Getting Help
Use `--help` to see available commands in CLI mode:
```bash
python 01_basic_typer_to_gui.py --cli --help
python 01_basic_typer_to_gui.py --cli add --help
```

## Progressive Learning Path

1. **Start with 01**: Learn the basics of converting a Typer app to GUI
2. **Move to 02**: Understand different parameter types and output modes
3. **Explore 03**: Create rich output with UI Blocks
4. **Master 04**: Advanced programmatic control with UIApp/UICommand

## Common Patterns

### Basic Command
```python
@app.command()
def my_command(name: str):
    print(f"Hello, {name}!")
```

### Command with GUI Options
```python
@app.command()
@ui.command(is_button=True, is_long=True)
def process_data():
    print("Processing...")
```

### Command with UI Blocks
```python
@app.command()
def show_data():
    ui.out.table(
        headers=["Col1", "Col2"],
        rows=[["A", "B"], ["C", "D"]]
    ).present()
```

### Command with UIApp Access
```python
@app.command()
def orchestrator():
    if ui.runtime:
        other_cmd = ui.runtime.get_command("other-command")
        result = other_cmd.run(param="value")
```

## Additional Resources

- **Main Documentation**: See `/docs` directory
- **API Reference**: Check `UIApp_UICommand_Guide.md` in `/docs`
- **Source Code**: Browse `/typer_gui` for implementation details

## Need Help?

If you have questions or run into issues:
1. Check the docstrings in each example
2. Review the comments in the code
3. Read the documentation in `/docs`
4. Open an issue on GitHub

---

Happy coding! 🚀
