"""A simple Typer CLI application for demonstration."""

from enum import Enum
import sys
from pathlib import Path
import time
from datetime import datetime
import typer

# Add parent directory to path for typer_gui import
sys.path.insert(0, str(Path(__file__).parent.parent))
import typer_gui

# Create the Typer app
app = typer.Typer(help="A simple demo CLI application")

# Create UI wrapper with app-level configuration
ui = typer_gui.Ui(
    app,
    title="Typer Demo GUI",
    description="A simple demonstration of typer-gui with various command types and parameters.",
)


class Color(str, Enum):
    """Available color choices."""

    RED = "red"
    GREEN = "green"
    BLUE = "blue"


@app.command()
def own2(key: int):
    print(key)


@app.command()
@ui.command(is_auto_exec=True)
def status():
    """Display system status (auto-executes when selected)."""
    print("System Status Report")
    print("=" * 50)
    print(f"Current Time: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print(f"Status: Running")
    print(f"Mode: Demo")
    print("=" * 50)


@app.command()
def greet(
    name: str = typer.Argument(..., help="The name to greet"),
    excited: bool = typer.Option(
        False, "--excited", "-e", help="Use exclamation marks"
    ),
    times: int = typer.Option(1, "--times", "-t", help="How many times to greet"),
) -> None:
    """Greet someone with a friendly message."""
    punctuation = "!" if excited else "."
    for _ in range(times):
        print(f"Hello {name}{punctuation}")


@app.command()
def add(
    a: int = typer.Argument(..., help="First number"),
    b: int = typer.Argument(..., help="Second number"),
) -> None:
    """Add two numbers together."""
    result = a + b
    print(f"{a} + {b} = {result}")


@app.command()
def calculate(
    x: float = typer.Argument(..., help="First operand"),
    y: float = typer.Argument(..., help="Second operand"),
    operation: str = typer.Option(
        "add", help="Operation: add, subtract, multiply, divide"
    ),
) -> None:
    """Perform a calculation on two numbers."""
    if operation == "add":
        result = x + y
        print(f"{x} + {y} = {result}")
    elif operation == "subtract":
        result = x - y
        print(f"{x} - {y} = {result}")
    elif operation == "multiply":
        result = x * y
        print(f"{x} * {y} = {result}")
    elif operation == "divide":
        if y == 0:
            print("Error: Cannot divide by zero!")
        else:
            result = x / y
            print(f"{x} / {y} = {result}")
    else:
        print(f"Unknown operation: {operation}")


@app.command()
def paint(
    color: Color = typer.Argument(..., help="Color to paint with"),
    background: Color = typer.Option(Color.BLUE, help="Background color"),
) -> None:
    """Paint something with colors."""
    print(f"Painting with {color.value} on {background.value} background!")


@app.command()
@ui.command(is_markdown=True)
def info(
    name: str = typer.Option("World", help="Name to show in the info"),
) -> str:
    """Display formatted information using Markdown.
    This command demonstrates Markdown output in the GUI.
    """
    return f"""
# Welcome to Typer-GUI, {name}! 👋

This is a **demonstration** of *Markdown formatting* in the GUI output.

## Features

- **Bold text** and *italic text*
- Lists (like this one!)
- Code blocks
- Links and more

## Example Code

```python
import typer_gui

ui = typer_gui.Ui(title="My App")

@ui.command(is_markdown=True)
def my_command() -> str:
    return "# Hello **World**!"

ui.app()
```

## Why use Markdown?

1. **Rich formatting** - Make your output beautiful
2. **Easy to read** - Clear structure and hierarchy
3. **Interactive** - Links are clickable!

---

*Generated for: {name}*
"""


@app.command()
@ui.command(is_button=True)
def clear():
    """Clear the output (displayed as a button)."""
    print("Output cleared!")
    print("This command is shown as a highlighted button in the left panel.")


@app.command()
@ui.command(is_long=True)
def process(
    steps: int = typer.Option(5, help="Number of processing steps"),
    delay: float = typer.Option(1.0, help="Delay between steps (seconds)"),
):
    """Simulate a long-running process with real-time output."""
    print(f"Starting processing with {steps} steps...")
    print("")

    for i in range(1, steps + 1):
        print(f"Step {i}/{steps}: Processing...")
        time.sleep(delay)
        print(f"  → Step {i} completed!")

    print("")
    print("=" * 50)
    print("All processing completed successfully!")


@app.command()
@ui.command(is_button=True, is_long=True)
def download(
    file_count: int = typer.Option(3, help="Number of files to download"),
):
    """Simulate downloading files (button + real-time output)."""
    print(f"Starting download of {file_count} files...")
    print("")

    for i in range(1, file_count + 1):
        filename = f"file_{i}.dat"
        print(f"[{i}/{file_count}] Downloading {filename}...")

        # Simulate download progress
        for progress in [25, 50, 75, 100]:
            time.sleep(0.3)
            print(f"  Progress: {progress}%")

        print(f"  ✓ {filename} downloaded successfully!")
        print("")

    print("All downloads completed!")


if __name__ == "__main__":
    # Launch the GUI
    ui.app()
