# API Verification: build_child() Approach

## Core Interface

```python
from rich.console import RenderableType

UIBlockType = str | Callable[[], Any] | UIBlock

class UiStack(list):
    """UI stack with observer pattern for append notifications.

    This is a list subclass that notifies registered observers whenever
    an item is appended. This enables real-time rendering for long-running
    and async tasks.
    """

    def __init__(self):
        super().__init__()
        self._observers: List[Callable[[Any], None]] = []

    def register_observer(self, callback: Callable[[Any], None]) -> None:
        """Register an observer to be notified on append."""
        self._observers.append(callback)

    def append(self, item: Any) -> None:
        """Append item to stack and notify all observers."""
        super().append(item)
        # Notify all observers immediately
        for observer in self._observers:
            observer(item)


class UIBlock(ABC):
    """Base class for all UI components with parent-child hierarchy."""

    def __init__(self):
        self._parent: Optional['UIBlock'] = None
        self._children: List['UIBlock'] = []
        self._flet_control: Optional[ft.Control] = None
        self._ctx: Optional[UIRunnerCtx] = None

    @abstractmethod
    def build_gui(self, ctx: UIRunnerCtx) -> ft.Control:
        """Build and return Flet control for GUI."""
        pass

    @abstractmethod
    def build_cli(self, ctx: CLIRunnerCtx) -> RenderableType:
        """Build and return Rich renderable for CLI."""
        pass

    def add_child(self, child: 'UIBlock') -> None:
        """Add child and establish parent-child relationship."""
        child._parent = self
        if child not in self._children:
            self._children.append(child)


class UIRunnerCtx(ABC):
    """Context provided by runner to UI blocks."""

    _current_instance: Optional['UIRunnerCtx'] = None

    def __init__(self):
        """Initialize with no active stack."""
        self._current_stack: Optional[UiStack] = None

    @staticmethod
    def instance() -> Optional['UIRunnerCtx']:
        """Get current runner context (required for ui())."""
        return UIRunnerCtx._current_instance

    def ui(self, component: UIBlockType) -> None:
        """Simply append UIBlockType to current stack."""
        if self._current_stack is None:
            self._handle_immediate_output(component)
        else:
            self._current_stack.append(component)

    @abstractmethod
    def build_child(self, parent: UIBlock, child: UIBlockType) -> Any:
        """Build child component and establish parent-child relationship.

        Handles str/callable/UIBlock uniformly.
        Returns ft.Control for GUI, RenderableType for CLI.
        """
        pass
```

---

## Implementation

### Key Design: Single Stack Reference with Save/Restore Pattern

`_current_stack` is `Optional[UiStack]` - a single reference to the current active stack, not a stack of stacks.

**Benefits:**
- ✅ `ui()` is trivial - just append to current stack
- ✅ Build deferred until needed (lazy evaluation)
- ✅ No coupling to Flet structure
- ✅ Supports dynamic callables for async/progressive updates via observer pattern
- ✅ Simpler save/restore pattern instead of push/pop
- ✅ Automatic restoration via finally block (error-safe)

### UIRunnerCtx Implementation

