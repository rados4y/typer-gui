"""Example 4: Advanced Customizations

This example demonstrates:
- Command options: is_button, is_long, is_auto_exec
- Auto-update components
- Progressive rendering
- Interactive buttons and actions
- Complex component composition
"""

import typer
import typer_ui as tg
import time

app = typer.Typer()
ui = tg.Ui(
    app,
    title="Advanced Customizations",
    description="Command options and advanced features"
)


# ============================================================================
# Command Options
# ============================================================================

@app.command()
@ui.command(is_button=True)
def quick_action():
    """Button-styled command - demonstrates is_button option.

    Commands with is_button=True appear as prominent buttons in the GUI,
    making them stand out for frequently used actions.
    """
    ui(tg.Md("## Quick Action Executed!"))
    ui(tg.Text("This command uses `is_button=True` to appear as a button."))
    ui(tg.Text("Perfect for frequently used actions that need prominence."))


@app.command()
@ui.command(is_long=True, is_button=True)
def long_process(steps: int = 5):
    """Long-running process - demonstrates is_long option.

    Commands with is_long=True show real-time output streaming,
    ideal for tasks that take time and produce incremental output.
    """
    ui(tg.Md(f"# Processing {steps} Steps"))

    # Progressive rendering with context manager
    with ui(tg.Table(cols=["Step", "Status", "Time"], data=[])) as table:
        for i in range(1, steps + 1):
            table.add_row([f"Step {i}/{steps}", "Processing...", f"{i*0.8:.1f}s"])
            time.sleep(0.8)

    ui(tg.Md("[OK] **Process completed successfully!**"))


@app.command()
@ui.command(is_auto_exec=True)
def welcome_screen():
    """Auto-executing command - demonstrates is_auto_exec option.

    Commands with is_auto_exec=True run automatically when selected,
    perfect for dashboards, info screens, or commands with no required parameters.
    """
    ui(tg.Md("""
# Welcome to Advanced Customizations!

This command runs **automatically** when selected because it uses `is_auto_exec=True`.

## When to use is_auto_exec:
- Dashboard screens
- Information displays
- Commands with no required parameters
- Welcome/help screens
"""))


# ============================================================================
# Auto-Update Demonstrations
# ============================================================================

@app.command()
@ui.command(is_long=True)
def auto_update_demo():
    """Demonstrate component auto-update feature."""
    ui(tg.Md("## Auto-Update Demo"))
    ui(tg.Text("Components automatically update when modified!"))

    # Create multiple tables that update independently
    table1 = tg.Table(cols=["Task", "Status"], data=[], title="Queue 1")
    table2 = tg.Table(cols=["Task", "Status"], data=[], title="Queue 2")

    ui(table1)
    ui(table2)

    # Update both tables in alternating fashion
    tasks = ["Init", "Load", "Process", "Validate", "Complete"]
    for task in tasks:
        table1.add_row([task, "[OK]"])
        time.sleep(0.3)
        table2.add_row([task, "[OK]"])
        time.sleep(0.3)

    ui(tg.Md("[OK] Both queues completed!"))


# ============================================================================
# Interactive Components
# ============================================================================

@app.command()
@ui.command(is_auto_exec=True)
def interactive_dashboard():
    """Interactive dashboard with buttons and actions."""
    ui(tg.Column([
        tg.Md("# Interactive Dashboard"),

        tg.Md("## Actions"),
        tg.Row([
            tg.Button("Refresh", on_click=lambda: print("Refreshing data...")),
            tg.Button("Export", on_click=lambda: print("Exporting report...")),
            tg.Button("Settings", on_click=lambda: print("Opening settings...")),
        ]),

        tg.Md("## System Status"),
        tg.Table(
            cols=["Component", "Status", "Uptime"],
            data=[
                ["Web Server", "Running", "15d 4h"],
                ["Database", "Running", "15d 4h"],
                ["Cache", "Running", "12d 8h"],
                ["Workers", "Running", "15d 4h"],
            ],
            title="Infrastructure"
        ),

        tg.Md("## Quick Links"),
        tg.Row([
            tg.Link("Documentation", on_click=lambda: print("Opening docs...")),
            tg.Link("Support", on_click=lambda: print("Opening support...")),
            tg.Link("Feedback", on_click=lambda: print("Opening feedback...")),
        ]),
    ]))


# ============================================================================
# Combined Features
# ============================================================================

@app.command()
@ui.command(is_button=True, is_long=True)
def combined_demo(items: int = 10):
    """Combine multiple features: button styling, long process, auto-update."""
    ui(tg.Md(f"# Processing {items} Items"))
    ui(tg.Md("This command combines:"))
    ui(tg.Column([
        tg.Text("[OK] Button styling (is_button=True)"),
        tg.Text("[OK] Real-time streaming (is_long=True)"),
        tg.Text("[OK] Auto-update components"),
        tg.Text("[OK] Progressive rendering"),
    ]))

    # Create status table
    status = tg.Table(
        cols=["Item", "Stage", "Progress"],
        data=[],
        title="Processing Status"
    )
    ui(status)

    # Process items with updates
    stages = ["Queued", "Processing", "Validating", "Complete"]
    for i in range(1, items + 1):
        for stage in stages:
            progress = f"{stages.index(stage) + 1}/4"
            status.add_row([f"Item {i}", stage, progress])
            time.sleep(0.1)

    ui(tg.Md(f"[OK] **All {items} items processed successfully!**"))


@app.command()
def complex_layout():
    """Demonstrate complex nested layout."""
    ui(tg.Column([
        tg.Md("# Complex Layout Example"),

        tg.Row([
            tg.Column([
                tg.Md("### Left Panel"),
                tg.Text("Navigation and controls"),
                tg.Button("Action 1", on_click=lambda: print("Action 1")),
                tg.Button("Action 2", on_click=lambda: print("Action 2")),
            ]),
            tg.Column([
                tg.Md("### Right Panel"),
                tg.Table(
                    cols=["Feature", "Enabled"],
                    data=[
                        ["Auto-update", "Yes"],
                        ["Progressive", "Yes"],
                        ["Interactive", "Yes"],
                    ]
                ),
            ]),
        ]),

        tg.Md("---"),
        tg.Md("### Footer"),
        tg.Text("You can nest Row and Column to create complex layouts!"),
    ]))


if __name__ == "__main__":
    ui.app()


"""
CLI Examples:
-------------
python examples/04_customizations.py --cli quick-action
python examples/04_customizations.py --cli long-process --steps 3
python examples/04_customizations.py --cli welcome-screen
python examples/04_customizations.py --cli auto-update-demo
python examples/04_customizations.py --cli interactive-dashboard
python examples/04_customizations.py --cli combined-demo --items 5
python examples/04_customizations.py --cli complex-layout

Command Options:
----------------
- is_button: Display command as a prominent button in GUI
- is_long: Enable real-time output streaming for long processes
- is_auto_exec: Auto-execute when selected (no "Run" button needed)

Key Features:
-------------
- Auto-update: Components update automatically when modified
- Progressive rendering: Use context managers for real-time updates
- Interactive: Buttons and links for GUI actions (GUI-only)
- Composition: Nest Row and Column for complex layouts
"""
