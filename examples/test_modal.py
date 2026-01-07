"""Test modal command functionality."""
import typer
import typer2ui as tu
from typer2ui import ui
from enum import Enum

tapp = typer.Typer()
upp = tu.UiApp(
    tapp,
    title="Modal Commands Test",
    description="Testing modal dialog functionality"
)


class Priority(str, Enum):
    """Task priority levels."""
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"


@tapp.command()
@upp.def_command(button=True, modal=True)
def create_user(name: str, email: str, role: str = "User"):
    """Create a new user (shown in modal dialog)."""
    ui("# User Created")
    ui(f"**Name:** {name}")
    ui(f"**Email:** {email}")
    ui(f"**Role:** {role}")

    ui(tu.Table(
        cols=["Field", "Value"],
        data=[
            ["Name", name],
            ["Email", email],
            ["Role", role],
        ],
        title="New User Details"
    ))

    return {"name": name, "email": email, "role": role}


@tapp.command()
@upp.def_command(button=True, modal=True)
def delete_item(item_id: int, confirm: bool = False):
    """Delete an item (with confirmation in modal)."""
    if not confirm:
        ui("## Warning")
        ui("You did not confirm the deletion. Item was **not** deleted.")
        ui("Please check the 'confirm' checkbox to delete the item.")
        return None

    ui("# Item Deleted")
    ui(f"Item with ID **{item_id}** has been successfully deleted.")
    ui()
    ui("This action cannot be undone.")

    return {"deleted": item_id}


@tapp.command()
@upp.def_command(button=True, modal=True, submit_name="Create Task")
def create_task(
    title: str,
    priority: Priority = Priority.MEDIUM,
    estimated_hours: int = 1
):
    """Create a new task with priority."""
    ui("# Task Created Successfully")
    ui()
    ui(f"**Title:** {title}")
    ui(f"**Priority:** {priority.value.upper()}")
    ui(f"**Estimated Hours:** {estimated_hours}")

    # Simulate task creation
    task_id = 12345
    ui()
    ui(f"Task ID: `{task_id}`")

    return {"id": task_id, "title": title, "priority": priority.value}


@tapp.command()
@upp.def_command(view=True)
def dashboard():
    """Main dashboard (not modal)."""
    ui("# Dashboard")
    ui("Use the buttons on the left to open modal dialogs for various actions.")
    ui()
    ui("## Available Actions")
    ui("- **Create User**: Add a new user to the system")
    ui("- **Delete Item**: Remove an item (requires confirmation)")
    ui("- **Create Task**: Create a new task with priority")


if __name__ == "__main__":
    upp()
