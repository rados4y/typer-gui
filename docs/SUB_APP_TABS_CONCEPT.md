# Typer Sub-Application Support - Concept & Implementation Plan

## Overview

Add support for Typer's `app.add_typer()` sub-applications with tab-based GUI navigation, where each sub-application is displayed as a separate tab.

## Current Behavior

**Typer Native:**
```python
app = typer.Typer()
users_app = typer.Typer()
orders_app = typer.Typer()

app.add_typer(users_app, name="users")
app.add_typer(orders_app, name="orders")

# CLI: python app.py users create --name "John"
# CLI: python app.py orders list
```

**Current typer2ui Behavior:**
- Only processes `app.registered_commands` (direct commands on main app)
- Ignores `app.registered_groups` (sub-applications)
- All commands appear in a single flat list

## Desired Behavior

### GUI Mode
```
┌─────────────────────────────────────────────────────────┐
│ Application Title                                       │
├─────────────────────────────────────────────────────────┤
│ ┌─────────┬─────────┬─────────┬─────────┐              │
│ │  Users  │ Orders  │ Reports │  Main   │ ← Tab Bar    │
│ └─────────┴─────────┴─────────┴─────────┘              │
│                                                         │
│ ┌──────────┬────────────────────────────────────────┐  │
│ │ Commands │ Content Area (Current Tab)             │  │
│ │          │                                        │  │
│ │ create   │ [Form and output for selected command] │  │
│ │ update   │                                        │  │
│ │ delete   │                                        │  │
│ │ list     │                                        │  │
│ └──────────┴────────────────────────────────────────┘  │
└─────────────────────────────────────────────────────────┘
```

**Tab Placement Options:**
1. **Bottom (Excel-style)** - Preferred if Flet supports (like Excel worksheets)
2. **Top** - Standard tab placement (fallback if bottom not possible)

### CLI Mode
Unchanged - follows Typer's native behavior:
```bash
python app.py users create --name "John"
python app.py orders list --status pending
```

## Technical Analysis

### 1. Typer Internals

**Main App Structure:**
- `app.registered_commands` → List of direct commands on main app
- `app.registered_groups` → List of TyperInfo objects (sub-apps)

**TyperInfo Structure:**
```python
class TyperInfo:
    name: str                    # Sub-app name ("users", "orders")
    typer_instance: typer.Typer  # The actual Typer sub-app
    help: Optional[str]          # Sub-app description
    # ... other metadata
```

**Access Pattern:**
```python
for group in app.registered_groups:
    sub_app_name = group.name
    sub_app = group.typer_instance
    sub_commands = sub_app.registered_commands
    sub_groups = sub_app.registered_groups  # Nested!
```

### 2. Current Architecture

**Spec Layer (specs.py):**
- `AppSpec` → Contains flat tuple of `CommandSpec`
- No concept of grouping or hierarchy

**Builder Layer (spec_builder.py):**
- `build_app_spec()` → Iterates `app.registered_commands`
- Ignores `app.registered_groups`

**GUI Runner (gui_runner.py):**
- Single command list in left panel
- Single content area on right
- No tab navigation

## Implementation Plan

### Phase 1: Data Model Extension

#### 1.1 Add SubAppSpec to specs.py

```python
@dataclass(frozen=True)
class SubAppSpec:
    """Specification for a sub-application (Typer group)."""

    name: str
    """Sub-app name (e.g., 'users', 'orders')"""

    commands: tuple[CommandSpec, ...]
    """Commands in this sub-app"""

    description: Optional[str] = None
    """Sub-app description"""

    sub_apps: tuple['SubAppSpec', ...] = ()
    """Nested sub-apps (for recursive groups)"""
```

#### 1.2 Extend AppSpec

```python
@dataclass(frozen=True)
class AppSpec:
    """Immutable specification for the entire application."""

    commands: tuple[CommandSpec, ...]
    """Direct commands on main app (root-level)"""

    sub_apps: tuple[SubAppSpec, ...] = ()
    """Sub-applications added via add_typer()"""

    title: Optional[str] = None
    description: Optional[str] = None
```

