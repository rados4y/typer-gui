# Typer-UI API Refactoring Concept

## Executive Summary

Refactor the API to be cleaner and more intuitive by:

1. **Renaming `Ui` → `UiApp`** - Clearer semantic meaning
2. **Creating standalone functions** - `ui()`, `md()`, `dx()` at module level
3. **Removing deprecated code** - Clean up legacy methods and parameters
4. **Simplifying the mental model** - Separate app configuration from output functions

---

## Current API (Before)

```python
import typer
import typer_ui as tg

app = typer.Typer()
ui = tg.Ui(app, title="My App")

@ui.def_command(long=True)
def my_command():
    # Output methods
    ui(tg.Text("Hello"))
    ui(tg.Md("**Bold**"))
    ui()  # Empty line
    ui("Auto markdown")  # Shortcut

    # Reactive/dynamic
    state = ui.state(0)
    ui(lambda: tg.Text(f"Count: {state.value}"), state)

    # Command control
    other = ui.command("other_command")
    other.run()

if __name__ == "__main__":
    ui.app()
```

**Issues:**

- Conflates app configuration (`ui = tg.Ui()`) with output (`ui(...)`)
- `ui` variable serves two purposes (object with methods, callable for output)
- Reactive syntax is unclear: `ui(lambda: ..., state)` - hard to read
- No clear distinction between static and dynamic content

---

## Proposed API (After)

```python
import typer
from typer_ui import UiApp, ui, md, dx

typer_app = typer.Typer()
app = UiApp(typer_app, title="My App")

@app.def_command(long=True)
def my_command():
    # Output functions (module-level)
    ui("Hello")  # Auto-converts to Text
    md("**Bold**")  # Shortcut for Markdown
    ui()  # Empty line

    # Explicit UI components
    ui(tg.Table(cols=["A", "B"], data=[[1, 2]]))

    # Dynamic content - clear and explicit
    state = app.state(0)
    ui(dx(lambda: f"Count: {state.value}", state))

    # Command control (unchanged)
    other = app.command("other_command")
    other.run()

if __name__ == "__main__":
    app.run()  # Or keep as app.app() for consistency
```

**Benefits:**ad

- Clear separation: `app` for configuration, `ui/md/dx` for output
- More intuitive: `ui("text")` instead of `ui(tg.Text("text"))`
- Explicit dynamic blocks: `dx(renderer, state)` is self-documenting
- Cleaner namespace: `from typer_ui import UiApp, ui, md, dx`

---

## Detailed Design

### 1. UiApp Class (renamed from Ui)

**File:** `typer_ui/ui_app.py` (renamed from `ui.py`)

```python
class UiApp:
    """Application wrapper for Typer CLI with GUI support."""

    def __init__(self, typer_app: typer.Typer, title: str = "App", description: str = ""):
        """Initialize UI application.

        Args:
            typer_app: Typer application instance
            title: Application title for GUI
            description: Application description for GUI
        """
        self.typer_app = typer_app
        self.title = title
        self.description = description
        self._app_spec = None

    # Command configuration
    def def_command(
        self,
        *,
        button: bool = False,
        long: bool = False,
        auto: bool = False,
        header: bool = True,
        submit_name: str = "Run Command",
        on_select: Optional[Callable] = None,
    ) -> Callable:
        """Decorator to configure command GUI options."""
        # Implementation same as current Ui.def_command()
        # REMOVE deprecated parameters (is_button, is_long, is_auto_exec)

    # State management
    def state(self, initial_value: Any) -> State:
        """Create a reactive state object."""
        return State(initial_value)

    # Command access
    def command(self, name: Optional[str] = None) -> UICommand:
        """Get UICommand wrapper for programmatic control."""
        # Implementation same as current Ui.command()

    @property
    def commands(self) -> List[UICommand]:
        """Get all commands as UICommand wrappers."""
        # Implementation same as current Ui.commands

    # Application lifecycle
    def run(self) -> None:
        """Launch the application (GUI or CLI based on --cli flag)."""
        # Implementation same as current Ui.app()
        # CONSIDER: rename app() → run() for clarity

    # Utility methods
    def clipboard(self, text: str) -> None:
        """Copy text to clipboard."""
        # Implementation same as current Ui.clipboard()

    @property
    def is_cli_mode(self) -> bool:
        """Check if running in CLI mode."""
        # Implementation same as current Ui.is_cli_mode

    # REMOVE: __call__ method (replaced by standalone ui())
    # REMOVE: out() method (deprecated)
    # REMOVE: _to_component() method (not needed)
```

