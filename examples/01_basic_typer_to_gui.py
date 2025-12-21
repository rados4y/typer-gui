"""Example 1: Adding GUI to an Existing Typer Application

This example demonstrates the minimal changes needed to add a GUI to an existing
Typer CLI application. The application works in both GUI and CLI modes.
"""

import typer
import typer_ui

# Step 1: Create your Typer app as usual
app = typer.Typer()

# Step 2: Create a Ui instance with optional title and description
ui = typer_ui.Ui(
    app,
    title="My First GUI App",
    description="A simple calculator with GUI"
)


# Step 3: Define your commands with standard Typer decorators
@app.command()
def add(a: int, b: int):
    """Add two numbers together."""
    result = a + b
    print(f"{a} + {b} = {result}")
    return result


@app.command()
def subtract(a: int, b: int):
    """Subtract b from a."""
    result = a - b
    print(f"{a} - {b} = {result}")
    return result


@app.command()
def multiply(a: int, b: int):
    """Multiply two numbers."""
    result = a * b
    print(f"{a} × {b} = {result}")
    return result


@app.command()
def divide(a: float, b: float):
    """Divide a by b."""
    if b == 0:
        print("Error: Cannot divide by zero!")
        return None
    result = a / b
    print(f"{a} ÷ {b} = {result:.2f}")
    return result


# Step 4: Launch the app
if __name__ == "__main__":
    # GUI mode: python 01_basic_typer_to_gui.py
    # CLI mode: python 01_basic_typer_to_gui.py --cli add 5 3
    ui.app()


"""
Key Points:
-----------
1. The app works in BOTH GUI and CLI modes automatically
2. Run without --cli for GUI: python 01_basic_typer_to_gui.py
3. Run with --cli for CLI: python 01_basic_typer_to_gui.py --cli add 5 3
4. All standard Typer features work (type hints, docstrings, etc.)
5. Minimal code changes - just wrap your app with Ui and call ui.app()
"""
