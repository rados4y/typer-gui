"""Example 3: UI Components

This example demonstrates individual UI components:
- Text and Markdown
- Table
- Row and Column layout
- Button and Link
- Tabs
- Nested composition
"""

import time

import typer2ui
from typer2ui import ui

app = typer2ui.Typer2Ui(
    title="UI Components", description="Demonstrations of each UI component"
)


@app.command(view=True)
def ui_text_md():
    """Text and Markdown components - simple text display and rich formatting."""
    # Plain text
    ui.print("This is plain text using ui.print()")

    # Markdown (use typer2ui.Md() directly or just ui() with string)
    ui(
        """
# Markdown Component

You can use **bold**, *italic*, and `code` formatting.

## Features
- Lists and tables
- Code blocks
- Headers and emphasis
"""
    )


@app.command(view=True)
def ui_table():
    """Table component - display tabular data."""
    ui(
        typer2ui.Table(
            cols=["Name", "Email", "Role"],
            data=[
                ["Alice Smith", "alice@example.com", "Admin"],
                ["Bob Johnson", "bob@example.com", "User"],
                ["Carol White", "carol@example.com", "Manager"],
            ],
            title="User Directory",
        )
    )


@app.command(threaded=True)
def ui_table_progressive():
    """Table with progressive rendering - add rows dynamically with context manager."""
    ui("## Progressive Table")

    # Use context manager for progressive rendering
    with ui(typer2ui.Table(cols=["Step", "Status"], data=[])) as table:
        steps = ["Initialize", "Load Data", "Process", "Validate", "Complete"]
        for step in steps:
            table.add_row([step, "[OK]"])
            time.sleep(0.5)


@app.command(view=True)
def ui_row_column():
    """Row and Column layout - arrange components horizontally and vertically."""
    ui("# Layout Components")

    # Horizontal layout
    ui("## Row (Horizontal)")
    ui(
        typer2ui.Row(
            [
                typer2ui.Text("Item 1"),
                typer2ui.Text("Item 2"),
                typer2ui.Text("Item 3"),
            ]
        )
    )

    # Vertical layout
    ui("## Column (Vertical)")
    ui(
        typer2ui.Column(
            [
                typer2ui.Text("First"),
                typer2ui.Text("Second"),
                typer2ui.Text("Third"),
            ]
        )
    )


@app.command(view=True)
def ui_button_link():
    """Button and Link components - interactive elements (GUI only)."""
    ui("# Interactive Components")

    ui("## Buttons")
    ui(
        typer2ui.Row(
            [
                typer2ui.Button("Save", on_click=lambda: print("Save clicked")),
                typer2ui.Button("Cancel", on_click=lambda: print("Cancel clicked")),
                typer2ui.Button("Delete", on_click=lambda: print("Delete clicked")),
            ]
        )
    )

    ui("## Links")
    ui(
        typer2ui.Column(
            [
                typer2ui.Link("Settings", on_click=lambda: print("Settings clicked")),
                typer2ui.Link("Help", on_click=lambda: print("Help clicked")),
                typer2ui.Link("About", on_click=lambda: print("About clicked")),
            ]
        )
    )

    ui("*Note: Buttons and Links are GUI-only and won't appear in CLI mode.*")


@app.command(view=True)
def ui_tabs():
    """Tabs component - organize content in tabbed interface."""
    ui("# Tabs Component")

    # Basic tabs with simple content
    ui("## Basic Tabs (Simple Content)")
    ui(
        typer2ui.Tabs(
            [
                typer2ui.Tab(
                    "Overview",
                    """
### Welcome to the Overview

This is the **first tab** with some markdown content.

- Feature 1
- Feature 2
- Feature 3
        """,
                ),
                typer2ui.Tab(
                    "Details",
                    typer2ui.Column(
                        [
                            typer2ui.Text("This tab contains multiple components:"),
                            typer2ui.Table(
                                cols=["Property", "Value"],
                                data=[
                                    ["Name", "Sample Project"],
                                    ["Version", "1.0.0"],
                                    ["Status", "Active"],
                                ],
                            ),
                        ]
                    ),
                ),
                typer2ui.Tab(
                    "Settings",
                    """
### Settings

Configure your preferences here.

**Note:** This is just a demo!
        """,
                ),
            ]
        )
    )

    ui()
    ui("## Tabs with Callable Content (Complex Tabs)")

    # Define complex tab content as functions
    def build_analysis_tab():
        ui("### Data Analysis")
        ui("Loading data from multiple sources...")
        ui()
        ui(
            typer2ui.Table(
                cols=["Source", "Records", "Status"],
                data=[
                    ["Database A", "1,234", "OK"],
                    ["Database B", "5,678", "OK"],
                    ["API Feed", "9,012", "OK"],
                ],
                title="Data Sources",
            )
        )
        ui()
        ui("### Processing Results")
        ui(
            typer2ui.Table(
                cols=["Step", "Duration", "Result"],
                data=[
                    ["Extract", "2.3s", "Success"],
                    ["Transform", "5.1s", "Success"],
                    ["Load", "3.7s", "Success"],
                ],
            )
        )
        ui()
        ui("**Analysis complete!** All systems operational.")

    def build_reports_tab():
        ui("### Available Reports")
        ui()
        ui("**Sales Reports:**")
        ui(typer2ui.Link("Q1 Sales Report", on_click=lambda: print("Opening Q1...")))
        ui(typer2ui.Link("Q2 Sales Report", on_click=lambda: print("Opening Q2...")))
        ui()
        ui("**User Reports:**")
        ui(typer2ui.Link("Active Users", on_click=lambda: print("Opening active users...")))
        ui(typer2ui.Link("User Growth", on_click=lambda: print("Opening user growth...")))
        ui()
        ui("**Financial Reports:**")
        ui(
            typer2ui.Table(
                cols=["Report", "Period", "Size"],
                data=[
                    ["Revenue Summary", "2024-Q4", "2.3 MB"],
                    ["Expense Breakdown", "2024-Q4", "1.8 MB"],
                    ["Profit & Loss", "2024-Q4", "1.2 MB"],
                ],
            )
        )

    def build_settings_tab():
        ui("### Application Settings")
        ui()
        ui("**General:**")
        ui("- Auto-refresh: Enabled")
        ui("- Theme: Light")
        ui("- Language: English")
        ui()
        ui("**Notifications:**")
        ui(
            typer2ui.Row(
                [
                    typer2ui.Button(
                        "Enable All",
                        on_click=lambda: print("Enabling notifications..."),
                    ),
                    typer2ui.Button(
                        "Disable All",
                        on_click=lambda: print("Disabling notifications..."),
                    ),
                ]
            )
        )
        ui()
        ui("**Data Management:**")
        ui("Cache size: 245 MB")
        ui(typer2ui.Button("Clear Cache", on_click=lambda: print("Clearing cache...")))

    # Use callables for complex tabs
    ui(
        typer2ui.Tabs(
            [
                typer2ui.Tab("Analysis", build_analysis_tab),
                typer2ui.Tab("Reports", build_reports_tab),
                typer2ui.Tab("Settings", build_settings_tab),
                typer2ui.Tab(
                    "Quick", lambda: ui("### Quick Tab\nThis is built with a lambda!")
                ),
            ]
        )
    )