### Phase 2: Spec Builder Updates

#### 2.1 Add Recursive Group Processing

**New Function in spec_builder.py:**
```python
def _build_sub_app_spec(
    typer_info,
    command_ui_specs: dict
) -> SubAppSpec:
    """Build SubAppSpec from TyperInfo."""

    # Extract commands from sub-app
    commands = []
    for cmd in typer_info.typer_instance.registered_commands:
        command_spec = _build_command_spec(cmd, command_ui_specs)
        commands.append(command_spec)

    # Recursively process nested groups
    nested_sub_apps = []
    for nested_group in typer_info.typer_instance.registered_groups:
        nested_spec = _build_sub_app_spec(nested_group, command_ui_specs)
        nested_sub_apps.append(nested_spec)

    return SubAppSpec(
        name=typer_info.name,
        commands=tuple(commands),
        description=typer_info.help,
        sub_apps=tuple(nested_sub_apps)
    )
```

#### 2.2 Update build_app_spec()

```python
def build_app_spec(...) -> AppSpec:
    # ... existing code for main commands ...

    # Process sub-applications
    sub_apps = []
    for group in app.registered_groups:
        sub_app_spec = _build_sub_app_spec(group, command_ui_specs)
        sub_apps.append(sub_app_spec)

    return AppSpec(
        commands=tuple(main_commands),
        sub_apps=tuple(sub_apps),
        title=title,
        description=description
    )
```

### Phase 3: GUI Runner Refactoring

#### 3.1 Tab Management

**New Structure:**
```python
class GUIRunner:
    # Existing...
    self.command_list: Optional[ft.ListView] = None
    self.views_container: Optional[ft.Column] = None

    # New for tabs
    self.tabs: Optional[ft.Tabs] = None
    self.current_tab_index: int = 0

    # Per-tab command views
    # Key: (tab_name, command_name) -> _CommandView
    self.tab_command_views: dict[tuple[str, str], _CommandView] = {}
```

#### 3.2 Layout Restructuring

**Current Layout:**
```
Row
├── Left Panel (command list)
└── Right Panel (views_container)
```

**New Layout (with tabs):**
```
Column
├── Tabs (if sub_apps exist)
│   ├── Main (root commands)
│   ├── Users (sub-app)
│   ├── Orders (sub-app)
│   └── Reports (sub-app)
└── TabContent
    └── Row
        ├── Left Panel (commands for current tab)
        └── Right Panel (views for current tab)
```

**New Layout (no sub-apps - backward compatible):**
```
Row (same as current)
├── Left Panel
└── Right Panel
```

#### 3.3 Flet Tab Implementation

**Tab Bar Creation:**
```python
def _create_tabs(self) -> ft.Tabs:
    """Create tab bar for sub-applications."""

    tabs = []

    # Main tab (root-level commands)
    if self.app_spec.commands:
        tabs.append(ft.Tab(
            text="Main",
            content=self._create_tab_content(None)  # None = main
        ))

    # Sub-app tabs
    for sub_app in self.app_spec.sub_apps:
        tabs.append(ft.Tab(
            text=sub_app.name.title(),
            content=self._create_tab_content(sub_app)
        ))

    return ft.Tabs(
        tabs=tabs,
        selected_index=0,
        on_change=self._on_tab_change,
        # Try bottom placement (Excel-style)
        # If not supported, will default to top
        expand=True
    )
```

**Tab Content Creation:**
```python
def _create_tab_content(
    self,
    sub_app: Optional[SubAppSpec]
) -> ft.Container:
    """Create content area for a tab (command list + views)."""

    # Get commands for this tab
    commands = (
        self.app_spec.commands if sub_app is None
        else sub_app.commands
    )

    # Create command list for this tab
    command_list = self._create_command_list_for_tab(commands)

    # Create views container for this tab
    views_container = ft.Column(controls=[], expand=True)

    # Layout
    return ft.Container(
        content=ft.Row([
            ft.Container(
                content=command_list,
                width=185,
                bgcolor=ft.Colors.BLUE_GREY_50,
                padding=10
            ),
            ft.Container(
                content=views_container,
                expand=True,
                padding=0
            )
        ]),
        expand=True
    )
```

