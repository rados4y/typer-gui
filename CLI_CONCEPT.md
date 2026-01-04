# CLI Rendering Concept

## Question: build_cli() vs show_cli()?

Should CLI rendering follow the same pattern as GUI (build/return), or use direct cascade printing?

---

## Option A: build_cli() Returns String (Consistent Pattern)

### Interface

```python
class UIBlock(ABC):
    @abstractmethod
    def build(self, ctx: UIRunnerCtx) -> ft.Control:
        """GUI: Build and return Flet control."""
        pass

    @abstractmethod
    def build_cli(self, ctx: CLIRunnerCtx) -> str:
        """CLI: Build and return string representation."""
        pass


class CLIRunnerCtx(UIRunnerCtx):
    def __init__(self):
        self._ui_flow_stack: List[List[str]] = []  # Stack of string lists

    def ui_flow_append(self, component: UIBlockType) -> None:
        """Append to current UI flow."""
        current_flow = self._ui_flow_stack[-1] if self._ui_flow_stack else None

        if current_flow is None:
            raise RuntimeError("No active UI flow")

        # Build string representation
        text = self._build_component(component)

        # Append to current flow (list of strings)
        current_flow.append(text)

    def build_child(self, parent: UIBlock, child: UIBlockType) -> str:
        """Build child and return string."""
        # Convert to UIBlock
        if isinstance(child, str):
            child_block = Md(child)
        elif isinstance(child, UIBlock):
            child_block = child
        elif callable(child):
            return self._build_callable(child)
        else:
            child_block = Text(str(child))

        # Establish parent-child relationship
        parent.add_child(child_block)
        child_block._ctx = self

        # Build CLI representation
        return child_block.build_cli(self)

    def _build_component(self, component: UIBlockType) -> str:
        """Build any component type to string."""
        if isinstance(component, str):
            return component
        elif isinstance(component, UIBlock):
            return component.build_cli(self)
        else:
            return str(component)
```

### Component Example

```python
class Text(UIBlock):
    def build(self, ctx: UIRunnerCtx) -> ft.Control:
        """GUI: Return Flet Text control."""
        return ft.Text(self.content)

    def build_cli(self, ctx: CLIRunnerCtx) -> str:
        """CLI: Return string."""
        return self.content


class Md(UIBlock):
    def build(self, ctx: UIRunnerCtx) -> ft.Control:
        """GUI: Return Flet Markdown control."""
        return ft.Markdown(self.content)

    def build_cli(self, ctx: CLIRunnerCtx) -> str:
        """CLI: Return plain text (strip markdown)."""
        text = self.content
        # Strip markdown formatting
        text = re.sub(r'\*\*([^*]+)\*\*', r'\1', text)
        text = re.sub(r'\*([^*]+)\*', r'\1', text)
        text = re.sub(r'^#+\s+(.+)$', lambda m: m.group(1).upper(), text, flags=re.MULTILINE)
        return text


class Table(UIBlock):
    def build(self, ctx: UIRunnerCtx) -> ft.Control:
        """GUI: Return Flet DataTable."""
        # ... create ft.DataTable ...

    def build_cli(self, ctx: CLIRunnerCtx) -> str:
        """CLI: Return ASCII table."""
        lines = []

        # Calculate column widths
        col_widths = [len(h) for h in self.cols]
        for row in self.data:
            for i, cell in enumerate(row):
                if isinstance(cell, UIBlock):
                    # Build nested component
                    cell_text = ctx.build_child(self, cell)
                else:
                    cell_text = str(cell)
                col_widths[i] = max(col_widths[i], len(cell_text))

        # Header
        header = " | ".join(h.ljust(col_widths[i]) for i, h in enumerate(self.cols))
        lines.append(header)
        lines.append("-" * len(header))

        # Rows
        for row in self.data:
            cells = []
            for i, cell in enumerate(row):
                if isinstance(cell, UIBlock):
                    cell_text = ctx.build_child(self, cell)
                else:
                    cell_text = str(cell)
                cells.append(cell_text.ljust(col_widths[i]))
            lines.append(" | ".join(cells))

        return "\n".join(lines)
```

### Command Execution