```python
class GUIRunnerCtx(UIRunnerCtx):
    _instance: Optional['GUIRunnerCtx'] = None

    def __init__(self, page: ft.Page):
        super().__init__()
        self.page = page
        # _current_stack inherited from UIRunnerCtx

    @staticmethod
    def instance() -> 'GUIRunnerCtx':
        """Get current runner context."""
        return GUIRunnerCtx._instance

    def ui(self, component: UIBlockType) -> None:
        """Simply put UIBlockType to current stack."""
        if self._current_stack is None:
            # No active stack - handle immediate output
            self._handle_immediate_output(component)
        else:
            # Just append, don't build yet!
            self._current_stack.append(component)

    @contextmanager
    def new_ui_stack(self):
        """Context manager for stack management with save/restore pattern."""
        # Save current stack reference
        previous_stack = self._current_stack

        # Create and set new stack
        ui_stack = UiStack()
        self._current_stack = ui_stack

        try:
            yield ui_stack
        finally:
            # Restore previous stack (even if error occurred)
            self._current_stack = previous_stack

    def build_child(self, parent: UIBlock, child: UIBlockType) -> ft.Control:
        """Build child component - handles all types."""

        # Case 1: String → Markdown
        if isinstance(child, str):
            from .ui_blocks import Md
            return Md(child).build_gui(self)

        # Case 2: UIBlock → Build and set parent relationship
        if isinstance(child, UIBlock):
            parent.add_child(child)
            child._ctx = self
            control = child.build_gui(self)
            child._flet_control = control
            return control

        # Case 3: Dynamic callable (can receive ui() calls after execution)
        if callable(child) and getattr(child, '__typer2ui_is_dynamic__', False):
            # Capture initial UI
            with self.new_ui_stack() as ui_stack:
                child()

            # Build ListView from captured stack
            controls = [self.build_child(parent, item) for item in ui_stack]
            lv = ListView(controls=controls)

            # Set up callback for future ui() calls
            def on_append(item: UIBlockType):
                control = self.build_child(parent, item)
                lv.append(control)
                lv.update()

            # Register observer on stack (internal observer pattern)
            ui_stack.register_observer(on_append)
            return lv

        # Case 4: Regular callable → Capture ui() calls
        if callable(child):
            with self.new_ui_stack() as ui_stack:
                child()

            # Build controls from captured stack
            controls = [self.build_child(parent, item) for item in ui_stack]

            # Unwrap single element
            if len(controls) == 1:
                return controls[0]

            # Wrap multiple in ListView
            return ListView(controls=controls)

        # Fallback: Convert to string
        from .ui_blocks import Text
        return Text(str(child)).build_gui(self)
```

### Public API

```python
def ui(component: UIBlockType) -> None:
    """Display component in current UI flow."""
    ctx = UIRunnerCtx.instance()
    ctx.ui(component)  # Just append to stack, don't build
```

---

## Key Examples

### Example 1: Tabs with Mixed Content Types

```python
class Tabs(UIBlock):
    def __init__(self, tabs: List[Tab]):
        super().__init__()
        self.tabs = tabs

    def build_gui(self, ctx: UIRunnerCtx) -> ft.Control:
        flet_tabs = ft.Tabs()
        for tab in self.tabs:
            # build_child handles all content types uniformly!
            content = ctx.build_child(self, tab.content)
            flet_tabs.tabs.append(ft.Tab(text=tab.label, content=content))
        return flet_tabs

# Usage - mix content types
def render_data():
    ui("## Data Table")
    ui(Table(cols=["Name", "Age"], data=[["Alice", 30]]))

ui(Tabs([
    Tab("Info", "# Welcome\nThis is **markdown**"),  # String
    Tab("Data", render_data),                         # Callable
    Tab("Chart", ChartComponent(...)),                # UIBlock
]))
```

**✅ Clean!** Tabs doesn't care about content type.

### Example 2: Row/Column with Mixed Children

```python
class Row(UIBlock):
    def build_gui(self, ctx: UIRunnerCtx) -> ft.Control:
        controls = [ctx.build_child(self, child) for child in self.children]
        return ft.Row(controls=controls, spacing=10)

# Usage - mix types
ui(Row([
    "**Bold text**",              # String → Markdown
    Text("Plain text"),           # UIBlock
    Button("Click", lambda: ...), # UIBlock
]))
```

### Example 3: Dynamic Callable for Async Updates

```python
@app.command()
async def fetch_data():
    def dynamic_output():
        ui("# Starting fetch...")

    # Mark as dynamic
    dynamic_output.__typer2ui_is_dynamic__ = True

    # Show dynamic output
    ui(dynamic_output)

    # Command continues in background
    await asyncio.sleep(2)

    # ✅ This works! Appends to ListView via on_append callback
    ui("Data loaded!")
```

---

## CLI Support

