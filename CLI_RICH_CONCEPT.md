# CLI Design with Rich Library

## Using Rich for Full Formatting Flexibility

Rich library provides rich text, tables, panels, markdown, progress bars, and more. How does this affect our `build_cli()` design?

---

## Design Decision: Return Rich RenderableType

### Key Insight

Rich defines `RenderableType` which includes:
- `str` - plain strings
- `Text` - Rich text with styles/colors
- `Table` - Rich tables
- `Panel` - Bordered panels
- `Markdown` - Markdown rendering
- Any object with `__rich__()` or `__rich_console__()`

**This means our `build_cli()` can return any Rich-compatible type!**

---

## Updated Interface

```python
from rich.console import RenderableType, Console

class UIBlock(ABC):
    @abstractmethod
    def build(self, ctx: UIRunnerCtx) -> ft.Control:
        """GUI: Build Flet control."""
        pass

    @abstractmethod
    def build_cli(self, ctx: CLIRunnerCtx) -> RenderableType:
        """CLI: Build Rich renderable (str, Text, Table, Panel, etc.)"""
        pass


class CLIRunnerCtx(UIRunnerCtx):
    def __init__(self):
        self.console = Console()  # Rich Console
        self._ui_flow_stack: List[List[RenderableType]] = []  # Stack of Rich renderables

    def ui_flow_append(self, component: UIBlockType) -> None:
        """Append to current UI flow."""
        current_flow = self._ui_flow_stack[-1] if self._ui_flow_stack else None

        if current_flow is None:
            raise RuntimeError("No active UI flow")

        # Build Rich renderable
        renderable = self._build_component(component)

        # Append to flow
        current_flow.append(renderable)

    def build_child(self, parent: UIBlock, child: UIBlockType) -> RenderableType:
        """Build child component and return Rich renderable."""
        # Convert to UIBlock
        if isinstance(child, str):
            from .ui_blocks import Md
            child_block = Md(child)
        elif isinstance(child, UIBlock):
            child_block = child
        elif callable(child):
            return self._build_callable(child)
        else:
            from .ui_blocks import Text
            child_block = Text(str(child))

        # Establish hierarchy
        parent.add_child(child_block)
        child_block._ctx = self

        # Build CLI representation (returns RenderableType)
        return child_block.build_cli(self)

    def _build_component(self, component: UIBlockType) -> RenderableType:
        """Build any component type to Rich renderable."""
        if isinstance(component, str):
            # Strings as Markdown
            from rich.markdown import Markdown
            return Markdown(component)
        elif isinstance(component, UIBlock):
            return component.build_cli(self)
        else:
            return str(component)
```

---

## Component Examples with Rich

### Simple Components

```python
from rich.text import Text as RichText
from rich.markdown import Markdown

class Text(UIBlock):
    def build_cli(self, ctx: CLIRunnerCtx) -> RenderableType:
        """Return Rich Text object (supports styles)."""
        return RichText(self.content)


class Md(UIBlock):
    def build_cli(self, ctx: CLIRunnerCtx) -> RenderableType:
        """Return Rich Markdown renderer."""
        return Markdown(self.content)
```

### Table Component

```python
from rich.table import Table as RichTable
from rich.text import Text as RichText

class Table(UIBlock):
    def build_cli(self, ctx: CLIRunnerCtx) -> RenderableType:
        """Return Rich Table."""
        table = RichTable(title=self.title, show_header=True, header_style="bold magenta")

        # Add columns
        for col in self.cols:
            table.add_column(col, style="cyan")

        # Add rows
        for row in self.data:
            cells = []
            for cell in row:
                if isinstance(cell, UIBlock):
                    # Build nested component
                    cell_renderable = ctx.build_child(self, cell)

                    # Rich Table cells can be RichText objects!
                    if isinstance(cell_renderable, RichText):
                        cells.append(cell_renderable)
                    elif isinstance(cell_renderable, str):
                        cells.append(RichText(cell_renderable))
                    else:
                        # For complex renderables (Panel, etc.), render to text
                        cells.append(self._render_to_text(ctx, cell_renderable))
                else:
                    cells.append(str(cell))

            table.add_row(*cells)

        return table

    def _render_to_text(self, ctx: CLIRunnerCtx, renderable: RenderableType) -> RichText:
        """Render complex renderable to RichText for table cell."""
        from rich.console import Console
        from rich.text import Text as RichText

        # Capture rendering
        temp_console = Console(width=40)  # Limit width for table cell
        with temp_console.capture() as capture:
            temp_console.print(renderable)

        return RichText(capture.get().strip())
```

