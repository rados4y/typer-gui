"""Test auto_scroll and view flags."""
import typer
import typer2ui as tu
from typer2ui import ui

tapp = typer.Typer()
upp = tu.UiApp(
    tapp,
    title="Scroll Flags Test",
    description="Testing auto_scroll and view flags"
)


@tapp.command()
@upp.def_command(button=True)
def with_auto_scroll():
    """Command with auto_scroll=True (default)."""
    ui("# With Auto Scroll (Default)")
    ui("This command should automatically scroll to the end after execution.")
    for i in range(30):
        ui(f"Line {i + 1}")


@tapp.command()
@upp.def_command(button=True, auto_scroll=False)
def without_auto_scroll():
    """Command with auto_scroll=False."""
    ui("# Without Auto Scroll")
    ui("This command should NOT scroll - stays at top.")
    for i in range(30):
        ui(f"Line {i + 1}")


@tapp.command()
@upp.def_command(view=True)
def dashboard_view():
    """Command with view=True (auto + no header + no auto_scroll)."""
    ui("# Dashboard View")
    ui("This is a **view** - auto-executes, no header, no auto-scroll")

    ui(tu.Table(
        cols=["Metric", "Value"],
        data=[
            ["Users", "1,234"],
            ["Revenue", "$56,789"],
            ["Active Sessions", "42"],
            ["Server Status", "Online"],
        ]
    ))

    for i in range(20):
        ui(f"Detail line {i + 1}")


@tapp.command()
@upp.def_command(auto=True, header=False, auto_scroll=False)
def equivalent_to_view():
    """Equivalent to view=True using individual flags."""
    ui("# Equivalent to View")
    ui("This uses `auto=True, header=False, auto_scroll=False`")
    ui("Should behave identically to the dashboard_view command")

    for i in range(20):
        ui(f"Line {i + 1}")


if __name__ == "__main__":
    upp()