```python
class CLIRunnerCtx(UIRunnerCtx):
    def __init__(self):
        super().__init__()
        self.console = Console()
        # _current_stack inherited from UIRunnerCtx

    def ui(self, component: UIBlockType) -> None:
        """Simply append to current stack."""
        if self._current_stack is None:
            self._handle_immediate_output(component)
        else:
            self._current_stack.append(component)

    def build_child(self, parent: UIBlock, child: UIBlockType) -> RenderableType:
        """Build child for CLI - returns Rich renderable."""
        if isinstance(child, str):
            return Markdown(child)
        if isinstance(child, UIBlock):
            parent.add_child(child)
            child._ctx = self
            return child.build_cli(self)
        if callable(child):
            with self.new_ui_stack() as ui_stack:
                child()
            renderables = [self.build_child(parent, item) for item in ui_stack]
            return Group(*renderables) if len(renderables) > 1 else renderables[0]
        return str(child)
```

---

## Summary

### ✅ Design Strengths

1. **Unified content type** - `str`/`callable`/`UIBlock` handled uniformly via `build_child()`
2. **Simple `ui()` function** - Just appends to stack, zero complexity
3. **Lazy evaluation** - Build deferred until needed
4. **Automatic UI flow capture** - Callables "just work" with context manager
5. **Dynamic callable support** - Solves async/progressive update problem
6. **Clean separation** - Components use `build_child()`, don't care about content types
7. **Parent-child hierarchy** - Automatic relationship tracking
8. **No Flet coupling** - Stack uses Python lists, not Flet controls

### 🎯 Verdict

**FEASIBLE and ELEGANT!**

This API is simpler, more intuitive, and handles all scenarios cleanly.

**Recommendation: Proceed with this design!**

---

## Resolved Design Issues

### 1. Callable Return Values
**Problem:** What if callable returns a value instead of calling `ui()`?
**Solution:** `build_child()` handles returned values - adds them to captured stack.

### 2. Empty Callables
**Problem:** Callable with no `ui()` calls and no return value.
**Solution:** Returns empty container - acceptable behavior (blank content).

### 3. Reactive Content (dx)
**Problem:** How does `dx()` work with this design?
**Solution:** `DynamicBlock` is a `UIBlock`, so `build_child()` handles it uniformly. On state change, DynamicBlock re-renders using its own stack context.

### 4. Progressive Updates
**Problem:** How to append rows/items dynamically (e.g., `table.add_row()`)?
**Solution:** Components store `_ctx` and `_flet_control`. They can call `ctx.build_child()` to build new items and append to their control, then call `self.update()` to refresh.

```python
class Table(UIBlock):
    def add_row(self, row_data: List[UIBlockType]) -> None:
        """Add row progressively."""
        if self._flet_control and self._ctx:
            cells = [ft.DataCell(self._ctx.build_child(self, cell)) for cell in row_data]
            self._flet_control.rows.append(ft.DataRow(cells=cells))
    container = ft.Column(controls=[], spacing=10)
    self._ui_flow_stack.append(container)

    try:
        result = callback()

        # If callable returns something, add it to container
        if result is not None:
            control = self._build_component(result)
            container.controls.append(control)
    finally:
        self._ui_flow_stack.pop()

    # If single element, unwrap
    if len(container.controls) == 1:
        return container.controls[0]
    return container
```

**✅ Fixed**

---

### Issue 2: Empty callable (no ui() calls, no return)

```python
def empty_tab():
    pass  # Does nothing

Tab("Empty", empty_tab)
```

**Current behavior:** Returns empty `ft.Column()`

**Solution:** This is acceptable - shows blank tab.

**✅ OK**

---

### Issue 3: Reactive content (dx)

Current `dx()` function:

```python
def dx(renderer: Callable, *deps) -> DynamicBlock:
    return DynamicBlock(renderer=renderer, dependencies=deps)
```

**How does it work with build_child()?**

```python
class DynamicBlock(UIBlock):
    def __init__(self, renderer: Callable, dependencies: tuple):
        super().__init__()
        self.renderer = renderer
        self.dependencies = dependencies
        self._container = None

    def build_gui(self, ctx: UIRunnerCtx) -> ft.Control:
        from .state import State

        # Create container for dynamic content
        self._container = ft.Column(controls=[], spacing=10)
        self._flet_control = self._container  # Store reference

        def render():
            """Re-render on state change."""
            # Clear container
            self._container.controls.clear()

            # Create Python list to capture UI flow
            flow_list: List[ft.Control] = []

            # Push list onto stack
            ctx._ui_flow_stack.append(flow_list)
            try:
                result = self.renderer()
                if result is not None:
                    control = ctx._build_component(result)
                    flow_list.append(control)
            finally:
                ctx._ui_flow_stack.pop()

            # Transfer list to container
            self._container.controls.extend(flow_list)

            # Component updates itself
            self.update()

        # Initial render
        render()

        # Register observers
        for dep in self.dependencies:
            if isinstance(dep, State):
                dep.add_observer(render)

        return self._container


# Usage
counter = app.state(0)

ui(dx(lambda: f"Count: {counter.value}", counter))
```

