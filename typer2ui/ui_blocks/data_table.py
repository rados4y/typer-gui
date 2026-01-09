"""DataTable component - Advanced table with pagination and filtering."""

from dataclasses import dataclass
from typing import Any, Optional, TYPE_CHECKING

from .base import Container

if TYPE_CHECKING:
    import flet as ft
    from ..data_source import DataSource


@dataclass
class DataTable(Container):
    """Advanced table with dynamic data loading, pagination, sorting, and filtering.

    Unlike the basic Table component which holds all data in memory, DataTable
    fetches data on-demand from a DataSource, supporting large datasets efficiently.

    Features:
    - Pagination with configurable page size
    - Column sorting (ascending/descending)
    - Full-text filtering/search
    - Displays total count and current page info

    Example:
        class UserDataSource(tu.DataSource):
            def fetch(self, offset, limit, sort_by=None, ascending=True, filter_text=None):
                # Fetch from database/API
                return rows, total_count

        table = tu.DataTable(
            cols=["Name", "Email", "Role"],
            page_size=25,
            title="User Directory"
        )
        table.set_data_source(UserDataSource())
        ui(table)
    """

    cols: list[str]
    page_size: int = 25
    title: Optional[str] = None
    initial_sort_by: Optional[str] = None
    initial_sort_desc: bool = False

    def __post_init__(self):
        """Initialize Container and state variables."""
        super().__init__()

        # Internal state
        self._current_page: int = 0
        self._sort_column: Optional[str] = self.initial_sort_by
        self._sort_ascending: bool = not self.initial_sort_desc
        self._filter_text: str = ""
        self._data_cache: list[list[Any]] = []
        self._total_count: int = 0
        self._data_source: Optional["DataSource"] = None

        # GUI control caching
        self.flet_control: Optional["ft.DataTable"] = None
        self.flet_filter_field: Optional["ft.TextField"] = None
        self.flet_pagination_prev: Optional["ft.IconButton"] = None
        self.flet_pagination_next: Optional["ft.IconButton"] = None
        self.flet_pagination_info: Optional["ft.Text"] = None

    def set_data_source(self, source: "DataSource") -> None:
        """Set the data source and load the first page.

        Args:
            source: DataSource implementation
        """
        self._data_source = source
        self._load_data()

    def _load_data(self) -> None:
        """Fetch data from the data source with current state."""
        if not self._data_source:
            return

        offset = self._current_page * self.page_size

        self._data_cache, self._total_count = self._data_source.fetch(
            offset=offset,
            limit=self.page_size,
            sort_by=self._sort_column,
            ascending=self._sort_ascending,
            filter_text=self._filter_text if self._filter_text else None,
        )

        # Update display if already presented
        self._update()

    def next_page(self) -> None:
        """Navigate to the next page if available."""
        max_page = (
            (self._total_count - 1) // self.page_size if self._total_count > 0 else 0
        )
        if self._current_page < max_page:
            self._current_page += 1
            self._load_data()

    def prev_page(self) -> None:
        """Navigate to the previous page if available."""
        if self._current_page > 0:
            self._current_page -= 1
            self._load_data()

    def sort_by(self, column: str) -> None:
        """Sort by the specified column, toggling direction if already sorted.

        Args:
            column: Column name to sort by
        """
        if self._sort_column == column:
            # Toggle direction
            self._sort_ascending = not self._sort_ascending
        else:
            # New column, default to ascending
            self._sort_column = column
            self._sort_ascending = True

        # Reset to first page when sorting changes
        self._current_page = 0
        self._load_data()

    def set_filter(self, text: str) -> None:
        """Set the filter text and reload from first page.

        Args:
            text: Filter/search text
        """
        self._filter_text = text
        self._current_page = 0  # Reset to first page
        self._load_data()

    def _get_pagination_info(self) -> str:
        """Get pagination info string (e.g., 'showing 1-25 of 247')."""
        if self._total_count == 0:
            return "No records found"

        start = self._current_page * self.page_size + 1
        end = min(start + len(self._data_cache) - 1, self._total_count)
        total_pages = (self._total_count - 1) // self.page_size + 1
        current_page = self._current_page + 1

        return f"Page {current_page} of {total_pages} (showing {start}-{end} of {self._total_count})"

    def to_dict(self) -> dict:
        return {
            "type": "data_table",
            "cols": self.cols,
            "page_size": self.page_size,
            "title": self.title,
            "current_page": self._current_page,
            "sort_column": self._sort_column,
            "sort_ascending": self._sort_ascending,
            "filter_text": self._filter_text,
            "total_count": self._total_count,
            "data": self._data_cache,
        }

    def build_cli(self, ctx) -> Any:
        """Build DataTable for CLI (returns Rich Table with pagination info).

        Args:
            ctx: CLI runner context

        Returns:
            Rich Group with table and pagination info
        """
        from rich.table import Table as RichTable
        from rich.console import Group
        from rich.text import Text as RichText

        # Build table
        table = RichTable(
            show_header=True, header_style="bold magenta", title=self.title
        )

        # Add columns
        for col in self.cols:
            table.add_column(col, style="cyan")

        # Add rows from current page
        for row in self._data_cache:
            cells = [str(cell) for cell in row]
            table.add_row(*cells)

        # Add pagination info
        total_pages = (self._total_count + self.page_size - 1) // self.page_size
        pagination_info = RichText(
            f"Page {self._current_page + 1} of {total_pages} | "
            f"Total: {self._total_count} rows"
        )

        if self._filter_text:
            filter_info = RichText(f"Filter: {self._filter_text}", style="italic")
            return Group(table, pagination_info, filter_info)

        return Group(table, pagination_info)

    def build_gui(self, ctx) -> Any:
        """Build DataTable for GUI (returns Flet Column with table and controls).

        Args:
            ctx: GUI runner context

        Returns:
            Flet Column containing table, filter, and pagination controls
        """
        import flet as ft

        # Create table columns
        columns = [
            ft.DataColumn(ft.Text(col, weight=ft.FontWeight.BOLD)) for col in self.cols
        ]

        # Create data rows
        rows = [
            ft.DataRow(cells=[ft.DataCell(ft.Text(str(cell))) for cell in row])
            for row in self._data_cache
        ]

        # Create table
        data_table = ft.DataTable(
            columns=columns,
            rows=rows,
            border=ft.Border.all(1, ft.Colors.GREY_400),
            border_radius=10,
            horizontal_lines=ft.BorderSide(1, ft.Colors.GREY_300),
        )

        # Store separate reference to the actual DataTable control
        # (Note: _flet_control will be overwritten with the Column by the caller)
        self._data_table_control = data_table

        # Calculate pagination
        total_pages = (self._total_count + self.page_size - 1) // self.page_size

        # Create pagination buttons
        prev_button = ft.IconButton(
            icon=ft.Icons.ARROW_BACK,
            on_click=lambda e: self.prev_page(),
            disabled=(self._current_page == 0),
            tooltip="Previous page",
        )

        next_button = ft.IconButton(
            icon=ft.Icons.ARROW_FORWARD,
            on_click=lambda e: self.next_page(),
            disabled=(self._current_page >= total_pages - 1),
            tooltip="Next page",
        )

        # Store references for updates
        self.flet_pagination_prev = prev_button
        self.flet_pagination_next = next_button
        self.flet_pagination_info = ft.Text(
            f"Page {self._current_page + 1} of {total_pages} | Total: {self._total_count} rows"
        )

        # Create pagination controls
        pagination = ft.Row(
            [
                prev_button,
                self.flet_pagination_info,
                next_button,
            ],
            spacing=10,
            alignment=ft.MainAxisAlignment.CENTER,
        )

        # Build container
        controls = []
        if self.title:
            controls.append(ft.Text(self.title, size=18, weight=ft.FontWeight.BOLD))

        controls.extend(
            [
                data_table,
                pagination,
            ]
        )

        return ft.Column(controls=controls, spacing=10)

    def _update(self) -> None:
        """Update GUI controls when data changes (pagination, sorting, filtering).

        Overrides Container._update() to refresh table rows, pagination info,
        and button states.
        """
        # Only update if in GUI mode and data table control exists
        if not hasattr(self, '_data_table_control') or not self._data_table_control:
            return

        import flet as ft

        # Update table rows
        new_rows = [
            ft.DataRow(cells=[ft.DataCell(ft.Text(str(cell))) for cell in row])
            for row in self._data_cache
        ]
        self._data_table_control.rows = new_rows

        # Update pagination info
        total_pages = (self._total_count + self.page_size - 1) // self.page_size
        if self.flet_pagination_info:
            self.flet_pagination_info.value = (
                f"Page {self._current_page + 1} of {total_pages} | "
                f"Total: {self._total_count} rows"
            )

        # Update button states
        if self.flet_pagination_prev:
            self.flet_pagination_prev.disabled = (self._current_page == 0)

        if self.flet_pagination_next:
            self.flet_pagination_next.disabled = (self._current_page >= total_pages - 1)

        # Trigger thread-safe page update for Flet 0.80+
        if self._ctx:
            if hasattr(self._ctx, 'runner') and self._ctx.runner:
                self._ctx.runner._safe_page_update()
            elif hasattr(self._ctx, 'page') and self._ctx.page:
                self._ctx.page.update()
