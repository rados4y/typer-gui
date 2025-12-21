"""Example 3: UI Components and Layout

This example demonstrates:
- Table component with auto-update
- Row and Column layout components
- Nested component composition
- Progressive rendering with context managers
"""

import typer
import typer_ui as tg
import time
import random

app = typer.Typer()
ui = tg.Ui(
    app,
    title="UI Components",
    description="Tables, layout, and composition"
)


@app.command()
def show_table():
    """Simple table display."""
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
def auto_update_table():
    """Demonstrate table auto-update feature."""
    ui(tg.Md("## Auto-Updating Table"))
    ui(tg.Text("Watch the table update as rows are added!"))

    # Create and present table
    table = tg.Table(cols=["Component", "Status"], data=[])
    ui(table)

    # Add rows - table automatically updates!
    components = ["Database", "API Server", "Cache", "Workers", "Frontend"]
    for comp in components:
        table.add_row([comp, "[OK] Initialized"])
        time.sleep(0.5)

    ui(tg.Md("[OK] **All components ready!**"))


@app.command()
@ui.command(is_long=True)
def progressive_table():
    """Demonstrate progressive rendering with context manager."""
    ui(tg.Md("## Progressive Rendering"))

    # Use context manager for cleaner code
    with ui(tg.Table(cols=["Step", "Progress", "Duration"], data=[])) as t:
        steps = ["Initializing", "Loading Data", "Processing", "Validating", "Complete"]
        for i, step in enumerate(steps, 1):
            progress = f"{i}/{len(steps)}"
            duration = f"{i * 0.5:.1f}s"
            t.add_row([step, progress, duration])
            time.sleep(0.5)

    ui(tg.Md("[OK] **Processing complete!**"))


@app.command()
def layout_demo():
    """Demonstrate Row and Column layout components."""
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
    """Demonstrate nested component composition."""
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


@app.command()
def show_markdown():
    """Display formatted markdown content."""
    ui(tg.Md("""
# Markdown Features

You can use **bold**, *italic*, and `code` formatting.

## Lists

### Unordered
- Feature 1
- Feature 2
- Feature 3

### Ordered
1. First step
2. Second step
3. Third step

## Tables

| Feature | Status | Priority |
|---------|--------|----------|
| Tables  | [OK]   | High     |
| Links   | [OK]   | Medium   |
| Images  | Planned| Low      |

## Code Blocks

```python
def hello():
    print("Hello from Typer-UI!")
```

---

Markdown works in both GUI and CLI modes!
    """))


@app.command()
def mixed_output():
    """Mix different component types and print statements."""
    ui(tg.Md("# Mixed Content Example"))

    # Regular print still works
    print("This is from print()")

    # Mix components
    ui(tg.Text("Plain text component"))

    ui(tg.Table(
        cols=["Output Type", "Method", "When to Use"],
        data=[
            ["Plain text", "print() or tg.Text()", "Simple messages"],
            ["Formatted", "tg.Md()", "Rich content"],
            ["Tabular", "tg.Table()", "Structured data"],
            ["Interactive", "tg.Button/Link", "GUI actions"],
        ]
    ))

    ui(tg.Md("""
## Summary
You can freely mix:
- `print()` statements
- UI components (`Text`, `Md`, `Table`)
- Layout elements (`Row`, `Column`)
- Interactive elements (`Button`, `Link`)

Everything works together seamlessly in both CLI and GUI!
    """))


if __name__ == "__main__":
    ui.app()


"""
CLI Examples:
-------------
python examples/03_ui_blocks.py --cli show-table
python examples/03_ui_blocks.py --cli auto-update-table
python examples/03_ui_blocks.py --cli progressive-table
python examples/03_ui_blocks.py --cli layout-demo
python examples/03_ui_blocks.py --cli dashboard
python examples/03_ui_blocks.py --cli show-markdown
python examples/03_ui_blocks.py --cli mixed-output
"""