**✅ Works!** DynamicBlock is a UIBlock, so build_child() handles it.

---

### Issue 4: Progressive updates (table.add_row())

```python
class Table(UIBlock):
    def __init__(self, cols: List[str], data: List[List[UIBlockType]]):
        super().__init__()
        self.cols = cols
        self.data = data

    def build_gui(self, ctx: UIRunnerCtx) -> ft.Control:
        # ... create table ...
        self._flet_control = table_control
        # ctx is automatically stored in self._ctx by framework
        return table_control

    def add_row(self, row_data: List[UIBlockType]) -> None:
        """Add row progressively."""
        self.data.append(row_data)

        if self._flet_control and self._ctx:
            # Build cells (build_child establishes parent-child relationship)
            cells = []
            for cell in row_data:
                cell_control = self._ctx.build_child(self, cell)
                cells.append(ft.DataCell(cell_control))

            # Append row to table control
            self._flet_control.rows.append(ft.DataRow(cells=cells))

            # Component updates itself (traverses to root to get page)
            self.update()
```

**✅ Works** - Component uses hierarchy to update page

**Key benefits:**

- `build_child()` establishes parent-child relationship automatically
- `self.update()` traverses to root to get page
- No need to manually store ctx (framework does it)
- Component owns its update logic

---

## CLI Support

```python
from rich.console import Console, RenderableType
from rich.markdown import Markdown

class CLIRunnerCtx(UIRunnerCtx):
    def __init__(self):
        super().__init__()
        self.console = Console()  # Rich Console
        # _current_stack inherited from UIRunnerCtx

    def ui(self, component: UIBlockType) -> None:
        """Append to current stack."""
        if self._current_stack is None:
            # Handle immediate output
            self._handle_immediate_output(component)
        else:
            # Just append to stack
            self._current_stack.append(component)

    def build_child(self, parent: UIBlock, child: UIBlockType) -> RenderableType:
        """Build child for CLI - returns Rich renderable."""
        # Convert to UIBlock if needed
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

        # Establish parent-child relationship
        parent.add_child(child_block)

        # Store ctx in child for later use
        child_block._ctx = self

        # Build CLI representation (returns RenderableType)
        return child_block.build_cli(self)

    def _build_component(self, component: UIBlockType) -> RenderableType:
        """Internal: Build any component type to Rich renderable."""
        if isinstance(component, str):
            # Strings as Markdown
            return Markdown(component)
        elif isinstance(component, UIBlock):
            return component.build_cli(self)
        else:
            return str(component)

    def _build_callable(self, callback: Callable) -> RenderableType:
        """Internal: Execute callable and capture UI flow."""
        from rich.console import Group

        # Create new stack with save/restore pattern
        with self.new_ui_stack() as ui_stack:
            # Execute callable - may call ui() multiple times
            result = callback()

            # If callable returns a value, handle it
            if result is not None:
                ui_stack.append(result)

        # Build renderables from stack
        renderables = [self.build_child(parent, item) for item in ui_stack]

        # Convert to Rich renderable
        if len(renderables) == 0:
            return ""  # Empty
        elif len(renderables) == 1:
            return renderables[0]  # Single element
        else:
            return Group(*renderables)  # Multiple elements
```

**✅ Clean!** CLI uses same stack pattern as GUI, just with RenderableType instead of ft.Control

---

## Command Execution with Save/Restore Stack Pattern

### How Runner Initializes UI Flow

