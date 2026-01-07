"""UI Blocks - Simple components with per-channel presentation."""

from abc import ABC, abstractmethod
from typing import Any, Optional, Callable, Union, TYPE_CHECKING
from dataclasses import dataclass, field
import re

if TYPE_CHECKING:
    import flet as ft
    from .data_source import DataSource

# Global reference to current runner (set by runner during command execution)
_current_runner = None


def get_current_runner() -> Optional[Any]:
    """Get the current active runner."""
    return _current_runner


def set_current_runner(runner: Optional[Any]) -> None:
    """Set the current active runner."""
    global _current_runner
    _current_runner = runner


def to_component(value: Any) -> 'UiBlock':
    """Convert a value to a UiBlock component.

    Handles automatic conversion:
    - None → Text("") (empty line)
    - str → Md(str) (markdown)
    - UiBlock → unchanged
    - any other object → Text(str(obj))

    Args:
        value: Value to convert

    Returns:
        UiBlock component
    """
    # Already a component - return as-is
    if isinstance(value, UiBlock):
        return value

    # None → empty line
    if value is None:
        return Text("")

    # String → Markdown
    if isinstance(value, str):
        return Md(value)

    # Anything else → convert to string
    return Text(str(value))


class UiBlock(ABC):
    """Base class for all UI components.

    Each component contains all presentation logic for every channel in a single class.
    """

    def __init__(self):
        """Initialize the UI block with hierarchy support."""
        # Parent-child hierarchy (for new architecture)
        self._parent: Optional["UiBlock"] = None
        self._children: list["UiBlock"] = []

        # Context and control references (for new architecture)
        self._ctx: Optional[Any] = None  # UIRunnerCtx instance
        self._flet_control: Optional[Any] = None  # ft.Control for GUI

    @abstractmethod
    def build_cli(self, ctx) -> Any:
        """Build component for CLI (returns Rich renderable).

        Args:
            ctx: CLI runner context
        """
        pass

    @abstractmethod
    def build_gui(self, ctx) -> Any:
        """Build component for GUI (returns Flet control).

        Args:
            ctx: GUI runner context
        """
        pass

    def show_rest(self, runner) -> None:
        """Render the component for REST API output.

        Args:
            runner: RESTRunner instance
        """
        runner.add_element(self.to_dict())

    def to_dict(self) -> dict:
        """Serialize component to dict for REST API."""
        return {"type": self.__class__.__name__.lower()}

    def to_text(self) -> str:
        """Convert component to plain text representation.

        This method reuses the component's show_cli() logic by capturing
        its stdout output. Components can override this for better performance
        or different text representation.

        Returns:
            Plain text representation of the component
        """
        import io
        from contextlib import redirect_stdout
        from rich.console import Console

        buffer = io.StringIO()
        console = Console(file=buffer, force_terminal=False)

        # Use CLIRunnerCtx to build the component
        from .runners.cli_context import CLIRunnerCtx

        ctx = CLIRunnerCtx()
        ctx.console = console

        # Build and render
        renderable = self.build_cli(ctx)
        console.print(renderable)

        return buffer.getvalue().rstrip("\n")

    def is_gui_only(self) -> bool:
        """Whether this component should only appear in GUI mode."""
        return False

    # Hierarchy management methods (for new architecture)
    @property
    def parent(self) -> Optional["UiBlock"]:
        """Get parent component."""
        return self._parent

    @property
    def children(self) -> list["UiBlock"]:
        """Get child components."""
        return self._children

    @children.setter
    def children(self, value: list["UiBlock"]) -> None:
        """Set child components."""
        self._children = value

    def add_child(self, child: "UiBlock") -> None:
        """Add child and establish parent-child relationship.

        Args:
            child: The child component to add
        """
        child._parent = self
        if child not in self._children:
            self._children.append(child)

    def get_root(self) -> "UiBlock":
        """Get root component by walking up the hierarchy.

        Returns:
            The root component (has no parent)
        """
        current = self
        while current._parent:
            current = current._parent
        return current


