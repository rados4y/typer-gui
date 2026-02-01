"""Example 1: Adding GUI to an Existing Typer Application

This example demonstrates the minimal changes needed to add a GUI to an existing
Typer CLI application. The application works in both GUI and CLI modes.

This pattern is useful when:
- You have an existing Typer app you want to add GUI to
- You want to use the app as a sub-app in another UiApp via add_subapp()
"""

import typer
import typer2ui as tu

# Step 1: Create your Typer app as usual
tapp = typer.Typer()


# Step 3: Define commands with standard Typer decorator
# Optionally add @upp.def_command() for GUI-specific options
@tapp.command()
def add(a: int, b: int):
    """Add two numbers together."""
    result = a + b
    print(f"{a} + {b} = {result}")
    return result


@tapp.command()
def subtract(a: int, b: int):
    """Subtract b from a."""
    result = a - b
    print(f"{a} - {b} = {result}")
    return result


@tapp.command()
def multiply(a: int, b: int):
    """Multiply two numbers."""
    result = a * b
    print(f"{a} × {b} = {result}")
    return result


@tapp.command()
def divide(a: float, b: float):
    """Divide a by b."""
    if b == 0:
        print("Error: Cannot divide by zero!")
        return None
    result = a / b
    print(f"{a} ÷ {b} = {result:.2f}")
    return result


@tapp.command()
def gui():
    upp = tu.UiApp(
        tapp, title="My First GUI App", description="A simple calculator with GUI"
    )
    upp()


# Step 4: Launch the app
if __name__ == "__main__":
    # GUI mode: python e01_basic_typer_to_gui.py
    # CLI mode: python e01_basic_typer_to_gui.py --cli add 5 3
    tapp()


"""
Key Points:
-----------
1. The app works in BOTH GUI and CLI modes automatically
2. Run without --cli for GUI: python e01_basic_typer_to_gui.py
3. Run with --cli for CLI: python e01_basic_typer_to_gui.py --cli add 5 3
4. Existing Typer apps can be wrapped with UiApp(tapp, ...) for GUI support
5. This UiApp can be added to another app via: main_upp.add_subapp(upp, name="calc")
"""
