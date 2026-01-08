"""Test to inspect the exact control structure being created."""
from enum import Enum
import typer
import typer2ui as tu
from typer2ui.spec_builder import build_app_spec
from typer2ui.runners.gui_runner import GUIRunner

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
    # Build spec
    spec = build_app_spec(tapp, title="Test", description="Test")
    command = spec.commands[0]
    param = command.params[0]

    print("=== Parameter Spec ===")
    print(f"Name: {param.name}")
    print(f"Type: {param.param_type}")
    print(f"Choices: {param.enum_choices}")
    print()

    # Create GUI runner and build the control
    runner = GUIRunner(spec)
    control = runner._create_param_control(param)

    print("=== Control Structure ===")
    print(f"Control type: {type(control).__name__}")

    if hasattr(control, 'controls'):
        print(f"Number of child controls: {len(control.controls)}")
        for i, child in enumerate(control.controls):
            print(f"  Child {i}: {type(child).__name__}")
            if hasattr(child, 'controls'):
                print(f"    Has {len(child.controls)} sub-controls:")
                for j, subchild in enumerate(child.controls):
                    print(f"      Sub-child {j}: {type(subchild).__name__}", end="")
                    if hasattr(subchild, 'label'):
                        print(f" (label: {subchild.label})")
                    else:
                        print()