class Container(UiBlock, ABC):
    """Base class for components that can contain children.

    Supports context manager pattern for progressive rendering.
    Also supports auto-update when presented via ui(component).
    """

    def __init__(self):
        # Initialize parent class
        super().__init__()

        # Only initialize children if not already set by dataclass
        if not hasattr(self, "children"):
            self.children: list[UiBlock] = []
        self._context_active = False
        self._runner = None
        self._presentation_runner = None
        self._presented = False

    def _mark_presented(self, runner) -> None:
        """Mark this container as presented for auto-updates.

        Called by ui() when component is first displayed.

        Args:
            runner: The runner that presented this component
        """
        self._presented = True
        self._presentation_runner = runner

    def __enter__(self) -> 'Container':
        """Enter context manager - start progressive rendering."""
        self._context_active = True
        self._runner = get_current_runner()

        # Mark as presented for update tracking
        # Note: The container is already in the ui_stack via ui() call
        # It will be built and displayed when stack is processed
        if not self._presented and self._runner:
            self._mark_presented(self._runner)

        return self

    def __exit__(self, exc_type: Optional[type], exc_val: Optional[BaseException], exc_tb: Optional[Any]) -> bool:
        """Exit context manager - finalize rendering."""
        self._context_active = False
        self._runner = None
        return False

    def _update(self) -> None:
        """Update display if presented or in context manager.

        In the new architecture, components update by calling page.update()
        on their context's page. The Flet control is already in the page,
        so we just need to refresh it.
        """
        # New architecture: use _ctx if available
        if self._ctx and hasattr(self._ctx, "page"):
            # Component's Flet control is already in the page
            # Use runner's thread-safe update for Flet 0.80+
            if hasattr(self._ctx, "runner") and self._ctx.runner:
                self._ctx.runner._safe_page_update()
            elif self._ctx.page:
                # Fallback to direct update if runner not available
                self._ctx.page.update()


# ============================================================================
# Simple Components
# ============================================================================


@dataclass
class Text(UiBlock):
    """Display plain text."""

    content: str

    def __post_init__(self):
        """Initialize parent class after dataclass fields."""
        UiBlock.__init__(self)

    def to_dict(self) -> dict:
        return {"type": "text", "content": self.content}

    def build_cli(self, ctx) -> Any:
        """Build Text for CLI (returns Rich Text).

        Args:
            ctx: CLI runner context

        Returns:
            Rich Text renderable
        """
        from rich.text import Text as RichText

        return RichText(self.content)

    def build_gui(self, ctx) -> Any:
        """Build Text for GUI (returns Flet Text).

        Args:
            ctx: GUI runner context

        Returns:
            Flet Text control
        """
        import flet as ft

        return ft.Text(self.content, selectable=True)


@dataclass
class Md(UiBlock):
    """Display Markdown content."""

    content: str

    def __post_init__(self):
        """Initialize parent class after dataclass fields."""
        UiBlock.__init__(self)

    def to_dict(self) -> dict:
        return {"type": "markdown", "content": self.content}

    def build_cli(self, ctx) -> Any:
        """Build Markdown for CLI (returns Rich Markdown).

        Args:
            ctx: CLI runner context

        Returns:
            Rich Markdown renderable
        """
        from rich.markdown import Markdown

        return Markdown(self.content)

    def build_gui(self, ctx) -> Any:
        """Build Markdown for GUI (returns Flet Markdown).

        Args:
            ctx: GUI runner context

        Returns:
            Flet Markdown control
        """
        import flet as ft

        return ft.Markdown(
            self.content,
            selectable=True,
            extension_set=ft.MarkdownExtensionSet.GITHUB_WEB,
            on_tap_link=lambda e: print(f"Link tapped: {e.data}"),
        )


# ============================================================================
# Data Display Components
# ============================================================================


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


# ============================================================================
# Layout Components
# ============================================================================


@dataclass
class Row(Container):
    """Display components horizontally."""

    children: list[Any] = field(default_factory=list)

    def __post_init__(self):
        """Initialize Container attributes after dataclass init."""
        # Store the children list from dataclass field before calling super().__init__()
        # because dataclass sets self.children directly, bypassing the property setter
        children_from_dataclass = self.children if hasattr(self, "children") else []

        # Only call super().__init__() if not already initialized
        if not hasattr(self, "_context_active"):
            super().__init__()

        # Now set children properly through the property setter
        # This ensures self._children gets populated
        if children_from_dataclass:
            self.children = children_from_dataclass

    def add(self, child: UiBlock) -> None:
        """Add a child component to the row."""
        self.children.append(child)
        self._update()

    def to_dict(self) -> dict:
        return {
            "type": "row",
            "children": [
                child.to_dict() if isinstance(child, UiBlock) else str(child)
                for child in self.children
            ],
        }

    def build_cli(self, ctx) -> Any:
        """Build Row for CLI (returns Rich Group - vertical in CLI).

        Args:
            ctx: CLI runner context

        Returns:
            Rich Group renderable
        """
        from rich.console import Group

        # CLI shows children vertically (no horizontal layout in terminal)
        renderables = []
        for child in self.children:
            if isinstance(child, UiBlock) and not child.is_gui_only():
                renderable = ctx.build_child(self, child)
                renderables.append(renderable)
            elif not isinstance(child, UiBlock):
                from rich.text import Text as RichText

                renderables.append(RichText(str(child)))

        return Group(*renderables) if renderables else ""

    def build_gui(self, ctx) -> Any:
        """Build Row for GUI (returns Flet Row).

        Args:
            ctx: GUI runner context

        Returns:
            Flet Row control
        """
        import flet as ft

        controls = [ctx.build_child(self, child) for child in self.children]
        return ft.Row(controls=controls, spacing=10, wrap=True)


