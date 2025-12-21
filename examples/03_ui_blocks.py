"""Example 3: UI Components and Layout

This example demonstrates:
- Table component
- Progressive rendering with context managers
- Row and Column layout components
- Nested component composition
"""

import typer
import typer_ui as tg
import time
import random

app = typer.Typer()
ui = tg.Ui(
    app,
    title="UI Components & Layout",
    description="Tables, progressive rendering, and layouts"
)


@app.command()
def show_table():
    """Simple table - basic table display."""
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
def progressive_table():
    """Progressive rendering - watch table update in real-time with context manager."""
    ui(tg.Md("## Progressive Table Rendering"))
    ui(tg.Text("Watch the table update as rows are added!"))

    # Use context manager for progressive rendering
    with ui(tg.Table(cols=["Step", "Progress", "Duration"], data=[])) as table:
        steps = ["Initializing", "Loading Data", "Processing", "Validating", "Complete"]
        for i, step in enumerate(steps, 1):
            progress = f"{i}/{len(steps)}"
            duration = f"{i * 0.5:.1f}s"
            table.add_row([step, progress, duration])
            time.sleep(0.5)

    ui(tg.Md("[OK] **Processing complete!**"))


@app.command()
def layout_demo():
    """Layout components - demonstrate Row and Column."""
    ui(tg.Md("# Layout Demo"))

    # Horizontal layout with Row
    ui(tg.Md("## Horizontal Buttons"))
    ui(tg.Row([
        tg.Button("Save", on_click=lambda: print("Save clicked")),
        tg.Button("Cancel", on_click=lambda: print("Cancel clicked")),
        tg.Button("Reset", on_click=lambda: print("Reset clicked")),
    ]))

    # Vertical layout with Column
    ui(tg.Md("## Vertical Content"))
    ui(tg.Column([
        tg.Text("First item"),
        tg.Text("Second item"),
        tg.Text("Third item"),
    ]))


@app.command()
def dashboard():
    """Nested composition - complex nested structure with all component types."""
    # Generate random stats
    users = random.randint(1000, 2000)
    revenue = random.randint(50000, 100000)
    growth = random.uniform(5, 15)

    # Complex nested structure
    ui(tg.Column([
        tg.Md("# System Dashboard"),
        tg.Md("Real-time system overview and metrics"),

        tg.Row([
            tg.Button("Refresh Data", on_click=lambda: print("Refreshing...")),
            tg.Button("Export Report", on_click=lambda: print("Exporting...")),
        ]),

        tg.Table(
            cols=["Metric", "Value", "Change"],
            data=[
                ["Active Users", f"{users:,}", f"+{random.randint(5, 15)}%"],
                ["Revenue", f"${revenue:,}", f"+{growth:.1f}%"],
                ["Conversion Rate", f"{random.uniform(2, 5):.2f}%", "+0.3%"],
                ["Server Uptime", "99.9%", "—"],
            ],
            title="Key Performance Indicators"
        ),

        tg.Md("""
## Quick Actions
- Check detailed analytics
- Review user feedback
- Manage system settings
- View audit logs
        """),
    ]))


if __name__ == "__main__":
    ui.app()


"""
CLI Examples:
-------------
python examples/03_ui_blocks.py --cli show-table
python examples/03_ui_blocks.py --cli progressive-table
python examples/03_ui_blocks.py --cli layout-demo
python examples/03_ui_blocks.py --cli dashboard
"""
