"""Example 3: UI Components

This example demonstrates individual UI components:
- Text and Markdown
- Table
- Row and Column layout
- Button and Link
- Nested composition
"""

import typer
import typer_ui as tg
import time

app = typer.Typer()
ui = tg.Ui(
    app,
    title="UI Components",
    description="Demonstrations of each UI component"
)


@app.command()
def ui_text_md():
    """Text and Markdown components - simple text display and rich formatting."""
    # Plain text
    ui(tg.Text("This is plain text using tg.Text()"))

    # Markdown
    ui(tg.Md("""
# Markdown Component

You can use **bold**, *italic*, and `code` formatting.

## Features
- Lists and tables
- Code blocks
- Headers and emphasis
"""))


@app.command()
def ui_table():
    """Table component - display tabular data."""
    ui(tg.Table(
        cols=["Name", "Email", "Role"],
        data=[
            ["Alice Smith", "alice@example.com", "Admin"],
            ["Bob Johnson", "bob@example.com", "User"],
            ["Carol White", "carol@example.com", "Manager"],
        ],
        title="User Directory"
    ))


@app.command()
@ui.command(is_long=True)
def ui_table_progressive():
    """Table with progressive rendering - add rows dynamically with context manager."""
    ui(tg.Md("## Progressive Table"))

    # Use context manager for progressive rendering
    with ui(tg.Table(cols=["Step", "Status"], data=[])) as table:
        steps = ["Initialize", "Load Data", "Process", "Validate", "Complete"]
        for step in steps:
            table.add_row([step, "[OK]"])
            time.sleep(0.5)


@app.command()
def ui_row_column():
    """Row and Column layout - arrange components horizontally and vertically."""
    ui(tg.Md("# Layout Components"))

    # Horizontal layout
    ui(tg.Md("## Row (Horizontal)"))
    ui(tg.Row([
        tg.Text("Item 1"),
        tg.Text("Item 2"),
        tg.Text("Item 3"),
    ]))

    # Vertical layout
    ui(tg.Md("## Column (Vertical)"))
    ui(tg.Column([
        tg.Text("First"),
        tg.Text("Second"),
        tg.Text("Third"),
    ]))


@app.command()
def ui_button_link():
    """Button and Link components - interactive elements (GUI only)."""
    ui(tg.Md("# Interactive Components"))

    ui(tg.Md("## Buttons"))
    ui(tg.Row([
        tg.Button("Save", on_click=lambda: print("Save clicked")),
        tg.Button("Cancel", on_click=lambda: print("Cancel clicked")),
        tg.Button("Delete", on_click=lambda: print("Delete clicked")),
    ]))

    ui(tg.Md("## Links"))
    ui(tg.Column([
        tg.Link("Settings", on_click=lambda: print("Settings clicked")),
        tg.Link("Help", on_click=lambda: print("Help clicked")),
        tg.Link("About", on_click=lambda: print("About clicked")),
    ]))

    ui(tg.Md("*Note: Buttons and Links are GUI-only and won't appear in CLI mode.*"))


@app.command()
def ui_nested():
    """Nested components - combining multiple components in a hierarchy."""
    ui(tg.Column([
        tg.Md("# Dashboard"),
        tg.Md("Example of nested component composition"),

        tg.Row([
            tg.Button("Refresh", on_click=lambda: print("Refreshing...")),
            tg.Button("Export", on_click=lambda: print("Exporting...")),
        ]),

        tg.Table(
            cols=["Metric", "Value"],
            data=[
                ["Users", "1,234"],
                ["Revenue", "$56,789"],
                ["Growth", "+12%"],
            ],
            title="Key Metrics"
        ),

        tg.Md("All components work together seamlessly!"),
    ]))


if __name__ == "__main__":
    ui.app()


"""
CLI Examples:
-------------
python examples/03_ui_blocks.py --cli ui-text-md
python examples/03_ui_blocks.py --cli ui-table
python examples/03_ui_blocks.py --cli ui-table-progressive
python examples/03_ui_blocks.py --cli ui-row-column
python examples/03_ui_blocks.py --cli ui-button-link
python examples/03_ui_blocks.py --cli ui-nested
"""
