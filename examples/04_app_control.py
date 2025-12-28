"""Example 4: Application Control with ui.command() API

This example demonstrates:
- ui.command("name").run(**kwargs) - Execute with output capture
- ui.command("name").include(**kwargs) - Execute inline
- ui.command("name").select() - Select a command (GUI mode)
"""

import typer
import typer_ui as tg

app = typer.Typer()
ui = tg.Ui(
    app,
    title="App Control Demo",
    description="Interactive demo of ui.command() operations",
)


# ============================================================================
# Sample Commands (used by demo)
# ============================================================================


@app.command()
def fetch_data(source: str = "database"):
    """Fetch data from a source."""
    ui(tg.Md(f"### Fetching from {source}"))
    ui(tg.Md(f"- Fetched 150 records from {source}"))
    return {"records": 150, "source": source}


@app.command()
def generate_report():
    """Generate a final report."""
    ui(tg.Md("### Final Report"))
    ui(
        tg.Table(
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
@ui.def_command(is_auto_exec=True)
def control_demo():
    """Interactive demo of run(), include(), and select()."""
    ui(tg.Md("# Command Control Demo"))
    ui(tg.Md("Click buttons to see how each method works:"))
    ui(tg.Md("---"))

    # Interactive buttons
    ui(
        tg.Row(
            [
                tg.Button(
                    "Demo .run()",
                    on_click=lambda: ui.command("fetch-data").run(source="api"),
                ),
                tg.Button(
                    "Demo .include()",
                    on_click=lambda: ui.command("generate-report").include(),
                ),
                tg.Button(
                    "Demo .clear()",
                    on_click=lambda: ui.command().clear(),
                ),
                tg.Button(
                    "Demo .select()", on_click=lambda: ui.command("fetch-data").select()
                ),
            ]
        )
    )

    ui(tg.Md("---"))
    ui(
        tg.Md(
            """
### Quick Reference

**`.run(**kwargs)`** - Execute and capture output separately
```python
cmd = ui.command("fetch-data").run(source="api")
output = cmd.out      # Captured text output
result = cmd.result   # Return value
```

**`.include(**kwargs)`** - Execute inline (output appears in current context)
```python
result = ui.command("generate-report").include()
```

**`.select()`** - Select command in GUI (changes form)
```python
ui.command("fetch-data").select()
```
    """
        )
    )


if __name__ == "__main__":
    ui.app()


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
