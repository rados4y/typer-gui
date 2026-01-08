"""Test text accumulation - multiple prints should become single ft.Text"""
import typer
import typer2ui as tu
from typer2ui import ui, text

tapp = typer.Typer()

upp = tu.UiApp(
    tapp,
    title="Text Accumulation Test",
    description="Testing consecutive text outputs"
)

@tapp.command()
@upp.def_command()
def test_prints():
    """Test multiple print statements."""
    print("Line 1 from print")
    print("Line 2 from print")
    print("Line 3 from print")

    # Add a UI component to flush the buffer
    ui(tu.Text("--- Component ---"))

    # More prints
    print("Line 4 from print")
    print("Line 5 from print")

@tapp.command()
@upp.def_command()
def test_text_calls():
    """Test multiple text() calls."""
    text("Text line 1")
    text("Text line 2")
    text("Text line 3")

    # Add a UI component to flush
    ui(tu.Row([tu.Text("Row component")]))

    text("Text line 4")
    text("Text line 5")

@tapp.command()
@upp.def_command()
def test_mixed():
    """Test mixed print and text calls."""
    print("Print line 1")
    print("Print line 2")
    text("Text line 1")
    text("Text line 2")

    ui("# Markdown Header")

    print("Print line 3")
    text("Text line 3")

if __name__ == "__main__":
    upp()
