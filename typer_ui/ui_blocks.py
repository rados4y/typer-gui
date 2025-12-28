"""UI Blocks - Simple components with per-channel presentation."""

from abc import ABC, abstractmethod
from typing import Any, Optional, List, Callable, Union, TYPE_CHECKING
from dataclasses import dataclass, field
import re

if TYPE_CHECKING:
    import flet as ft

# Global reference to current runner (set by runner during command execution)
_current_runner = None


def get_current_runner():
    """Get the current active runner."""
    return _current_runner


def set_current_runner(runner):
    """Set the current active runner."""
    global _current_runner
    _current_runner = runner


class UiBlock(ABC):
    """Base class for all UI components.

    Each component contains all presentation logic for every channel in a single class.
    """

    @abstractmethod
    def show_cli(self, runner) -> None:
        """Render the component for CLI output.

        Args:
            runner: CLIRunner instance with helper methods
        """
        pass

    @abstractmethod
    def show_gui(self, runner) -> None:
        """Render the component for GUI output.

        Args:
            runner: GUIRunner instance with Flet page and output view
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

        buffer = io.StringIO()
        with redirect_stdout(buffer):
            # Create a minimal mock runner just for text conversion
            # We can't import CLIRunner here due to circular dependency,
            # so we use a simple object with the required interface
            class MockRunner:
                channel = "cli"

            mock_runner = MockRunner()
            self.show_cli(mock_runner)

        return buffer.getvalue().rstrip('\n')

    def is_gui_only(self) -> bool:
        """Whether this component should only appear in GUI mode."""
        return False


class Container(UiBlock, ABC):
    """Base class for components that can contain children.

    Supports context manager pattern for progressive rendering.
    Also supports auto-update when presented via ui(component).
    """

    def __init__(self):
        # Only initialize children if not already set by dataclass
        if not hasattr(self, 'children'):
            self.children: List[UiBlock] = []
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

    def __enter__(self):
        """Enter context manager - start progressive rendering."""
        self._context_active = True
        self._runner = get_current_runner()

        # If not already presented, show initial state
        if not self._presented and self._runner:
            self._runner.show(self)

        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        """Exit context manager - finalize rendering."""
        self._context_active = False
        self._runner = None
        return False

    def _update(self) -> None:
        """Update display if presented or in context manager.

        Checks in priority order:
        1. Context manager runner (if active)
        2. Presentation runner (if component was presented via ui())
        """
        runner = None

        # Context manager takes priority
        if self._context_active and self._runner:
            runner = self._runner
        # Fallback to presentation runner
        elif self._presented and self._presentation_runner:
            runner = self._presentation_runner

        if runner:
            runner.update(self)


# ============================================================================
# Simple Components
# ============================================================================

@dataclass
class Text(UiBlock):
    """Display plain text."""

    content: str

    def show_cli(self, runner) -> None:
        print(self.content)

    def show_gui(self, runner) -> None:
        import flet as ft
        runner.add_to_output(ft.Text(self.content, selectable=True), component=self)

    def to_dict(self) -> dict:
        return {"type": "text", "content": self.content}


@dataclass
class Md(UiBlock):
    """Display Markdown content."""

    content: str

    def show_cli(self, runner) -> None:
        # Strip markdown formatting for CLI
        text = self.content
        text = re.sub(r'\*\*([^*]+)\*\*', r'\1', text)
        text = re.sub(r'\*([^*]+)\*', r'\1', text)
        text = re.sub(r'__([^_]+)__', r'\1', text)
        text = re.sub(r'_([^_]+)_', r'\1', text)
        text = re.sub(r'`([^`]+)`', r'\1', text)
        text = re.sub(r'^#+\s+(.+)$', lambda m: m.group(1).upper(), text, flags=re.MULTILINE)
        print(text)

    def show_gui(self, runner) -> None:
        import flet as ft
        runner.add_to_output(
            ft.Markdown(
                self.content,
                selectable=True,
                extension_set=ft.MarkdownExtensionSet.GITHUB_WEB,
                on_tap_link=lambda e: runner.page.launch_url(e.data) if runner.page else None,
            ),
            component=self
        )

    def to_dict(self) -> dict:
        return {"type": "markdown", "content": self.content}


# ============================================================================
# Data Display Components
# ============================================================================

@dataclass
class Table(Container):
    """Display tabular data.

    Supports progressive row addition via context manager.
    """

    cols: List[str]
    data: List[List[Any]] = field(default_factory=list)
    title: Optional[str] = None

    def __post_init__(self):
        """Initialize Container attributes after dataclass init."""
        super().__init__()
        self.flet_control: Optional["ft.DataTable"] = None

    def add_row(self, row: Union[List[Any], 'Row']) -> None:
        """Add a row to the table.

        Args:
            row: List of cell values or Row component
        """
        if isinstance(row, Row):
            row_data = row.children
        else:
            row_data = row

        self.data.append(row_data)
        self._update()

    def update_cell(self, row_index: int, col_index: int, value: Any) -> None:
        """Update a cell value and trigger display update.

        Args:
            row_index: Row index (0-based)
            col_index: Column index (0-based)
            value: New cell value
        """
        if 0 <= row_index < len(self.data) and 0 <= col_index < len(self.data[row_index]):
            self.data[row_index][col_index] = value
            self._update()

    def show_cli(self, runner) -> None:
        lines = []

        if self.title:
            lines.append(self.title)
            lines.append("=" * len(self.title))
            lines.append("")

        # Helper function to get CLI-friendly cell representation
        def cell_to_str(cell):
            if isinstance(cell, UiBlock):
                # For GUI-only components, show their text if available
                if hasattr(cell, 'text'):
                    return f"[{cell.text}]"
                else:
                    return "[UI Component]"
            else:
                return str(cell)

        # Calculate column widths
        col_widths = [len(h) for h in self.cols]
        for row in self.data:
            for i, cell in enumerate(row):
                if i < len(col_widths):
                    col_widths[i] = max(col_widths[i], len(cell_to_str(cell)))

        # Header
        header_line = " | ".join(
            h.ljust(col_widths[i]) for i, h in enumerate(self.cols)
        )
        lines.append(header_line)
        lines.append("-" * len(header_line))

        # Rows
        for row in self.data:
            row_line = " | ".join(
                cell_to_str(cell).ljust(col_widths[i]) if i < len(col_widths) else cell_to_str(cell)
                for i, cell in enumerate(row)
            )
            lines.append(row_line)

        print("\n".join(lines))

    def show_gui(self, runner) -> None:
        import flet as ft

        # On first render, create the control and add it to the output
        if self.flet_control is None:
            columns = [
                ft.DataColumn(ft.Text(header, weight=ft.FontWeight.BOLD))
                for header in self.cols
            ]

            # Helper function to convert cell to Flet control
            def cell_to_control(cell):
                if isinstance(cell, UiBlock):
                    # Render UI component to Flet control
                    control = runner.render_to_control(cell)
                    return control if control else ft.Text("")
                else:
                    # Convert to text
                    return ft.Text(str(cell))

            data_rows = [
                ft.DataRow(
                    cells=[ft.DataCell(cell_to_control(cell)) for cell in row]
                )
                for row in self.data
            ]

            self.flet_control = ft.DataTable(
                columns=columns,
                rows=data_rows,
                border=ft.border.all(1, ft.Colors.GREY_400),
                border_radius=10,
                horizontal_lines=ft.border.BorderSide(1, ft.Colors.GREY_300),
            )

            if self.title:
                # If there's a title, wrap the table in a Column
                control_to_add = ft.Column([
                    ft.Text(self.title, size=16, weight=ft.FontWeight.BOLD),
                    self.flet_control,
                ])
            else:
                control_to_add = self.flet_control

            runner.add_to_output(control_to_add, component=self)

    def to_dict(self) -> dict:
        return {
            "type": "table",
            "cols": self.cols,
            "data": self.data,
            "title": self.title,
        }


# ============================================================================
# Layout Components
# ============================================================================

@dataclass
class Row(Container):
    """Display components horizontally."""

    children: List[Any] = field(default_factory=list)

    def __post_init__(self):
        """Initialize Container attributes after dataclass init."""
        # Only call super().__init__() if not already initialized
        if not hasattr(self, '_context_active'):
            super().__init__()

    def add(self, child: UiBlock) -> None:
        """Add a child component to the row."""
        self.children.append(child)
        self._update()

    def show_cli(self, runner) -> None:
        # CLI shows children vertically (no horizontal layout in terminal)
        for child in self.children:
            if isinstance(child, UiBlock):
                if not child.is_gui_only():
                    runner.show(child)
            else:
                print(str(child))

    def show_gui(self, runner) -> None:
        import flet as ft

        controls = []
        for child in self.children:
            if isinstance(child, UiBlock):
                control = runner.render_to_control(child)
                if control:
                    controls.append(control)
            else:
                controls.append(ft.Text(str(child)))

        runner.add_to_output(ft.Row(controls=controls, spacing=10, wrap=True), component=self)

    def to_dict(self) -> dict:
        return {
            "type": "row",
            "children": [
                child.to_dict() if isinstance(child, UiBlock) else str(child)
                for child in self.children
            ],
        }


@dataclass
class Column(Container):
    """Display components vertically."""

    children: List[UiBlock] = field(default_factory=list)

    def __post_init__(self):
        """Initialize Container attributes after dataclass init."""
        if not hasattr(self, '_context_active'):
            super().__init__()

    def add(self, child: UiBlock) -> None:
        """Add a child component to the column."""
        self.children.append(child)
        self._update()

    def show_cli(self, runner) -> None:
        for child in self.children:
            if isinstance(child, UiBlock):
                runner.show(child)

    def show_gui(self, runner) -> None:
        import flet as ft

        controls = [runner.render_to_control(child) for child in self.children]
        runner.add_to_output(ft.Column(controls=controls, spacing=10), component=self)

    def to_dict(self) -> dict:
        return {
            "type": "column",
            "children": [child.to_dict() for child in self.children],
        }


# ============================================================================
# Interactive Components
# ============================================================================

@dataclass
class Button(UiBlock):
    """Interactive button that executes an action (GUI only)."""

    text: str
    on_click: Callable
    icon: Optional[str] = None

    def show_cli(self, runner) -> None:
        # Buttons don't render in CLI
        pass

    def show_gui(self, runner) -> None:
        import flet as ft

        icon_obj = None
        if self.icon:
            icon_obj = getattr(ft.Icons, self.icon.upper(), None)

        def handle_click(e):
            # Set runner context for callback execution
            saved_runner = get_current_runner()
            set_current_runner(runner)
            try:
                self.on_click()
            finally:
                set_current_runner(saved_runner)
            # Optionally refresh runner
            if hasattr(runner, 'refresh'):
                runner.refresh()

        runner.add_to_output(
            ft.ElevatedButton(
                text=self.text,
                icon=icon_obj,
                on_click=handle_click,
            ),
            component=self
        )

    def is_gui_only(self) -> bool:
        return True

    def to_dict(self) -> dict:
        return {
            "type": "button",
            "text": self.text,
            "icon": self.icon,
            "action_id": id(self.on_click),  # Can't serialize callback
        }


@dataclass
class Link(UiBlock):
    """Interactive link that executes an action (GUI only)."""

    text: str
    on_click: Callable

    def show_cli(self, runner) -> None:
        # Links don't render in CLI
        pass

    def show_gui(self, runner) -> None:
        import flet as ft

        def handle_click(e):
            # Set runner context for callback execution
            saved_runner = get_current_runner()
            set_current_runner(runner)
            try:
                self.on_click()
            finally:
                set_current_runner(saved_runner)

        runner.add_to_output(
            ft.TextButton(
                text=self.text,
                icon=ft.Icons.LINK,
                on_click=handle_click,
            ),
            component=self
        )

    def is_gui_only(self) -> bool:
        return True

    def to_dict(self) -> dict:
        return {
            "type": "link",
            "text": self.text,
            "action_id": id(self.on_click),
        }


@dataclass
class TextInput(UiBlock):
    """Text input field."""

    label: str
    value: str = ""
    on_change: Optional[Callable[[str], None]] = None

    def show_cli(self, runner) -> None:
        # Prompt for input in CLI
        new_value = input(f"{self.label}: ") or self.value
        self.value = new_value
        if self.on_change:
            self.on_change(new_value)

    def show_gui(self, runner) -> None:
        import flet as ft

        def handle_change(e):
            self.value = e.control.value
            if self.on_change:
                # Set runner context for callback execution
                saved_runner = get_current_runner()
                set_current_runner(runner)
                try:
                    self.on_change(e.control.value)
                finally:
                    set_current_runner(saved_runner)

        textfield = ft.TextField(
            label=self.label,
            value=self.value,
            on_change=handle_change,
        )
        runner.add_to_output(textfield)

        # Store reference for later access if needed
        if hasattr(runner, 'register_control'):
            runner.register_control(self, textfield)

    def to_dict(self) -> dict:
        return {
            "type": "text_input",
            "label": self.label,
            "value": self.value,
        }
