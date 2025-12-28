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
@ui.def_command(long=True)
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
def ui_tabs():
    """Tabs component - organize content in tabbed interface."""
    ui("# Tabs Component")

    # Basic tabs with simple content
    ui("## Basic Tabs (Simple Content)")
    ui(tg.Tabs([
        tg.Tab("Overview", tg.Md("""
### Welcome to the Overview

This is the **first tab** with some markdown content.

- Feature 1
- Feature 2
- Feature 3
        """)),
        tg.Tab("Details", tg.Column([
            tg.Text("This tab contains multiple components:"),
            tg.Table(
                cols=["Property", "Value"],
                data=[
                    ["Name", "Sample Project"],
                    ["Version", "1.0.0"],
                    ["Status", "Active"],
                ]
            ),
        ])),
        tg.Tab("Settings", tg.Md("""
### Settings

Configure your preferences here.

**Note:** This is just a demo!
        """)),
    ]))

    ui()
    ui("## Tabs with Callable Content (Complex Tabs)")

    # Define complex tab content as functions
    def build_analysis_tab():
        ui("### Data Analysis")
        ui("Loading data from multiple sources...")
        ui()
        ui(tg.Table(
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
        ui(tg.Table(
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
        ui(tg.Link("Q1 Sales Report", on_click=lambda: print("Opening Q1...")))
        ui(tg.Link("Q2 Sales Report", on_click=lambda: print("Opening Q2...")))
        ui()
        ui("**User Reports:**")
        ui(tg.Link("Active Users", on_click=lambda: print("Opening active users...")))
        ui(tg.Link("User Growth", on_click=lambda: print("Opening user growth...")))
        ui()
        ui("**Financial Reports:**")
        ui(tg.Table(
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
        ui(tg.Row([
            tg.Button("Enable All", on_click=lambda: print("Enabling notifications...")),
            tg.Button("Disable All", on_click=lambda: print("Disabling notifications...")),
        ]))
        ui()
        ui("**Data Management:**")
        ui(tg.Md("Cache size: 245 MB"))
        ui(tg.Button("Clear Cache", on_click=lambda: print("Clearing cache...")))

    # Use callables for complex tabs
    ui(tg.Tabs([
        tg.Tab("Analysis", build_analysis_tab),
        tg.Tab("Reports", build_reports_tab),
        tg.Tab("Settings", build_settings_tab),
        tg.Tab("Quick", lambda: ui("### Quick Tab\nThis is built with a lambda!")),
    ]))


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
python examples/03_ui_blocks.py --cli ui-tabs
python examples/03_ui_blocks.py --cli ui-nested
"""