@dataclass
class Column(Container):
    """Display components vertically."""

    children: list[UiBlock] = field(default_factory=list)

    def __post_init__(self):
        """Initialize Container attributes after dataclass init."""
        # Store the children list from dataclass field before calling super().__init__()
        # because dataclass sets self.children directly, bypassing the property setter
        children_from_dataclass = self.children if hasattr(self, "children") else []

        # Only call super().__init__() if not already initialized
        if not hasattr(self, "_context_active"):
            super().__init__()

        # Now set children properly through the property setter
        # This ensures self._children gets populated
        if children_from_dataclass:
            self.children = children_from_dataclass

    def add(self, child: UiBlock) -> None:
        """Add a child component to the column."""
        self.children.append(child)
        self._update()

    def to_dict(self) -> dict:
        return {
            "type": "column",
            "children": [child.to_dict() for child in self.children],
        }

    def build_cli(self, ctx) -> Any:
        """Build Column for CLI (returns Rich Group - vertical layout).

        Args:
            ctx: CLI runner context

        Returns:
            Rich Group renderable
        """
        from rich.console import Group

        renderables = [ctx.build_child(self, child) for child in self.children]
        return Group(*renderables) if renderables else ""

    def build_gui(self, ctx) -> Any:
        """Build Column for GUI (returns Flet Column).

        Args:
            ctx: GUI runner context

        Returns:
            Flet Column control
        """
        import flet as ft

        controls = [ctx.build_child(self, child) for child in self.children]
        return ft.Column(controls=controls, spacing=10)


# ============================================================================
# Interactive Components
# ============================================================================


@dataclass
class Button(UiBlock):
    """Interactive button that executes an action (GUI only)."""

    text: str
    on_click: Callable
    icon: Optional[str] = None

    def __post_init__(self):
        """Initialize parent class after dataclass fields."""
        UiBlock.__init__(self)

    def is_gui_only(self) -> bool:
        return True

    def to_dict(self) -> dict:
        return {
            "type": "button",
            "text": self.text,
            "icon": self.icon,
            "action_id": id(self.on_click),  # Can't serialize callback
        }

    def build_cli(self, ctx) -> Any:
        """Build Button for CLI (returns empty string - GUI only).

        Args:
            ctx: CLI runner context

        Returns:
            Empty string (buttons don't render in CLI)
        """
        return ""

    def build_gui(self, ctx) -> Any:
        """Build Button for GUI (returns Flet ElevatedButton).

        Args:
            ctx: GUI runner context

        Returns:
            Flet ElevatedButton control
        """
        import flet as ft

        icon_obj = None
        if self.icon:
            icon_obj = getattr(ft.Icons, self.icon.upper(), None)

        def handle_click(e):
            # Set runner context for callback execution
            saved_runner = get_current_runner()
            # Try to get runner from ctx if available
            runner = getattr(ctx, "runner", None)
            if runner:
                set_current_runner(runner)
            try:
                self.on_click()
            finally:
                set_current_runner(saved_runner)

        return ft.ElevatedButton(
            self.text,
            icon=icon_obj,
            on_click=handle_click,
        )


@dataclass
class Link(UiBlock):
    """Interactive link that executes an action (GUI only)."""

    text: str
    on_click: Callable

    def __post_init__(self):
        """Initialize parent class after dataclass fields."""
        UiBlock.__init__(self)

    def is_gui_only(self) -> bool:
        return True

    def to_dict(self) -> dict:
        return {
            "type": "link",
            "text": self.text,
            "action_id": id(self.on_click),
        }

    def build_cli(self, ctx) -> Any:
        """Build Link for CLI (returns empty string - GUI only).

        Args:
            ctx: CLI runner context

        Returns:
            Empty string (links don't render in CLI)
        """
        return ""

    def build_gui(self, ctx) -> Any:
        """Build Link for GUI (returns Flet TextButton).

        Args:
            ctx: GUI runner context

        Returns:
            Flet TextButton control
        """
        import flet as ft

        def handle_click(e):
            # Set runner context for callback execution
            saved_runner = get_current_runner()
            runner = getattr(ctx, "runner", None)
            if runner:
                set_current_runner(runner)
            try:
                self.on_click()
            finally:
                set_current_runner(saved_runner)

        return ft.TextButton(
            self.text,
            icon=ft.Icons.LINK,
            on_click=handle_click,
        )


