"""UI Blocks - Rich components that can be returned from commands."""

from abc import ABC, abstractmethod
from typing import Any, Optional, List, Callable, Union, TYPE_CHECKING
from dataclasses import dataclass
import threading

if TYPE_CHECKING:
    import flet as ft


# Global context storage using thread-local storage
_context_storage = threading.local()


class UiContext:
    """Execution context for UI blocks.

    Tracks whether we're in CLI or GUI mode and provides rendering targets.
    """

    def __init__(self, mode: str, page: Optional[Any] = None, output_view: Optional[Any] = None, gui_app: Optional[Any] = None, ui_app: Optional[Any] = None):
        """Initialize UI context.

        Args:
            mode: "cli" or "gui"
            page: Flet page object (GUI mode only)
            output_view: Flet ListView for output (GUI mode only)
            gui_app: Reference to GUI app for command execution (GUI mode only)
            ui_app: Reference to UIApp instance (GUI mode only)
        """
        self.mode = mode
        self.page = page
        self.output_view = output_view
        self.gui_app = gui_app
        self.ui_app = ui_app
        self._row_stack: List[List['UiBlock']] = []  # Stack of row contexts

    def is_cli(self) -> bool:
        """Check if in CLI mode."""
        return self.mode == "cli"

    def is_gui(self) -> bool:
        """Check if in GUI mode."""
        return self.mode == "gui"

    def is_in_row(self) -> bool:
        """Check if currently inside a row context."""
        return len(self._row_stack) > 0

    def enter_row(self) -> None:
        """Enter a row context - blocks will be collected instead of rendered."""
        self._row_stack.append([])

    def exit_row(self) -> List['UiBlock']:
        """Exit a row context and return collected blocks."""
        if self._row_stack:
            return self._row_stack.pop()
        return []

    def add_to_row(self, block: 'UiBlock') -> None:
        """Add a block to the current row context."""
        if self._row_stack:
            self._row_stack[-1].append(block)

    def render(self, block: 'UiBlock') -> None:
        """Render a UI block to the current context."""
        # If inside a row context, collect the block instead of rendering
        if self.is_in_row():
            self.add_to_row(block)
            return

        # Normal rendering
        if self.is_cli():
            # CLI mode - print if not GUI-only
            if not block.is_gui_only():
                print(block.render_cli())
        else:
            # GUI mode - append to output view
            if self.output_view:
                flet_component = block.render_flet(self)
                if flet_component:
                    self.output_view.controls.append(flet_component)
                    if self.page:
                        self.page.update()


def get_context() -> Optional[UiContext]:
    """Get the current UI context."""
    return getattr(_context_storage, 'context', None)


def set_context(context: Optional[UiContext]) -> None:
    """Set the current UI context."""
    _context_storage.context = context


class UiBlock(ABC):
    """Base class for UI blocks that have both GUI and CLI representations."""

    @abstractmethod
    def render_cli(self) -> str:
        """Render the block for CLI output.

        Returns:
            String representation for terminal output.
        """
        pass

    @abstractmethod
    def render_flet(self, context: UiContext) -> Any:
        """Render the block as a Flet component.

        Args:
            context: The UI context with page and app references

        Returns:
            Flet component (ft.Control) for GUI display.
        """
        pass

    def is_gui_only(self) -> bool:
        """Whether this block should only appear in GUI mode.

        Returns:
            True if block is GUI-only, False otherwise.
        """
        return False

    def present(self) -> None:
        """Present this block in the current context."""
        context = get_context()
        if context:
            context.render(self)


@dataclass
class Table(UiBlock):
    """Display tabular data in both GUI and CLI."""

    headers: List[str]
    rows: List[List[Any]]
    title: Optional[str] = None

    def render_cli(self) -> str:
        """Render table as ASCII art for CLI."""
        lines = []

        if self.title:
            lines.append(self.title)
            lines.append("=" * len(self.title))
            lines.append("")

        # Calculate column widths
        col_widths = [len(h) for h in self.headers]
        for row in self.rows:
            for i, cell in enumerate(row):
                col_widths[i] = max(col_widths[i], len(str(cell)))

        # Header
        header_line = " | ".join(
            h.ljust(col_widths[i]) for i, h in enumerate(self.headers)
        )
        lines.append(header_line)
        lines.append("-" * len(header_line))

        # Rows
        for row in self.rows:
            row_line = " | ".join(
                str(cell).ljust(col_widths[i]) for i, cell in enumerate(row)
            )
            lines.append(row_line)

        return "\n".join(lines)

    def render_flet(self, context: UiContext) -> Any:
        """Render table as Flet DataTable."""
        import flet as ft

        columns = [
            ft.DataColumn(ft.Text(header, weight=ft.FontWeight.BOLD))
            for header in self.headers
        ]

        data_rows = [
            ft.DataRow(
                cells=[ft.DataCell(ft.Text(str(cell))) for cell in row]
            )
            for row in self.rows
        ]

        table = ft.DataTable(
            columns=columns,
            rows=data_rows,
            border=ft.border.all(1, ft.Colors.GREY_400),
            border_radius=10,
            horizontal_lines=ft.border.BorderSide(1, ft.Colors.GREY_300),
        )

        if self.title:
            return ft.Column([
                ft.Text(self.title, size=16, weight=ft.FontWeight.BOLD),
                table,
            ])

        return table


