# AppShell Architecture - Key Decisions Required

## Executive Summary

**Status:** Architecture analysis complete
**Recommendation:** Event-driven interface with `build()` + event handlers
**Next Step:** Make decisions on 7 key questions below, then implement

---

## ✅ What We Agree On

1. **Event-Driven Architecture** - Shell handles events, not component creation
2. **Single Build Method** - `build(page, app_spec)` gives total freedom
3. **Bidirectional Communication** - App→Shell events + Shell→App callbacks
4. **No Prescriptive Structure** - Each shell builds whatever it wants

---

## 🤔 Decisions Needed

### Decision 1: Terminology

**Question:** What names should we use for core concepts?

| Concept | Option A | Option B | Option C |
|---------|----------|----------|----------|
| Commands | "action" | "command" | "operation" |
| Sub-apps | "module" | "sub_app" | "tab" |
| Run | "execute" | "run" | "invoke" |

**Recommendation:**
- **Action** (better UI terminology, less CLI-specific)
- **Module** (more generic than "sub_app", less UI-specific than "tab")
- **Run** (simplest, most common)

**Example API:**
```python
# With "action" and "module"
shell.on_action_selected(action, module)
shell.on_module_selected(module)

# vs "command" and "sub_app"
shell.on_command_selected(command, sub_app)
shell.on_sub_app_selected(sub_app)
```

**Your choice:** _________________

---

### Decision 2: Parameter Handling

**Question:** Who creates and manages parameter form controls?

#### Option A: Shell Creates and Manages (Recommended)
```python
class AppShell(ABC):
    @abstractmethod
    def build(self, page, app_spec):
        """Shell builds forms internally"""

    @abstractmethod
    def get_action_parameters(self, action) -> dict:
        """Shell extracts values from its forms"""
```

**Pros:**
- Shell has full control over form styling
- Different shells can have different form layouts
- Natural for dashboard shells (no forms)

**Cons:**
- Each shell must implement parameter extraction
- Need shared helper for standard controls

#### Option B: App Provides Controls
```python
# App creates controls
controls = app.create_parameter_controls(action)

# Shell just displays them
shell.display_parameter_form(controls)
```

**Pros:**
- Consistent parameter handling across shells
- Less code in each shell

**Cons:**
- Shell has less control over styling
- Tight coupling to Flet control types

#### Option C: Hybrid (Shell can override)
```python
class AppShell(ABC):
    def create_param_control(self, param: ParamSpec):
        """Override for custom controls, or use default"""
        return self._default_param_control(param)
```

**Pros:**
- Flexibility + consistency
- Easy to customize when needed

**Cons:**
- More API surface

**Your choice:** _________________

---

### Decision 3: Event Granularity

**Question:** How detailed should events be?

#### Option A: Coarse Events (Simpler)
```python
def on_action_executed(self, action, result, error=None):
    """Single event for execution (handles start, output, complete)"""
```

#### Option B: Fine-Grained Events (Recommended)
```python
def on_action_started(self, action):
    """Action started"""

def on_action_output(self, output, action, append=False):
    """Action produced output (can be called multiple times)"""

def on_action_completed(self, action, success, error=None):
    """Action finished"""
```

#### Option C: Very Fine-Grained
```python
def on_action_started(self, action):
def on_action_progress(self, action, percent, message):
def on_action_output_line(self, line, action):
def on_action_output_component(self, component, action):
def on_action_error(self, error, action):
def on_action_completed(self, action):
```

**Recommendation:** Option B (fine-grained but not excessive)

**Your choice:** _________________

---

### Decision 4: Module/Sub-App Support

**Question:** Should module handling be required or optional?

#### Option A: Required
```python
class AppShell(ABC):
    @abstractmethod
    def on_module_selected(self, module: str):
        """All shells MUST support modules"""
```

**Pros:** Clear expectation
**Cons:** Forces shells without modules to implement anyway

#### Option B: Optional (Shell can ignore)
```python
class AppShell(ABC):
    def on_module_selected(self, module: str):
        """Optional - override if shell supports modules"""
        pass  # Default: do nothing
```

**Pros:** Flexible
**Cons:** Less explicit

#### Option C: Detected from AppSpec
```python
class AppShell(ABC):
    def build(self, page, app_spec):
        if app_spec.sub_apps:
            self._setup_modules(app_spec.sub_apps)
```

**Pros:** Automatic
**Cons:** Shell must check app_spec

**Recommendation:** Option B (optional with pass default)

**Your choice:** _________________

---

### Decision 5: State Management Integration

**Question:** How do reactive State objects integrate with shells?

#### Option A: Shell Observes States
```python
def on_state_changed(self, state_changes: dict[str, Any]):
    """App notifies shell of state changes"""
    # Shell updates reactive components
```

#### Option B: Shell Registers Observers
```python
def register_states(self, states: list[State]):
    """Shell subscribes to states directly"""
    for state in states:
        state.subscribe(self._on_value_change)
```

