"""Example 4: Application Control with upp.command() API

This example demonstrates:
- upp.command("name").run(**kwargs) - Execute with output capture
- upp.command("name").include(**kwargs) - Execute inline
- upp.command("name").select() - Select a command (GUI mode)
- upp.hold.page - Access to Flet Page for customization
- upp.hold.result['command-name'] - Access to command output controls
- @upp.init() - Decorator for initialization code (runs when GUI starts)
"""

import typer
import typer2ui as tu
from typer2ui import ui, text, dx
import time

tapp = typer.Typer()
upp = tu.UiApp(
    tapp,
    title="App Control Demo",
    description="Interactive demo of upp.command() operations",
)


# ============================================================================
# Initialization (runs when GUI starts)
# ============================================================================


@tapp.command()
def show_welcome_dialog():
    """Show welcome dialog when GUI starts (GUI only)."""
    import flet as ft

    if upp.hold.page:
        print("executed")
        dlg = ft.AlertDialog(
            title=ft.Text("Welcome to App Control Demo!"),
            content=ft.Text(
                "This example demonstrates advanced app control features:\n\n"
                "• Command execution with .run() and .include()\n"
                "• GUI customization with upp.hold.page\n"
                "• Output control access with upp.hold.result\n"
                "• Initialization with @upp.init()\n\n"
                "Explore the commands to see these features in action!"
            ),
            actions=[
                ft.TextButton("Get Started", on_click=lambda e: close_dialog(dlg))
            ],
            actions_alignment=ft.MainAxisAlignment.END,
        )
        upp.hold.page.show_dialog(dlg)
        # upp.hold.page.dialog = dlg
        # dlg.open = True
        # upp.hold.page.update()


def close_dialog(dialog):
    """Helper to close dialog."""
    dialog.open = False
    if upp.hold.page:
        upp.hold.page.update()


# ============================================================================
# Sample Commands (used by demo)
# ============================================================================


@tapp.command()
def fetch_data(source: str = "database"):
    """Fetch data from a source."""
    ui(f"### Fetching from {source}")
    ui(f"- Fetched 150 records from {source}")
    return {"records": 150, "source": source}


@tapp.command()
@upp.def_command(view=True)
def generate_report():
    """Generate a final report."""
    ui("### Final Report")
    ui(
        tu.Table(
            cols=["Metric", "Value"],
            data=[
                ["Total Records", "150"],
                ["Processed", "120"],
                ["Success Rate", "95%"],
            ],
            title="Summary",
        )
    )
    return {"status": "complete"}


# ============================================================================
# Interactive Demo
# ============================================================================


@tapp.command()
@upp.def_command()
def hold_demo():
    """Demo of upp.hold for GUI customization (GUI only)."""
    ui("# GUI Customization with upp.hold")

    # Check if we're in GUI mode
    if upp.hold.page is None:
        ui("**Note:** This demo only works in GUI mode")
        ui("Run: `python examples/04_app_control.py`")
        return

    ui("## 1. Access Flet Page")
    ui("Customize the Flet page directly:")

    ui(
        tu.Row(
            [
                tu.Button(
                    "Toggle Dark Mode",
                    on_click=lambda: toggle_theme(),
                    icon="dark_mode",
                ),
                tu.Button(
                    "Change Window Title", on_click=lambda: change_title(), icon="title"
                ),
            ]
        )
    )

    ui("## 2. Access Command Output Controls")
    ui("Modify output areas of other commands:")

    ui(
        tu.Row(
            [
                tu.Button(
                    "Style Fetch Output",
                    on_click=lambda: customize_fetch_output(),
                    icon="palette",
                ),
                tu.Button(
                    "Clear Report Output",
                    on_click=lambda: clear_report_output(),
                    icon="clear",
                ),
            ]
        )
    )

    ui("---")
    ui(
        """
### Code Examples

**Initialize with @upp.init():**
```python
@upp.init()
def show_welcome_dialog():
    import flet as ft
    if upp.hold.page:
        dlg = ft.AlertDialog(
            title=ft.Text("Welcome!"),
            content=ft.Text("Welcome to the app!"),
            actions=[ft.TextButton("OK", on_click=lambda e: close_dlg(dlg))]
        )
        upp.hold.page.dialog = dlg
        dlg.open = True
        upp.hold.page.update()
```

**Access Flet Page:**
```python
import flet as ft

# Toggle theme
page = upp.hold.page
page.theme_mode = (
    ft.ThemeMode.DARK
    if page.theme_mode == ft.ThemeMode.LIGHT
    else ft.ThemeMode.LIGHT
)
page.update()
```

**Access Command Output:**
```python
# Get output control for a command
output = upp.hold.result['fetch-data']
if output:
    # Modify the ListView directly
    output.scroll = ft.ScrollMode.ALWAYS
    output.bgcolor = ft.colors.BLUE_50
```
    """
    )


