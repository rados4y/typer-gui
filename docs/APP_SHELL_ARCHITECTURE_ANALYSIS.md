# AppShell Architecture Analysis

## Problem Statement

The initial implementation was **WRONG** because it prescribed HOW shells should be built:
- `create_header()`, `create_tabs()`, `create_command_list()` etc.
- Assumes all shells have headers, tabs, command lists
- Too opinionated - limits layout freedom
- Mixes "what to build" with "how to build it"

## Core Issue: Wrong Abstraction Level

### ❌ Wrong Approach (Initial Implementation)

```python
class AppShell(ABC):
    @abstractmethod
    def create_header() -> Container:
        """Forces all shells to have headers"""

    @abstractmethod
    def create_tabs() -> Control:
        """Forces all shells to have tabs"""

    @abstractmethod
    def create_command_list() -> ListView:
        """Forces all shells to have command lists"""
```

**Problems:**
1. **Prescriptive Structure** - Dictates UI components (header, tabs, lists)
2. **Limited Flexibility** - Dashboard shell might not have command lists
3. **Tight Coupling** - Shell internals exposed to outside
4. **Wrong Responsibility** - Mixing "what" with "how"

---

## ✅ Correct Approach: Event-Driven Architecture

### Core Principle
**AppShell is a black box that:**
1. **Builds whatever UI it wants** (complete freedom)
2. **Handles events from the application** (app tells shell what happened)
3. **Sends events to the application** (shell tells app what user did)

### Terminology

- **Action** = Command (e.g., `create`, `update`, `delete`)
- **Module** = Sub-application/Tab (e.g., `users`, `orders`)
- **Shell** = Complete GUI layout implementation
- **App** = Application layer (UiApp, GUIRunner)

---

## Proposed Architecture

### 1. Event-Driven Interface

```python
class AppShell(ABC):
    """Abstract shell with event-driven interface."""

    # ==================== BUILDING ====================

    @abstractmethod
    def build(self, page: ft.Page, app_spec: AppSpec) -> None:
        """Build complete UI with total freedom.

        Shell can create ANY layout structure it wants:
        - Sidebar layout
        - Top navigation
        - Dashboard with cards
        - Split panes
        - Custom layouts

        No assumptions about components or structure.
        """
        pass

    # ==================== EVENTS FROM APP (App → Shell) ====================
    # These are called by the application to inform shell of changes

    @abstractmethod
    def on_action_selected(
        self,
        action: CommandSpec,
        module: Optional[str] = None
    ) -> None:
        """Action was selected (programmatically or by user).

        Shell should:
        - Highlight selected action in UI
        - Show parameter form
        - Clear previous output (if needed)
        - Update any visual indicators

        Args:
            action: The selected command/action
            module: Which module/sub-app it belongs to (None = root)
        """
        pass

    @abstractmethod
    def on_action_output(
        self,
        output: Any,
        action: CommandSpec,
        append: bool = False
    ) -> None:
        """Action produced output.

        Shell should:
        - Display output in its own way
        - Handle different output types (text, tables, components)
        - Append or replace based on flag

        Args:
            output: Output to display (UiBlock, string, etc.)
            action: Which action produced this output
            append: True to append, False to replace
        """
        pass

    @abstractmethod
    def on_action_started(
        self,
        action: CommandSpec,
        module: Optional[str] = None
    ) -> None:
        """Action execution started.

        Shell should:
        - Show loading indicator
        - Disable run button
        - Clear previous output
        - Show progress UI

        Args:
            action: Action being executed
            module: Which module it belongs to
        """
        pass

    @abstractmethod
    def on_action_completed(
        self,
        action: CommandSpec,
        success: bool,
        error: Optional[Exception] = None
    ) -> None:
        """Action execution completed.

        Shell should:
        - Hide loading indicator
        - Re-enable run button
        - Show success/error state
        - Display error message if failed

        Args:
            action: Action that completed
            success: Whether execution succeeded
            error: Exception if failed
        """
        pass

    @abstractmethod
    def on_action_clear(
        self,
        action: Optional[CommandSpec] = None,
        module: Optional[str] = None
    ) -> None:
        """Clear output for action(s).

        Shell should:
        - Clear output area
        - Reset UI state
        - Clear buffers

        Args:
            action: Specific action to clear (None = all in module)
            module: Which module (None = current)
        """
        pass

    @abstractmethod
    def on_module_selected(
        self,
        module: str
    ) -> None:
        """Module/sub-app was selected.

        Shell should:
        - Switch to module view
        - Update tab highlighting
        - Show module's actions
        - Reset module state

        Args:
            module: Name of selected module
        """
        pass

    @abstractmethod
    def on_state_changed(
        self,
        state_changes: dict[str, Any]
    ) -> None:
        """Application state changed (for reactive UIs).

        Shell should:
        - Update reactive components
        - Refresh affected views
        - Trigger re-renders

        Args:
            state_changes: Dict of state_key -> new_value
        """
        pass

    # ==================== EVENTS TO APP (Shell → App) ====================
    # Shell calls these when user interacts with UI

    def set_callbacks(
        self,
        on_user_select_action: Callable[[CommandSpec, Optional[str]], None],
        on_user_run_action: Callable[[CommandSpec, dict[str, Any]], None],
        on_user_select_module: Callable[[str], None],
        on_user_clear: Callable[[Optional[CommandSpec]], None]
    ) -> None:
        """Register callbacks for user interactions.

        These are called BY the shell when user interacts with UI.

        Args:
            on_user_select_action: User clicked/selected an action
            on_user_run_action: User clicked run button
            on_user_select_module: User switched tabs/modules
            on_user_clear: User clicked clear button
        """
        self._on_user_select_action = on_user_select_action
        self._on_user_run_action = on_user_run_action
        self._on_user_select_module = on_user_select_module
        self._on_user_clear = on_user_clear

    # ==================== PARAMETER EXTRACTION ====================

    @abstractmethod
    def get_action_parameters(
        self,
        action: CommandSpec
    ) -> dict[str, Any]:
        """Extract parameter values from form inputs.

        Shell is responsible for:
        - Managing form controls
        - Extracting values
        - Validating input
        - Type conversion

        Args:
            action: Action to get parameters for

        Returns:
            Dict of parameter_name -> value
        """
        pass
```

