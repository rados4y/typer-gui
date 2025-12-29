"""Debug script to identify tabs error"""
import sys
import traceback
import typer
import typer_ui as tg

app = typer.Typer()
ui = tg.Ui(app, title='Debug Tabs Error')

@app.command()
@ui.def_command(auto=True, header=False)
def test_tabs():
    """Test tabs with different content types"""

    print("Step 1: Creating simple tab...")
    def simple_tab():
        print("Inside simple_tab callable")
        ui("Simple content from callable")
        print("simple_tab completed")

    print("Step 2: Creating complex tab...")
    def complex_tab():
        print("Inside complex_tab callable")
        ui("### Complex Tab Header")
        ui(tg.Table(cols=["A", "B"], data=[["1", "2"]]))
        ui("More content")
        print("complex_tab completed")

    print("Step 3: Creating Tabs component...")
    tabs = tg.Tabs([
        tg.Tab("Simple", simple_tab),
        tg.Tab("Complex", complex_tab),
        tg.Tab("Static", tg.Text("Static text content")),
    ])

    print("Step 4: Displaying tabs with ui()...")
    ui(tabs)

    print("Step 5: All done!")

if __name__ == "__main__":
    try:
        print("=== STARTING GUI MODE ===")
        ui.app()
    except KeyboardInterrupt:
        print("\n=== INTERRUPTED BY USER ===")
    except Exception as e:
        print("\n=== ERROR OCCURRED ===")
        print(f"Error type: {type(e).__name__}")
        print(f"Error message: {e}")
        print("\n=== FULL TRACEBACK ===")
        traceback.print_exc()
        sys.exit(1)
