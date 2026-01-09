"""Table component - Display tabular data."""

from dataclasses import dataclass, field
from typing import Any, Optional, Union, TYPE_CHECKING

from .base import Container, UiBlock

if TYPE_CHECKING:
    import flet as ft
    from .layout import Row


@dataclass
class Table(Container):
    """Display tabular data.

    Supports progressive row addition via context manager.
    """

    cols: list[str]
    data: list[list[Any]] = field(default_factory=list)
    title: Optional[str] = None

    def __post_init__(self):
        """Initialize Container attributes after dataclass init."""
        super().__init__()
        self.flet_control: Optional["ft.DataTable"] = None

    def add_row(self, row: Union[list[Any], "Row"]) -> None:
        """Add a row to the table.

        Args:
            row: List of cell values or Row component
        """
        # Import here to avoid circular dependency
        from .layout import Row

        if isinstance(row, Row):
            row_data = row.children
        else:
            row_data = row

        self.data.append(row_data)

        # New architecture: if ctx and flet_control exist, add row progressively
        if self._ctx and self._flet_control:
            import flet as ft

            # Build cells using ctx.build_child for new architecture
            cells = []
            for cell in row_data:
                if isinstance(cell, UiBlock):
                    cell_control = self._ctx.build_child(self, cell)
                else:
                    cell_control = ft.Text(str(cell))
                cells.append(ft.DataCell(cell_control))

            # Append to existing table
            self._flet_control.rows.append(ft.DataRow(cells=cells))

        self._update()

    def update_cell(self, row_index: int, col_index: int, value: Any) -> None:
        """Update a cell value and trigger display update.

        Args:
            row_index: Row index (0-based)
            col_index: Column index (0-based)
            value: New cell value
        """
        if 0 <= row_index < len(self.data) and 0 <= col_index < len(
            self.data[row_index]
        ):
            self.data[row_index][col_index] = value
            self._update()

    def to_dict(self) -> dict:
        return {
            "type": "table",
            "cols": self.cols,
            "data": self.data,
            "title": self.title,
        }

    def build_cli(self, ctx) -> Any:
        """Build Table for CLI (returns Rich Table).

        Args:
            ctx: CLI runner context

        Returns:
            Rich Table renderable
        """
        from rich.table import Table as RichTable

        table = RichTable(
            show_header=True, header_style="bold magenta", title=self.title
        )

        # Add columns
        for col in self.cols:
            table.add_column(col, style="cyan")

        # Add rows - convert cells to strings
        for row in self.data:
            cells = []
            for cell in row:
                if isinstance(cell, UiBlock):
                    # Use build_cli for UiBlock cells
                    renderable = ctx.build_child(self, cell)
                    # Convert to string for table cell
                    cells.append(str(renderable))
                else:
                    cells.append(str(cell))
            table.add_row(*cells)

        return table

    def build_gui(self, ctx) -> Any:
        """Build Table for GUI (returns Flet DataTable).

        Args:
            ctx: GUI runner context

        Returns:
            Flet DataTable control (or Column if title is present)
        """
        import flet as ft

        columns = [
            ft.DataColumn(ft.Text(header, weight=ft.FontWeight.BOLD))
            for header in self.cols
        ]

        # Build cells - can be UIBlocks or plain values
        def cell_to_control(cell):
            if isinstance(cell, UiBlock):
                return ctx.build_child(self, cell)
            else:
                return ft.Text(str(cell))

        data_rows = [
            ft.DataRow(cells=[ft.DataCell(cell_to_control(cell)) for cell in row])
            for row in self.data
        ]

        self._flet_control = ft.DataTable(
            columns=columns,
            rows=data_rows,
            border=ft.Border.all(1, ft.Colors.GREY_400),
            border_radius=10,
            horizontal_lines=ft.BorderSide(1, ft.Colors.GREY_300),
        )

        if self.title:
            # If there's a title, wrap the table in a Column
            return ft.Column(
                [
                    ft.Text(self.title, size=16, weight=ft.FontWeight.BOLD),
                    self._flet_control,
                ]
            )
        else:
            return self._flet_control