#### 3.4 Tab Placement Options

**Attempt 1: Bottom Tabs (Excel-style)**
```python
# Flet may not support bottom tabs directly
# If available, use tab_alignment or similar property
tabs = ft.Tabs(
    tabs=[...],
    # tab_alignment=ft.TabAlignment.BOTTOM  # If exists
)
```

**Attempt 2: Custom Bottom Tab Bar**
```python
# Create custom tab buttons at bottom
tab_buttons = ft.Row([
    ft.TextButton(
        "Users",
        on_click=lambda: switch_tab("users"),
        style=ft.ButtonStyle(...)
    ),
    # ...
])

layout = ft.Column([
    content_area,  # Takes most space
    ft.Divider(),
    tab_buttons,   # At bottom
])
```

**Fallback: Top Tabs (Standard)**
```python
# Use Flet's standard Tabs control (top placement)
tabs = ft.Tabs(tabs=[...])
```

### Phase 4: Command Namespacing

#### 4.1 Qualified Command Names

**Internal Representation:**
- Main app command: `"create"` → `"create"`
- Sub-app command: `"users" + "create"` → `"users:create"`

**Command View Storage:**
```python
# Old: self.command_views[command_name]
# New: self.command_views[(tab_name, command_name)]

# Access pattern
tab_name = self.current_tab_name  # "users" or None (main)
command_name = "create"
view = self.command_views.get((tab_name, command_name))
```

#### 4.2 Command Execution

**Update execute_command():**
```python
async def execute_command(
    self,
    command_name: str,
    params: dict,
    tab_name: Optional[str] = None
) -> tuple[Any, Optional[Exception], str]:
    """Execute command from specific tab."""

    # Find command in correct tab
    if tab_name is None:
        commands = self.app_spec.commands
    else:
        sub_app = next(
            (sa for sa in self.app_spec.sub_apps if sa.name == tab_name),
            None
        )
        commands = sub_app.commands if sub_app else []

    # Find specific command
    command_spec = next(
        (cmd for cmd in commands if cmd.name == command_name),
        None
    )

    # ... execute as before ...
```

### Phase 5: Backward Compatibility

#### 5.1 Detection

```python
def has_sub_apps(app_spec: AppSpec) -> bool:
    """Check if app uses sub-applications."""
    return len(app_spec.sub_apps) > 0
```

#### 5.2 Layout Selection

```python
def build(self, page: ft.Page):
    if has_sub_apps(self.app_spec):
        # Use tabbed layout
        content = self._create_tabbed_layout()
    else:
        # Use current flat layout
        content = self._create_flat_layout()

    page.add(content)
```

### Phase 6: Nested Sub-Apps (Future)

**For deeply nested hierarchies:**
```python
app = typer.Typer()
users = typer.Typer()
admin_users = typer.Typer()

users.add_typer(admin_users, name="admin")
app.add_typer(users, name="users")

# CLI: app.py users admin create
```

**Strategy:**
- Phase 1: Support one level (main → sub-app)
- Phase 2: Support nested (main → sub-app → sub-sub-app)
  - Option A: Nested tabs (tabs within tabs)
  - Option B: Breadcrumb navigation
  - Option C: Flatten with prefixes ("users:admin:create")

## UI/UX Considerations

### Tab Naming
- Capitalize tab names: "users" → "Users"
- Handle long names: Truncate or scroll
- Support icons (future): `@upp.def_sub_app(icon="person")`

### Empty Tabs
- Main tab with no commands: Hide "Main" tab
- Sub-app with no commands: Show message "No commands in this section"

### Default Tab
- If main has commands: Start on "Main" tab
- If main empty: Start on first sub-app tab
- Remember last selected tab (future: localStorage)

### CLI Mode
- No changes - Typer handles naturally
- `python app.py users create` works as-is

## Example Usage

