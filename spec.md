# Typer-GUI Simplified Architecture

This design prioritizes **simplicity** and **ease of adding new UI components** while maintaining clean separation between application definition, control logic, and presentation.

The goal is to make the system simple to understand, easy to extend with new components, and straightforward to debug.

---

## 1. Definition Layer — _What the application is_

**Artifacts**

- `AppSpec` - Immutable application specification
- `CommandSpec` - Command metadata and callback
- `ParamSpec` - Parameter type and validation info
- `CommandUiSpec` - UI presentation hints (is_button, is_long, etc.)

**Description**
The definition layer is a **static, reflected model** of the application.
It is produced by introspection of a Typer app and fully describes commands, parameters, defaults, help text, and UI-related metadata.

**Rules**

- Immutable or treated as immutable
- Serializable
- No execution logic
- No CLI / GUI / REST dependencies

**Purpose**
Provide a stable, deterministic input for all runtimes and frontends.

---

## 2. Controller / Session Layer — _What the application is doing_

### `UIApp`

**Description**
`UIApp` is the **central controller** and manages session state.
It coordinates command selection and execution, delegates presentation to the active runner.

**Responsibilities**

- Owns a reference to `AppSpec`
- Maintains session state:
  - current command
  - execution history
- Exposes command API:
  - `select_command(name)`
  - `run_command(**kwargs)`
  - `include_command(**kwargs)`
- Provides access to runner for component output

**Rules**

- Presentation-agnostic (doesn't render)
- Framework-free (doesn't import Flet/Flask/etc.)
- Lightweight - just state management

---

## 3. UI Components — _What can be displayed_

### Component Design Principles

**Single Class, All Presentation**

Each UI component is a **single class** containing all presentation logic for every channel:

```python
class Table(UiBlock):
    # Data
    cols: List[str]
    data: List[List[Any]]

    # Presentation per channel
    def show_cli(self, runner: CLIRunner) -> None:
        # ASCII table rendering

    def show_gui(self, runner: GUIRunner) -> None:
        # Flet DataTable rendering

    def show_rest(self, runner: RESTRunner) -> None:
        # JSON serialization
```

**Why Single Class?**
- ✅ **Easy to add new components** - edit one file, one class
- ✅ **All logic together** - no hunting across multiple files
- ✅ **Simple to understand** - clear what component does
- ✅ **Handles interactions** - click, input, etc. all in one place

**Component Types**

1. **Simple Components** - Just data and rendering
   - `Text` - Plain text
   - `Md` - Markdown content

2. **Container Components** - Can hold children
   - `Table` - Tabular data, can add rows progressively
   - `Row` - Horizontal layout
   - `Column` - Vertical layout

3. **Interactive Components** - Handle user input
   - `Button` - Clickable action
   - `TextInput` - Text entry
   - `Link` - Clickable link

**Container Context Manager Pattern**

Containers support progressive rendering via context managers:

```python
with tg.Table(cols=["Name", "Status"], data=[]) as table:
    for item in items:
        table.add_row([item.name, "Processing"])
        process(item)
        # Table updates in real-time!
```

---

## 4. Runner Layer — _How the application is run_

### Runners

- `CLIRunner` - Terminal/console execution
- `GUIRunner` - Flet desktop application
- `RESTRunner` - REST API server (future)

**Description**
A Runner hosts the application in a specific environment.

**Responsibilities**

- Boot the environment (CLI process, Flet app, REST server)
- Create and own `UIApp` instance
- Execute command callbacks with stdout/stderr capture
- Show components by calling their channel-specific method:
  - `CLIRunner.show(component)` → calls `component.show_cli(self)`
  - `GUIRunner.show(component)` → calls `component.show_gui(self)`
- Support progressive updates for container components
- Handle return values (auto-display returned components)
- Intercept print() and convert to `Text` components

**Rules**

- May import UI frameworks (Flet, Rich, Flask, etc.)
- Must not leak framework concerns into UIApp or components
- Responsible for stdout/stderr capture during command execution

---

## 5. User API — _How developers use it_

### Universal Output Method

```python
ui.out(component)  # Output any component
```

**Examples:**

```python
# Explicit output
ui.out(tg.Table(cols=["Name"], data=[["Alice"]]))

# Return value auto-displayed
@app.command()
def stats():
    return tg.Table(cols=["Metric", "Value"], data=get_stats())

# Progressive rendering
with tg.Table(cols=["Task", "Status"], data=[]) as t:
    for task in tasks:
        t.add_row([task.name, "Running"])
        task.execute()

# Nested components
ui.out(
    tg.Column([
        tg.Md("# Dashboard"),
        tg.Row([
            tg.Button("Refresh", on_click=refresh),
            tg.Button("Export", on_click=export),
        ]),
        tg.Table(cols=["Name"], data=get_data()),
    ])
)

# print() is intercepted
print("Processing...")  # Same as ui.out(tg.Text("Processing..."))
```

---

## 6. Architecture Flow

### Component Output Flow

```
User Code
    ↓
ui.out(component) or return component
    ↓
Runner.show(component)
    ↓
component.show_cli(runner) or component.show_gui(runner)
    ↓
Terminal output or Flet UI update
```

**Simple and Direct**
- No events
- No queues
- No async complexity
- Just method calls

### Dependency Direction

```
AppSpec / CommandSpec
    ↓
UIApp (state management)
    ↓
Runner (execution + presentation)
    ↓
UiBlock components (presentation logic)
```

- Specs are immutable
- UIApp manages state
- Runner orchestrates execution
- Components handle their own rendering

---

## 7. Design Priorities

### Optimized For

1. **Adding new UI components** (frequent) ✅
   - One class, one file
   - All presentation together

2. **Debugging** ✅
   - Direct method calls
   - Clear stack traces

3. **Simplicity** ✅
   - No events, no queues, no async overhead
   - Straightforward control flow

### Not Optimized For

1. **Adding new channels** (rare)
   - Requires adding method to all components
   - Acceptable trade-off given priorities

---

## Final Principles

1. **Specs describe** - Immutable application structure
2. **UIApp coordinates** - Lightweight state management
3. **Runner executes and captures** - Stdout/stderr, return values
4. **Components render themselves** - Per-channel presentation in single class
5. **Simplicity over abstraction** - Direct calls over event indirection

This structure keeps the system simple, makes adding components easy, and maintains clear separation of concerns without over-engineering.
