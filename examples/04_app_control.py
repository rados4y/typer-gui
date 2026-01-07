"""Example 4: Application Control with upp.command() API

This example demonstrates:
- upp.command("name").run(**kwargs) - Execute with output capture
- upp.command("name").include(**kwargs) - Execute inline
- upp.command("name").select() - Select a command (GUI mode)
"""

import typer
import typer2ui as tu
from typer2ui import ui, text, dx

tapp = typer.Typer()
upp = tu.UiApp(
    tapp,
    title="App Control Demo",
    description="Interactive demo of upp.command() operations",
)


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
                    "Demo .select()", on_click=lambda: upp.command("fetch-data").select()
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
