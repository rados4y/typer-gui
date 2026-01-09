"""Example 2: Parameters, Outputs, and Async

This example demonstrates:
- Handling different parameter types (str, int, bool, enum).
- Displaying various output components (Text, Markdown, Table).
- Modal dialogs for parameter input and output display (GUI only).
- Long-running commands with real-time updates.
- Asynchronous command execution (CLI mode only).
- Auto-executing commands for welcome screens or dashboards.
"""

import asyncio
import time
from enum import Enum

import typer
import typer2ui as tu
from typer2ui import ui, text, dx

tapp = typer.Typer()
upp = tu.UiApp(
    tapp,
    title="Parameters & Outputs",
    description="Demonstrates arguments, UI components, and async commands.",
)


class Priority(str, Enum):
    """Priority levels for tasks."""

    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    URGENT = "urgent"


@tapp.command()
@upp.def_command(view=True)
def welcome_screen():
    """
    Demonstrates a command that runs automatically when selected in the GUI.
    This is useful for dashboards or information-only screens.
    """
    # Shortcut: ui(str) renders as Markdown
    ui(
        """
# Welcome!

This command runs **automatically** when selected because `view=True`.

It's a great way to present initial information or a dashboard without requiring user interaction to click a "Run" button.
"""
    )


@tapp.command()
@upp.def_command(button=True)
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


@tapp.command()
@upp.def_command(button=True)
def list_parameters(
    names: list[str],
    numbers: list[int] = [1, 2, 3],
    priority: list[Priority] = [Priority.MEDIUM],
):
    ui(f"## Greeting for {', '.join(names)}")
    ui(f"## Numbers: {', '.join(map(str, numbers))}")
    ui(f"## Priorities: {', '.join([p.value for p in priority])}")


@tapp.command()
@upp.def_command(button=True, modal=True)
def create_task(
    title: str,
    priority: Priority = Priority.MEDIUM,
    estimated_hours: int = 1,
):
    """Demonstrates a modal dialog with form inputs and output display.

    In GUI mode, parameters and output are shown in a popup dialog.
    In CLI mode, works the same as any other command.
    """
    # Shortcut: ui(str) renders as Markdown
    ui("# Task Created Successfully")
    ui()

    ui(f"**Title:** {title}")
    ui(f"**Priority:** {priority.value.upper()}")
    ui(f"**Estimated Hours:** {estimated_hours}")

    # Simulate task creation
    task_id = 12345
    ui()
    ui(f"Task ID: `{task_id}`")

    # Show task details in a table
    ui(
        tu.Table(
            cols=["Field", "Value"],
            data=[
                ["Title", title],
                ["Priority", priority.value],
                ["Estimated Hours", str(estimated_hours)],
                ["Task ID", str(task_id)],
            ],
            title="Task Details",
        )
    )

    return {"id": task_id, "title": title, "priority": priority.value}


@tapp.command()
@upp.def_command(view=True, modal=True)
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


@tapp.command()
@upp.def_command(threaded=True)
def long_running_task(steps: int = 5):
    """Demonstrates a long-running task with real-time table updates."""
    # Shortcut: ui(str) renders as Markdown
    ui(f"## Processing {steps} steps...")

    # Use a context manager for progressive table updates
    for i in range(5):
        print(f"Processing step {i + 1}...")
        time.sleep(0.8)

    ui("[OK] **All steps completed!**")


@tapp.command()
@upp.def_command(threaded=True)
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
    upp()


"""
CLI Examples:
-------------
python examples/02_arguments_and_output.py --cli welcome-screen
python examples/02_arguments_and_output.py --cli basic-parameters "Alice" --times 3 --excited --priority urgent
python examples/02_arguments_and_output.py --cli create-task "Implement feature X" --priority high --estimated-hours 8
python examples/02_arguments_and_output.py --cli output-types
python examples/02_arguments_and_output.py --cli long-running-task --steps 3
python examples/02_arguments_and_output.py --cli async-task --delay 1.5
"""