---

## Event Flow Examples

### Scenario 1: User Selects Command

```
1. User clicks "create" command in Shell's UI
2. Shell calls: self._on_user_select_action(create_cmd, "users")
3. App (GUIRunner) processes selection
4. App calls: shell.on_action_selected(create_cmd, "users")
5. Shell highlights command, shows form
```

### Scenario 2: User Runs Command

```
1. User fills form and clicks "Run"
2. Shell extracts params: params = shell.get_action_parameters(cmd)
3. Shell calls: self._on_user_run_action(cmd, params)
4. App calls: shell.on_action_started(cmd)
5. Shell shows loading indicator
6. App executes command
7. App calls: shell.on_action_output(output, cmd)
8. Shell displays output
9. App calls: shell.on_action_completed(cmd, success=True)
10. Shell hides loading indicator
```

### Scenario 3: Programmatic Command Execution

```
1. App wants to auto-execute command
2. App calls: shell.on_action_selected(cmd, "users")
3. Shell shows form (if needed)
4. App calls: shell.on_action_started(cmd)
5. App executes command
6. App calls: shell.on_action_output(output, cmd)
7. App calls: shell.on_action_completed(cmd, success=True)
```

### Scenario 4: Tab/Module Switch

```
1. User clicks "Orders" tab
2. Shell calls: self._on_user_select_module("orders")
3. App processes module switch
4. App calls: shell.on_module_selected("orders")
5. Shell switches view, shows orders' actions
```

---

## Alternative Architectures

### Alternative 1: Observer Pattern

```python
class AppShell(ABC):
    def build(self, page, app_spec):
        """Build UI"""

    def observe(self, observable: AppState):
        """Shell observes app state changes"""
        observable.subscribe(self._on_state_update)

    def _on_state_update(self, changes):
        """React to state changes"""
```

**Pros:**
- More reactive
- Decoupled state management

**Cons:**
- More complex
- Harder to debug
- Overkill for simple apps

### Alternative 2: Event Bus

```python
class EventBus:
    def publish(self, event_type, data):
        """Publish event"""

    def subscribe(self, event_type, handler):
        """Subscribe to events"""

# Usage
bus = EventBus()
shell.connect(bus)
app.connect(bus)

# Shell publishes
bus.publish("action.selected", command_spec)

# App subscribes
bus.subscribe("action.selected", app.handle_selection)
```

**Pros:**
- Very decoupled
- Easy to add more listeners
- Central event log