@dataclass
class Markdown(UiBlock):
    """Display Markdown content in both GUI and CLI."""

    content: str

    def render_cli(self) -> str:
        """Render markdown as plain text for CLI."""
        # Simple markdown-to-text conversion
        # Remove markdown formatting for CLI
        import re

        text = self.content
        # Remove bold/italic markers
        text = re.sub(r'\*\*([^*]+)\*\*', r'\1', text)  # **bold**
        text = re.sub(r'\*([^*]+)\*', r'\1', text)      # *italic*
        text = re.sub(r'__([^_]+)__', r'\1', text)      # __bold__
        text = re.sub(r'_([^_]+)_', r'\1', text)        # _italic_
        # Remove inline code markers
        text = re.sub(r'`([^`]+)`', r'\1', text)        # `code`
        # Convert headers to uppercase
        text = re.sub(r'^#+\s+(.+)$', lambda m: m.group(1).upper(), text, flags=re.MULTILINE)

        # Replace Unicode characters with ASCII equivalents for better CLI compatibility
        replacements = {
            '\u2713': '[x]',  # ✓ -> [x]
            '\u2717': '[ ]',  # ✗ -> [ ]
            '\u2022': '*',    # • -> *
            '\u2014': '--',   # — -> --
            '\u2013': '-',    # – -> -
            '\u201c': '"',    # " -> "
            '\u201d': '"',    # " -> "
            '\u2018': "'",    # ' -> '
            '\u2019': "'",    # ' -> '
        }
        for unicode_char, ascii_char in replacements.items():
            text = text.replace(unicode_char, ascii_char)

        return text

    def render_flet(self, context: UiContext) -> Any:
        """Render markdown as Flet Markdown component."""
        import flet as ft

        return ft.Markdown(
            self.content,
            selectable=True,
            extension_set=ft.MarkdownExtensionSet.GITHUB_WEB,
            on_tap_link=lambda e: context.page.launch_url(e.data) if context.page else None,
        )


@dataclass
class Link(UiBlock):
    """Interactive link that executes a callable action (GUI only)."""

    text: str
    do: Callable

    def render_cli(self) -> str:
        """Links are not rendered in CLI mode."""
        return ""

    def render_flet(self, context: UiContext) -> Any:
        """Render as clickable link in Flet."""
        import flet as ft

        def on_click(e):
            """Handle link click to execute the action."""
            self.do()

        return ft.TextButton(
            text=self.text,
            icon=ft.Icons.LINK,
            on_click=on_click,
        )

    def is_gui_only(self) -> bool:
        """Links are GUI-only."""
        return True


@dataclass
class Button(UiBlock):
    """Interactive button that executes a callable action (GUI only)."""

    text: str
    do: Callable
    icon: Optional[str] = None

    def render_cli(self) -> str:
        """Buttons are not rendered in CLI mode."""
        return ""

    def render_flet(self, context: UiContext) -> Any:
        """Render as button in Flet."""
        import flet as ft

        # Map icon name to Flet icon
        icon_obj = None
        if self.icon:
            icon_obj = getattr(ft.Icons, self.icon.upper(), None)

        def on_click(e):
            """Handle button click to execute the action."""
            self.do()

        return ft.ElevatedButton(
            text=self.text,
            icon=icon_obj,
            on_click=on_click,
        )

    def is_gui_only(self) -> bool:
        """Buttons are GUI-only."""
        return True


@dataclass
class Row(UiBlock):
    """Container for displaying UI blocks in a horizontal row.

    In GUI mode, displays children side-by-side.
    In CLI mode, displays children vertically (one per line).
    """

    children: List[UiBlock]

    def render_cli(self) -> str:
        """Render children vertically in CLI mode."""
        lines = []
        for child in self.children:
            if not child.is_gui_only():
                rendered = child.render_cli()
                if rendered:
                    lines.append(rendered)
        return "\n".join(lines)

    def render_flet(self, context: UiContext) -> Any:
        """Render children horizontally in Flet."""
        import flet as ft

        # Render each child and collect the controls
        controls = []
        for child in self.children:
            control = child.render_flet(context)
            if control:
                controls.append(control)

        return ft.Row(controls=controls, spacing=10, wrap=True)

    def is_gui_only(self) -> bool:
        """Row is not GUI-only, but renders differently in CLI."""
        return False


