"""Example 7: Sub-Applications with Tab Navigation

This example demonstrates:
- Creating sub-applications with typer2ui.Typer2Ui()
- Adding sub-apps with app.add_typer()
- Automatic tab-based GUI layout
- Qualified command names (e.g., "users:create")
- Tab-aware command execution
"""

import typer2ui
from typer2ui import ui

# Main app
app = typer2ui.Typer2Ui(
    title="Business Management System",
    description="Manage users, orders, and view reports",
)

# Sub-applications (each gets its own tab)
users_app = typer2ui.Typer2Ui()
orders_app = typer2ui.Typer2Ui()
reports_app = typer2ui.Typer2Ui()


# ============================================================================
# Main App Commands
# ============================================================================


@app.command()
def create(name: str, email: str = ""):
    """Create a new user."""
    ui("# Create User")
    ui(f"**Name:** {name}")
    if email:
        ui(f"**Email:** {email}")

    ui()
    ui(
        typer2ui.Table(
            cols=["Field", "Value"],
            data=[
                ["Name", name],
                ["Email", email or "(not provided)"],
                ["Status", "Active"],
            ],
            title="New User Details",
        )
    )

    ui()
    ui("✅ User created successfully!")


# ============================================================================
# Users Sub-Application
# ============================================================================


@users_app.command()
def list_users(status: str = "all"):
    """List all users."""
    ui("# User List")
    ui(f"Showing users with status: **{status}**")
    ui()

    users_data = [
        ["Alice Johnson", "alice@example.com", "Active"],
        ["Bob Smith", "bob@example.com", "Active"],
        ["Charlie Brown", "charlie@example.com", "Inactive"],
    ]

    if status != "all":
        users_data = [u for u in users_data if u[2].lower() == status.lower()]

    ui(
        typer2ui.Table(
            cols=["Name", "Email", "Status"],
            data=users_data,
            title=f"Users ({len(users_data)} total)",
        )
    )


@users_app.command()
def update(user_id: int, name: str = "", email: str = ""):
    """Update user information."""
    ui("# Update User")
    ui(f"Updating user ID: **{user_id}**")
    ui()

    changes = []
    if name:
        changes.append(f"- Name updated to: {name}")
    if email:
        changes.append(f"- Email updated to: {email}")

    if changes:
        ui("**Changes:**")
        for change in changes:
            ui(change)
        ui()
        ui("✅ User updated successfully!")
    else:
        ui("⚠️ No changes specified")


@users_app.command()
def delete(user_id: int, confirm: bool = False):
    """Delete a user."""
    ui("# Delete User")

    if not confirm:
        ui("⚠️ **Warning:** This will permanently delete the user!")
        ui()
        ui("Please use `--confirm` flag to proceed with deletion.")
        return

    ui(f"Deleting user ID: **{user_id}**")
    ui()
    ui("✅ User deleted successfully!")


# ============================================================================
# Orders Sub-Application
# ============================================================================


@orders_app.command()
def create_order(product: str, quantity: int = 1):
    """Create a new order."""
    ui("# Create Order")

    price_per_item = 29.99
    total = price_per_item * quantity

    ui(
        typer2ui.Table(
            cols=["Field", "Value"],
            data=[
                ["Product", product],
                ["Quantity", str(quantity)],
                ["Price per item", f"${price_per_item:.2f}"],
                ["Total", f"${total:.2f}"],
            ],
            title="Order Details",
        )
    )

    ui()
    ui("✅ Order created successfully!")


@orders_app.command()
def list_orders(status: str = "all"):
    """List all orders."""
    ui("# Order List")
    ui(f"Showing orders with status: **{status}**")
    ui()

    orders_data = [
        ["1001", "Laptop", "3", "Shipped"],
        ["1002", "Mouse", "10", "Processing"],
        ["1003", "Keyboard", "5", "Delivered"],
        ["1004", "Monitor", "2", "Processing"],
    ]

    if status != "all":
        orders_data = [o for o in orders_data if o[3].lower() == status.lower()]

    ui(
        typer2ui.Table(
            cols=["Order ID", "Product", "Qty", "Status"],
            data=orders_data,
            title=f"Orders ({len(orders_data)} total)",
        )
    )