### 2. Standalone ui() Function

**File:** `typer_ui/output.py` (new file)

```python
def ui(component_or_value: Any = None) -> UiBlock:
    """Present a UI component or value.

    Automatic conversions:
    - None → Text("") (empty line)
    - str → Text(str) (plain text)
    - int/float/etc → Text(str(value))
    - UiBlock → unchanged
    - DynamicBlock → setup reactive rendering

    Args:
        component_or_value: Component or value to display

    Returns:
        The displayed component (for chaining/context manager)

    Raises:
        RuntimeError: If called outside command execution context

    Examples:
        >>> ui("Hello")  # Plain text
        >>> ui()  # Empty line
        >>> ui(tg.Table(...))  # Component
        >>> ui(dx(lambda: "...", state))  # Dynamic content
    """
    runner = get_current_runner()
    if not runner:
        raise RuntimeError("ui() can only be called during command execution.")

    # Handle None (empty line)
    if component_or_value is None:
        component = Text("")

    # Handle DynamicBlock (reactive content)
    elif isinstance(component_or_value, DynamicBlock):
        return _render_dynamic_block(component_or_value, runner)

    # Handle strings and other values (convert to Text)
    elif not isinstance(component_or_value, UiBlock):
        component = Text(str(component_or_value))

    # Already a UiBlock
    else:
        component = component_or_value

    # Check if in reactive mode
    if runner.is_reactive_mode():
        runner.add_to_reactive_container(component)
    else:
        runner.show(component)

    # Mark component as presented for auto-updates
    if hasattr(component, '_mark_presented'):
        component._mark_presented(runner)

    return component


def _render_dynamic_block(dyn_block: DynamicBlock, runner) -> Column:
    """Internal: Render a dynamic block with reactive updates."""
    from .ui_blocks import Column
    from .state import State

    container = Column([])

    # Execute renderer in reactive mode
    flet_control = runner.execute_in_reactive_mode(container, dyn_block.renderer)

    # Store control for updates (GUI mode)
    if flet_control is not None:
        runner._reactive_components[id(container)] = flet_control
        runner.add_to_output(flet_control, component=container)

    # Register observer callbacks
    def on_state_change():
        runner.update_reactive_container(container, dyn_block.renderer)

    for dep in dyn_block.dependencies:
        if isinstance(dep, State):
            dep.add_observer(on_state_change)

    return container
```

### 3. Standalone md() Function

**File:** `typer_ui/output.py`

```python
def md(markdown: str) -> Md:
    """Present markdown content.

    Shortcut for ui(tg.Md(markdown)).

    Args:
        markdown: Markdown-formatted string

    Returns:
        The Md component

    Examples:
        >>> md("# Title")
        >>> md("**Bold** and *italic*")
    """
    from .ui_blocks import Md
    component = Md(markdown)
    return ui(component)
```

### 4. dx() Function (Dynamic Blocks)

**File:** `typer_ui/output.py`

