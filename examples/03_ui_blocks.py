"""Example 3: UI Components

This example demonstrates individual UI components:
- Text and Markdown
- Table
- Row and Column layout
- Button and Link
- Tabs
- Nested composition
"""

import typer
import typer_ui as tu
from typer_ui import ui, text, dx
import time

typer_app = typer.Typer()
app = tu.UiApp(
    typer_app,
    title="UI Components",
    description="Demonstrations of each UI component"
)


@typer_app.command()
def ui_text_md():
    """Text and Markdown components - simple text display and rich formatting."""
    # Plain text
    text("This is plain text using text()")

    # Markdown (use tu.Md() directly or just ui() with string)
    ui("""
# Markdown Component

You can use **bold**, *italic*, and `code` formatting.

## Features
- Lists and tables
- Code blocks
- Headers and emphasis
""")


@typer_app.command()
def ui_table():
    """Table component - display tabular data."""
    ui(tu.Table(
        cols=["Name", "Email", "Role"],
        data=[
            ["Alice Smith", "alice@example.com", "Admin"],
            ["Bob Johnson", "bob@example.com", "User"],
            ["Carol White", "carol@example.com", "Manager"],
        ],
        title="User Directory"
    ))


@typer_app.command()
@app.def_command(long=True)
def ui_table_progressive():
    """Table with progressive rendering - add rows dynamically with context manager."""
    ui("## Progressive Table")

    # Use context manager for progressive rendering
    with ui(tu.Table(cols=["Step", "Status"], data=[])) as table:
        steps = ["Initialize", "Load Data", "Process", "Validate", "Complete"]
        for step in steps:
            table.add_row([step, "[OK]"])
            time.sleep(0.5)


@typer_app.command()
def ui_row_column():
    """Row and Column layout - arrange components horizontally and vertically."""
    ui("# Layout Components")

    # Horizontal layout
    ui("## Row (Horizontal)")
    ui(tu.Row([
        tu.Text("Item 1"),
        tu.Text("Item 2"),
        tu.Text("Item 3"),
    ]))

    # Vertical layout
    ui("## Column (Vertical)")
    ui(tu.Column([
        tu.Text("First"),
        tu.Text("Second"),
        tu.Text("Third"),
    ]))


@typer_app.command()
def ui_button_link():
    """Button and Link components - interactive elements (GUI only)."""
    ui("# Interactive Components")

    ui("## Buttons")
    ui(tu.Row([
        tu.Button("Save", on_click=lambda: print("Save clicked")),
        tu.Button("Cancel", on_click=lambda: print("Cancel clicked")),
        tu.Button("Delete", on_click=lambda: print("Delete clicked")),
    ]))

    ui("## Links")
    ui(tu.Column([
        tu.Link("Settings", on_click=lambda: print("Settings clicked")),
        tu.Link("Help", on_click=lambda: print("Help clicked")),
        tu.Link("About", on_click=lambda: print("About clicked")),
    ]))

    ui("*Note: Buttons and Links are GUI-only and won't appear in CLI mode.*")