```python
class CLIRunner:
    def _run_command(self, command_callback: Callable) -> str:
        """Execute command and capture output."""
        # Create output list
        output_list: List[str] = []

        # Push onto stack
        self.ctx._ui_flow_stack.append(output_list)

        try:
            # Execute command - all ui() calls append strings to output_list
            command_callback()
        finally:
            self.ctx._ui_flow_stack.pop()

        # Print all collected output
        output_text = '\n'.join(output_list)
        print(output_text)

        # Return for cmd.out property
        return output_text
```

### Pros ✅

1. **Consistent pattern**: build() returns control, build_cli() returns string
2. **Easy to capture**: Output collected in list for cmd.out property
3. **Same stack pattern**: `List[List[str]]` same as GUI's `List[List[ft.Control]]`
4. **Testable**: Can collect output without stdout
5. **Clean separation**: Build vs print separated
6. **Nested components work**: build_child() returns string

### Cons ❌

1. **Extra method**: Components implement both build() and build_cli()
2. **No immediate output**: Collects then prints (not cascade)

---

## Option B: show_cli() Cascade Printing

### Interface

```python
class UIBlock(ABC):
    @abstractmethod
    def build(self, ctx: UIRunnerCtx) -> ft.Control:
        """GUI: Build and return Flet control."""
        pass

    @abstractmethod
    def show_cli(self, ctx: CLIRunnerCtx) -> None:
        """CLI: Print output directly (cascade)."""
        pass


class CLIRunnerCtx(UIRunnerCtx):
    def __init__(self):
        self._output_buffer: List[str] = []  # Buffer for cmd.out
        self._capture_mode: bool = False

    def ui_flow_append(self, component: UIBlockType) -> None:
        """Show component in CLI (prints immediately)."""
        # Convert to UIBlock
        if isinstance(component, str):
            component_block = Md(component)
        elif isinstance(component, UIBlock):
            component_block = component
        else:
            component_block = Text(str(component))

        # Show component (prints)
        component_block.show_cli(self)

    def print(self, text: str) -> None:
        """Print text and optionally capture for cmd.out."""
        print(text)  # Print immediately (cascade!)

        if self._capture_mode:
            self._output_buffer.append(text)

    def build_child(self, parent: UIBlock, child: UIBlockType) -> str:
        """Build child for nested components.

        Problem: For nested components (table cells), we need the string,
        not to print it immediately.

        Solution: Capture mode - temporarily buffer instead of print.
        """
        # Convert to UIBlock
        if isinstance(child, str):
            child_block = Md(child)
        elif isinstance(child, UIBlock):
            child_block = child
        else:
            child_block = Text(str(child))

        # Establish relationship
        parent.add_child(child_block)
        child_block._ctx = self

        # Capture output instead of printing
        self._capture_mode = True
        self._output_buffer.clear()

        try:
            child_block.show_cli(self)
        finally:
            self._capture_mode = False

        # Return captured output
        return '\n'.join(self._output_buffer)
```

### Component Example

```python
class Text(UIBlock):
    def build(self, ctx: UIRunnerCtx) -> ft.Control:
        """GUI: Return Flet Text control."""
        return ft.Text(self.content)

    def show_cli(self, ctx: CLIRunnerCtx) -> None:
        """CLI: Print text."""
        ctx.print(self.content)


class Table(UIBlock):
    def show_cli(self, ctx: CLIRunnerCtx) -> None:
        """CLI: Print ASCII table."""
        # ... build table ...

        for row in self.data:
            cells = []
            for cell in row:
                if isinstance(cell, UIBlock):
                    # build_child captures output (doesn't print)
                    cell_text = ctx.build_child(self, cell)
                else:
                    cell_text = str(cell)
                cells.append(cell_text.ljust(col_widths[i]))

            # Print row
            ctx.print(" | ".join(cells))
```

### Command Execution

```python
class CLIRunner:
    def _run_command(self, command_callback: Callable) -> str:
        """Execute command."""
        # Enable capture for cmd.out
        self.ctx._capture_mode = True
        self.ctx._output_buffer.clear()

        try:
            # Execute - prints cascade as components render
            command_callback()
        finally:
            self.ctx._capture_mode = False

        # Return captured output for cmd.out
        return '\n'.join(self.ctx._output_buffer)
```

