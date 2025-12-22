"""Example 4: Application Control with app.command() API

This example demonstrates:
- ui.runtime.command("name") - Get a command by name
- cmd.select() - Select a command (GUI mode)
- cmd.run(**kwargs) - Execute with output capture
- cmd.include(**kwargs) - Execute inline
- cmd.clear() - Clear command output
- ui.runtime.command() - Get current command
- Retrieving output from executed commands
"""

import typer
import typer_ui as tg

app = typer.Typer()
ui = tg.Ui(
    app,
    title="App Control API",
    description="Interactive demos of app.command() operations"
)


# ============================================================================
# Base Commands (used by demos)
# ============================================================================

@app.command()
def fetch_data(source: str = "database"):
    """Fetch data from a source."""
    ui(tg.Md(f"### Fetching from {source}"))
    ui(tg.Text(f"✓ Fetched 150 records from {source}"))
    return {"records": 150, "source": source}


@app.command()
def process_data():
    """Process the fetched data."""
    ui(tg.Md("### Processing data"))
    ui(tg.Text("✓ Processed 120 records"))
    return {"processed": 120}


@app.command()
def generate_report():
    """Generate a final report."""
    ui(tg.Table(
        cols=["Metric", "Value"],
        data=[
            ["Total Records", "150"],
            ["Processed", "120"],
            ["Success Rate", "95%"],
        ],
        title="Final Report"
    ))
    return {"status": "complete"}


# ============================================================================
# Demo: cmd.include()
# ============================================================================

@app.command()
def demo_include():
    """Demo: cmd.include() - Execute command inline using buttons."""
    ui(tg.Md("# Demo: cmd.include()"))
    ui(tg.Md("Click buttons to execute commands **inline** - output appears here:"))
    ui(tg.Md("---"))

    # Button handlers
    def run_fetch():
        ui(tg.Md("**Button clicked:** Executing fetch-data inline..."))
        result = ui.runtime.command("fetch-data").include(source="button-api")
        ui(tg.Md(f"**Returned:** `{result}`"))
        ui(tg.Md(""))

    def run_process():
        ui(tg.Md("**Button clicked:** Executing process-data inline..."))
        result = ui.runtime.command("process-data").include()
        ui(tg.Md(f"**Returned:** `{result}`"))
        ui(tg.Md(""))

    def run_report():
        ui(tg.Md("**Button clicked:** Executing generate-report inline..."))
        result = ui.runtime.command("generate-report").include()
        ui(tg.Md(f"**Returned:** `{result}`"))
        ui(tg.Md(""))

    # Interactive buttons
    ui(tg.Row([
        tg.Button("Fetch Data", on_click=lambda: run_fetch()),
        tg.Button("Process Data", on_click=lambda: run_process()),
        tg.Button("Generate Report", on_click=lambda: run_report()),
    ]))

    ui(tg.Md("---"))
    ui(tg.Md("*Note: include() executes the command inline - output appears in current context.*"))


# ============================================================================
# Demo: cmd.run()
# ============================================================================

@app.command()
def demo_run():
    """Demo: cmd.run() - Execute with chaining to access output/result."""
    ui(tg.Md("# Demo: cmd.run() with Chaining"))
    ui(tg.Md("Click buttons to execute and access output/result via chaining:"))
    ui(tg.Md("---"))

    # Button handlers
    def run_and_show_result():
        ui(tg.Md("**Executing with chaining...**"))
        # Chain to get result directly
        result = ui.runtime.command("fetch-data").run(source="run-api").result
        ui(tg.Md(f"**Result:** `{result}`"))
        ui(tg.Md(""))

    def run_and_show_output():
        ui(tg.Md("**Executing and showing output...**"))
        # Chain to get output
        output = ui.runtime.command("fetch-data").run(source="run-api").out
        ui(tg.Text(f"Captured output: {output}"))
        ui(tg.Md(""))

    # Interactive buttons
    ui(tg.Row([
        tg.Button("Show Result", on_click=lambda: run_and_show_result()),
        tg.Button("Show Output", on_click=lambda: run_and_show_output()),
    ]))

    ui(tg.Md("---"))
    ui(tg.Md("""
**Chaining Pattern:**
```python
# Get result
result = ui.runtime.command("cmd").run(x=10).result

# Get output
output = ui.runtime.command("cmd").run(x=10).out

# Chain in lambda
ui(tg.Button("Get Result",
    on_click=lambda: process(
        ui.runtime.command("cmd").run(x=10).result
    )))
```
    """))