class RowContext:
    """Context manager for creating rows of UI blocks.

    Blocks created inside a row context are collected and displayed together.
    """

    def __enter__(self):
        """Enter row context - blocks will be collected."""
        context = get_context()
        if context:
            context.enter_row()
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        """Exit row context - render collected blocks as a row."""
        context = get_context()
        if context:
            blocks = context.exit_row()
            if blocks:
                row = Row(children=blocks)
                row.present()
        return False


class UiOutput:
    """Container for UI output methods.

    Provides methods to create and present UI blocks like tables, markdown, links, and buttons.
    Available as ui.out in command contexts.
    """

    @staticmethod
    def table(headers: List[str], rows: List[List[Any]], title: Optional[str] = None) -> Table:
        """Create and present a table UI block.

        Args:
            headers: List of column headers
            rows: List of rows, where each row is a list of cell values
            title: Optional title for the table

        Returns:
            The created Table block

        Example:
            >>> # Standalone use (auto-presents)
            >>> ui.out.table(
            ...     headers=["Name", "Age"],
            ...     rows=[["Alice", 30]]
            ... )
            >>>
            >>> # In a row context (collected, not auto-presented)
            >>> with ui.out.row():
            ...     ui.out.table(...)
            ...     ui.out.md(...)
        """
        block = Table(headers=headers, rows=rows, title=title)
        block.present()
        return block

    @staticmethod
    def md(content: str) -> Markdown:
        """Create and present a markdown UI block.

        Args:
            content: Markdown-formatted string

        Returns:
            The created Markdown block

        Example:
            >>> # Standalone use (auto-presents)
            >>> ui.out.md("# Hello")
            >>>
            >>> # In a row context (collected, not auto-presented)
            >>> with ui.out.row():
            ...     ui.out.md("**Bold**")
            ...     ui.out.link(...)
        """
        block = Markdown(content=content)
        block.present()
        return block

    @staticmethod
    def link(text: str, do: Callable) -> Link:
        """Create and present a link UI block (GUI only).

        Args:
            text: Link text to display
            do: Callable to execute when clicked

        Returns:
            The created Link block

        Example:
            >>> # Standalone use (auto-presents)
            >>> ui.out.link("Click me", do=lambda: ...)
            >>>
            >>> # In a row context (collected, not auto-presented)
            >>> with ui.out.row():
            ...     ui.out.link(...)
            ...     ui.out.button(...)
        """
        block = Link(text=text, do=do)
        block.present()
        return block

    @staticmethod
    def button(text: str, do: Callable, icon: Optional[str] = None) -> Button:
        """Create and present a button UI block (GUI only).

        Args:
            text: Button text to display
            do: Callable to execute when clicked
            icon: Optional icon name (Flet icon name)

        Returns:
            The created Button block

        Example:
            >>> # Standalone use (auto-presents)
            >>> ui.out.button("Click", do=lambda: ...)
            >>>
            >>> # In a row context (collected, not auto-presented)
            >>> with ui.out.row():
            ...     ui.out.button(...)
            ...     ui.out.link(...)
        """
        block = Button(text=text, do=do, icon=icon)
        block.present()
        return block

    @staticmethod
    def row() -> RowContext:
        """Create a row context for displaying UI blocks horizontally.

        In GUI mode, displays children side-by-side.
        In CLI mode, displays children vertically.

        Returns:
            A context manager for collecting blocks into a row

        Example:
            >>> # Use as context manager
            >>> with ui.out.row():
            ...     ui.out.link("Link 1", do=lambda: ...)
            ...     ui.out.link("Link 2", do=lambda: ...)
            ...     ui.out.button("Action", do=lambda: ...)
        """
        return RowContext()


def render_for_mode(blocks: Union[UiBlock, List[UiBlock]]) -> Union[UiBlock, List[UiBlock], None]:
    """Helper function to render UI blocks appropriately for CLI or GUI mode.

    In CLI mode, prints the blocks and returns None.
    In GUI mode, returns the blocks unchanged for GUI rendering.

    Args:
        blocks: A single UiBlock or list of UiBlocks

    Returns:
        The blocks if in GUI mode, None if in CLI mode

    Example:
        >>> @app.command()
        >>> def my_command():
        >>>     return render_for_mode(ui.table(...))
    """
    # Import here to avoid circular dependency
    from .ui import Ui

    if Ui.is_cli_mode():
        # CLI mode - print the blocks
        if isinstance(blocks, UiBlock):
            if not blocks.is_gui_only():
                print(blocks.render_cli())
        elif isinstance(blocks, list):
            for block in blocks:
                if isinstance(block, UiBlock) and not block.is_gui_only():
                    print(block.render_cli())
                    print()  # Add spacing
        return None
    else:
        # GUI mode - return blocks for GUI rendering
        return blocks
