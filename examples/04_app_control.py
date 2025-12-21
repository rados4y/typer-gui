"""Example 4: Application Control

This example demonstrates:
- Using buttons to execute commands
- Command composition and orchestration
- Programmatic command execution
- Interactive workflows
"""

import typer
import typer_ui as tg
import time
import random

app = typer.Typer()
ui = tg.Ui(
    app,
    title="App Control",
    description="Control commands with buttons and composition"
)


# ============================================================================
# Individual Commands
# ============================================================================

@app.command()
def fetch_data(source: str = "database"):
    """Fetch data from a source."""
    ui(tg.Md(f"## Fetching from {source}..."))
    time.sleep(1)
    ui(tg.Text(f"[OK] Data fetched from {source}"))
    return {"records": random.randint(100, 500), "source": source}


@app.command()
def process_data():
    """Process the fetched data."""
    ui(tg.Md("## Processing data..."))
    time.sleep(1)
    ui(tg.Text("[OK] Data processed successfully"))
    return {"processed": True, "items": random.randint(50, 200)}


@app.command()
def generate_report():
    """Generate a report from processed data."""
    ui(tg.Md("## Generating report..."))
    time.sleep(1)
    ui(tg.Table(
        cols=["Metric", "Value"],
        data=[
            ["Total Records", f"{random.randint(100, 500)}"],
            ["Processed", f"{random.randint(50, 200)}"],
            ["Success Rate", f"{random.randint(85, 99)}%"],
        ],
        title="Report Summary"
    ))
    ui(tg.Text("[OK] Report generated"))


# ============================================================================
# Button-Controlled Commands
# ============================================================================

@app.command()
def button_menu():
    """Button menu - use buttons to execute other commands."""
    ui(tg.Md("# Command Menu"))
    ui(tg.Md("Click any button to execute a command:"))

    ui(tg.Row([
        tg.Button("Fetch Data", on_click=lambda: exec_fetch()),
        tg.Button("Process Data", on_click=lambda: exec_process()),
        tg.Button("Generate Report", on_click=lambda: exec_report()),
    ]))

    ui(tg.Md("---"))
    ui(tg.Md("*Output will appear below when you click a button*"))


def exec_fetch():
    """Execute fetch_data command."""
    ui(tg.Md("### Button clicked: Fetch Data"))
    fetch_data("api")


def exec_process():
    """Execute process_data command."""
    ui(tg.Md("### Button clicked: Process Data"))
    process_data()


def exec_report():
    """Execute generate_report command."""
    ui(tg.Md("### Button clicked: Generate Report"))
    generate_report()


# ============================================================================
# Workflow Examples
# ============================================================================

@app.command()
@ui.command(is_long=True)
def run_workflow():
    """Complete workflow - execute multiple commands in sequence."""
    ui(tg.Md("# Running Complete Workflow"))
    ui(tg.Md("This will execute all steps automatically:"))
    ui(tg.Md(""))

    # Step 1
    ui(tg.Md("**Step 1/3:** Fetching data..."))
    result1 = fetch_data("database")
    ui(tg.Md(""))

    # Step 2
    ui(tg.Md("**Step 2/3:** Processing data..."))
    result2 = process_data()
    ui(tg.Md(""))

    # Step 3
    ui(tg.Md("**Step 3/3:** Generating report..."))
    generate_report()
    ui(tg.Md(""))

    ui(tg.Md("[OK] **Workflow completed successfully!**"))


@app.command()
def workflow_with_buttons():
    """Interactive workflow - control execution with buttons."""
    ui(tg.Md("# Interactive Workflow"))
    ui(tg.Md("Execute the workflow one step at a time:"))

    steps_completed = []

    def step1():
        ui(tg.Md("### Executing Step 1..."))
        fetch_data("api")
        steps_completed.append(1)
        ui(tg.Text(f"Steps completed: {len(steps_completed)}/3"))

    def step2():
        ui(tg.Md("### Executing Step 2..."))
        process_data()
        steps_completed.append(2)
        ui(tg.Text(f"Steps completed: {len(steps_completed)}/3"))

    def step3():
        ui(tg.Md("### Executing Step 3..."))
        generate_report()
        steps_completed.append(3)
        ui(tg.Md("[OK] **All steps completed!**"))

    ui(tg.Column([
        tg.Md("## Workflow Steps"),
        tg.Button("Step 1: Fetch Data", on_click=lambda: step1()),
        tg.Button("Step 2: Process Data", on_click=lambda: step2()),
        tg.Button("Step 3: Generate Report", on_click=lambda: step3()),
    ]))


@app.command()
def quick_actions():
    """Quick actions - common operations accessible via buttons."""
    ui(tg.Md("# Quick Actions Panel"))

    ui(tg.Row([
        tg.Button("Refresh", on_click=lambda: ui(tg.Text("[OK] Refreshed!"))),
        tg.Button("Save", on_click=lambda: ui(tg.Text("[OK] Saved!"))),
        tg.Button("Export", on_click=lambda: ui(tg.Text("[OK] Exported!"))),
    ]))

    ui(tg.Md("---"))

    ui(tg.Table(
        cols=["Action", "Description"],
        data=[
            ["Refresh", "Reload current data"],
            ["Save", "Save changes"],
            ["Export", "Export to file"],
        ]
    ))


if __name__ == "__main__":
    ui.app()


"""
CLI Examples:
-------------
# Individual commands
python examples/04_app_control.py --cli fetch-data --source api
python examples/04_app_control.py --cli process-data
python examples/04_app_control.py --cli generate-report

# Workflows
python examples/04_app_control.py --cli run-workflow
python examples/04_app_control.py --cli button-menu
python examples/04_app_control.py --cli workflow-with-buttons
python examples/04_app_control.py --cli quick-actions
"""