#### Option C: App Manages (Shell agnostic)
```python
# App renders state changes to components
state.value = 5
rendered = render_component(state_component)
shell.on_action_output(rendered, action)
```

**Recommendation:** Option C (app manages, shell just displays output)

**Your choice:** _________________

---

### Decision 6: Modal Commands

**Question:** Who handles `modal=True` commands?

#### Option A: Shell Handles Modals
```python
def on_action_selected(self, action, module):
    if action.ui_spec.modal:
        self._show_modal(action)
    else:
        self._show_inline(action)
```

**Pros:** Shell controls all UI
**Cons:** Every shell must implement modals

#### Option B: App Handles Modals
```python
# In app/runner:
if command.ui_spec.modal:
    show_modal_dialog(command)  # App's modal
else:
    shell.on_action_selected(command)  # Shell's UI
```

**Pros:** Consistent modals across shells
**Cons:** Shell has less control

#### Option C: Optional (Shell can override)
```python
def supports_modals(self) -> bool:
    """Override to indicate modal support"""
    return False  # Default: App handles modals
```

**Recommendation:** Option C (app by default, shell can override)

**Your choice:** _________________

---

### Decision 7: Auto-Execute Behavior

**Question:** How does `auto=True` work with event architecture?

#### Option A: App Auto-Executes
```python
# In app:
if command.ui_spec.auto:
    shell.on_action_selected(command)
    params = shell.get_action_parameters(command)
    # Execute immediately
    run_command(command, params)
```

**Pros:** Shell doesn't need special handling
**Cons:** App must know about auto flag

#### Option B: Shell Decides
```python
def on_action_selected(self, action, module):
    if action.ui_spec.auto:
        params = self.get_action_parameters(action)
        self._on_user_run_action(action, params)  # Auto-trigger
```

**Pros:** Shell has full control
**Cons:** More logic in shell

#### Option C: App Notifies, Shell Executes
```python
# App calls:
shell.on_action_selected(action, auto=action.ui_spec.auto)

# Shell handles:
def on_action_selected(self, action, module, auto=False):
    if auto:
        self._auto_execute(action)
```

**Recommendation:** Option A (app auto-executes, simpler)

**Your choice:** _________________

---

## Implementation Priority

Once decisions are made:

### Phase 1: Core Interface
1. Define `AppShell` ABC with event methods
2. Define callback registration
3. Define `get_action_parameters()` method
4. Document event flow

### Phase 2: Reference Implementation
1. Implement `SidebarShell` with new interface
2. Create mock preview system
3. Test event flow

### Phase 3: Integration
1. Update `GUIRunner` to use shell
2. Migrate existing layout code
3. Update `UiApp` to accept shell parameter

### Phase 4: Additional Shells
1. Implement `DashboardShell`
2. Implement `TopNavShell`
3. Create shell gallery

---

## Quick Decision Form

Fill this out and we'll proceed with implementation:

```
DECISION 1 (Terminology):
  [ ] Action + Module (recommended)
  [ ] Command + SubApp
  [ ] Other: ___________

DECISION 2 (Parameters):
  [ ] Shell manages (recommended)
  [ ] App provides
  [ ] Hybrid

DECISION 3 (Event Granularity):
  [ ] Fine-grained: started/output/completed (recommended)
  [ ] Coarse: single executed event
  [ ] Very fine: progress, line-by-line

DECISION 4 (Module Support):
  [ ] Optional with pass default (recommended)
  [ ] Required
  [ ] Auto-detected

DECISION 5 (State Integration):
  [ ] App manages, shell displays (recommended)
  [ ] Shell observes states
  [ ] Shell registers observers

DECISION 6 (Modal Commands):
  [ ] Optional shell override, app default (recommended)
  [ ] Shell handles
  [ ] App handles

DECISION 7 (Auto-Execute):
  [ ] App auto-executes (recommended)
  [ ] Shell decides
  [ ] App notifies, shell executes
```

---

## Risk Analysis

### Low Risk Decisions
- **Terminology** - Easy to refactor later
- **Event granularity** - Can add more events later

### Medium Risk Decisions
- **Parameter handling** - Affects all shells
- **Module support** - Affects multi-module apps

### High Risk Decisions
- **State integration** - Core to reactive features
- **Modal handling** - Affects user experience

**Recommendation:** Make low/medium risk decisions first, test with SidebarShell, then decide high-risk items based on experience.

---

## Next Steps After Decisions

1. **Review decisions** - Get stakeholder approval
2. **Create minimal API** - Just event methods needed for SidebarShell
3. **Implement SidebarShell** - Prove the architecture works
4. **Test event flow** - Verify bidirectional communication
5. **Document patterns** - Best practices for shell authors
6. **Extend API** - Add more events as needed
7. **Implement more shells** - Dashboard, TopNav, etc.

---

## Questions?

- How should progressive output (`long=True`) work with events?
- Should shells expose their current state (selected action, etc.)?
- How do we handle shell-specific configuration?
- Should there be a ShellContext object passed to events?
- How do validation errors get displayed by shells?

**Ready to decide and implement!**