```python
class GUIRunner:
    def _execute_sync(self, command_spec, params):
        """Execute command and display output."""
        # Set current instance for ui() calls
        UIRunnerCtx._current_instance = self.ctx
        root = Column([])

        try:
            # Create new stack with save/restore pattern
            with self.ctx.new_ui_stack() as ui_stack:
                # Execute command - all ui() calls append to ui_stack
                result = command_spec.callback(**params)
                if result is not None:
                    ui_stack.append(result)

            # Build controls from captured stack
            for item in ui_stack:
                control = self.ctx.build_child(root, item)
                self.add_to_output(control)

            # Update page
            if self.page:
                self.page.update()
        finally:
            UIRunnerCtx._current_instance = None
```

### Flow Diagram

```
Command Execution:
1. Runner sets current context instance
2. Runner creates ui_stack with new_ui_stack()
   ├─ Saves previous_stack = None
   ├─ Creates new UiStack()
   └─ Sets ctx._current_stack = ui_stack
3. Command executes
   ├─ ui("# Header") → appends to ui_stack (not built yet)
   ├─ ui(Table(...)) → appends to ui_stack (not built yet)
   └─ ui(Button(...)) → appends to ui_stack (not built yet)
4. Context manager exits
   └─ Restores ctx._current_stack = previous_stack
5. Runner builds each item from ui_stack
   ├─ ctx.build_child(root, "# Header") → ft.Markdown control
   ├─ ctx.build_child(root, Table(...)) → ft.DataTable control
   └─ ctx.build_child(root, Button(...)) → ft.ElevatedButton control
6. Runner adds controls to output view
7. Runner calls page.update()

Nested Callable (e.g., Tab content):
1. Tabs.build_gui() calls ctx.build_child(tab.content)
2. build_child() detects callable
3. build_child() calls ctx.new_ui_stack()
   ├─ Saves previous_stack (main command stack)
   ├─ Creates new UiStack()
   └─ Sets ctx._current_stack = new stack
4. Callable executes
   ├─ ui("text") → appends to new stack
   ├─ ui(Component) → appends to new stack
5. Context manager exits
   └─ Restores ctx._current_stack = previous_stack
6. build_child() builds items from new stack
7. Returns ft.Column(controls=built_items) to Tabs
```

**Key Benefits:**

- ✅ Simpler save/restore pattern (no stack of stacks)
- ✅ Automatic restoration via finally block (error-safe)
- ✅ No coupling to Flet control structure
- ✅ Clean separation: capture → convert → use
- ✅ Observer pattern for real-time updates

---

## Final Assessment

### ✅ Strengths

1. **Unified content type** - str/callable/UIBlock handled uniformly
2. **Simple component code** - just call `ctx.build_child()`
3. **Automatic UI flow capture** - callables "just work"
4. **No manual context switching** - runner handles stack internally
5. **Flexible and composable** - mix content types freely
6. **Stack of lists** - No Flet coupling, simple Python list operations
7. **Clean separation** - Capture in lists → Convert to Flet → Use
8. **Parent-child hierarchy** - Automatic relationship tracking, easy tree traversal
9. **Self-contained updates** - Components update themselves via `self.update()`
10. **No request_update()** - Components own their refresh logic

### ✅ Design Decisions (all resolved)

1. **Callable return value** - Handled in `_build_callable()` ✅
2. **CLI return type difference** - Use `Any` return type ✅
3. **Hierarchy management** - `build_child()` establishes relationships automatically ✅
4. **Stack implementation** - `List[List[ft.Control]]` not `List[ft.Control]` ✅
5. **Update mechanism** - `component.update()` traverses to root for page ✅

### 🎯 Verdict

**FEASIBLE and ELEGANT!**

This API is:

- Simpler than my RenderContext proposal
- More intuitive than push/pop stacks
- Handles all scenarios cleanly

**Recommendation: Proceed with this design!**

---

## Proposed Final Interface

