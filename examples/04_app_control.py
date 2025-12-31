"""Example 4: Application Control with app.command() API

This example demonstrates:
- app.command("name").run(**kwargs) - Execute with output capture
- app.command("name").include(**kwargs) - Execute inline
- app.command("name").select() - Select a command (GUI mode)
"""

import typer
import typer_ui as tu
from typer_ui import ui, text, dx

typer_app = typer.Typer()
app = tu.UiApp(
    typer_app,
    title="App Control Demo",
    description="Interactive demo of app.command() operations",
)


# ============================================================================
# Sample Commands (used by demo)
# ============================================================================


@typer_app.command()
def fetch_data(source: str = "database"):
    """Fetch data from a source."""
    ui(f"### Fetching from {source}")
    ui(f"- Fetched 150 records from {source}")
    return {"records": 150, "source": source}


@typer_app.command()
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


@typer_app.command()
@app.def_command(auto=True)
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
                    on_click=lambda: app.command("fetch-data").run(source="api"),
                ),
                tu.Button(
                    "Demo .include()",
                    on_click=lambda: app.command("generate-report").include(),
                ),
                tu.Button(
                    "Demo .clear()",
                    on_click=lambda: app.command().clear(),
                ),
                tu.Button(
                    "Demo .select()", on_click=lambda: app.command("fetch-data").select()
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
cmd = app.command("fetch-data").run(source="api")
output = cmd.out      # Captured text output
result = cmd.result   # Return value
```

**`.include(**kwargs)`** - Execute inline (output appears in current context)
```python
result = app.command("generate-report").include()
```

**`.select()`** - Select command in GUI (changes form)
```python
app.command("fetch-data").select()
```
    """
    )


if __name__ == "__main__":
    app()


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