@orders_app.command()
def update_status(order_id: int, status: str):
    """Update order status."""
    ui("# Update Order Status")
    ui(f"**Order ID:** {order_id}")
    ui(f"**New Status:** {status}")
    ui()
    ui("✅ Order status updated successfully!")


# ============================================================================
# Reports Sub-Application
# ============================================================================


@reports_app.command(view=True)
def sales_report():
    """View sales report dashboard."""
    ui("# Sales Report")
    ui("Monthly sales overview")
    ui()

    ui(
        typer2ui.Table(
            cols=["Month", "Orders", "Revenue"],
            data=[
                ["January", "145", "$12,450"],
                ["February", "163", "$14,200"],
                ["March", "187", "$16,800"],
            ],
            title="Q1 2024 Sales",
        )
    )

    ui()
    ui("**Total Q1 Revenue:** $43,450")
    ui("**Average Order Value:** $87.23")


@reports_app.command(view=True)
def user_stats():
    """View user statistics dashboard."""
    ui("# User Statistics")
    ui()

    ui(
        typer2ui.Row(
            [
                typer2ui.Column(
                    [typer2ui.Text("Total Users"), typer2ui.Text("1,234", size=32, weight="bold")]
                ),
                typer2ui.Column(
                    [typer2ui.Text("Active Users"), typer2ui.Text("987", size=32, weight="bold")]
                ),
                typer2ui.Column(
                    [typer2ui.Text("New This Month"), typer2ui.Text("156", size=32, weight="bold")]
                ),
            ]
        )
    )

    ui()

    ui(
        typer2ui.Table(
            cols=["Status", "Count", "Percentage"],
            data=[
                ["Active", "987", "80%"],
                ["Inactive", "247", "20%"],
            ],
            title="User Status Breakdown",
        )
    )


@reports_app.command()
def generate_report(report_type: str = "summary"):
    """Generate a custom report."""
    ui("# Generate Report")
    ui(f"**Report Type:** {report_type}")
    ui()

    import time

    ui("Generating report...")
    time.sleep(1)

    ui()
    ui("✅ Report generated successfully!")
    ui()
    ui(f"📄 Report saved to: `reports/{report_type}_{int(time.time())}.pdf`")


# ============================================================================
# Add sub-applications to main app using add_typer()
# ============================================================================

app.add_typer(users_app, name="users", help="User management")
app.add_typer(orders_app, name="orders", help="Order management")
app.add_typer(reports_app, name="reports", help="Reports and analytics")


# ============================================================================
# Demonstrate programmatic command control with qualified names
# ============================================================================

# Note: This would be used programmatically, not in the GUI
# Example usage:
# - app.get_command("users:list-users").run(status="active")
# - app.get_command("orders:list-orders").run(status="processing")
# - app.get_command("reports:sales-report").select()  # Switch to that tab and command


if __name__ == "__main__":
    app()


"""
Usage Examples:
---------------

GUI Mode (default):
    python examples/e07_sub_applications.py

    - You'll see tabs for: main | users | orders | reports
    - Click tabs to switch between sub-applications
    - Each tab has its own set of commands
    - Commands are scoped to the current tab

CLI Mode:
    # Main app command
    python examples/e07_sub_applications.py --cli create --name "Alice" --email "alice@example.com"

    # User commands
    python examples/e07_sub_applications.py --cli users list-users
    python examples/e07_sub_applications.py --cli users delete --user-id 5 --confirm

    # Order commands
    python examples/e07_sub_applications.py --cli orders create-order --product "Laptop" --quantity 2
    python examples/e07_sub_applications.py --cli orders list-orders --status processing

    # Report commands
    python examples/e07_sub_applications.py --cli reports sales-report
    python examples/e07_sub_applications.py --cli reports generate-report --report-type detailed

Programmatic Command Control:
    from typer2ui import ui
    import typer2ui

    # In your code, you can programmatically control commands:

    # Execute command with qualified name
    app.get_command("users:list-users").run(status="active")

    # Switch tabs and commands
    app.get_command("orders:list-orders").select()  # Switches to orders tab and selects command
"""