### Container Components with Rich Panels

```python
from rich.panel import Panel
from rich.text import Text as RichText

class Card(UIBlock):
    """Card component - renders as Rich Panel in CLI."""

    def __init__(self, title: str, content: UIBlockType):
        super().__init__()
        self.title = title
        self.content = content

    def build(self, ctx: UIRunnerCtx) -> ft.Control:
        """GUI: Render as Flet Card."""
        # ... Flet Card implementation ...

    def build_cli(self, ctx: CLIRunnerCtx) -> RenderableType:
        """CLI: Render as Rich Panel."""
        # Build content
        content_renderable = ctx.build_child(self, self.content)

        # Wrap in panel
        return Panel(
            content_renderable,
            title=self.title,
            border_style="blue",
            padding=(1, 2)
        )


# Usage
ui(Card("User Info", "**Name:** Alice\n**Age:** 30"))
```

### Row/Column with Rich Layout

```python
from rich.columns import Columns
from rich.console import Group

class Row(UIBlock):
    def build_cli(self, ctx: CLIRunnerCtx) -> RenderableType:
        """CLI: Render as Rich Columns."""
        # Build all children
        renderables = []
        for child in self.children:
            renderable = ctx.build_child(self, child)
            renderables.append(renderable)

        # Return Rich Columns for horizontal layout
        return Columns(renderables, equal=True, expand=True)


class Column(UIBlock):
    def build_cli(self, ctx: CLIRunnerCtx) -> RenderableType:
        """CLI: Render as Rich Group (vertical)."""
        # Build all children
        renderables = []
        for child in self.children:
            renderable = ctx.build_child(self, child)
            renderables.append(renderable)

        # Return Rich Group for vertical layout
        return Group(*renderables)
```

### Interactive Components

```python
from rich.text import Text as RichText

class Button(UIBlock):
    def build_cli(self, ctx: CLIRunnerCtx) -> RenderableType:
        """CLI: Render as text indicator (buttons don't work in CLI)."""
        return RichText(f"[{self.text}]", style="dim")


class Link(UIBlock):
    def build_cli(self, ctx: CLIRunnerCtx) -> RenderableType:
        """CLI: Render as text with URL style."""
        return RichText(f"{self.text}", style="link https://example.com")
```

---

## Command Execution with Rich

```python
from rich.console import Console

class CLIRunner:
    def __init__(self, app_spec: AppSpec):
        super().__init__(app_spec)
        self.ctx = CLIRunnerCtx()

    def _run_command(self, command_callback: Callable) -> str:
        """Execute command and print with Rich."""
        # Create output list
        output_list: List[RenderableType] = []

        # Push onto stack
        self.ctx._ui_flow_stack.append(output_list)

        try:
            # Execute command - all ui() calls append to output_list
            command_callback()
        finally:
            self.ctx._ui_flow_stack.pop()

        # Print all collected output using Rich Console
        for renderable in output_list:
            self.ctx.console.print(renderable)

        # Capture output for cmd.out property
        output_text = self._capture_output(output_list)
        return output_text

    def _capture_output(self, renderables: List[RenderableType]) -> str:
        """Capture rendered output as plain text for cmd.out."""
        from rich.console import Console

        # Create console with capture
        capture_console = Console()
        with capture_console.capture() as capture:
            for renderable in renderables:
                capture_console.print(renderable)

        return capture.get()
```

---

## Benefits of Rich Integration

### 1. ✅ Full Rich Formatting

```python
# Markdown with Rich rendering
ui("# Header\n**bold** *italic* `code`")

# Tables with colors and styles
ui(Table(
    cols=["Name", "Status"],
    data=[["Alice", "✓ Active"], ["Bob", "✗ Inactive"]]
))

# Panels and borders
ui(Card("Info", "Content here"))
```

