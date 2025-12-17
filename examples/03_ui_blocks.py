"""Example 3: UI Blocks and UICommand Methods

This example demonstrates:
- UI Blocks: table, markdown, link
- UICommand methods: select(), run(), include(), clear()
- Auto-executed vs manual commands
- Passing parameters to commands
"""

import typer
import typer_gui
import random

app = typer.Typer()
ui = typer_gui.Ui(
    app, title="UI Blocks & Commands", description="Rich components and command control"
)


@app.command()
@ui.options(is_auto_exec=True)
def show_table():
    """Display random data as a table (auto-executed)."""
    # Generate random data
    users = [
        ["Alice Smith", "alice@example.com", "Admin"],
        ["Bob Johnson", "bob@example.com", "User"],
        ["Carol White", "carol@example.com", "Manager"],
        ["David Brown", "david@example.com", "User"],
        ["Eve Davis", "eve@example.com", "Admin"],
    ]

    # Randomly select 3 users
    selected = random.sample(users, 3)

    ui.out.table(
        headers=["Name", "Email", "Role"],
        rows=selected,
        title="Random Users Sample",
    )


@app.command()
@ui.options(is_auto_exec=True)
def show_markdown():
    """Display random data as markdown (auto-executed)."""
    # Generate random stats
    uptime = random.uniform(95.0, 99.9)
    response_time = random.randint(50, 200)
    active_users = random.randint(800, 1500)

    ui.out.md(
        f"""
# System Statistics

Current system metrics (randomly generated):

## Performance
- **Uptime**: {uptime:.2f}%
- **Response Time**: {response_time}ms
- **Active Users**: {active_users:,}

## Status
All systems operational.
"""
    )


@app.command()
def calc(x: int = 10, y: int = 5):
    """Simple calculator - NOT auto-executed (requires manual run)."""
    result_add = x + y
    result_mult = x * y
    result_sub = x - y

    print(f"Calculator Results for x={x}, y={y}:")
    print(f"  Addition: {x} + {y} = {result_add}")
    print(f"  Multiplication: {x} * {y} = {result_mult}")
    print(f"  Subtraction: {x} - {y} = {result_sub}")

    return {"add": result_add, "mult": result_mult, "sub": result_sub}


@app.command()
@ui.options(is_auto_exec=True)
def command_methods():
    """Demonstrates all UICommand methods using links (auto-executed)."""
    if not ui.runtime:
        print("This demo requires GUI mode (UICommand methods are GUI-only)")
        return

    # Display intro
    ui.out.md(
        """
# UICommand Methods Demo

This demonstrates all four UICommand methods with both:
- **Auto-executed commands** (run automatically when selected)
- **Manual commands** (require explicit execution)
"""
    )

    print()
    ui.out.md("### SELECT Method - Navigate to Commands:")
    print()

    with ui.out.row():
        ui.out.button("show-table", do=lambda: ui.command("show-table").select())
        ui.out.link("calc", do=lambda: ui.command("calc").select())

    print()
    ui.out.md("### RUN Method - Execute and Capture Output:")
    print()

    with ui.out.row():
        ui.out.button(
            "show-markdown", do=lambda: ui.command("show-markdown").run()
        )
        ui.out.link(
            "calc(x=15, y=3)", do=lambda: ui.command("calc").run(x=15, y=3)
        )

    print()
    ui.out.md("### INCLUDE Method - Execute Inline:")
    print()

    with ui.out.row():
        ui.out.button(
            "show-markdown", do=lambda: ui.command("show-markdown").include()
        )
        ui.out.link(
            "calc(x=20, y=4)", do=lambda: ui.command("calc").include(x=20, y=4)
        )

    print()
    ui.out.md("### CLEAR Method - Clear and Re-execute:")
    print()

    with ui.out.row():
        ui.out.button("clear", do=lambda: ui.command("command-methods").clear())

    print()
    ui.out.md("---")


if __name__ == "__main__":
    ui.app()


"""
CLI Examples:
-------------
python 03_ui_blocks.py --cli show-table
python 03_ui_blocks.py --cli show-markdown
python 03_ui_blocks.py --cli calc --x 100 --y 25

UICommand Methods (GUI only):
------------------------------
- select()       : Navigate to command (auto-exec runs immediately)
- run(**params)  : Execute with params, capture output/result
- include(**params) : Execute with params inline (output in current context)
- clear()        : Clear output (auto-exec re-runs after clear)

Auto-exec Behavior:
-------------------
- Auto-exec commands run automatically when selected or after clear()
- Manual commands require explicit run() or include() with parameters
- Both types can be executed programmatically with run()/include()

Note: The command-methods demo is interactive and best experienced in GUI mode.
"""
