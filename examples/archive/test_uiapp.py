"""Test UIApp and UICommand functionality."""

import typer
import typer_gui

app = typer.Typer()
ui = typer_gui.Ui(
    app,
    title="UIApp Test Application",
    description="Testing UIApp and UICommand features"
)


@app.command()
@ui.command(is_button=True)
def test_uiapp():
    """Test accessing UIApp from within a command."""
    print("=== UIApp Test ===\n")

    # Access UIApp
    if ui.runtime:
        print(f"[OK] UIApp is accessible: {ui.runtime}")
        print(f"[OK] Current command: {ui.runtime.cmd.name if ui.runtime.cmd else 'None'}")
        print(f"[OK] Total commands: {len(ui.runtime.commands)}")
        print(f"[OK] Command names: {[cmd.name for cmd in ui.runtime.commands]}")

        # Access blocks
        print(f"\n[OK] Header block: {ui.runtime.blocks.header}")
        print(f"[OK] Body block: {ui.runtime.blocks.body}")

        # Access current command blocks
        if ui.runtime.cmd:
            print(f"\n[OK] Current command title block: {ui.runtime.cmd.blocks.title}")
            print(f"[OK] Current command arguments block: {ui.runtime.cmd.blocks.arguments}")
            print(f"[OK] Current command actions block: {ui.runtime.cmd.blocks.actions}")
            print(f"[OK] Current command result block: {ui.runtime.cmd.blocks.result}")
    else:
        print("[FAIL] UIApp is not accessible (likely in CLI mode)")


@app.command()
@ui.command()
def greet(name: str = "World", excited: bool = False):
    """Greet someone."""
    greeting = f"Hello, {name}!"
    if excited:
        greeting += " How exciting!"
    print(greeting)
    return greeting


@app.command()
@ui.command()
def test_command_operations():
    """Test UICommand operations (select, run, include)."""
    print("=== UICommand Operations Test ===\n")

    if not ui.runtime:
        print("[FAIL] UIApp not accessible")
        return

    # Get the greet command
    greet_cmd = ui.runtime.get_command("greet")
    if greet_cmd:
        print(f"[OK] Found greet command: {greet_cmd.name}")

        # Test run operation
        print("\n--- Testing run() ---")
        result = greet_cmd.run(name="Alice", excited=True)
        print(f"Result: {result}")
        print(f"Captured output: {greet_cmd.output}")

        # Test include operation
        print("\n--- Testing include() ---")
        result2 = greet_cmd.include(name="Bob", excited=False)
        print(f"Result (inline): {result2}")
    else:
        print("[FAIL] Could not find greet command")


@app.command()
@ui.command()
def add(a: int, b: int):
    """Add two numbers."""
    result = a + b
    print(f"{a} + {b} = {result}")
    return result


@app.command()
@ui.command()
def test_nested_execution():
    """Test calling one command from another using include."""
    print("=== Nested Execution Test ===\n")

    if not ui.runtime:
        print("[FAIL] UIApp not accessible")
        return

    # Get the add command
    add_cmd = ui.runtime.get_command("add")
    if add_cmd:
        print("Calling add command from within this command:")
        result1 = add_cmd.include(a=5, b=3)
        result2 = add_cmd.include(a=10, b=20)

        total = result1 + result2
        print(f"\nTotal of all results: {total}")
        return total
    else:
        print("[FAIL] Could not find add command")


if __name__ == "__main__":
    ui.app()
