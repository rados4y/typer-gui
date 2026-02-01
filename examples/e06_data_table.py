"""Example 06: DataTable with Dynamic Data Loading

This example demonstrates the DataTable component with:
- Mock data source with 100+ records
- Pagination (configurable page size)
- Sorting (by any column)
- Full-text filtering (search across all columns)

Run in CLI mode: python examples/e06_data_table.py --cli browse-users
Run in GUI mode: python examples/e06_data_table.py
"""

import typer2ui as tu
from typer2ui import ui
from typing import List, Tuple, Optional, Any

# Create UiApp wrapper
upp = tu.UiApp(
    title="DataTable Demo",
    description="Demonstrates dynamic data loading with pagination, sorting, and filtering",
)


# ============================================================================
# Mock Data Source Implementation
# ============================================================================


class UserDataSource(tu.DataSource):
    """Mock data source with in-memory user data.

    Demonstrates how to implement the DataSource interface with:
    - Full-text filtering across all columns
    - Multi-column sorting
    - Pagination support
    """

    def __init__(self):
        """Initialize with mock user data."""
        # Generate 100 mock users
        self.users = self._generate_mock_users(100)

    def _generate_mock_users(self, count: int) -> List[List[Any]]:
        """Generate mock user data.

        Args:
            count: Number of users to generate

        Returns:
            List of user rows [name, email, role, status]
        """
        first_names = [
            "Alice",
            "Bob",
            "Charlie",
            "Diana",
            "Eve",
            "Frank",
            "Grace",
            "Henry",
            "Iris",
            "Jack",
            "Kate",
            "Leo",
            "Mia",
            "Noah",
            "Olivia",
            "Peter",
            "Quinn",
            "Rose",
            "Sam",
            "Tara",
        ]
        last_names = [
            "Smith",
            "Johnson",
            "Williams",
            "Brown",
            "Jones",
            "Garcia",
            "Miller",
            "Davis",
            "Rodriguez",
            "Martinez",
        ]
        roles = ["Admin", "User", "Manager", "Developer", "Designer"]
        statuses = ["Active", "Inactive", "Pending"]

        users = []
        for i in range(count):
            first_name = first_names[i % len(first_names)]
            last_name = last_names[i % len(last_names)]
            name = f"{first_name} {last_name} {i + 1}"
            email = f"{first_name.lower()}.{last_name.lower()}{i + 1}@example.com"
            role = roles[i % len(roles)]
            status = statuses[i % len(statuses)]
            users.append([name, email, role, status])

        return users

    def fetch(
        self,
        offset: int,
        limit: int,
        sort_by: Optional[str] = None,
        ascending: bool = True,
        filter_text: Optional[str] = None,
    ) -> Tuple[List[List[Any]], int]:
        """Fetch paginated, sorted, and filtered user data.

        Args:
            offset: Number of rows to skip
            limit: Maximum rows to return
            sort_by: Column name to sort by (Name, Email, Role, Status)
            ascending: Sort direction
            filter_text: Search text (searches across all columns)

        Returns:
            Tuple of (rows, total_count)
        """
        # Start with all data
        data = list(self.users)

        # Apply filter
        if filter_text:
            filter_lower = filter_text.lower()
            data = [
                row
                for row in data
                if any(filter_lower in str(cell).lower() for cell in row)
            ]

        # Apply sorting
        if sort_by:
            column_index = {
                "Name": 0,
                "Email": 1,
                "Role": 2,
                "Status": 3,
            }.get(sort_by)

            if column_index is not None:
                data.sort(key=lambda x: str(x[column_index]), reverse=not ascending)

        # Get total count (after filtering, before pagination)
        total = len(data)

        # Apply pagination
        page_data = data[offset : offset + limit]

        return page_data, total


# ============================================================================
# Commands
# ============================================================================


@upp.command(button=True, view=True)
def browse_users():
    """Browse users with pagination, sorting, and filtering.

    - Click column headers to sort (GUI mode)
    - Use search field to filter (GUI mode)
    - Navigate pages with prev/next buttons
    """
    ui("# User Directory")
    ui("Browse and search through the user database.")
    ui("")

    # Create DataTable
    table = tu.DataTable(
        cols=["Name", "Email", "Role", "Status"],
        page_size=10,
        title="Users",
        initial_sort_by="Name",
    )

    # Set data source
    table.set_data_source(UserDataSource())

    # Display table
    ui(table)


@upp.command(button=True, view=True)
def large_dataset():
    """Browse a larger dataset (500 records) with smaller page size.

    Demonstrates DataTable performance with larger datasets.
    """
    ui("# Large Dataset Demo")
    ui("Browse through 500 user records with pagination.")
    ui("")

    # Create custom data source with more records
    class LargeUserDataSource(UserDataSource):
        def __init__(self):
            self.users = self._generate_mock_users(500)

    table = tu.DataTable(
        cols=["Name", "Email", "Role", "Status"],
        page_size=25,
        title="Large User Database (500 records)",
    )

    table.set_data_source(LargeUserDataSource())
    ui(table)


@upp.command(button=True, view=True)
def admin_only():
    """View only admin users (pre-filtered data source).

    Demonstrates how to create a filtered data source.
    """
    ui("# Admin Users Only")
    ui("")

    class AdminDataSource(UserDataSource):
        """Data source that only shows admin users."""

        def fetch(
            self,
            offset: int,
            limit: int,
            sort_by: Optional[str] = None,
            ascending: bool = True,
            filter_text: Optional[str] = None,
        ) -> Tuple[List[List[Any]], int]:
            # Pre-filter to admins only
            admin_users = [row for row in self.users if row[2] == "Admin"]
            self.users = admin_users

            # Apply normal fetch logic
            return super().fetch(offset, limit, sort_by, ascending, filter_text)

    table = tu.DataTable(
        cols=["Name", "Email", "Role", "Status"],
        page_size=10,
        title="Admin Users",
    )

    table.set_data_source(AdminDataSource())
    ui(table)


# ============================================================================
# App Entry Point
# ============================================================================

if __name__ == "__main__":
    upp()