@app.command(view=True)
def ui_alert_confirm():
    """Alert and Confirm dialogs - interactive dialogs for notifications and confirmations."""
    ui("# Dialog Components")
    ui("## Alert Dialog")
    ui("Show informational alerts with OK button:")

    ui(
        typer2ui.Row(
            [
                typer2ui.Link(
                    "Simple Alert",
                    on_click=lambda: ui(
                        typer2ui.Alert("Information", "This is a simple alert message.")
                    ),
                ),
                typer2ui.Link(
                    "Markdown Alert",
                    on_click=lambda: ui(
                        typer2ui.Alert(
                            "Formatted Content",
                            typer2ui.Md(
                                """
## Important Notice

This alert contains **formatted** content:
- Feature 1 enabled
- Feature 2 configured
- All systems operational
                """
                            ),
                        )
                    ),
                ),
            ]
        )
    )

    ui()
    ui("## Confirm Dialog")
    ui("Ask for user confirmation with Yes/No buttons:")

    def on_confirmed():
        ui("✓ User confirmed the action!")

    def on_cancelled():
        ui("✗ User cancelled the action.")

    ui(
        typer2ui.Row(
            [
                typer2ui.Link(
                    "Confirm Action",
                    on_click=lambda: ui(
                        typer2ui.Confirm(
                            "Confirm Action",
                            "Are you sure you want to proceed with this operation?",
                            on_yes=on_confirmed,
                            on_no=on_cancelled,
                        )
                    ),
                ),
                typer2ui.Link(
                    "Delete Confirmation",
                    on_click=lambda: ui(
                        typer2ui.Confirm(
                            "Delete Item",
                            typer2ui.Md(
                                "**Warning:** This action cannot be undone!\n\nAre you sure?"
                            ),
                            on_yes=lambda: ui("Item deleted."),
                            on_no=lambda: ui("Delete cancelled."),
                        )
                    ),
                ),
            ]
        )
    )

    ui()
    ui(
        "*Note: Dialogs work in both GUI and CLI modes. In CLI, they prompt for user input.*"
    )


@app.command(view=True)
def ui_nested():
    """Nested components - combining multiple components in a hierarchy."""
    ui("# Dashboard")
    ui("Example of nested component composition")

    ui(
        typer2ui.Row(
            [
                typer2ui.Button("Refresh", on_click=lambda: print("Refreshing...")),
                typer2ui.Button("Export", on_click=lambda: print("Exporting...")),
            ]
        )
    )

    ui(
        typer2ui.Table(
            cols=["Metric", "Value"],
            data=[
                ["Users", "1,234"],
                ["Revenue", "$56,789"],
                ["Growth", "+12%"],
            ],
            title="Key Metrics",
        )
    )

    ui("All components work together seamlessly!")


if __name__ == "__main__":
    app()


"""
CLI Examples:
-------------
python examples/e03_ui_blocks.py --cli ui-text-md
python examples/e03_ui_blocks.py --cli ui-table
python examples/e03_ui_blocks.py --cli ui-table-progressive
python examples/e03_ui_blocks.py --cli ui-row-column
python examples/e03_ui_blocks.py --cli ui-button-link
python examples/e03_ui_blocks.py --cli ui-tabs
python examples/e03_ui_blocks.py --cli ui-alert-confirm
python examples/e03_ui_blocks.py --cli ui-nested
"""
