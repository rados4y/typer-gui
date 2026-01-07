"""Test list parameters."""
import typer
import typer2ui as tu
from typer2ui import ui

tapp = typer.Typer()
upp = tu.UiApp(tapp, title="List Parameter Test")


@tapp.command()
def test_str_list(items: list[str]):
    """Test string list parameter."""
    ui(f"# Received {len(items)} items")
    for i, item in enumerate(items, 1):
        ui(f"{i}. {item}")


@tapp.command()
def test_int_list(numbers: list[int]):
    """Test integer list parameter."""
    ui(f"# Received {len(numbers)} numbers")
    ui(f"Sum: {sum(numbers)}")
    ui(f"Numbers: {numbers}")


@tapp.command()
def test_optional_list(values: list[str] = ["default1", "default2"]):
    """Test optional list with defaults."""
    ui(f"# Values: {values}")


if __name__ == "__main__":
    upp()