```python
import typer
import typer2ui as tu
from typer2ui import ui

# Main app
app = typer.Typer()

# Sub-applications
users_app = typer.Typer()
orders_app = typer.Typer()
reports_app = typer.Typer()

# Users commands
@users_app.command()
def create(name: str):
    ui(f"Creating user: {name}")

@users_app.command()
def list():
    ui("Listing all users...")

# Orders commands
@orders_app.command()
def create(product: str, quantity: int):
    ui(f"Creating order: {product} x {quantity}")

@orders_app.command()
def list(status: str = "all"):
    ui(f"Listing orders with status: {status}")

# Add sub-apps to main
app.add_typer(users_app, name="users", help="User management")
app.add_typer(orders_app, name="orders", help="Order management")
app.add_typer(reports_app, name="reports", help="Reporting")

# Main app command (optional)
@app.command()
def dashboard():
    ui("# Main Dashboard")
    ui("Select a tab to manage users, orders, or reports")

# Create GUI
upp = tu.UiApp(app, title="Business Management System")

if __name__ == "__main__":
    upp()
```

**Result in GUI:**
- Tabs: Main | Users | Orders | Reports
- Click "Users" → See: create, list commands
- Click "Orders" → See: create, list commands
- Each tab has its own command list and views

## Implementation Checklist

### Must Have (MVP)
- [ ] SubAppSpec data model
- [ ] AppSpec.sub_apps field
- [ ] spec_builder processes registered_groups
- [ ] Tab-based GUI layout (top or bottom)
- [ ] Per-tab command lists
- [ ] Per-tab command views
- [ ] Backward compatible (no tabs for flat apps)

### Nice to Have (Phase 2)
- [ ] Bottom tab placement (Excel-style)
- [ ] Tab icons
- [ ] Remember last selected tab
- [ ] Nested sub-app support (2+ levels)
- [ ] Tab context in upp.command() API
- [ ] upp.command("users:create").run()

### Future Enhancements
- [ ] Tab-specific settings (@upp.def_sub_app())
- [ ] Drag-and-drop tab reordering
- [ ] Hide/show tabs dynamically
- [ ] Tab badges (notification counts)
- [ ] Keyboard shortcuts (Ctrl+1, Ctrl+2, etc.)

## Testing Strategy

### Unit Tests
- SubAppSpec creation and immutability
- spec_builder with sub-apps
- Nested group processing

### Integration Tests
- GUI with tabs rendering
- Tab switching
- Command execution per tab
- Backward compatibility (no tabs)

### Example Files
- examples/06_sub_applications.py
  - Basic sub-app example
  - 3 tabs: Main, Users, Orders
  - Demonstrates tab navigation

## Migration Path

### For Existing Apps
1. No changes required
2. Apps without sub-apps continue working
3. Adding `app.add_typer()` automatically enables tabs

### For Users
1. No API changes in typer2ui
2. Just use Typer's native `add_typer()`
3. GUI automatically shows tabs

## Risks & Mitigations

**Risk 1: Flet doesn't support bottom tabs**
- Mitigation: Use top tabs or custom button row

**Risk 2: Performance with many tabs**
- Mitigation: Lazy-load tab content (create views only when tab selected)

**Risk 3: Complex nested hierarchies**
- Mitigation: Start with 1-level support, add nesting later

**Risk 4: Breaking changes to AppSpec**
- Mitigation: Add sub_apps=() as default, maintain backward compatibility

## Questions for Confirmation

1. **Tab Placement Preference:**
   - Try bottom first (Excel-style), fallback to top?
   - Or just use top tabs (standard)?

2. **Main Tab Handling:**
   - Always show "Main" tab even if empty?
   - Or hide "Main" if no root commands?

3. **Nested Sub-Apps:**
   - Support now or defer to Phase 2?
   - If now, what UI approach (nested tabs vs breadcrumbs)?

4. **Tab Naming:**
   - Auto-capitalize ("users" → "Users")?
   - Allow custom labels via decorator?

5. **Command API:**
   - Support `upp.command("users:create")` qualified names?
   - Or keep current `upp.command("create")` and use context?

---

**Status:** Ready for confirmation and approval to proceed with implementation.