# ============================================================================
# Demo: Retrieve and Append Output
# ============================================================================

@app.command()
def demo_output_retrieval():
    """Demo: Retrieve output from executed command and append here."""
    ui(tg.Md("# Demo: Output Retrieval"))
    ui(tg.Md("Execute a command and retrieve its output/result:"))
    ui(tg.Md("---"))

    def fetch_and_show():
        ui(tg.Md("**Executing fetch-data and retrieving output...**"))
        ui(tg.Md(""))

        # Execute command with run() to capture output
        cmd = ui.runtime.command("fetch-data").run(source="retrieval-test")

        # Show result
        ui(tg.Md("### Retrieved Result:"))
        ui(tg.Text(f"Return value: {cmd.result}"))
        ui(tg.Md(""))

        # Show captured output
        ui(tg.Md("### Captured Output:"))
        ui(tg.Text(cmd.out))
        ui(tg.Md(""))

        # Demonstrate with another command
        ui(tg.Md("### Running generate-report and capturing output:"))
        cmd2 = ui.runtime.command("generate-report").run()
        ui(tg.Md("**Captured Output:**"))
        ui(tg.Text(cmd2.out))
        ui(tg.Md(""))

    ui(tg.Button("Execute & Retrieve", on_click=lambda: fetch_and_show()))

    ui(tg.Md("---"))
    ui(tg.Md("""
**Pattern:**
```python
# Execute and capture
cmd = ui.runtime.command("fetch-data").run(source="api")

# Access return value
result = cmd.result

# Access captured text output
output = cmd.out

# Or chain directly:
output = ui.runtime.command("fetch-data").run(source="api").out
```
    """))


# ============================================================================
# Demo: cmd.select()
# ============================================================================

@app.command()
def demo_select():
    """Demo: cmd.select() - Change selected command (GUI mode)."""
    ui(tg.Md("# Demo: cmd.select()"))
    ui(tg.Md("Click buttons to select different commands (GUI mode only):"))
    ui(tg.Md("---"))

    # Get current command
    current = ui.runtime.command()
    ui(tg.Text(f"Currently executing: {current.name if current else 'None'}"))
    ui(tg.Md(""))

    # Button handlers
    def select_fetch():
        ui(tg.Md("**Selecting fetch-data command...**"))
        ui.runtime.command("fetch-data").select()
        ui(tg.Text("Command form should now show 'fetch-data' (GUI only)"))
        ui(tg.Md(""))

    def select_report():
        ui(tg.Md("**Selecting generate-report command...**"))
        ui.runtime.command("generate-report").select()
        ui(tg.Text("Command form should now show 'generate-report' (GUI only)"))
        ui(tg.Md(""))

    # Interactive links (similar to buttons but styled as links)
    ui(tg.Column([
        tg.Link("→ Select fetch-data", on_click=lambda: select_fetch()),
        tg.Link("→ Select generate-report", on_click=lambda: select_report()),
    ]))

    ui(tg.Md("---"))
    ui(tg.Md("*Note: select() changes the GUI form. In CLI mode, it has no visible effect.*"))


# ============================================================================
# Demo: Current Command
# ============================================================================

@app.command()
def demo_current():
    """Demo: ui.runtime.command() - Get current command info."""
    ui(tg.Md("# Demo: Current Command"))
    ui(tg.Md("Click button to show information about the currently executing command:"))
    ui(tg.Md("---"))

    def show_current():
        current = ui.runtime.command()
        if current:
            ui(tg.Table(
                cols=["Property", "Value"],
                data=[
                    ["Command Name", current.name],
                    ["Has Callback", str(current.command_spec.callback is not None)],
                    ["Help Text", current.command_spec.help_text or "None"],
                ],
                title="Current Command Info"
            ))
        else:
            ui(tg.Text("No command currently executing"))

    ui(tg.Button("Show Current Command", on_click=lambda: show_current()))

    ui(tg.Md("---"))
    ui(tg.Md("*Call ui.runtime.command() with no arguments to get the currently executing command.*"))


# ============================================================================
# Demo: Clipboard Copy with Chaining
# ============================================================================