@dataclass
class TextInput(UiBlock):
    """Text input field."""

    label: str
    value: str = ""
    on_change: Optional[Callable[[str], None]] = None

    def __post_init__(self):
        """Initialize parent class after dataclass fields."""
        UiBlock.__init__(self)

    def to_dict(self) -> dict:
        return {
            "type": "text_input",
            "label": self.label,
            "value": self.value,
        }

    def build_cli(self, ctx) -> Any:
        """Build TextInput for CLI (returns Rich Text - prompts for input).

        Args:
            ctx: CLI runner context

        Returns:
            Rich Text renderable with input result
        """
        from rich.text import Text as RichText

        # Note: In CLI mode, this would typically use input() during show_cli
        # For build_cli, we just return the current state
        return RichText(f"{self.label}: {self.value}")

    def build_gui(self, ctx) -> Any:
        """Build TextInput for GUI (returns Flet TextField).

        Args:
            ctx: GUI runner context

        Returns:
            Flet TextField control
        """
        import flet as ft

        def handle_change(e):
            self.value = e.control.value
            if self.on_change:
                # Set runner context for callback execution
                saved_runner = get_current_runner()
                runner = getattr(ctx, "runner", None)
                if runner:
                    set_current_runner(runner)
                try:
                    self.on_change(e.control.value)
                finally:
                    set_current_runner(saved_runner)

        return ft.TextField(
            label=self.label,
            value=self.value,
            on_change=handle_change,
        )


# ============================================================================
# Tabs Components
# ============================================================================


@dataclass
class Tab:
    """A single tab with label and content.

    Args:
        label: Tab label/title
        content: Either a UiBlock component, a callable that builds content using ui(), or a string (converted to markdown)
    """

    label: str
    content: Union[UiBlock, Callable, str, Any]

    def __post_init__(self):
        """Validate and convert tab content."""
        if not callable(self.content):
            # Convert non-callable content to a UiBlock component
            # This handles strings (→ Md), None (→ Text("")), and other values
            if not isinstance(self.content, UiBlock):
                self.content = to_component(self.content)


@dataclass
class Tabs(UiBlock):
    """Tabbed interface container.

    Args:
        tabs: List of Tab objects
    """

    tabs: list[Tab]

    def __post_init__(self):
        """Validate tabs configuration."""
        UiBlock.__init__(self)
        if not self.tabs:
            raise ValueError("Tabs must contain at least one tab")
        if not all(isinstance(tab, Tab) for tab in self.tabs):
            raise ValueError("All items must be Tab objects")

    def to_dict(self) -> dict:
        return {
            "type": "tabs",
            "tabs": [
                {
                    "label": tab.label,
                    "content": (
                        tab.content.to_dict()
                        if isinstance(tab.content, UiBlock)
                        else "<callable>"
                    ),
                }
                for tab in self.tabs
            ],
        }

    def build_cli(self, ctx) -> Any:
        """Build Tabs for CLI (returns Rich Group - sequential rendering).

        Args:
            ctx: CLI runner context

        Returns:
            Rich Group renderable
        """
        from rich.console import Group
        from rich.text import Text as RichText
        from rich.rule import Rule

        renderables = []
        for i, tab in enumerate(self.tabs):
            # Add spacing between tabs
            if i > 0:
                renderables.append(RichText(""))

            # Tab header
            renderables.append(Rule(tab.label))

            # Tab content - use ctx.build_child to handle all content types
            content = ctx.build_child(self, tab.content)
            renderables.append(content)

        return Group(*renderables)

    def build_gui(self, ctx) -> Any:
        """Build Tabs for GUI (returns Flet Tabs with TabBar + TabBarView).

        Args:
            ctx: GUI runner context

        Returns:
            Flet Tabs control containing TabBar and TabBarView
        """
        import flet as ft

        # Create tab labels (for TabBar)
        tab_controls = [ft.Tab(tab.label) for tab in self.tabs]

        # Create tab content (for TabBarView)
        content_controls = []
        for tab in self.tabs:
            # Use ctx.build_child to handle all content types (string/callable/UIBlock)
            tab_content = ctx.build_child(self, tab.content)

            # Wrap in Container for padding
            wrapped_content = ft.Container(
                content=tab_content,
                padding=10,
            )
            content_controls.append(wrapped_content)

        # Create TabBar and TabBarView (Flet 0.80+ API)
        tab_bar = ft.TabBar(tabs=tab_controls)
        tab_view = ft.TabBarView(
            controls=content_controls,
            expand=True,  # Required: TabBarView needs bounded height
        )

        # Wrap in Tabs control (required coordinator in Flet 0.80+)
        return ft.Tabs(
            content=ft.Column(
                controls=[tab_bar, tab_view],
                spacing=0,
            ),
            length=len(self.tabs),
        )


# ============================================================================
# DataTable Component
# ============================================================================


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