### Pros ✅

1. **Cascade printing**: Immediate output as components render
2. **Different name**: show_cli() vs build() emphasizes different behavior
3. **Simpler components**: Just print, don't build/return
4. **Real-time feedback**: See output as it's generated

### Cons ❌

1. **Inconsistent pattern**: build() returns, show_cli() prints
2. **Capture mode hack**: Need special mode for nested components
3. **Complex context**: Needs _capture_mode flag and buffer management
4. **Testing harder**: Must capture stdout
5. **Mixed concerns**: Components call ctx.print() which does two things

---

## Option C: Unified build() with Polymorphism

### Interface

```python
class UIBlock(ABC):
    @abstractmethod
    def build(self, ctx: RunnerCtx) -> Any:
        """Build representation - ft.Control for GUI, str for CLI."""
        pass

    # Optional: Override for performance
    def _build_gui(self, ctx: GUIRunnerCtx) -> ft.Control:
        """GUI-specific build."""
        pass

    def _build_cli(self, ctx: CLIRunnerCtx) -> str:
        """CLI-specific build."""
        pass
```

### Component Example

```python
class Text(UIBlock):
    def build(self, ctx: RunnerCtx) -> Any:
        """Build based on context type."""
        if isinstance(ctx, GUIRunnerCtx):
            return ft.Text(self.content)
        else:  # CLIRunnerCtx
            return self.content


# Or with helper methods
class Table(UIBlock):
    def build(self, ctx: RunnerCtx) -> Any:
        if isinstance(ctx, GUIRunnerCtx):
            return self._build_gui(ctx)
        else:
            return self._build_cli(ctx)

    def _build_gui(self, ctx: GUIRunnerCtx) -> ft.Control:
        # ... return ft.DataTable ...

    def _build_cli(self, ctx: CLIRunnerCtx) -> str:
        # ... return ASCII table ...
```

### Pros ✅

1. **Single method name**: Just build()
2. **Polymorphic**: Behavior based on context type

### Cons ❌

1. **Type checking needed**: if isinstance(ctx, GUIRunnerCtx)
2. **Mixed concerns**: GUI and CLI logic in same method
3. **Return type ambiguous**: Any (could be ft.Control or str)
4. **Less clear**: Not obvious what it returns

---

## Recommendation

**Option A: build_cli() Returns String**

### Rationale

1. **✅ Consistent**: Same pattern as GUI (build → return → collect → use)
2. **✅ Clean**: Separate methods for GUI vs CLI
3. **✅ Simple context**: No capture mode, no special flags
4. **✅ Easy nesting**: build_child() returns string directly
5. **✅ Testable**: Output in list, no stdout capture needed
6. **✅ cmd.out works**: Easy to collect all output

### Trade-off

- ❌ Not cascade printing (prints at end, not during execution)
- But this is acceptable since:
  - CLI commands are typically fast
  - Collecting then printing is simpler
  - Can add streaming later if needed via print hooks

### Final Interface

```python
class UIBlock(ABC):
    # GUI
    def build(self, ctx: UIRunnerCtx) -> ft.Control:
        """Build Flet control."""
        pass

    # CLI
    def build_cli(self, ctx: CLIRunnerCtx) -> str:
        """Build string representation."""
        pass

    # Hierarchy (shared)
    parent: Optional[UIBlock]
    children: List[UIBlock]
    def add_child(child) -> None
    def get_root() -> UIBlock
    def update() -> None
```

---

## Alternative: Hybrid Approach

If cascade printing is important:

```python
class CLIRunnerCtx:
    def __init__(self, stream_output: bool = False):
        self._stream_output = stream_output
        self._ui_flow_stack: List[List[str]] = []

    def ui_flow_append(self, component: UIBlockType) -> None:
        current_flow = self._ui_flow_stack[-1]

        # Build string
        text = self._build_component(component)

        # Collect
        current_flow.append(text)

        # Optionally stream
        if self._stream_output:
            print(text)
```

This allows:
- Default: Collect then print (for testing, cmd.out)
- Stream mode: Print immediately (for long commands)

**Still uses build_cli() pattern, just adds streaming option.**