@app.command()
def demo_clipboard():
    """Demo: Copy command output to clipboard using chaining."""
    ui(tg.Md("# Demo: Clipboard Copy with Chaining"))
    ui(tg.Md("Click buttons to copy command output/results:"))
    ui(tg.Md("---"))

    # Method 1: Copy current command output
    ui(tg.Md("## Method 1: Current Command Output"))
    ui(tg.Button("Copy Current Output",
        on_click=lambda: ui.clipboard(ui.runtime.command().out)))

    ui(tg.Md(""))

    # Method 2: Execute and copy output (chaining)
    ui(tg.Md("## Method 2: Execute & Copy Output (Chaining)"))
    ui(tg.Button("Execute & Copy Output",
        on_click=lambda: ui.clipboard(
            ui.runtime.command("fetch-data").run(source="button-api").out
        )))

    ui(tg.Md(""))

    # Method 3: Execute and copy result
    ui(tg.Md("## Method 3: Execute & Copy Result"))
    ui(tg.Button("Execute & Copy Result",
        on_click=lambda: ui.clipboard(
            str(ui.runtime.command("fetch-data").run(source="api").result)
        )))

    ui(tg.Md(""))

    # Method 4: Include and copy result
    ui(tg.Md("## Method 4: Include & Show Result"))
    def include_and_show():
        cmd = ui.runtime.command("fetch-data").include(source="inline-test")
        ui(tg.Md(f"**Result:** `{cmd.result}`"))
        ui.clipboard(str(cmd.result))

    ui(tg.Button("Include & Copy Result",
        on_click=lambda: include_and_show()))

    ui(tg.Md("---"))
    ui(tg.Md("""
**Chaining Patterns:**
```python
# Pattern 1: Current command output
ui(tg.Button("Copy",
    on_click=lambda: ui.clipboard(ui.runtime.command().out)))

# Pattern 2: Execute and copy output (RECOMMENDED)
ui(tg.Button("Copy",
    on_click=lambda: ui.clipboard(
        ui.runtime.command("cmd").run(x=10).out
    )))

# Pattern 3: Execute and copy result
ui(tg.Button("Copy",
    on_click=lambda: ui.clipboard(
        str(ui.runtime.command("cmd").run(x=10).result)
    )))
```
    """))


# ============================================================================
# Complete Workflow Demo
# ============================================================================

@app.command()
@ui.def_command(is_long=True)
def workflow_with_buttons():
    """Complete workflow controlled by buttons."""
    ui(tg.Md("# Interactive Workflow"))
    ui(tg.Md("Execute a multi-step workflow using buttons:"))
    ui(tg.Md("---"))

    def step1():
        ui(tg.Md("## Step 1: Fetching Data"))
        ui.runtime.command("fetch-data").include(source="workflow")
        ui(tg.Md(""))

    def step2():
        ui(tg.Md("## Step 2: Processing Data"))
        ui.runtime.command("process-data").include()
        ui(tg.Md(""))

    def step3():
        ui(tg.Md("## Step 3: Generating Report"))
        ui.runtime.command("generate-report").include()
        ui(tg.Md(""))

    def run_all():
        ui(tg.Md("# Running Complete Workflow"))
        step1()
        step2()
        step3()
        ui(tg.Md("---"))
        ui(tg.Md("✓ **Workflow completed!**"))

    ui(tg.Row([
        tg.Button("Step 1", on_click=lambda: step1()),
        tg.Button("Step 2", on_click=lambda: step2()),
        tg.Button("Step 3", on_click=lambda: step3()),
    ]))

    ui(tg.Md(""))
    ui(tg.Button("Run All Steps", on_click=lambda: run_all()))


if __name__ == "__main__":
    ui.app()


"""
CLI Examples:
-------------
# Interactive demos (best in GUI mode with buttons)
python examples/04_app_control.py --cli demo-include
python examples/04_app_control.py --cli demo-run
python examples/04_app_control.py --cli demo-output-retrieval
python examples/04_app_control.py --cli demo-select
python examples/04_app_control.py --cli demo-current
python examples/04_app_control.py --cli demo-clipboard
python examples/04_app_control.py --cli workflow-with-buttons

# Base commands
python examples/04_app_control.py --cli fetch-data --source api
python examples/04_app_control.py --cli process-data
python examples/04_app_control.py --cli generate-report
"""
