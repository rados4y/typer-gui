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
import typer_ui as tu
from typer_ui import ui, text, dx

typer_app = typer.Typer()
app = tu.UiApp(
    typer_app,
    title="Parameters & Outputs",
    description="Demonstrates arguments, UI components, and async commands.",
)


class Priority(str, Enum):
    """Priority levels for tasks."""

    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    URGENT = "urgent"


@typer_app.command()
@app.def_command(auto=True)
def welcome_screen():
    """
    Demonstrates a command that runs automatically when selected in the GUI.
    This is useful for dashboards or information-only screens.
    """
    # Shortcut: ui(str) renders as Markdown
    ui(
        """
# Welcome!

This command runs **automatically** when selected because `auto=True`.

It's a great way to present initial information or a dashboard without requiring user interaction to click a "Run" button.
"""
    )


@typer_app.command()
@app.def_command(button=True)
def basic_parameters(
    name: str,
    times: int = 1,
    excited: bool = False,
    priority: Priority = Priority.MEDIUM,
):
    """Demonstrates string, integer, boolean, and enum parameters."""
    # Shortcut: ui(str) renders as Markdown
    ui(f"## Greeting for {name}")

    greeting = f"Hello, {name}!"
    if excited:
        greeting += " How exciting!"

    for i in range(times):
        # Shortcut: ui(str) works for simple text too
        ui(f"({i+1}/{times}) {greeting}")

    ui(f"Task priority set to: {priority.value}")


@typer_app.command()
def output_types():
    """Demonstrates shortcuts and different output methods."""
    # Shortcut: ui(str) renders as Markdown
    ui("# Output Methods Demo")
    ui()  # Empty line (shortcut for spacing)

    # Regular print() statements are captured and displayed
    print("This line comes from a standard print() statement.")

    # Shortcut: ui(str) renders as Markdown
    ui("This line uses the **ui(str)** shortcut.")

    # Shortcut: ui() with no args creates empty line
    ui()

    # Rich markdown content
    ui(
        """
---
### Markdown Content
You can use **bold**, *italic*, and `code` formatting.
- Item 1
- Item 2
"""
    )

    # Use Table component for structured data (no shortcut for this)
    ui(
        tu.Table(
            title="Output Methods Comparison",
            cols=["Method", "Code", "Use Case"],
            data=[
                ["Print", "print(...)", "Quick debugging, simple text"],
                ["UI Shortcut", "ui(str)", "Markdown-formatted content"],
                ["UI Empty", "ui()", "Add spacing/empty lines"],
                ["UI Object", "ui(42)", "Display any object as text"],
                ["Table", "ui(tu.Table(...))", "Structured data"],
            ],
        )
    )


@typer_app.command()
@app.def_command(long=True)
def long_running_task(steps: int = 5):
    """Demonstrates a long-running task with real-time table updates."""
    # Shortcut: ui(str) renders as Markdown
    ui(f"## Processing {steps} steps...")

    # Use a context manager for progressive table updates
    with ui(tu.Table(cols=["Step", "Status"], data=[])) as table:
        for i in range(1, steps + 1):
            table.add_row([f"Step {i}/{steps}", "In Progress..."])
            time.sleep(0.8)
            table.update_cell(i - 1, 1, "[OK] Complete")  # Update status to complete

    ui("[OK] **All steps completed!**")


@typer_app.command()
@app.def_command(long=True)
async def async_task(delay: float = 1.0):
    """
    Demonstrates an async command.

    NOTE: Async commands are currently supported in CLI mode but not in GUI mode.
    In GUI mode, this command may not execute as expected.
    """
    ui("## Async Task Started")
    ui(f"Waiting for {delay:.1f} seconds...")

    await asyncio.sleep(delay)

    ui("First delay complete.")
    ui(f"Waiting for another {delay:.1f} seconds...")

    await asyncio.sleep(delay)

    ui("[OK] **Async task finished!**")


if __name__ == "__main__":
    app()


"""
CLI Examples:
-------------
python examples/02_arguments_and_output.py --cli welcome-screen
python examples/02_arguments_and_output.py --cli basic-parameters "Alice" --times 3 --excited --priority urgent
python examples/02_arguments_and_output.py --cli output-types
python examples/02_arguments_and_output.py --cli long-running-task --steps 3
python examples/02_arguments_and_output.py --cli async-task --delay 1.5
"""
