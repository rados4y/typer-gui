"""Example 4: Application Control with app.get_command() API

This example demonstrates:
- app.get_command("name").run(**kwargs) - Execute with output capture
- app.get_command("name").include(**kwargs) - Execute inline
- app.get_command("name").select() - Select a command (GUI mode)
- app.hold.page - Access to Flet Page for customization
- app.hold.result['command-name'] - Access to command output controls
- @app.init() - Decorator for initialization code (runs when GUI starts)
"""

import time

import typer2ui
from typer2ui import ui

app = typer2ui.Typer2Ui(
    title="App Control Demo",
    description="Interactive demo of app.get_command() operations",
)


# ============================================================================
# Initialization (runs when GUI starts)
# ============================================================================


@app.command()
def show_welcome_dialog():
    """Show welcome dialog when GUI starts (GUI only)."""
    import flet as ft

    if app.hold.page:
        print("executed")
        dlg = ft.AlertDialog(
            title=ft.Text("Welcome to App Control Demo!"),
            content=ft.Text(
                "This example demonstrates advanced app control features:\n\n"
                "• Command execution with .run() and .include()\n"
                "• GUI customization with app.hold.page\n"
                "• Output control access with app.hold.result\n"
                "• Initialization with @app.init()\n\n"
                "Explore the commands to see these features in action!"
            ),
            actions=[
                ft.TextButton("Get Started", on_click=lambda e: close_dialog(dlg))
            ],
            actions_alignment=ft.MainAxisAlignment.END,
        )
        app.hold.page.show_dialog(dlg)


def close_dialog(dialog):
    """Helper to close dialog."""
    dialog.open = False
    if app.hold.page:
        app.hold.page.update()


# ============================================================================
# Sample Commands (used by demo)
# ============================================================================


@app.command()
def fetch_data(source: str = "database"):
    """Fetch data from a source."""
    ui(f"### Fetching from {source}")
    ui(f"- Fetched 150 records from {source}")
    return {"records": 150, "source": source}


@app.command(view=True)
def generate_report():
    """Generate a final report."""
    ui("### Final Report")
    ui(
        typer2ui.Table(
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


@app.command()
def hold_demo():
    """Demo of app.hold for GUI customization (GUI only)."""
    ui("# GUI Customization with app.hold")

    # Check if we're in GUI mode
    if app.hold.page is None:
        ui("**Note:** This demo only works in GUI mode")
        ui("Run: `python examples/e04_app_control.py`")
        return

    ui("## 1. Access Flet Page")
    ui("Customize the Flet page directly:")

    ui(
        typer2ui.Row(
            [
                typer2ui.Button(
                    "Toggle Dark Mode",
                    on_click=lambda: toggle_theme(),
                    icon="dark_mode",
                ),
                typer2ui.Button(
                    "Change Window Title", on_click=lambda: change_title(), icon="title"
                ),
            ]
        )
    )

    ui("## 2. Access Command Output Controls")
    ui("Modify output areas of other commands:")

    ui(
        typer2ui.Row(
            [
                typer2ui.Button(
                    "Style Fetch Output",
                    on_click=lambda: customize_fetch_output(),
                    icon="palette",
                ),
                typer2ui.Button(
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

**Initialize with @app.init():**
```python
@app.init()
def show_welcome_dialog():
    import flet as ft
    if app.hold.page:
        dlg = ft.AlertDialog(
            title=ft.Text("Welcome!"),
            content=ft.Text("Welcome to the app!"),
            actions=[ft.TextButton("OK", on_click=lambda e: close_dlg(dlg))]
        )
        app.hold.page.dialog = dlg
        dlg.open = True
        app.hold.page.update()
```

**Access Flet Page:**
```python
import flet as ft

# Toggle theme
page = app.hold.page
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
output = app.hold.result['fetch-data']
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

    page = app.hold.page
    if page:
        page.theme_mode = (
            ft.ThemeMode.DARK
            if page.theme_mode == ft.ThemeMode.LIGHT
            else ft.ThemeMode.LIGHT
        )
        page.update()


def change_title():
    """Change the window title."""
    page = app.hold.page
    if page:
        page.title = f"Custom Title - {time.strftime('%H:%M:%S')}"
        page.update()


def customize_fetch_output():
    """Customize the fetch-data command output style."""
    import flet as ft

    output = app.hold.result["fetch-data"]
    if output:
        # Customize the output ListView
        output.bgcolor = ft.colors.GREEN_50
        output.padding = 20
        output.border = ft.border.all(2, ft.colors.GREEN_400)
        output.border_radius = 10

        if app.hold.page:
            app.hold.page.update()
            ui("✓ Styled fetch-data output!")
    else:
        ui("⚠ Run fetch-data command first")


def clear_report_output():
    """Clear the generate-report command output."""
    output = app.hold.result["generate-report"]
    if output:
        output.controls.clear()
        if app.hold.page:
            app.hold.page.update()
            ui("✓ Cleared generate-report output!")
    else:
        ui("⚠ Run generate-report command first")


@app.command(view=True)
def control_demo():
    """Interactive demo of run(), include(), and select()."""
    ui("# Command Control Demo")
    ui("Click buttons to see how each method works:")
    ui("---")

    # Interactive buttons
    ui(
        typer2ui.Row(
            [
                typer2ui.Button(
                    "Demo .run()",
                    on_click=lambda: app.get_command("fetch-data").run(source="api"),
                ),
                typer2ui.Button(
                    "Demo .include()",
                    on_click=lambda: app.get_command("generate-report").include(),
                ),
                typer2ui.Button(
                    "Demo .clear()",
                    on_click=lambda: app.get_command().clear(),
                ),
                typer2ui.Button(
                    "Demo .select()",
                    on_click=lambda: app.get_command("fetch-data").select(),
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
cmd = app.get_command("fetch-data").run(source="api")
output = cmd.out      # Captured text output
result = cmd.result   # Return value
```

**`.include(**kwargs)`** - Execute inline (output appears in current context)
```python
result = app.get_command("generate-report").include()
```

**`.select()`** - Select command in GUI (changes form)
```python
app.get_command("fetch-data").select()
```
    """
    )


if __name__ == "__main__":
    app()


"""
CLI Examples:
-------------
# Interactive demo (best viewed in GUI)
python examples/e04_app_control.py

# CLI mode
python examples/e04_app_control.py --cli control-demo
python examples/e04_app_control.py --cli fetch-data --source api
python examples/e04_app_control.py --cli generate-report
"""
