# UIApp and UICommand Guide

This guide explains the new `UIApp` and `UICommand` classes that provide programmatic access to the application UI, commands, and execution context.

## Overview

The `UIApp` and `UICommand` classes enable advanced UI operations and extensions by providing:

1. **UIApp** - Application-level context with access to:
   - Current command being executed
   - List of all commands
   - UI block references (header, body)

2. **UICommand** - Command-level operations with:
   - Command execution (`run()`, `include()`)
   - Command selection (`select()`)
   - Output capture
   - UI block references (title, arguments, actions, result)

## Accessing UIApp

The `UIApp` instance is accessible through the `Ui` class using the `runtime` property:

```python
import typer
import typer_gui

app = typer.Typer()
ui = typer_gui.Ui(app, title="My App")

@app.command()
def my_command():
    # Access UIApp during command execution
    if ui.runtime:
        current_cmd = ui.runtime.cmd
        all_commands = ui.runtime.commands
        header_block = ui.runtime.blocks.header
```

**Important Notes:**
- `ui.runtime` is only available during GUI mode command execution
- Returns `None` in CLI mode or before GUI starts
- The name `runtime` was chosen to avoid conflict with the `ui.app()` method used to launch the application

## UIApp Reference

### Properties

#### `cmd: Optional[UICommand]`
Reference to the currently selected or executing command.

```python
current = ui.runtime.cmd
if current:
    print(f"Current command: {current.name}")
```

#### `commands: List[UICommand]`
List of all UICommand instances in the application.

```python
for cmd in ui.runtime.commands:
    print(f"Command: {cmd.name}")
```

### Methods

#### `get_command(name: str) -> Optional[UICommand]`
Get a command by name.

```python
greet_cmd = ui.runtime.get_command("greet")
if greet_cmd:
    greet_cmd.run(name="Alice")
```

### UI Blocks

#### `blocks.header: ft.Container`
Reference to the header container. You can add custom Flet components here.

```python
import flet as ft

if ui.runtime:
    # Add a custom button to the header
    custom_btn = ft.ElevatedButton(text="Custom Action")
    if ui.runtime.blocks.header and ui.runtime.blocks.header.content:
        ui.runtime.blocks.header.content.controls.append(custom_btn)
```

#### `blocks.body: ft.Column`
Reference to the main application body container (the form area).

## UICommand Reference

### Properties

#### `name: str`
The command name.

```python
cmd = ui.runtime.get_command("greet")
print(cmd.name)  # "greet"
```

#### `output: Optional[str]`
Captured output from the last execution.

```python
cmd.run(name="Alice")
print(cmd.output)  # "Hello, Alice!"
```

#### `result: Any`
Return value from the last execution.

```python
result = cmd.run(a=5, b=3)
print(cmd.result)  # 8
```

### Methods

#### `select() -> None`
Select this command in the UI, updating the form to show its parameters.

```python
@app.command()
def navigate():
    """Navigate to another command."""
    other_cmd = ui.runtime.get_command("settings")
    if other_cmd:
        other_cmd.select()
```

#### `run(**kwargs) -> Any`
Execute this command with given parameters. Captures output and stores result.

```python
greet_cmd = ui.runtime.get_command("greet")
result = greet_cmd.run(name="Alice", excited=True)
print(f"Result: {result}")
print(f"Output: {greet_cmd.output}")
```

#### `include(**kwargs) -> Any`
Execute this command within the context of the current command. Unlike `run()`:
- Output goes to current context (not captured separately)
- Useful for composing commands

```python
@app.command()
def batch_greet():
    """Greet multiple people."""
    greet_cmd = ui.runtime.get_command("greet")

    # Output appears inline in current command's output
    greet_cmd.include(name="Alice")
    greet_cmd.include(name="Bob")
    greet_cmd.include(name="Charlie")
```

### UI Blocks

#### `blocks.title: ft.Container`
Container with the command title and description.

#### `blocks.arguments: ft.Container`
Container with the command parameter input controls.

