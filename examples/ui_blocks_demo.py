"""Demonstration of UI Blocks - rich interactive components."""

import sys
from pathlib import Path

# Add parent directory to path for typer_gui import
sys.path.insert(0, str(Path(__file__).parent.parent))

import typer
import typer_gui

# Create the Typer app
app = typer.Typer(help="Demo of UI Blocks functionality")

# Create UI wrapper
ui = typer_gui.Ui(
    app,
    title="UI Blocks Demo",
    description="Demonstration of rich UI components: tables, markdown, links, and buttons.",
)


@app.command()
def users():
    """Display a table of users."""
    return typer_gui.ui_blocks.render_for_mode(
        ui.table(
            headers=["Name", "Age", "City", "Status"],
            rows=[
                ["Alice Johnson", 30, "New York", "Active"],
                ["Bob Smith", 25, "San Francisco", "Active"],
                ["Charlie Brown", 35, "Los Angeles", "Inactive"],
                ["Diana Prince", 28, "Chicago", "Active"],
            ],
            title="User Directory"
        )
    )


@app.command()
def report():
    """Generate a formatted report using markdown."""
    return typer_gui.ui_blocks.render_for_mode(ui.md("""
# System Status Report

## Overview
This report provides a comprehensive overview of the system status.

## Metrics

### Performance
- **CPU Usage**: 45%
- **Memory**: 8.2 GB / 16 GB (51%)
- **Disk**: 250 GB / 500 GB (50%)

### System Health
All systems are operational and running smoothly.

## Recent Activity

| Time     | Event              | Status |
|----------|-------------------|--------|
| 10:30 AM | Backup Completed  | ✓      |
| 11:15 AM | Update Installed  | ✓      |
| 02:45 PM | Health Check      | ✓      |

## Code Example

```python
# Example system check
def check_system():
    return {"cpu": 45, "memory": 51, "disk": 50}
```

## Recommendations

1. **Monitor** disk usage - approaching 50% capacity
2. **Review** recent backup logs
3. **Schedule** next maintenance window

---

*Report generated on: 2025-12-01*
"""))


@app.command()
def dashboard():
    """Display a dashboard with multiple UI blocks."""
    # Return a list of UI blocks
    return typer_gui.ui_blocks.render_for_mode([
        ui.md("# Welcome to the Dashboard\n\nHere's an overview of your system:"),
        ui.table(
            headers=["Metric", "Value", "Change"],
            rows=[
                ["Active Users", "1,234", "+12%"],
                ["Revenue", "$45,678", "+8%"],
                ["Orders", "567", "+15%"],
            ],
            title="Key Performance Indicators"
        ),
        ui.md("## Quick Actions\n\nUse the buttons below to perform common tasks:"),
        ui.button("Refresh Data", "dashboard", icon="refresh"),
        ui.link("View User Details", "users"),
    ])


@app.command()
def products():
    """Display product catalog."""
    return typer_gui.ui_blocks.render_for_mode([
        ui.md("# Product Catalog"),
        ui.table(
            headers=["ID", "Product", "Price", "Stock"],
            rows=[
                ["001", "Laptop", "$999", "24"],
                ["002", "Mouse", "$29", "150"],
                ["003", "Keyboard", "$79", "89"],
                ["004", "Monitor", "$299", "42"],
            ]
        ),
        ui.button("Add New Product", "products", icon="add"),
    ])


@app.command()
def navigation():
    """Show navigation links (GUI only)."""
    return typer_gui.ui_blocks.render_for_mode([
        ui.md("# Navigation Menu\n\nClick a link to navigate:"),
        ui.link("📊 View Dashboard", "dashboard"),
        ui.link("👥 User Directory", "users"),
        ui.link("📦 Product Catalog", "products"),
        ui.link("📈 System Report", "report"),
    ])


@app.command()
def mixed_output():
    """Demonstrate mixing print statements with UI blocks."""
    print("Starting data processing...")
    print("Loading data...")

    # You can mix print statements with UI blocks
    result = ui.table(
        headers=["Step", "Status", "Duration"],
        rows=[
            ["Load Data", "✓ Complete", "1.2s"],
            ["Process", "✓ Complete", "2.5s"],
            ["Validate", "✓ Complete", "0.8s"],
        ],
        title="Processing Summary"
    )

    print("Processing completed successfully!")
    return typer_gui.ui_blocks.render_for_mode(result)


if __name__ == "__main__":
    # Launch the GUI
    # Or use: python ui_blocks_demo.py --cli <command>
    ui.app()