### 2. ✅ Consistent API

```python
class MyComponent(UIBlock):
    def build(self, ctx: UIRunnerCtx) -> ft.Control:
        """GUI rendering."""
        return ft.Text(...)

    def build_cli(self, ctx: CLIRunnerCtx) -> RenderableType:
        """CLI rendering with Rich."""
        return RichText(...)
```

### 3. ✅ Rich Features Available

- **Syntax highlighting** - Code blocks
- **Progress bars** - Long operations
- **Trees** - Hierarchical data
- **Live displays** - Real-time updates
- **Colors and styles** - Better UX
- **Tables** - Professional formatting
- **Panels** - Grouped content

### 4. ✅ Nested Components Work

```python
# Rich Table can contain RichText in cells
table = RichTable()
table.add_row(
    RichText("Name", style="bold"),
    RichText("Value", style="green")
)
```

---

## Advanced: Rich Live Display for Reactive Content

```python
from rich.live import Live

class DynamicBlock(UIBlock):
    def build_cli(self, ctx: CLIRunnerCtx) -> RenderableType:
        """CLI: Use Rich Live for reactive updates."""
        from rich.live import Live
        from rich.text import Text as RichText

        # Initial render
        initial = self._render_content(ctx)

        # In CLI, we can't really have reactive updates
        # But we could use Rich Live if we had a way to re-render
        # For now, just return static content
        return initial

    def _render_content(self, ctx: CLIRunnerCtx) -> RenderableType:
        """Render current state."""
        # Push temporary flow
        flow_list = []
        ctx._ui_flow_stack.append(flow_list)

        try:
            result = self.renderer()
            if result is not None:
                flow_list.append(ctx._build_component(result))
        finally:
            ctx._ui_flow_stack.pop()

        # Return Group of all renderables
        from rich.console import Group
        return Group(*flow_list) if len(flow_list) > 1 else flow_list[0]
```

---

## Type Annotations

```python
from rich.console import RenderableType
from typing import Union

# RenderableType already includes:
# - str
# - Text
# - Table
# - Panel
# - Markdown
# - Group
# - Columns
# - Any object with __rich__() or __rich_console__()

class UIBlock(ABC):
    @abstractmethod
    def build_cli(self, ctx: CLIRunnerCtx) -> RenderableType:
        """Return any Rich-compatible renderable."""
        pass
```

---

## Migration Path

### Phase 1: Basic Rich Support

```python
def build_cli(self, ctx: CLIRunnerCtx) -> RenderableType:
    return str(self.content)  # Still works! str is RenderableType
```

### Phase 2: Add Rich Formatting

```python
def build_cli(self, ctx: CLIRunnerCtx) -> RenderableType:
    from rich.text import Text as RichText
    return RichText(self.content, style="bold blue")
```

### Phase 3: Use Rich Components

```python
def build_cli(self, ctx: CLIRunnerCtx) -> RenderableType:
    from rich.table import Table as RichTable
    table = RichTable(...)
    return table
```

---

## Conclusion

**✅ Rich library integrates perfectly with build_cli() design!**

### Key Points

1. **Return `RenderableType`** - Rich's union type for any renderable
2. **Stack stores renderables** - `List[List[RenderableType]]`
3. **Console.print()** - Use Rich Console to print
4. **Full flexibility** - Components can use any Rich feature
5. **Gradual adoption** - Start with strings, add Rich features later
6. **Nested components** - Rich Table accepts RichText in cells

### Design Impact

**No changes needed to core architecture!**
- ✅ build_cli() pattern still works
- ✅ Stack pattern still works
- ✅ Hierarchy still works
- ✅ Just use `RenderableType` instead of `str`
- ✅ Use `Console` instead of `print()`

**Enhanced capabilities:**
- ✅ Professional table formatting
- ✅ Colors and styles
- ✅ Markdown rendering
- ✅ Panels and borders
- ✅ Progress bars and spinners
- ✅ Syntax highlighting

**The `build_cli()` design actually enables Rich's full power!**