```python
@dataclass
class DynamicBlock:
    """Wrapper for dynamic/reactive UI content.

    Created by dx() function. When passed to ui(), renders
    content that auto-updates when dependencies change.
    """
    renderer: Callable
    dependencies: tuple

    def __repr__(self):
        deps = ', '.join(str(d) for d in self.dependencies)
        return f"DynamicBlock(renderer={self.renderer.__name__}, deps=[{deps}])"


def dx(renderer: Callable, *dependencies) -> DynamicBlock:
    """Create a dynamic UI block that re-renders when dependencies change.

    The renderer can return:
    - A UiBlock component
    - A string (converted to Text)
    - None (empty)

    Or the renderer can call ui() internally to build content.

    Args:
        renderer: Function that builds the UI content
        *dependencies: State objects to observe for changes

    Returns:
        DynamicBlock that can be passed to ui()

    Examples:
        >>> state = app.state(0)
        >>> ui(dx(lambda: f"Count: {state.value}", state))
        >>>
        >>> # Or return a component
        >>> ui(dx(lambda: tg.Table(...), state1, state2))
        >>>
        >>> # Or use ui() inside renderer
        >>> def render():
        ...     ui("### Dynamic Section")
        ...     ui(tg.Table(...))
        >>> ui(dx(render, state))
    """
    return DynamicBlock(renderer=renderer, dependencies=dependencies)
```

---

## Code Changes Required

### Files to Create

1. **`typer_ui/output.py`** (new)
   - `ui()` function
   - `md()` function
   - `dx()` function
   - `DynamicBlock` class
   - `_render_dynamic_block()` helper

### Files to Modify

1. **`typer_ui/ui.py` → `typer_ui/ui_app.py`** (rename)

   - Rename class `Ui` → `UiApp`
   - **REMOVE:** `__call__()` method (replaced by standalone `ui()`)
   - **REMOVE:** `out()` method (deprecated, unused)
   - **REMOVE:** `_to_component()` method (not needed)
   - **REMOVE:** Deprecated parameters in `def_command()`:
     - `is_button` → use `button`
     - `is_long` → use `long`
     - `is_auto_exec` → use `auto`
   - **RENAME:** `app()` → `run()` (optional, for clarity)

2. **`typer_ui/__init__.py`**

   - Export `UiApp` instead of `Ui`
   - Export `ui`, `md`, `dx` functions
   - **REMOVE:** Export of deprecated `Ui` alias (clean break)

3. **`typer_ui/ui_blocks.py`**

   - **KEEP:** `to_component()` helper (still used by runners)
   - Update docstrings to reference new API

4. **`typer_ui/specs.py`**

   - **REMOVE:** Deprecated property aliases:
     - `CommandUiSpec.is_button` property
     - `CommandUiSpec.is_long` property
     - `CommandUiSpec.is_auto_exec` property
   - Update all internal code to use `button`, `long`, `auto` directly

5. **`typer_ui/runners/gui_runner.py`**

   - Update property access: `.is_button` → `.button`
   - Update property access: `.is_long` → `.long`
   - Update property access: `.is_auto_exec` → `.auto`
   - 7 locations total (lines 533, 586, 595, 647, 662, 867, 869, 892, 894)

