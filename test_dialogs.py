"""Quick test for Alert and Confirm dialogs."""

import typer
import typer2ui as tu
from typer2ui import ui

tapp = typer.Typer()
upp = tu.UiApp(tapp, title="Dialog Test")


@tapp.command()
@upp.def_command(view=True)
def test_dialogs():
    """Test Alert and Confirm dialogs."""
    ui("# Dialog Test")
    ui("Click links to test dialogs:")
    ui()

    ui(tu.Row([
        tu.Link(
            "Test Alert",
            on_click=lambda: ui(tu.Alert(
                "Test Alert",
                "This is a test alert message!"
            ))
        ),
        tu.Link(
            "Test Confirm",
            on_click=lambda: ui(tu.Confirm(
                "Test Confirm",
                "Do you want to proceed?",
                on_yes=lambda: ui("✓ Confirmed!"),
                on_no=lambda: ui("✗ Cancelled!")
            ))
        ),
    ]))


if __name__ == "__main__":
    upp()
