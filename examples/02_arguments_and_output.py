"""Example 2: Parameters and UI Components

This example demonstrates:
- Different parameter types (str, int, bool, enum)
- UI components (Text, Markdown, Table)
- Long-running commands (is_long)
- Auto-execute commands (is_auto_exec)
- Button styling (is_button)
"""

import typer
import typer_ui as tg
import time
from enum import Enum

app = typer.Typer()
ui = tg.Ui(
    app,
    title="Parameters & Components",
    description="Parameter types and UI components"
)


class Priority(str, Enum):
    """Priority levels for tasks."""
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    URGENT = "urgent"


@app.command()
@ui.command(is_button=True)
def greet(name: str = "World", times: int = 1, excited: bool = False):
    """Greet someone - demonstrates string, integer, and boolean parameters."""
    greeting = f"Hello, {name}!"
    if excited:
        greeting += " How exciting!"

    for _ in range(times):
        ui(tg.Text(greeting))


@app.command()
def create_task(title: str, priority: Priority = Priority.MEDIUM):
    """Create a task - demonstrates enum parameter (renders as dropdown)."""
    ui(tg.Md("## Task Created"))
    ui(tg.Table(
        cols=["Field", "Value"],
        data=[
            ["Title", title],
            ["Priority", priority.value],
        ]
    ))


@app.command()
def markdown_demo():
    """Markdown output - demonstrates Markdown component for rich formatting."""
    ui(tg.Md("""
# Markdown Example

Format text with **bold**, *italic*, and `code`.

## Features
- Rich formatting in GUI
- Plain text fallback in CLI
- Tables, lists, and more

| Feature | Status |
|---------|--------|
| Tables  | [OK]   |
| Code    | [OK]   |
| Links   | [OK]   |
"""))


@app.command()
@ui.command(is_long=True)
def long_process(steps: int = 5):
    """Long process - demonstrates is_long for real-time output streaming."""
    ui(tg.Md(f"## Processing {steps} steps"))

    # Progressive table updates
    with ui(tg.Table(cols=["Step", "Status"], data=[])) as table:
        for i in range(1, steps + 1):
            table.add_row([f"Step {i}/{steps}", "Processing..."])
            time.sleep(0.8)

    ui(tg.Md("[OK] **All done!**"))


@app.command()
@ui.command(is_auto_exec=True)
def welcome():
    """Welcome screen - demonstrates is_auto_exec (runs automatically when selected)."""
    ui(tg.Md("""
# Welcome! 👋

This command runs **automatically** when selected.

## When to use is_auto_exec
- Info screens and dashboards
- Commands with no required parameters
- Display-only commands
"""))


if __name__ == "__main__":
    ui.app()


"""
CLI Examples:
-------------
python examples/02_arguments_and_output.py --cli greet --name Alice --times 3 --excited
python examples/02_arguments_and_output.py --cli create-task "Fix bug" --priority urgent
python examples/02_arguments_and_output.py --cli long-process --steps 3
"""