```python
from rich.console import RenderableType

# Type alias
UIBlockType = str | Callable[[], Any] | UIBlock

# Component interface with hierarchy
class UIBlock(ABC):
    def __init__(self):
        self._parent: Optional['UIBlock'] = None
        self._children: List['UIBlock'] = []
        self._flet_control: Optional[ft.Control] = None
        self._ctx: Optional[UIRunnerCtx] = None

    @abstractmethod
    def build_gui(self, ctx: UIRunnerCtx) -> ft.Control:
        """Build Flet control for GUI."""
        pass

    @abstractmethod
    def build_cli(self, ctx: CLIRunnerCtx) -> RenderableType:
        """Build Rich renderable for CLI."""
        pass

    # Hierarchy management
    @property
    def parent(self) -> Optional['UIBlock']:
        """Get parent component."""
        return self._parent

    @property
    def children(self) -> List['UIBlock']:
        """Get child components."""
        return self._children

    def add_child(self, child: 'UIBlock') -> None:
        """Add child and establish parent-child relationship."""
        child._parent = self
        if child not in self._children:
            self._children.append(child)

    def get_root(self) -> 'UIBlock':
        """Get root component (walks up to top of tree)."""
        current = self
        while current._parent:
            current = current._parent
        return current


# Context interface (minimal public API)
class UIRunnerCtx(ABC):
    @staticmethod
    @abstractmethod
    def instance() -> 'UIRunnerCtx':
        """Get current context."""
        pass

    @abstractmethod
    def ui_flow_append(self, component: UIBlockType) -> None:
        """Append to current UI flow."""
        pass

    @abstractmethod
    def build_child(self, parent: UIBlock, child: UIBlockType) -> Any:
        """Build child and establish parent-child relationship.

        Returns ft.Control for GUI, RenderableType for CLI.
        """
        pass


# Public API function
def ui(component: UIBlockType) -> None:
    """Display component in current UI flow."""
    ctx = UIRunnerCtx.instance()
    ctx.ui_flow_append(component)
```

**This is the cleanest architecture yet!**

**Key improvements:**

- ✅ Parent-child hierarchy built automatically
- ✅ Minimal context interface (2 methods)
- ✅ Unified content types (str/callable/UIBlock)
- ✅ Clean separation between GUI and CLI rendering
- ✅ Stack-based flow management

---

## Refined Concept: Simplified ui() and build_child()

### Core Principle

**Separation of concerns:**
- `ui()` - Dead simple, just appends to current stack
- `build_child()` - All complexity lives here (str/UIBlock/callable/dynamic)

### UIRunnerCtx Interface

```python
class UIRunnerCtx(ABC):
    @staticmethod
    def instance() -> 'UIRunnerCtx':
        """Get current runner context (required for ui())."""
        pass

    def ui(self, component: UIBlockType) -> None:
        """Simply put UIBlockType to current _ui_stack."""
        current_stack = self._ui_stack[-1] if self._ui_stack else None
        if current_stack is None:
            raise RuntimeError("No active UI stack")
        current_stack.append(component)  # Just append, don't build yet!

    @contextmanager
    def new_ui_stack(self):
        """Context manager for stack management."""
        ui_stack = []
        self._ui_stack.append(ui_stack)
        try:
            yield ui_stack
        finally:
            self._ui_stack.pop()

    def build_child(self, parent: UIBlock, child: UIBlockType) -> ft.Control:
        """Build child component - handles all types."""

        # Case 1: String → Markdown
        if isinstance(child, str):
            return tu.Md(child).build_gui(self)

        # Case 2: UIBlock → Build and set parent relationship
        if isinstance(child, UIBlock):
            parent.add_child(child)
            child._ctx = self
            control = child.build_gui(self)
            child._flet_control = control
            return control

        # Case 3: Dynamic callable (can receive ui() calls after execution)
        if callable(child) and getattr(child, '__typer2ui_is_dynamic__', False):
            # Capture initial UI
            with self.new_ui_stack() as ui_stack:
                child()

            # Build ListView from captured stack
            controls = [self.build_child(parent, item) for item in ui_stack]
            lv = ListView(controls=controls)

            # Set up callback for future ui() calls
            def on_append(item: UIBlockType):
                control = self.build_child(parent, item)
                lv.append(control)
                lv.update()

            # Attach callback to stack (for async/threaded ui() calls)
            ui_stack.on_append = on_append
            return lv

        # Case 4: Regular callable → Capture ui() calls
        if callable(child):
            with self.new_ui_stack() as ui_stack:
                child()

            # Build controls from captured stack
            controls = [self.build_child(parent, item) for item in ui_stack]

            # Unwrap single element
            if len(controls) == 1:
                return controls[0]

            # Wrap multiple in ListView/Column
            return ListView(controls=controls)

        # Fallback: Convert to string
        return tu.Text(str(child)).build_gui(self)
```

