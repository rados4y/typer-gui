"""Example 5: State Management"""

from dataclasses import dataclass
import typer
import typer_ui as tu
from typer_ui import ui, text, dx

typer_app = typer.Typer()
app = tu.UiApp(
    typer_app,
    title="State Management Demo",
    description="Demonstrates reactive UI based on application state.",
)


@dataclass
class Order:
    id: int
    item: str
    quantity: int
    total: float


@typer_app.command()
@app.def_command(auto=True, header=False)
def state_demo():
    """Demonstrates reactive UI components tied to state."""
    counter = app.state(0)
    # --- Counter Example ---
    ui("## 🔢 Counter")
    # Reactive shortcut: lambda returns string → auto-converted to Markdown
    ui(dx(lambda: f"### **Current Count:** {counter.value}", counter))

    ui(
        tu.Row(
            [
                tu.Button(
                    "Increment +", on_click=lambda: counter.set(counter.value + 1)
                ),
                tu.Button(
                    "Decrement -", on_click=lambda: counter.set(counter.value - 1)
                ),
                tu.Button("Reset", on_click=lambda: counter.set(0)),
            ]
        )
    )


@typer_app.command()
@app.def_command(auto=True, header=False)
def orders_demo():
    """Demonstrates a master-detail view using state."""

    # A plain list for our data, not a state object
    orders_data = [
        Order(id=1, item="Laptop", quantity=1, total=1200.50),
        Order(id=2, item="Mouse", quantity=2, total=55.00),
        Order(id=3, item="Keyboard", quantity=1, total=75.99),
    ]

    # The ID of the currently selected order is the only state we need
    selected_order_id = app.state(None)

    # --- Display List of Orders ---
    ui("## 📦 Orders")

    # The table of orders. We add a "Select" link to each row.
    table_data = [
        [
            order.id,
            order.item,
            order.quantity,
            f"${order.total:.2f}",
            # This Link modifies the `selected_order_id` state on click
            tu.Link("Select", on_click=lambda o=order: selected_order_id.set(o)),
        ]
        for order in orders_data
    ]
    ui(tu.Table(cols=["ID", "Item", "Quantity", "Total", "Action"], data=table_data))
    ui()  # Empty line shortcut
    ui("---")

    # --- Display Details of Selected Order ---
    ui("## ℹ️ Order Details")

    # Reactive renderer that calls ui() internally with shortcuts
    # When `selected_order_id` changes, this function is re-executed.
    def render_order_details():
        order = selected_order_id.value
        if order is None:
            # Shortcut: ui(str) renders as Markdown
            ui("Select an order from the list above to see its details.")
            return

        # Shortcut: ui(str) renders markdown
        ui(
            f"""
- **Order ID:** `{order.id}`
- **Item:** {order.item}
- **Quantity:** {order.quantity}
- **Total:** ${order.total:.2f}
        """
        )

    # The dx() call wraps the renderer and dependencies, ui() displays it
    ui(dx(render_order_details, selected_order_id))


if __name__ == "__main__":
    app()
