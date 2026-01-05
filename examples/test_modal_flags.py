"""Test modal with different flags."""
import time
import typer
import typer_ui as tu
from typer_ui import ui

typer_app = typer.Typer()
app = tu.UiApp(
    typer_app,
    title="Modal Flags Test",
    description="Testing modal with different command flags"
)


@typer_app.command()
@app.def_command(button=True, modal=True, view=True)
def auto_modal():
    """Modal with auto-execution (view=True).

    Should:
    - Auto-execute when opened
    - No submit button
    - No header
    - No auto-scroll
    """
    ui("# Auto-Executed Modal")
    ui("This modal executed automatically when opened!")
    ui()
    for i in range(10):
        ui(f"Line {i+1}")


@typer_app.command()
@app.def_command(button=True, modal=True, long=True)
def long_modal():
    """Modal with long-running task.

    Should show real-time updates as they happen.
    """
    ui("# Long-Running Task in Modal")
    ui()

    for i in range(5):
        ui(f"Processing step {i+1}/5...")
        time.sleep(1)
        ui(f"  → Step {i+1} complete!")

    ui()
    ui("**All steps completed!**")


@typer_app.command()
@app.def_command(button=True, modal=True, header=False)
def no_header_modal(name: str = "World"):
    """Modal with no header.

    Should not show title or description.
    """
    ui("# Greeting")
    ui(f"Hello, {name}!")


@typer_app.command()
@app.def_command(button=True, modal=True, auto_scroll=False)
def no_scroll_modal():
    """Modal with no auto-scroll.

    Should not scroll to bottom automatically.
    """
    ui("# No Auto-Scroll")
    ui("This output should stay at the top.")
    ui()
    for i in range(20):
        ui(f"Line {i+1}")


@typer_app.command()
@app.def_command(button=True, modal=True, submit_name="Create Item")
def custom_submit(item_name: str):
    """Modal with custom submit button name."""
    ui("# Item Created")
    ui(f"Created item: **{item_name}**")


if __name__ == "__main__":
    app()