def toggle_theme():
    """Toggle between light and dark mode."""
    import flet as ft

    page = upp.hold.page
    if page:
        page.theme_mode = (
            ft.ThemeMode.DARK
            if page.theme_mode == ft.ThemeMode.LIGHT
            else ft.ThemeMode.LIGHT
        )
        page.update()


def change_title():
    """Change the window title."""
    page = upp.hold.page
    if page:
        page.title = f"Custom Title - {time.strftime('%H:%M:%S')}"
        page.update()


def customize_fetch_output():
    """Customize the fetch-data command output style."""
    import flet as ft

    output = upp.hold.result["fetch-data"]
    if output:
        # Customize the output ListView
        output.bgcolor = ft.colors.GREEN_50
        output.padding = 20
        output.border = ft.border.all(2, ft.colors.GREEN_400)
        output.border_radius = 10

        if upp.hold.page:
            upp.hold.page.update()
            ui("✓ Styled fetch-data output!")
    else:
        ui("⚠ Run fetch-data command first")


def clear_report_output():
    """Clear the generate-report command output."""
    output = upp.hold.result["generate-report"]
    if output:
        output.controls.clear()
        if upp.hold.page:
            upp.hold.page.update()
            ui("✓ Cleared generate-report output!")
    else:
        ui("⚠ Run generate-report command first")


@tapp.command()
@upp.def_command(view=True)
def control_demo():
    """Interactive demo of run(), include(), and select()."""
    ui("# Command Control Demo")
    ui("Click buttons to see how each method works:")
    ui("---")

    # Interactive buttons
    ui(
        tu.Row(
            [
                tu.Button(
                    "Demo .run()",
                    on_click=lambda: upp.command("fetch-data").run(source="api"),
                ),
                tu.Button(
                    "Demo .include()",
                    on_click=lambda: upp.command("generate-report").include(),
                ),
                tu.Button(
                    "Demo .clear()",
                    on_click=lambda: upp.command().clear(),
                ),
                tu.Button(
                    "Demo .select()",
                    on_click=lambda: upp.command("fetch-data").select(),
                ),
            ]
        )
    )

    ui("---")
    ui(
        """
### Quick Reference

**`.run(**kwargs)`** - Execute and capture output separately
```python
cmd = upp.command("fetch-data").run(source="api")
output = cmd.out      # Captured text output
result = cmd.result   # Return value
```

**`.include(**kwargs)`** - Execute inline (output appears in current context)
```python
result = upp.command("generate-report").include()
```

**`.select()`** - Select command in GUI (changes form)
```python
app.command("fetch-data").select()
```
    """
    )


if __name__ == "__main__":
    upp()


"""
CLI Examples:
-------------
# Interactive demo (best viewed in GUI)
python examples/04_app_control.py

# CLI mode
python examples/04_app_control.py --cli control-demo
python examples/04_app_control.py --cli fetch-data --source api
python examples/04_app_control.py --cli generate-report
"""