6. **`typer_ui/runners/cli_runner.py`**
   - No changes needed (doesn't use deprecated properties)

### Files to Update (Examples)

Update all examples to use new API:

1. **`examples/01_basic_typer_to_gui.py`**
2. **`examples/02_arguments_and_output.py`**
3. **`examples/03_ui_blocks.py`**
4. **`examples/04_app_control.py`**
5. **`examples/05_state.py`**

**Pattern:**

```python
# OLD
ui = tg.Ui(app)
ui(tg.Text("hello"))
ui(tg.Md("**bold**"))

# NEW
from typer_ui import UiApp, ui, md
app = UiApp(typer_app)
ui("hello")
md("**bold**")
```

### Files to Remove/Archive

1. **Archive old examples** that use deprecated API:
   - Move to `examples/archive/` (already there)
   - Update `examples/README.md` to show new API only

---

## Migration Impact Analysis

### Breaking Changes

1. **Import changes** (all users affected):

   ```python
   # OLD
   import typer_ui as tg
   ui = tg.Ui(app)

   # NEW
   from typer_ui import UiApp, ui, md, dx
   app = UiApp(typer_app)
   ```

2. **Output syntax changes** (all users affected):

   ```python
   # OLD
   ui(tg.Text("hello"))
   ui(tg.Md("**bold**"))
   ui(lambda: tg.Text(f"{state.value}"), state)

   # NEW
   ui("hello")
   md("**bold**")
   ui(dx(lambda: f"{state.value}", state))
   ```

3. **Reactive syntax changes** (users with reactive content):

   ```python
   # OLD
   ui(lambda: ..., state1, state2)

   # NEW
   ui(dx(lambda: ..., state1, state2))
   ```

4. **Deprecated parameters removed** (minimal impact, examples already updated):

   ```python
   # OLD (deprecated but worked)
   @ui.def_command(is_button=True, is_long=True)

   # NEW
   @app.def_command(button=True, long=True)
   ```

### Non-Breaking (Backward Compatible)

None - this is a clean break refactoring.

### Migration Effort

**Low effort** - straightforward find-replace:

1. Rename `tg.Ui` → `UiApp`
2. Add imports: `from typer_ui import ui, md, dx`
3. Replace `ui(tg.Text(...))` → `ui(...)`
4. Replace `ui(tg.Md(...))` → `md(...)`
5. Replace `ui(lambda: ..., state)` → `ui(dx(lambda: ..., state))`

---

## Implementation Strategy

### Phase 1: Create New Code (No Breaking Changes)

1. Create `typer_ui/output.py` with `ui()`, `md()`, `dx()`
2. Create `UiApp` class in `typer_ui/ui_app.py` (copy from `ui.py`)
3. Export both old and new APIs from `__init__.py`:

   ```python
   # Old API (deprecated)
   from .ui import Ui

   # New API
   from .ui_app import UiApp
   from .output import ui, md, dx
   ```

4. Test that new API works alongside old API

### Phase 2: Update Examples

1. Update examples 01-05 to use new API
2. Keep archive examples unchanged (for reference)
3. Update documentation

### Phase 3: Remove Old Code (Breaking Changes)

1. Remove `typer_ui/ui.py` entirely
2. Remove `Ui` export from `__init__.py`
3. Remove deprecated properties from `CommandUiSpec`
4. Update runners to use new property names
5. Run full test suite

### Phase 4: Cleanup

1. Remove `to_component()` if no longer needed (check usage)
2. Update docstrings and comments
3. Update README.md
4. Update CLAUDE.md

---

## Code Removal Summary

### Definitely Remove

1. **`Ui.out()` method** - Deprecated, zero usage
2. **`Ui.__call__()` method** - Replaced by `ui()`
3. **`Ui._to_component()` method** - Not needed, use `to_component()` directly
4. **Deprecated parameters in `def_command()`:**
   - `is_button`, `is_long`, `is_auto_exec`
5. **Deprecated properties in `CommandUiSpec`:**
   - `.is_button`, `.is_long`, `.is_auto_exec`
6. **Old parameter names in examples and docs**

### Keep

1. **`to_component()` helper** - Used by runners for result conversion
2. **`State` class** - Core reactive functionality
3. **`UICommand` class** - Command control API
4. **All UI components** - Text, Md, Table, Row, Column, etc.

---

## Expected File Structure After Refactoring

```
typer_ui/
├── __init__.py           # Exports: UiApp, ui, md, dx, State, UICommand, components
├── ui_app.py             # UiApp class (renamed from ui.py)
├── output.py             # ui(), md(), dx() functions (NEW)
├── state.py              # State class (unchanged)
├── ui_blocks.py          # UI components (minor updates)
├── spec_builder.py       # Unchanged
├── specs.py              # Remove deprecated properties
└── runners/
    ├── base.py           # Unchanged
    ├── cli_runner.py     # Unchanged
    └── gui_runner.py     # Update property access (7 locations)

examples/
├── 01_basic_typer_to_gui.py      # Updated to new API
├── 02_arguments_and_output.py    # Updated to new API
├── 03_ui_blocks.py               # Updated to new API
├── 04_app_control.py             # Updated to new API
├── 05_state.py                   # Updated to new API
└── archive/                      # Old examples (reference only)
```

---

## Validation Checklist

Before implementation:

- [ ] All examples identified and migration path clear
- [ ] All deprecated code identified
- [ ] All property accesses mapped (is_button → button, etc.)
- [ ] Test coverage reviewed

During implementation:

- [ ] Phase 1: New code works alongside old code
- [ ] Phase 2: Examples updated and tested
- [ ] Phase 3: Old code removed, tests pass
- [ ] Phase 4: Documentation updated

After implementation:

- [ ] All examples work in CLI mode
- [ ] All examples work in GUI mode
- [ ] No references to old API in code
- [ ] Documentation reflects new API
- [ ] CLAUDE.md updated with new patterns

---

## API Comparison Table

| Feature               | Old API                      | New API                       | Status        |
| --------------------- | ---------------------------- | ----------------------------- | ------------- |
| **App setup**         | `ui = tg.Ui(app)`            | `app = UiApp(typer_app)`      | ✅ Cleaner    |
| **Text output**       | `ui(tg.Text("hello"))`       | `ui("hello")`                 | ✅ Simpler    |
| **Markdown**          | `ui(tg.Md("**bold**"))`      | `md("**bold**")`              | ✅ Clearer    |
| **Empty line**        | `ui()`                       | `ui()`                        | ✅ Same       |
| **String shortcut**   | `ui("text")` → Md            | `ui("text")` → Text           | ⚠️ Changed    |
| **Components**        | `ui(tg.Table(...))`          | `ui(tg.Table(...))`           | ✅ Same       |
| **Reactive**          | `ui(lambda: ..., s)`         | `ui(dx(lambda: ..., s))`      | ✅ Explicit   |
| **State**             | `ui.state(0)`                | `app.state(0)`                | ✅ Logical    |
| **Command decorator** | `@ui.def_command(long=True)` | `@app.def_command(long=True)` | ✅ Consistent |
| **Launch**            | `ui.app()`                   | `app.run()`                   | ✅ Clearer    |
| **Deprecated params** | `is_button=True`             | `button=True`                 | ✅ Removed    |
| **Deprecated method** | `ui.out(...)`                | ❌ Removed                    | ✅ Cleanup    |

---

## Open Questions

1. **String handling in `ui()`:**

   - Current: `ui("text")` → `Md("text")` (markdown)
   - Proposed: `ui("text")` → `Text("text")` (plain text)
   - Rationale: More intuitive, use `md()` for markdown
   - **Decision needed:** Change behavior or keep for compatibility?

2. **`app.run()` vs `app.app()`:**

   - Current: `ui.app()`
   - Proposed: `app.run()`
   - Rationale: `run()` is more conventional
   - **Decision needed:** Rename or keep `app()` for consistency?

3. **`to_component()` visibility:**

   - Currently exported in `__init__.py`
   - Used internally by runners
   - **Decision needed:** Keep as public API or make internal-only?

4. **Backward compatibility period:**
   - Option A: Clean break (remove old API immediately)
   - Option B: Deprecation warnings for 1-2 versions
   - **Decision needed:** Which approach?

---

## Recommendation

**Proceed with clean break refactoring:**

1. Implement all phases
2. Update all examples
3. Remove all deprecated code
4. Clear, simple API with no legacy baggage

**Benefits:**

- Cleaner codebase
- Easier to maintain
- More intuitive for new users
- Clear mental model (app vs output functions)

**Timeline:**

- Analysis: ✅ Complete
- Implementation: ~2-3 hours
- Testing: ~1 hour
- Documentation: ~1 hour
- **Total: ~4-5 hours of focused work**
