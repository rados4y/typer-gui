"""Example 4: Advanced Customizations

This example demonstrates:
- Command options: is_button, is_long, is_auto_exec
- UIApp access: ui.runtime
- Command composition with cmd.run()
- UI customization with buttons
"""

import typer
import typer_gui
import time

app = typer.Typer()
ui = typer_gui.Ui(
    app,
    title="Advanced Customizations",
    description="Command options and advanced features"
)


# ============================================================================
# Command Options Demonstrations
# ============================================================================

@app.command()
@ui.options(is_button=True)
def quick_action():
    """Button-styled command - demonstrates is_button option.

    Commands with is_button=True appear as prominent buttons in the GUI,
    making them stand out for frequently used actions.
    """
    ui.out.md("## Quick Action Executed!").present()
    print("\nThis command uses `is_button=True` to appear as a button.")
    print("Perfect for frequently used actions that need prominence.")


@app.command()
@ui.options(is_long=True)
def long_process(steps: int = 5):
    """Long-running process - demonstrates is_long option.

    Commands with is_long=True show real-time output streaming,
    ideal for tasks that take time and produce incremental output.
    """
    print("Starting long-running process...\n")

    for i in range(1, steps + 1):
        print(f"[{i}/{steps}] Processing step {i}...")
        time.sleep(0.8)
        print(f"  OK Step {i} completed\n")

    print("Process finished!")


@app.command()
@ui.options(is_auto_exec=True)
def welcome_screen():
    """Auto-executing command - demonstrates is_auto_exec option.

    Commands with is_auto_exec=True run automatically when selected,
    perfect for dashboards, info screens, or commands with no required parameters.
    """
    ui.out.md("""
# Welcome to Advanced Customizations!

This command runs **automatically** when selected because it uses `is_auto_exec=True`.

## When to use is_auto_exec:
- Dashboard screens
- Information displays
- Commands with no required parameters
- Welcome/help screens
""").present()


# ============================================================================
# Advanced Features
# ============================================================================

@app.command()
@ui.options(is_button=True)
def app_info():
    """Application info - demonstrates ui.runtime access."""
    if not ui.runtime:
        print("UIApp only available in GUI mode")
        return

    ui.out.md("## Application Information\n").present()

    print(f"**Current command:** {ui.runtime.cmd.name}")
    print(f"**Total commands:** {len(ui.runtime.commands)}\n")

    print("**Available commands:**")
    for cmd in ui.runtime.commands:
        print(f"  • {cmd.name}")


@app.command()
def add(a: int, b: int):
    """Add two numbers - helper for composition demo."""
    result = a + b
    print(f"{a} + {b} = {result}")
    return result


@app.command()
def multiply(a: int, b: int):
    """Multiply two numbers - helper for composition demo."""
    result = a * b
    print(f"{a} * {b} = {result}")
    return result


@app.command()
@ui.options(is_button=True)
def composed_calculation(x: int = 7, y: int = 3):
    """Command composition - demonstrates cmd.run() for combining commands."""
    if not ui.runtime:
        print("This command requires GUI mode")
        return

    ui.out.md("## Composed Calculation\n").present()

    # Get commands by name
    add_cmd = ui.command("add")
    mult_cmd = ui.command("multiply")

    # Execute and capture results
    print("**Step 1:** Running add command...")
    add_cmd.run(a=x, b=y)

    print("\n**Step 2:** Running multiply command...")
    mult_cmd.run(a=x, b=y)


@app.command()
@ui.options(is_auto_exec=True)
def button_menu():
    """Interactive menu - demonstrates ui.out.button() with actions."""
    ui.out.md("# Interactive Button Menu\n").present()
    ui.out.md("Click buttons to navigate or execute commands:").present()

    print()

    # Navigation buttons
    ui.out.button(
        "Quick Action",
        do=lambda: ui.command("quick-action").select(),
        icon="flash_on"
    ).present()

    ui.out.button(
        "Long Process",
        do=lambda: ui.command("long-process").select(),
        icon="hourglass_empty"
    ).present()

    ui.out.button(
        "App Info",
        do=lambda: ui.command("app-info").select(),
        icon="info"
    ).present()

    ui.out.button(
        "Run Calculation",
        do=lambda: ui.command("composed-calculation").select(),
        icon="calculate"
    ).present()


if __name__ == "__main__":
    ui.app()


"""
CLI Examples:
-------------
python 04_customizations.py --cli quick-action
python 04_customizations.py --cli long-process --steps 3
python 04_customizations.py --cli app-info
python 04_customizations.py --cli composed-calculation --x 10 --y 5

Command Options:
----------------
- is_button: Display command as a prominent button
- is_long: Enable real-time output streaming for long processes
- is_auto_exec: Auto-execute when selected (no manual trigger needed)

Advanced Features:
------------------
- ui.runtime: Access UIApp instance for app-level operations
- ui.command(name): Get UICommand instance by name
- cmd.run(): Execute command and capture output/result
- ui.out.button(): Create interactive buttons with icons
"""