#### `blocks.actions: ft.Container`
Container with the "Run Command" button.

#### `blocks.result: ft.ListView`
Container (ListView) that displays command execution results.

```python
@app.command()
def customize_ui():
    """Customize the current command's UI."""
    if ui.runtime and ui.runtime.cmd:
        # Access current command's blocks
        title_block = ui.runtime.cmd.blocks.title
        args_block = ui.runtime.cmd.blocks.arguments

        # You can modify these containers to customize the UI
        # (advanced usage - be careful!)
```

## Usage Examples

### Example 1: Command Composition

```python
@app.command()
def process_data(input_file: str):
    """Process data from a file."""
    print(f"Processing {input_file}...")
    # ... processing logic ...
    return {"status": "success", "rows": 100}

@app.command()
def batch_process():
    """Process multiple files."""
    if not ui.runtime:
        return

    process_cmd = ui.runtime.get_command("process-data")
    files = ["data1.csv", "data2.csv", "data3.csv"]

    results = []
    for file in files:
        result = process_cmd.include(input_file=file)
        results.append(result)

    print(f"\nProcessed {len(results)} files")
    return results
```

### Example 2: Navigation

```python
@app.command()
def quick_links():
    """Show quick navigation links."""
    if not ui.runtime:
        return

    # Create navigation using ui.link blocks
    ui.link("Go to Settings", "settings")
    ui.link("Run Report", "generate-report")
    ui.link("View Data", "show-data")
```

### Example 3: Dynamic Command Execution

```python
@app.command()
def run_tests():
    """Run all test commands."""
    if not ui.runtime:
        return

    # Find all commands with "test" in the name
    test_commands = [
        cmd for cmd in ui.runtime.commands
        if "test" in cmd.name
    ]

    print(f"Running {len(test_commands)} test commands...\n")

    for cmd in test_commands:
        print(f"--- {cmd.name} ---")
        try:
            cmd.include()  # Run with no arguments
        except Exception as e:
            print(f"Error: {e}")
```

### Example 4: Accessing UI State

```python
@app.command()
def show_app_info():
    """Display application information."""
    if not ui.runtime:
        print("Not running in GUI mode")
        return

    print(f"Application: {ui.runtime._gui_model.title}")
    print(f"Total commands: {len(ui.runtime.commands)}")
    print(f"Current command: {ui.runtime.cmd.name if ui.runtime.cmd else 'None'}")

    print("\nAvailable commands:")
    for cmd in ui.runtime.commands:
        print(f"  - {cmd.name}")
```

## CLI Mode Behavior

In CLI mode (when using `--cli` flag), `ui.runtime` returns `None`:

```python
@app.command()
def my_command():
    if ui.runtime:
        # GUI mode - use UIApp features
        print("Running in GUI mode")
    else:
        # CLI mode - fallback behavior
        print("Running in CLI mode")
```

## Best Practices

1. **Always check for None**: Always check if `ui.runtime` exists before using it
2. **Use include() for composition**: Use `include()` when composing commands to keep output inline
3. **Use run() for isolation**: Use `run()` when you need to capture output separately
4. **Avoid modifying blocks directly**: Modifying UI blocks directly is advanced usage and should be done carefully

## API Summary

```python
# Accessing UIApp
ui.runtime -> Optional[UIApp]

# UIApp properties and methods
ui.runtime.cmd -> Optional[UICommand]
ui.runtime.commands -> List[UICommand]
ui.runtime.get_command(name) -> Optional[UICommand]
ui.runtime.blocks.header -> ft.Container
ui.runtime.blocks.body -> ft.Column

# UICommand properties and methods
cmd.name -> str
cmd.output -> Optional[str]
cmd.result -> Any
cmd.select() -> None
cmd.run(**kwargs) -> Any
cmd.include(**kwargs) -> Any
cmd.blocks.title -> ft.Container
cmd.blocks.arguments -> ft.Container
cmd.blocks.actions -> ft.Container
cmd.blocks.result -> ft.ListView
```