@typer_app.command()
def ui_tabs():
    """Tabs component - organize content in tabbed interface."""
    ui("# Tabs Component")

    # Basic tabs with simple content
    ui("## Basic Tabs (Simple Content)")
    ui(tu.Tabs([
        tu.Tab("Overview", """
### Welcome to the Overview

This is the **first tab** with some markdown content.

- Feature 1
- Feature 2
- Feature 3
        """),
        tu.Tab("Details", tu.Column([
            tu.Text("This tab contains multiple components:"),
            tu.Table(
                cols=["Property", "Value"],
                data=[
                    ["Name", "Sample Project"],
                    ["Version", "1.0.0"],
                    ["Status", "Active"],
                ]
            ),
        ])),
        tu.Tab("Settings", """
### Settings

Configure your preferences here.

**Note:** This is just a demo!
        """),
    ]))

    ui()
    ui("## Tabs with Callable Content (Complex Tabs)")

    # Define complex tab content as functions
    def build_analysis_tab():
        ui("### Data Analysis")
        ui("Loading data from multiple sources...")
        ui()
        ui(tu.Table(
            cols=["Source", "Records", "Status"],
            data=[
                ["Database A", "1,234", "OK"],
                ["Database B", "5,678", "OK"],
                ["API Feed", "9,012", "OK"],
            ],
            title="Data Sources"
        ))
        ui()
        ui("### Processing Results")
        ui(tu.Table(
            cols=["Step", "Duration", "Result"],
            data=[
                ["Extract", "2.3s", "Success"],
                ["Transform", "5.1s", "Success"],
                ["Load", "3.7s", "Success"],
            ]
        ))
        ui()
        ui("**Analysis complete!** All systems operational.")

    def build_reports_tab():
        ui("### Available Reports")
        ui()
        ui("**Sales Reports:**")
        ui(tu.Link("Q1 Sales Report", on_click=lambda: print("Opening Q1...")))
        ui(tu.Link("Q2 Sales Report", on_click=lambda: print("Opening Q2...")))
        ui()
        ui("**User Reports:**")
        ui(tu.Link("Active Users", on_click=lambda: print("Opening active users...")))
        ui(tu.Link("User Growth", on_click=lambda: print("Opening user growth...")))
        ui()
        ui("**Financial Reports:**")
        ui(tu.Table(
            cols=["Report", "Period", "Size"],
            data=[
                ["Revenue Summary", "2024-Q4", "2.3 MB"],
                ["Expense Breakdown", "2024-Q4", "1.8 MB"],
                ["Profit & Loss", "2024-Q4", "1.2 MB"],
            ]
        ))

    def build_settings_tab():
        ui("### Application Settings")
        ui()
        ui("**General:**")
        ui("- Auto-refresh: Enabled")
        ui("- Theme: Light")
        ui("- Language: English")
        ui()
        ui("**Notifications:**")
        ui(tu.Row([
            tu.Button("Enable All", on_click=lambda: print("Enabling notifications...")),
            tu.Button("Disable All", on_click=lambda: print("Disabling notifications...")),
        ]))
        ui()
        ui("**Data Management:**")
        ui("Cache size: 245 MB")
        ui(tu.Button("Clear Cache", on_click=lambda: print("Clearing cache...")))

    # Use callables for complex tabs
    ui(tu.Tabs([
        tu.Tab("Analysis", build_analysis_tab),
        tu.Tab("Reports", build_reports_tab),
        tu.Tab("Settings", build_settings_tab),
        tu.Tab("Quick", lambda: ui("### Quick Tab\nThis is built with a lambda!")),
    ]))


@typer_app.command()
def ui_nested():
    """Nested components - combining multiple components in a hierarchy."""
    ui("# Dashboard")
    ui("Example of nested component composition")

    ui(tu.Row([
        tu.Button("Refresh", on_click=lambda: print("Refreshing...")),
        tu.Button("Export", on_click=lambda: print("Exporting...")),
    ]))

    ui(tu.Table(
        cols=["Metric", "Value"],
        data=[
            ["Users", "1,234"],
            ["Revenue", "$56,789"],
            ["Growth", "+12%"],
        ],
        title="Key Metrics"
    ))

    ui("All components work together seamlessly!")


if __name__ == "__main__":
    app()


"""
CLI Examples:
-------------
python examples/03_ui_blocks.py --cli ui-text-md
python examples/03_ui_blocks.py --cli ui-table
python examples/03_ui_blocks.py --cli ui-table-progressive
python examples/03_ui_blocks.py --cli ui-row-column
python examples/03_ui_blocks.py --cli ui-button-link
python examples/03_ui_blocks.py --cli ui-tabs
python examples/03_ui_blocks.py --cli ui-nested
"""
