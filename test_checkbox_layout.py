"""Debug script to verify checkbox layout structure."""
from enum import Enum
import typer
import typer2ui as tu

tapp = typer.Typer()
app = tu.UiApp(tapp, title="Test")

class Priority(str, Enum):
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    URGENT = "urgent"

@tapp.command()
def test_enum_list(priority: list[Priority] = [Priority.MEDIUM]):
    """Test command with enum list parameter."""
    tu.ui(f"Selected priorities: {[p.value for p in priority]}")

if __name__ == "__main__":
    # Import the spec builder to inspect what's being created
    from typer2ui.spec_builder import build_app_spec

    spec = build_app_spec(tapp, title="Test", description="Test")

    print("=== App Spec ===")
    print(f"Commands: {len(spec.commands)}")

    for cmd in spec.commands:
        print(f"\nCommand: {cmd.name}")
        for param in cmd.params:
            print(f"  Param: {param.name}")
            print(f"    Type: {param.param_type}")
            print(f"    Python type: {param.python_type}")
            print(f"    Choices: {param.enum_choices}")
            print(f"    Required: {param.required}")
            print(f"    Default: {param.default}")
