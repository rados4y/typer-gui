"""Example 5: State Management"""

from dataclasses import dataclass
import typer
import typer_ui as tg

app = typer.Typer()
ui = tg.Ui(
    app,
    title="State Management Demo",
    description="Demonstrates reactive UI based on application state.",
)


@dataclass
class Order:
    id: int
    item: str
    quantity: int
    total: float


@app.command()
def state_demo():
    """Demonstrates reactive UI components tied to state."""
    counter = ui.state(0)
    # --- Counter Example ---
    ui(tg.Md("## 🔢 Counter"))
    ui(lambda: tg.Md(f"### **Current Count:** {counter.value}"), counter)

    ui(
        tg.Row(
            [
                tg.Button(
                    "Increment +", on_click=lambda: counter.set(counter.value + 1)
                ),
                tg.Button(
                    "Decrement -", on_click=lambda: counter.set(counter.value - 1)
                ),
                tg.Button("Reset", on_click=lambda: counter.set(0)),
            ]
        )
    )


@app.command()
def orders_demo():
    """Demonstrates a master-detail view using state."""

    # A plain list for our data, not a state object
    orders_data = [
        Order(id=1, item="Laptop", quantity=1, total=1200.50),
        Order(id=2, item="Mouse", quantity=2, total=55.00),
        Order(id=3, item="Keyboard", quantity=1, total=75.99),
    ]

    # The ID of the currently selected order is the only state we need
    selected_order_id = ui.state(None)

    # --- Display List of Orders ---
    ui(tg.Md("## 📦 Orders"))

    # The table of orders. We add a "Select" link to each row.
    table_data = [
        [
            order.id,
            order.item,
            order.quantity,
            f"${order.total:.2f}",
            # This Link modifies the `selected_order_id` state on click
            tg.Link("Select", on_click=lambda o=order: selected_order_id.set(o[0])),
        ]
        for order in orders_data
    ]
    ui(tg.Table(cols=["ID", "Item", "Quantity", "Total", "Action"], data=table_data))

    ui(tg.Md("---"))

    # --- Display Details of Selected Order ---
    ui(tg.Md("## ℹ️ Order Details"))

    # This is a reactive component that depends on `selected_order_id`.
    # When `selected_order_id` changes, this lambda is re-run.
    def render_order_details():
        order_id = selected_order_id.value
        if order_id is None:
            return tg.Text("Select an order from the list above to see its details.")

        # Find the selected order from the plain data list
        order = next((o for o in orders_data if o.id == order_id), None)

        if order is None:
            return tg.Text(f"Error: Order with ID {order_id} not found.")

        # Return a Markdown component with the order details
        return tg.Md(
            f"""
- **Order ID:** `{order.id}`
- **Item:** {order.item}
- **Quantity:** {order.quantity}
- **Total:** ${order.total:.2f}
        """
        )

    # The ui() call registers the dependency on the `selected_order_id` state
    ui(render_order_details, selected_order_id)


if __name__ == "__main__":
    ui.app()
