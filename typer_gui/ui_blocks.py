"""UI Blocks - Rich components that can be returned from commands."""

from abc import ABC, abstractmethod
from typing import Any, Optional, List, Callable, Union
from dataclasses import dataclass


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
    def render_flet(self) -> Any:
        """Render the block as a Flet component.

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

    def render_flet(self) -> Any:
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

    def render_flet(self) -> Any:
        """Render markdown as Flet Markdown component."""
        import flet as ft

        return ft.Markdown(
            self.content,
            selectable=True,
            extension_set=ft.MarkdownExtensionSet.GITHUB_WEB,
            on_tap_link=lambda e: print(f"Link clicked: {e.data}"),
        )


@dataclass
class Link(UiBlock):
    """Interactive link that triggers command selection (GUI only)."""

    text: str
    command_name: str
    params: Optional[dict] = None

    def render_cli(self) -> str:
        """Links are not rendered in CLI mode."""
        return ""

    def render_flet(self) -> Any:
        """Render as clickable link in Flet."""
        import flet as ft

        # This will need to be wired up to actually trigger command selection
        # For now, return a styled text button
        return ft.TextButton(
            text=self.text,
            icon=ft.Icons.LINK,
            on_click=lambda e: self._on_click(e),
        )

    def is_gui_only(self) -> bool:
        """Links are GUI-only."""
        return True

    def _on_click(self, e):
        """Handle link click - to be implemented in Flet UI integration."""
        # This will be connected to the command selection mechanism
        print(f"Link clicked: {self.command_name} with params {self.params}")


@dataclass
class Button(UiBlock):
    """Interactive button that triggers command selection (GUI only)."""

    text: str
    command_name: str
    params: Optional[dict] = None
    icon: Optional[str] = None

    def render_cli(self) -> str:
        """Buttons are not rendered in CLI mode."""
        return ""

    def render_flet(self) -> Any:
        """Render as button in Flet."""
        import flet as ft

        # Map icon name to Flet icon
        icon_obj = None
        if self.icon:
            icon_obj = getattr(ft.Icons, self.icon.upper(), None)

        return ft.ElevatedButton(
            text=self.text,
            icon=icon_obj,
            on_click=lambda e: self._on_click(e),
        )

    def is_gui_only(self) -> bool:
        """Buttons are GUI-only."""
        return True

    def _on_click(self, e):
        """Handle button click - to be implemented in Flet UI integration."""
        # This will be connected to the command selection mechanism
        print(f"Button clicked: {self.command_name} with params {self.params}")


# Convenience functions for creating UI blocks
def table(headers: List[str], rows: List[List[Any]], title: Optional[str] = None) -> Table:
    """Create a table UI block.

    Args:
        headers: List of column headers
        rows: List of rows, where each row is a list of cell values
        title: Optional title for the table

    Example:
        >>> return ui.table(
        ...     headers=["Name", "Age", "City"],
        ...     rows=[
        ...         ["Alice", 30, "NYC"],
        ...         ["Bob", 25, "SF"],
        ...     ],
        ...     title="Users"
        ... )
    """
    return Table(headers=headers, rows=rows, title=title)


def md(content: str) -> Markdown:
    """Create a markdown UI block.

    Args:
        content: Markdown-formatted string

    Example:
        >>> return ui.md(\"\"\"
        ... # Hello World
        ...
        ... This is **bold** text.
        ... \"\"\")
    """
    return Markdown(content=content)


def link(text: str, command_name: str, params: Optional[dict] = None) -> Link:
    """Create a link UI block (GUI only).

    Args:
        text: Link text to display
        command_name: Name of command to trigger
        params: Optional parameters to pass to command

    Example:
        >>> return ui.link("View details", "show_details", {"id": 123})
    """
    return Link(text=text, command_name=command_name, params=params)


def button(text: str, command_name: str, params: Optional[dict] = None, icon: Optional[str] = None) -> Button:
    """Create a button UI block (GUI only).

    Args:
        text: Button text to display
        command_name: Name of command to trigger
        params: Optional parameters to pass to command
        icon: Optional icon name (Flet icon name)

    Example:
        >>> return ui.button("Refresh", "refresh_data", icon="refresh")
    """
    return Button(text=text, command_name=command_name, params=params, icon=icon)


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