**Cons:**
- More boilerplate
- Harder to trace event flow
- Need event bus infrastructure

### Alternative 3: Command Pattern

```python
class ActionCommand:
    def execute(self):
        """Execute action"""

    def get_parameters(self):
        """Get params from form"""

# Shell creates commands
command = shell.create_action_command(cmd_spec)
params = command.get_parameters()
result = command.execute()
```

**Pros:**
- Encapsulates operations
- Easier undo/redo

**Cons:**
- More abstraction layers
- Overkill for this use case

### Alternative 4: Direct Property Access

```python
class AppShell(ABC):
    current_action: Optional[CommandSpec] = None
    current_module: Optional[str] = None
    output_buffer: List[Any] = []

    def build(self, page, app_spec):
        """Build UI"""

    def refresh(self):
        """Re-render based on current properties"""

# Usage
shell.current_action = cmd
shell.refresh()
```

**Pros:**
- Simple
- Direct access

**Cons:**
- Tight coupling
- No encapsulation
- Hard to track changes
- No validation

---

## Recommended Approach

### ✅ Event-Driven Interface (Proposed)

**Why:**
1. **Clear Separation** - Shell handles UI, App handles logic
2. **Flexible** - Shell can build ANY layout
3. **Testable** - Easy to mock events
4. **Debuggable** - Clear event flow
5. **Standard Pattern** - Familiar to developers

**Trade-offs:**
- More verbose than property access
- Need to manage callbacks
- Event ordering matters

---

## Implementation Variants

### Variant A: Synchronous Events (Recommended)

```python
# Simple, direct calls
shell.on_action_selected(cmd)
shell.on_action_output(output, cmd)
```

**Pros:** Simple, predictable
**Cons:** Can't handle async operations well

### Variant B: Async Events

```python
# Async event handlers
async def on_action_selected(self, action):
    await self._update_ui()
    await self._load_form()

# App calls
await shell.on_action_selected(cmd)
```

**Pros:** Handles async operations
**Cons:** More complex, need async throughout

### Variant C: Queued Events

```python
# Events are queued and processed
shell.enqueue_event("action.selected", cmd)
shell.process_events()
```

**Pros:** Better for high-frequency events
**Cons:** Delayed processing, more complex

---

## Parameter Handling Analysis

### Option 1: Shell Manages Forms (Recommended)

```python
# Shell creates and manages form controls internally
shell.build(page, app_spec)  # Creates forms

# When needed, app asks for values
params = shell.get_action_parameters(cmd)
```

**Pros:**
- Shell has full control over form UI
- Different shells can have different form styles

**Cons:**
- Shell must understand parameter types
- Need shared parameter control creation logic

### Option 2: App Provides Form Controls

```python
# App creates form controls
form_controls = app.create_parameter_form(cmd)

# Shell just displays them
shell.display_form(form_controls)
```

**Pros:**
- Consistent parameter handling
- App controls validation

**Cons:**
- Shell has less UI freedom
- Tight coupling to Flet controls

### Option 3: Hybrid

```python
# Shell can override parameter control creation
class MyShell(AppShell):
    def create_param_control(self, param: ParamSpec):
        # Custom control creation
        return my_custom_control

    # Falls back to default if not overridden
```

**Pros:**
- Flexibility + consistency
- Easy to customize

**Cons:**
- Need good default implementations

---

## Module/Tab Handling

### Question: Should modules be in AppShell interface?

**Option 1: Explicit Module Support**
```python
def on_module_selected(self, module: str):
    """Shell must handle modules"""
```

**Pros:** Clear expectation
**Cons:** Forces shells to support modules/tabs

**Option 2: Optional Module Support**
```python
def on_context_changed(self, context: dict):
    """Generic context change (may include module)"""
```

**Pros:** More flexible
**Cons:** Less clear

**Recommendation:** Keep explicit `on_module_selected` but make it optional (pass if not supported)

---

## State Management Integration

### Question: How do reactive states (State objects) integrate?

**Option 1: Shell Observes States**
```python
def on_state_changed(self, state_changes: dict):
    """Shell updates reactive components"""
```

**Option 2: Shell Registers State Observers**
```python
def register_state(self, state: State):
    """Shell subscribes to state changes"""
    state.subscribe(self._on_value_change)
```

**Option 3: App Manages State Updates**
```python
# App calls shell with new rendered output
state.value = 5
shell.on_action_output(rendered_output, cmd)
```

