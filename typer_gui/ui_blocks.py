"""UI Blocks - Rich components with async event-driven rendering."""

from abc import ABC, abstractmethod
from typing import Any, Optional, List, Callable, Union, TYPE_CHECKING
from dataclasses import dataclass
import threading
import asyncio
import uuid

if TYPE_CHECKING:
    import flet as ft
    from .ui_app import UIApp

# Global context storage using thread-local storage
_context_storage = threading.local()


class UiContext:
    """Execution context for UI blocks.

    Tracks whether we're in CLI or GUI mode and provides rendering targets.
    """

    def __init__(
        self,
        mode: str,
        ui_app: Optional['UIApp'] = None,
        page: Optional[Any] = None,
        output_view: Optional[Any] = None,
    ):
        """Initialize UI context.

        Args:
            mode: "cli" or "gui"
            ui_app: Reference to UIApp instance for event emission
            page: Flet page object (GUI mode only)
            output_view: Flet ListView for output (GUI mode only)
        """
        self.mode = mode
        self.ui_app = ui_app
        self.page = page
        self.output_view = output_view
        self._row_stack: List[List['UiBlock']] = []  # Stack of row contexts
        self._container_stack: List[str] = []  # Stack of container IDs

    def is_cli(self) -> bool:
        """Check if in CLI mode."""
        return self.mode == "cli"

    def is_gui(self) -> bool:
        """Check if in GUI mode."""
        return self.mode == "gui"

    def is_in_row(self) -> bool:
        """Check if currently inside a row context."""
        return len(self._row_stack) > 0

    async def enter_row(self) -> str:
        """Enter a row context - blocks will be collected instead of rendered.

        Returns:
            Container ID
        """
        self._row_stack.append([])
        container_id = str(uuid.uuid4())
        self._container_stack.append(container_id)

        # Emit ContainerStarted event
        if self.ui_app:
            from .events import ContainerStarted
            await self.ui_app.emit_event(
                ContainerStarted(
                    container_type="row",
                    container_id=container_id,
                    params={},
                )
            )

        return container_id

    async def exit_row(self) -> List['UiBlock']:
        """Exit a row context and return collected blocks.

        Returns:
            List of collected blocks
        """
        if self._row_stack:
            blocks = self._row_stack.pop()
            container_id = self._container_stack.pop() if self._container_stack else ""

            # Emit ContainerEnded event
            if self.ui_app:
                from .events import ContainerEnded
                await self.ui_app.emit_event(
                    ContainerEnded(container_id=container_id)
                )

            return blocks
        return []

    def add_to_row(self, block: 'UiBlock') -> None:
        """Add a block to the current row context."""
        if self._row_stack:
            self._row_stack[-1].append(block)

    async def render(self, block: 'UiBlock') -> None:
        """Render a UI block to the current context.

        Args:
            block: Block to render
        """
        # If inside a row context, collect the block instead of rendering
        if self.is_in_row():
            self.add_to_row(block)
            return

        # Emit BlockEmitted event for runner to handle
        if self.ui_app:
            from .events import BlockEmitted
            await self.ui_app.emit_event(BlockEmitted(block=block))
        else:
            # Fallback: direct rendering (for legacy compatibility)
            if self.is_cli():
                if not block.is_gui_only():
                    print(block.render_cli())
            else:
                # GUI mode fallback
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

    async def present(self) -> None:
        """Present this block in the current context (async)."""
        context = get_context()
        if context:
            await context.render(self)

    def present_sync(self) -> None:
        """Present this block synchronously (for backward compatibility)."""
        try:
            loop = asyncio.get_event_loop()
            if loop.is_running():
                # Already in async context - schedule as task
                asyncio.create_task(self.present())
            else:
                # No event loop - run sync
                loop.run_until_complete(self.present())
        except RuntimeError:
            # No event loop at all - create one
            asyncio.run(self.present())


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
        import re

        text = self.content
        # Remove markdown formatting
        text = re.sub(r'\*\*([^*]+)\*\*', r'\1', text)
        text = re.sub(r'\*([^*]+)\*', r'\1', text)
        text = re.sub(r'__([^_]+)__', r'\1', text)
        text = re.sub(r'_([^_]+)_', r'\1', text)
        text = re.sub(r'`([^`]+)`', r'\1', text)
        text = re.sub(r'^#+\s+(.+)$', lambda m: m.group(1).upper(), text, flags=re.MULTILINE)

        # Unicode to ASCII
        replacements = {
            '\u2713': '[x]', '\u2717': '[ ]', '\u2022': '*',
            '\u2014': '--', '\u2013': '-', '\u201c': '"',
            '\u201d': '"', '\u2018': "'", '\u2019': "'",
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

        icon_obj = None
        if self.icon:
            icon_obj = getattr(ft.Icons, self.icon.upper(), None)

        def on_click(e):
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
    """Container for displaying UI blocks in a horizontal row."""

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

        controls = []
        for child in self.children:
            control = child.render_flet(context)
            if control:
                controls.append(control)

        return ft.Row(controls=controls, spacing=10, wrap=True)


class RowContext:
    """Async context manager for creating rows of UI blocks."""

    def __init__(self):
        self.container_id: Optional[str] = None

    async def __aenter__(self):
        """Enter row context - blocks will be collected."""
        context = get_context()
        if context:
            self.container_id = await context.enter_row()
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """Exit row context - render collected blocks as a row."""
        context = get_context()
        if context:
            blocks = await context.exit_row()
            if blocks:
                row = Row(children=blocks)
                await row.present()
        return False

    # Synchronous context manager support for backward compatibility
    def __enter__(self):
        """Synchronous enter (for backward compatibility)."""
        context = get_context()
        if context:
            try:
                loop = asyncio.get_event_loop()
                if loop.is_running():
                    # Create task but don't await
                    task = asyncio.create_task(context.enter_row())
                    # Store for exit
                    self._enter_task = task
                else:
                    self.container_id = loop.run_until_complete(context.enter_row())
            except RuntimeError:
                self.container_id = asyncio.run(context.enter_row())
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        """Synchronous exit (for backward compatibility)."""
        context = get_context()
        if context:
            try:
                loop = asyncio.get_event_loop()
                if loop.is_running():
                    asyncio.create_task(self._async_exit(context))
                else:
                    loop.run_until_complete(self._async_exit(context))
            except RuntimeError:
                asyncio.run(self._async_exit(context))
        return False

    async def _async_exit(self, context):
        """Helper for async exit."""
        blocks = await context.exit_row()
        if blocks:
            row = Row(children=blocks)
            await row.present()


class UiOutput:
    """Container for UI output methods."""

    @staticmethod
    def table(headers: List[str], rows: List[List[Any]], title: Optional[str] = None) -> Table:
        """Create and present a table UI block.

        Args:
            headers: List of column headers
            rows: List of rows
            title: Optional title

        Returns:
            The created Table block
        """
        block = Table(headers=headers, rows=rows, title=title)
        try:
            loop = asyncio.get_event_loop()
            if loop.is_running():
                asyncio.create_task(block.present())
            else:
                loop.run_until_complete(block.present())
        except RuntimeError:
            asyncio.run(block.present())
        return block

    @staticmethod
    def md(content: str) -> Markdown:
        """Create and present a markdown UI block.

        Args:
            content: Markdown-formatted string

        Returns:
            The created Markdown block
        """
        block = Markdown(content=content)
        try:
            loop = asyncio.get_event_loop()
            if loop.is_running():
                asyncio.create_task(block.present())
            else:
                loop.run_until_complete(block.present())
        except RuntimeError:
            asyncio.run(block.present())
        return block

    @staticmethod
    def link(text: str, do: Callable) -> Link:
        """Create and present a link UI block (GUI only).

        Args:
            text: Link text
            do: Callable to execute when clicked

        Returns:
            The created Link block
        """
        block = Link(text=text, do=do)
        try:
            loop = asyncio.get_event_loop()
            if loop.is_running():
                asyncio.create_task(block.present())
            else:
                loop.run_until_complete(block.present())
        except RuntimeError:
            asyncio.run(block.present())
        return block

    @staticmethod
    def button(text: str, do: Callable, icon: Optional[str] = None) -> Button:
        """Create and present a button UI block (GUI only).

        Args:
            text: Button text
            do: Callable to execute when clicked
            icon: Optional icon name

        Returns:
            The created Button block
        """
        block = Button(text=text, do=do, icon=icon)
        try:
            loop = asyncio.get_event_loop()
            if loop.is_running():
                asyncio.create_task(block.present())
            else:
                loop.run_until_complete(block.present())
        except RuntimeError:
            asyncio.run(block.present())
        return block

    @staticmethod
    def row() -> RowContext:
        """Create a row context for displaying UI blocks horizontally.

        Returns:
            A context manager for collecting blocks into a row

        Example:
            >>> with ui.out.row():
            ...     ui.out.link("Link 1", do=lambda: ...)
            ...     ui.out.button("Action", do=lambda: ...)
        """
        return RowContext()
