"""Example 2: Parameters, Outputs, and Async

This example demonstrates:
- Handling different parameter types (str, int, bool, enum).
- Displaying various output components (Text, Markdown, Table).
- Long-running commands with real-time updates.
- Asynchronous command execution (CLI mode only).
- Auto-executing commands for welcome screens or dashboards.
"""

import asyncio
import time
from enum import Enum

import typer
import typer_ui as tg

app = typer.Typer()
ui = tg.Ui(
    app,
    title="Parameters & Outputs",
    description="Demonstrates arguments, UI components, and async commands."
)


class Priority(str, Enum):
    """Priority levels for tasks."""
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    URGENT = "urgent"


@app.command()
@ui.def_command(is_auto_exec=True)
def welcome_screen():
    """
    Demonstrates a command that runs automatically when selected in the GUI.
    This is useful for dashboards or information-only screens.
    """
    ui(tg.Md("""
# Welcome!

This command runs **automatically** when selected because `is_auto_exec=True`.

It's a great way to present initial information or a dashboard without requiring user interaction to click a "Run" button.
"""))


@app.command()
@ui.def_command(is_button=True)
def basic_parameters(
    name: str,
    times: int = 1,
    excited: bool = False,
    priority: Priority = Priority.MEDIUM,
):
    """Demonstrates string, integer, boolean, and enum parameters."""
    ui(tg.Md(f"## Greeting for {name}"))

    greeting = f"Hello, {name}!"
    if excited:
        greeting += " How exciting!"

    for i in range(times):
        ui(tg.Text(f"({i+1}/{times}) {greeting}"))

    ui(tg.Text(f"Task priority set to: {priority.value}"))


@app.command()
def output_types():
    """Demonstrates mixing different component types and print statements."""
    ui(tg.Md("# Mixed Content Example"))

    # Regular print() statements are captured and displayed
    print("This line comes from a standard print() statement.")

    # Use a Text component for simple, unformatted text
    ui(tg.Text("This line comes from a tg.Text() component."))

    # Use a Markdown component for rich, formatted content
    ui(tg.Md("""
---
### Markdown Content
You can use **bold**, *italic*, and `code` formatting.
- Item 1
- Item 2
"""))

    # Use a Table component for structured data
    ui(tg.Table(
        title="Output Methods",
        cols=["Output Type", "Method", "When to Use"],
        data=[
            ["Plain text", "print() or tg.Text()", "Simple messages"],
            ["Formatted", "tg.Md()", "Rich content"],
            ["Tabular", "tg.Table()", "Structured data"],
        ]
    ))


@app.command()
@ui.def_command(is_long=True)
def long_running_task(steps: int = 5):
    """Demonstrates a long-running task with real-time table updates."""
    ui(tg.Md(f"## Processing {steps} steps..."))

    # Use a context manager for progressive table updates
    with ui(tg.Table(cols=["Step", "Status"], data=[])) as table:
        for i in range(1, steps + 1):
            table.add_row([f"Step {i}/{steps}", "In Progress..."])
            time.sleep(0.8)
            table.update_cell(i - 1, 1, "[OK] Complete")  # Update status to complete

    ui(tg.Md("[OK] **All steps completed!**"))


@app.command()
@ui.def_command(is_long=True)
async def async_task(delay: float = 1.0):
    """
    Demonstrates an async command.

    NOTE: Async commands are currently supported in CLI mode but not in GUI mode.
    In GUI mode, this command may not execute as expected.
    """
    ui(tg.Md("## Async Task Started"))
    ui(tg.Text(f"Waiting for {delay:.1f} seconds..."))

    await asyncio.sleep(delay)

    ui(tg.Text("First delay complete."))
    ui(tg.Text(f"Waiting for another {delay:.1f} seconds..."))

    await asyncio.sleep(delay)

    ui(tg.Md("[OK] **Async task finished!**"))


if __name__ == "__main__":
    ui.app()


"""
CLI Examples:
-------------
python examples/02_arguments_and_output.py --cli welcome-screen
python examples/02_arguments_and_output.py --cli basic-parameters "Alice" --times 3 --excited --priority urgent
python examples/02_arguments_and_output.py --cli output-types
python examples/02_arguments_and_output.py --cli long-running-task --steps 3
python examples/02_arguments_and_output.py --cli async-task --delay 1.5
"""