**Recommendation:** Option 1 + Option 3 hybrid
- App renders state changes to components
- Calls `shell.on_state_changed()` for special cases
- Shell doesn't need to know about State internals

---

## Error Handling

### Question: How does shell handle errors?

**Option 1: Separate Error Event**
```python
def on_action_error(self, action, error: Exception):
    """Display error in shell-specific way"""
```

**Option 2: Status in completion Event**
```python
def on_action_completed(self, action, success, error=None):
    """Single completion event with status"""
```

**Recommendation:** Option 2 (simpler)

---

## Loading/Progress Indicators

### Question: How to show progress for long operations?

**Option 1: Start/Complete Events**
```python
shell.on_action_started(cmd)
# ... command runs ...
shell.on_action_completed(cmd, success=True)
```

**Option 2: Progress Events**
```python
shell.on_action_started(cmd)
shell.on_action_progress(cmd, percent=50, message="Processing...")
shell.on_action_completed(cmd)
```

**Recommendation:** Start with Option 1, add progress if needed later

---

## Mock Preview System

### Question: How to preview shells without app?

**Approach:**
```python
def create_mock_shell_preview(shell: AppShell):
    # Create mock app_spec
    # Set up mock callbacks
    # Build shell
    # Simulate events

    def main(page):
        shell.build(page, mock_spec)

        # Simulate user clicking command
        def click_create():
            shell.on_action_selected(create_cmd)

        # Add test buttons
        page.add(ft.Button("Test Select", on_click=click_create))

    return main
```

This allows UX review without full integration.

---

## Comparison Matrix

| Aspect | Event-Driven | Observer | Event Bus | Direct Props |
|--------|-------------|----------|-----------|--------------|
| Decoupling | ⭐⭐⭐⭐ | ⭐⭐⭐⭐⭐ | ⭐⭐⭐⭐⭐ | ⭐⭐ |
| Simplicity | ⭐⭐⭐⭐ | ⭐⭐⭐ | ⭐⭐ | ⭐⭐⭐⭐⭐ |
| Debuggability | ⭐⭐⭐⭐ | ⭐⭐⭐ | ⭐⭐ | ⭐⭐⭐⭐⭐ |
| Flexibility | ⭐⭐⭐⭐⭐ | ⭐⭐⭐⭐ | ⭐⭐⭐⭐⭐ | ⭐⭐⭐ |
| Testability | ⭐⭐⭐⭐⭐ | ⭐⭐⭐⭐ | ⭐⭐⭐⭐ | ⭐⭐⭐ |
| Learning Curve | ⭐⭐⭐⭐ | ⭐⭐⭐ | ⭐⭐ | ⭐⭐⭐⭐⭐ |

**Legend:** ⭐⭐⭐⭐⭐ = Best

---

## Final Recommendation

### Adopt: Event-Driven Interface with these specifics:

1. **Single Build Method:** `build(page, app_spec)` - total freedom
2. **Event Methods:** App → Shell communication
   - `on_action_selected()`
   - `on_action_started()`
   - `on_action_output()`
   - `on_action_completed()`
   - `on_action_clear()`
   - `on_module_selected()`
3. **Callback Registration:** Shell → App communication
   - `set_callbacks(on_user_select_action, on_user_run_action, ...)`
4. **Parameter Extraction:** `get_action_parameters(action)` - shell manages
5. **Shared Helpers:** Provide default param control creation (can override)

### Benefits:
- ✅ Total layout freedom for shells
- ✅ Clear event flow
- ✅ Easy to test and debug
- ✅ Supports all planned shell types
- ✅ No prescriptive structure

### Next Steps:
1. Review this architecture
2. Decide on specific event names
3. Finalize parameter handling approach
4. Create minimal working example
5. Implement SidebarShell with new interface

---

## Questions for Review

1. **Event naming:** Use "action" vs "command"? "module" vs "sub_app" vs "tab"?
2. **Parameter handling:** Should shells create param controls or receive them?
3. **State integration:** How should reactive State objects work with shells?
4. **Modal support:** Should `modal=True` be handled by shell or app?
5. **Output buffering:** Should shell buffer output or app manages it?
6. **Auto-execution:** How does `auto=True` work with this architecture?
7. **Progress indication:** Need `on_action_progress()` or just start/complete?

**Ready for architectural decision and refinement.**