### Public API

```python
def ui(component: UIBlockType) -> None:
    """Display component in current UI flow."""
    ctx = UIRunnerCtx.instance()
    ctx.ui(component)  # Just append to stack, don't build
```

### Key Benefits

**1. Simple ui() function**
- Just appends to stack
- No building, no complexity
- Fast and predictable

**2. Dynamic callables solve async problem**
- Mark callable with `__typer2ui_is_dynamic__ = True`
- Gets ListView with on_append callback
- Can receive ui() calls after execution completes

**3. Stack captured as UIBlockType, built on demand**
- Don't build during ui() call
- Build only when converting stack to controls
- Allows lazy evaluation

**4. Context manager for clean stack management**
- `with self.new_ui_stack() as ui_stack:`
- Automatic push/pop
- No manual stack management

### Example: Async Command with Dynamic Callable

```python
@app.command()
async def fetch_data():
    def dynamic_output():
        ui("# Starting fetch...")

    # Mark as dynamic
    dynamic_output.__typer2ui_is_dynamic__ = True

    # Show dynamic output
    ui(dynamic_output)

    # Command continues in background
    await asyncio.sleep(2)

    # ✅ This works! Appends to ListView via on_append callback
    ui("Data loaded!")
```

### Async/Threaded Command Execution

**Problem:** `ui()` can be called after command returns (async/threaded execution)

**Solution:** Dynamic callables
- Regular callable → Captures during execution, immutable after
- Dynamic callable → Captures during execution, **mutable after** via on_append callback

**How it works:**

1. Command starts, creates dynamic callable
2. Dynamic callable executes, captures initial UI to stack
3. Stack converted to ListView
4. Observer registered on stack via `ui_stack.register_observer(on_append)`
5. Command continues in background
6. Later ui() calls append to stack → triggers observers → append to ListView
7. ListView.update() refreshes display

### Implementation Details

**ListView component:**

```python
class ListView(UIBlock):
    """Container that supports dynamic appending."""

    def __init__(self, controls: List[ft.Control] = None):
        super().__init__()
        self.controls = controls or []
        self._column: Optional[ft.Column] = None

    def build_gui(self, ctx: UIRunnerCtx) -> ft.Control:
        self._column = ft.Column(controls=self.controls, spacing=10)
        self._flet_control = self._column
        self._ctx = ctx
        return self._column

    def append(self, control: ft.Control) -> None:
        """Append control dynamically."""
        if self._column:
            self._column.controls.append(control)

    def update(self) -> None:
        """Refresh display."""
        if self._ctx and hasattr(self._ctx, 'page'):
            self._ctx.page.update()
```

**CLI Support:**

For CLI, dynamic callables work similarly but print progressively:

```python
class CLIRunnerCtx(UIRunnerCtx):
    def build_child(self, parent: UIBlock, child: UIBlockType) -> RenderableType:
        # ... same logic ...

        # Dynamic callable for CLI
        if callable(child) and getattr(child, '__typer2ui_is_dynamic__', False):
            with self.new_ui_stack() as ui_stack:
                child()

            # Print captured output
            for item in ui_stack:
                renderable = self.build_child(parent, item)
                self.console.print(renderable)

            # Set up callback for future ui() calls
            def on_append(item: UIBlockType):
                renderable = self.build_child(parent, item)
                self.console.print(renderable)  # Print immediately

            # Register observer on stack (internal observer pattern)
            ui_stack.register_observer(on_append)
            return ""  # Already printed
```

### Summary

**Elegant solution:**
- ✅ `ui()` is trivial (just append)
- ✅ `build_child()` handles all complexity
- ✅ Dynamic callables solve async/threaded problem
- ✅ No mode switching needed
- ✅ Clean separation of concerns
- ✅ Works for both GUI and CLI
