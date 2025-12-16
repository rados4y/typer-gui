"""Example 2: Parameters and Command Options

This example demonstrates:
- Different parameter types (str, int, bool, enum)
- Markdown output with ui.out.md()
- Long-running commands (is_long)
- Auto-execute commands (is_auto_exec)
- Button styling (is_button)
"""

import typer
import typer_gui
import time
from enum import Enum

app = typer.Typer()
ui = typer_gui.Ui(
    app,
    title="Parameters & Options",
    description="Parameter types and command options"
)


class Priority(str, Enum):
    """Priority levels for tasks."""
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    URGENT = "urgent"


@app.command()
@ui.options(is_button=True)
def greet(name: str = "World", times: int = 1, excited: bool = False):
    """Greet someone - demonstrates string, integer, and boolean parameters."""
    greeting = f"Hello, {name}!"
    if excited:
        greeting += " How exciting!"

    for _ in range(times):
        print(greeting)


@app.command()
def create_task(title: str, priority: Priority = Priority.MEDIUM):
    """Create a task - demonstrates enum parameter (renders as dropdown)."""
    print(f"✓ Task created: {title}")
    print(f"  Priority: {priority.value}")


@app.command()
def markdown_demo():
    """Markdown output - demonstrates ui.out.md() for rich formatting."""
    ui.out.md("""
# Markdown Example

Format text with **bold**, *italic*, and `code`.

## Features
- Rich formatting in GUI
- Plain text fallback in CLI
- Tables, lists, and more

| Feature | Status |
|---------|--------|
| Tables  | ✓      |
| Code    | ✓      |
| Links   | ✓      |
""").present()


@app.command()
@ui.options(is_long=True)
def long_process(steps: int = 5):
    """Long process - demonstrates is_long for real-time output streaming."""
    print("Starting process...\n")

    for i in range(1, steps + 1):
        print(f"[{i}/{steps}] Processing...")
        time.sleep(0.8)
        print(f"  ✓ Step {i} complete\n")

    print("All done!")


@app.command()
@ui.options(is_auto_exec=True)
def welcome():
    """Welcome screen - demonstrates is_auto_exec (runs automatically when selected)."""
    ui.out.md("""
# Welcome! 👋

This command runs **automatically** when selected.

## When to use is_auto_exec
- Info screens and dashboards
- Commands with no required parameters
- Display-only commands
""").present()


if __name__ == "__main__":
    ui.app()


"""
CLI Examples:
-------------
python 02_arguments_and_output.py --cli greet --name Alice --times 3 --excited
python 02_arguments_and_output.py --cli create-task "Fix bug" --priority urgent
python 02_arguments_and_output.py --cli long-process --steps 3
"""
