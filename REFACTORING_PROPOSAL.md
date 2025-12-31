# Typer-UI: Final Refactoring Proposal

**Date:** 2025-12-31
**Status:** Proposal for Review
**Priority:** HIGH

---

## Table of Contents

1. [Executive Summary](#executive-summary)
2. [Critical Issues Identified](#critical-issues-identified)
3. [Proposed Architecture Changes](#proposed-architecture-changes)
4. [Detailed Refactoring Plan](#detailed-refactoring-plan)
5. [Implementation Phases](#implementation-phases)
6. [Migration Guide](#migration-guide)
7. [Risk Assessment](#risk-assessment)

---

## Executive Summary

This proposal outlines a comprehensive refactoring of the typer-ui codebase to address critical architectural issues while maintaining backward compatibility where possible. The refactoring focuses on three main areas:

1. **Context-Based Rendering** - Replace global state with explicit context objects
2. **Interface Redesign** - Unify rendering methods with context pattern
3. **Reactive Components** - Fix dx() to produce proper reactive components instead of special wrapper types

### Key Benefits

- **Better Testability** - Eliminate global state, enable proper unit testing
- **Clear Extensibility** - Add new renderers (REST, JSON, etc.) without modifying components
- **Improved Maintainability** - Smaller, focused classes with single responsibilities
- **Type Safety** - Better IDE support and type checking
- **Thread Safety** - Proper context management instead of global variables

---

## Critical Issues Identified

### Issue 1: Global Runner State ⚠️ CRITICAL

**Current Implementation:**
```python
# ui_blocks.py
_current_runner = None  # Module-level global

def get_current_runner():
    return _current_runner

def set_current_runner(runner):
    global _current_runner
    _current_runner = runner

# Used everywhere:
def ui(component_or_value: Any = None):
    runner = get_current_runner()  # Implicit dependency
    runner.show(component)
```

**Problems:**
- Thread unsafe
- Hard to test
- Hidden dependencies
- Saves/restores scattered across codebase

**Impact:** HIGH - affects testing, threading, maintainability

---

### Issue 2: dx() Implementation ⚠️ DESIGN FLAW

**Current Implementation:**
```python
@dataclass
class DynamicBlock:  # Special type, not a real component
    renderer: Callable
    dependencies: tuple

def _render_dynamic_block(dyn_block: DynamicBlock, runner) -> Column:
    container = Column([])  # Hardcoded to Column
    _, flet_control = runner.execute_in_reactive_mode(container, dyn_block.renderer)
    # ... register observers
    return container  # Returns Column, not DynamicBlock
```

**Problems:**
1. `DynamicBlock` is not a `UiBlock` - special case handling
2. Hardcoded to return `Column` - inflexible
3. Assumes GUIRunner has `execute_in_reactive_mode()` - tight coupling
4. Mixing reactive rendering logic with component creation
5. Cannot nest dynamic blocks properly

**User Feedback:**
> "I don't like the way dx() is implemented, it should produce regular component that is refreshing its controls when state changes."

**Impact:** MEDIUM - limits composability, creates technical debt

---

### Issue 3: Inconsistent Interface Design ⚠️ EXTENSIBILITY

**Current Implementation:**
```python
class UiBlock(ABC):
    @abstractmethod
    def show_cli(self, runner) -> None: ...

    @abstractmethod
    def show_gui(self, runner) -> None: ...

    def show_rest(self, runner) -> None:  # Not abstract, default impl
        runner.add_element(self.to_dict())
```

**Problems:**
1. Method names inconsistent (`show_cli`, `show_gui` vs `show_rest`)
2. Adding new output format requires modifying base class
3. Runner type not explicit in signature
4. No clear control flow (returns None, side effects)

**User Feedback:**
> "Maybe it will be more generic to have methods like to_ui(UIRunnerContext), to_cli(CliRunnerContext), to_rest(RestRunnerContext). UI runner context should provide current controls stack that ui() should attach new control etc."

**Impact:** MEDIUM - limits extensibility to new formats (JSON, HTML, etc.)

---

## Proposed Architecture Changes

### Change 1: Context-Based Rendering Architecture

**New Design:**

```python
# core/context.py
from abc import ABC, abstractmethod
from typing import Any, List, Generic, TypeVar

T = TypeVar('T')  # Control type (ft.Control for GUI, str for CLI, dict for REST)

class RenderContext(ABC, Generic[T]):
    """Base context for rendering components to specific output format."""

    def __init__(self):
        self._controls_stack: List[List[T]] = [[]]  # Stack of control lists

    @property
    def current_container(self) -> List[T]:
        """Get the current container to add controls to."""
        return self._controls_stack[-1]

    def push_container(self, container: List[T]):
        """Push a new container onto the stack."""
        self._controls_stack.append(container)

    def pop_container(self) -> List[T]:
        """Pop the current container from the stack."""
        if len(self._controls_stack) <= 1:
            raise RuntimeError("Cannot pop root container")
        return self._controls_stack.pop()

    @abstractmethod
    def add_control(self, control: T) -> None:
        """Add a control to the current container."""
        pass

    @abstractmethod
    def update_control(self, control: T) -> None:
        """Update an existing control."""
        pass


class CLIRenderContext(RenderContext[str]):
    """Context for rendering to CLI (terminal output)."""

    def __init__(self, output_stream):
        super().__init__()
        self.output_stream = output_stream

    def add_control(self, control: str) -> None:
        """Add text to output."""
        self.current_container.append(control)
        print(control, file=self.output_stream)

    def update_control(self, control: str) -> None:
        """CLI doesn't support updates, just print again."""
        print(control, file=self.output_stream)


class GUIRenderContext(RenderContext['ft.Control']):
    """Context for rendering to GUI (Flet controls)."""

    def __init__(self, page: 'ft.Page', output_view: 'ft.Column'):
        super().__init__()
        self.page = page
        self.output_view = output_view
        # Root container is the output_view.controls
        self._controls_stack[0] = output_view.controls

    def add_control(self, control: 'ft.Control') -> None:
        """Add Flet control to current container."""
        self.current_container.append(control)
        if self.page:
            self.page.update()

    def update_control(self, control: 'ft.Control') -> None:
        """Update Flet control."""
        if self.page:
            control.update()


class RESTRenderContext(RenderContext[dict]):
    """Context for rendering to REST API (JSON objects)."""

    def __init__(self):
        super().__init__()

    def add_control(self, control: dict) -> None:
        """Add JSON object to response."""
        self.current_container.append(control)

    def update_control(self, control: dict) -> None:
        """REST doesn't support live updates."""
        pass

    def to_json(self) -> List[dict]:
        """Get the complete JSON response."""
        return self._controls_stack[0]


# Context management
_current_context: Optional[RenderContext] = None

def get_current_context() -> RenderContext:
    """Get the current render context."""
    if _current_context is None:
        raise RuntimeError("No render context. Must be called within command execution.")
    return _current_context

def set_current_context(context: Optional[RenderContext]):
    """Set the current render context."""
    global _current_context
    _current_context = context


class RenderContextManager:
    """Context manager for render contexts."""

    def __init__(self, context: RenderContext):
        self.context = context
        self.previous_context = None

    def __enter__(self):
        self.previous_context = get_current_context() if _current_context else None
        set_current_context(self.context)
        return self.context

    def __exit__(self, *args):
        set_current_context(self.previous_context)
```

**Usage:**
```python
# In runner
with RenderContextManager(CLIRenderContext(sys.stdout)):
    command.execute()
    # Inside execute:
    ctx = get_current_context()
    component.render(ctx)
```

---

### Change 2: Unified Component Interface

**New Design:**

```python
# core/component.py
from abc import ABC, abstractmethod
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from .context import RenderContext, CLIRenderContext, GUIRenderContext, RESTRenderContext

class Component(ABC):
    """Base class for all UI components.

    Components implement rendering for different contexts.
    The context provides the output destination and control stack.
    """

    @abstractmethod
    def render(self, context: 'RenderContext') -> None:
        """Render component to the given context.

        This method dispatches to specific render implementations
        based on context type.

        Args:
            context: The render context (CLI, GUI, REST, etc.)
        """
        pass

    # Convenience methods for type-specific rendering
    # These are called by render() after type checking

    def render_cli(self, context: 'CLIRenderContext') -> None:
        """Render to CLI context (terminal).

        Override this method to customize CLI rendering.
        Default implementation converts to text and prints.
        """
        text = self.to_text()
        context.add_control(text)

    def render_gui(self, context: 'GUIRenderContext') -> None:
        """Render to GUI context (Flet).

        Override this method to customize GUI rendering.
        Must create and add Flet controls to context.
        """
        raise NotImplementedError(
            f"{self.__class__.__name__} must implement render_gui()"
        )

    def render_rest(self, context: 'RESTRenderContext') -> None:
        """Render to REST context (JSON).

        Override this method to customize REST rendering.
        Default implementation uses to_dict().
        """
        data = self.to_dict()
        context.add_control(data)

    # Default implementations for serialization

    def to_text(self) -> str:
        """Convert component to plain text.

        Used by CLI rendering and as fallback.
        Override for custom text representation.
        """
        return f"[{self.__class__.__name__}]"

    def to_dict(self) -> dict:
        """Convert component to dictionary for JSON/REST.

        Override for custom JSON representation.
        """
        return {"type": self.__class__.__name__.lower()}


# Concrete implementation example
class Text(Component):
    """Plain text component."""

    def __init__(self, content: str):
        self.content = content

    def render(self, context: RenderContext) -> None:
        """Dispatch to appropriate render method based on context type."""
        if isinstance(context, CLIRenderContext):
            self.render_cli(context)
        elif isinstance(context, GUIRenderContext):
            self.render_gui(context)
        elif isinstance(context, RESTRenderContext):
            self.render_rest(context)
        else:
            raise ValueError(f"Unsupported context type: {type(context)}")

    def render_cli(self, context: CLIRenderContext) -> None:
        """Print plain text to CLI."""
        context.add_control(self.content)

    def render_gui(self, context: GUIRenderContext) -> None:
        """Create Flet Text control."""
        import flet as ft
        control = ft.Text(self.content)
        context.add_control(control)

    def to_text(self) -> str:
        return self.content

    def to_dict(self) -> dict:
        return {"type": "text", "content": self.content}
```

**Benefits:**
1. Single `render()` method with context dispatch
2. Easy to add new output formats (just add new context type)
3. Type-safe context access
4. Clear control flow (context manages output)
5. No need to modify base class for new formats

---

### Change 3: Proper Reactive Component Design

**Problem with Current dx():**
```python
# Current: dx() returns DynamicBlock (not a Component)
ui(dx(lambda: f"Count: {counter.value}", counter))
# Returns Column internally, user doesn't know
```

**New Design - Reactive Component:**

```python
# core/reactive.py
from typing import Callable, List
from .component import Component
from .context import RenderContext, GUIRenderContext

class ReactiveComponent(Component):
    """A component that auto-refreshes when state changes.

    Instead of being a special wrapper type, ReactiveComponent is
    a proper Component that manages its own refresh logic.
    """

    def __init__(self, renderer: Callable[[], Component], *dependencies):
        """Create a reactive component.

        Args:
            renderer: Function that returns a Component
            *dependencies: State objects to observe
        """
        self.renderer = renderer
        self.dependencies = dependencies
        self._rendered_component: Optional[Component] = None
        self._context: Optional[RenderContext] = None
        self._control_index: Optional[int] = None

        # Register as observer of all dependencies
        from ..state import State
        for dep in dependencies:
            if isinstance(dep, State):
                dep.add_observer(self._on_state_change)

    def render(self, context: RenderContext) -> None:
        """Render the reactive component."""
        # Store context for future updates
        self._context = context

        # Initial render
        self._refresh()

    def _refresh(self):
        """Re-render by calling renderer and updating display."""
        if not self._context:
            return

        # Execute renderer to get new component
        new_component = self.renderer()

        if isinstance(self._context, GUIRenderContext):
            # GUI: We can update in place
            if self._rendered_component is None:
                # First render - add control
                # We need a container to hold the dynamic content
                import flet as ft
                self._container = ft.Column(controls=[], spacing=5)

                # Render into container's controls
                with ContainerContext(self._context, self._container.controls):
                    new_component.render(self._context)

                # Add container to main output
                self._context.add_control(self._container)
            else:
                # Update - clear container and re-render
                self._container.controls.clear()
                with ContainerContext(self._context, self._container.controls):
                    new_component.render(self._context)

                # Update the container
                self._context.update_control(self._container)
        else:
            # CLI/REST: Just render again (can't update in place)
            new_component.render(self._context)

        self._rendered_component = new_component

    def _on_state_change(self):
        """Called when any dependency state changes."""
        self._refresh()

    # Serialization
    def to_text(self) -> str:
        if self._rendered_component:
            return self._rendered_component.to_text()
        return "[ReactiveComponent]"

    def to_dict(self) -> dict:
        if self._rendered_component:
            return {
                "type": "reactive",
                "content": self._rendered_component.to_dict()
            }
        return {"type": "reactive"}


class ContainerContext:
    """Context manager to temporarily change control stack."""

    def __init__(self, render_context: RenderContext, container: List):
        self.render_context = render_context
        self.container = container

    def __enter__(self):
        self.render_context.push_container(self.container)
        return self.container

    def __exit__(self, *args):
        self.render_context.pop_container()


# New dx() implementation
def dx(renderer: Callable[[], Component], *dependencies) -> ReactiveComponent:
    """Create a reactive component that updates when state changes.

    Args:
        renderer: Function that returns a Component to display
        *dependencies: State objects to observe

    Returns:
        ReactiveComponent (a proper Component, not a wrapper)

    Example:
        >>> counter = app.state(0)
        >>> # dx() returns a ReactiveComponent (is a Component)
        >>> reactive_text = dx(lambda: Text(f"Count: {counter.value}"), counter)
        >>> ui(reactive_text)
        >>>
        >>> # Can also use inline:
        >>> ui(dx(lambda: Md(f"# Count: {counter.value}"), counter))
    """
    return ReactiveComponent(renderer, *dependencies)
```

**Benefits:**
1. `dx()` returns a proper `Component` (ReactiveComponent)
2. Can be nested, composed, stored in variables
3. Self-contained refresh logic
4. Works uniformly across CLI/GUI/REST
5. No special case handling in `ui()`

**Migration:**
```python
# Before (returns DynamicBlock, special handling):
ui(dx(lambda: f"Count: {counter.value}", counter))

# After (returns ReactiveComponent, regular Component):
ui(dx(lambda: Text(f"Count: {counter.value}"), counter))
# Or with string auto-conversion:
ui(dx(lambda: md(f"Count: {counter.value}"), counter))
```

---

### Change 4: Simplified ui() Function

**Current Implementation (Complex):**
```python
def ui(component_or_value: Any = None) -> UiBlock:
    runner = get_current_runner()  # Global state

    # Type coercion (20 lines)
    if isinstance(component_or_value, DynamicBlock):  # Special case
        return _render_dynamic_block(...)
    # ... more special cases

    # Reactive mode check
    if runner.is_reactive_mode():  # Another special case
        runner.add_to_reactive_container(component)
    else:
        runner.show(component)

    # Presentation tracking
    if hasattr(component, '_mark_presented'):
        component._mark_presented(runner)

    return component
```

**New Implementation (Simple):**
```python
def ui(component_or_value: Any = None) -> Component:
    """Present a component or value.

    Auto-converts values to components:
    - None → Text("")
    - str → Md(str)
    - Component → unchanged
    - other → Text(str(value))

    Args:
        component_or_value: Component or value to display

    Returns:
        The component that was displayed
    """
    # Get context (replaces get_current_runner)
    context = get_current_context()

    # Convert to component if needed
    component = to_component(component_or_value)

    # Render component to context
    component.render(context)

    return component


def to_component(value: Any) -> Component:
    """Convert value to Component.

    This is the single place for type coercion logic.
    """
    if isinstance(value, Component):
        return value
    if value is None:
        return Text("")
    if isinstance(value, str):
        return Md(value)
    return Text(str(value))
```

**Benefits:**
1. No global state access
2. No special cases (DynamicBlock, reactive mode)
3. Single responsibility (convert + render)
4. Easy to test
5. Clear control flow

---

## Detailed Refactoring Plan

### Phase 1: Foundation (Week 1-2)

#### 1.1 Create Core Module Structure
```
typer_ui/
├── core/
│   ├── __init__.py
│   ├── context.py        # RenderContext hierarchy
│   ├── component.py      # Component base class
│   └── reactive.py       # ReactiveComponent
```

**Tasks:**
- [ ] Create `core/context.py` with RenderContext classes
- [ ] Create `core/component.py` with Component base class
- [ ] Create `core/reactive.py` with ReactiveComponent
- [ ] Add type stubs for better IDE support

#### 1.2 Implement Context Management

**File:** `core/context.py`

```python
class RenderContext(ABC, Generic[T]):
    """Base context for rendering."""
    # ... (implementation above)

class CLIRenderContext(RenderContext[str]):
    # ... (implementation above)

class GUIRenderContext(RenderContext['ft.Control']):
    # ... (implementation above)

class RESTRenderContext(RenderContext[dict]):
    # ... (implementation above)
```

**Testing:**
```python
# test_context.py
def test_cli_context_controls_stack():
    ctx = CLIRenderContext(io.StringIO())
    assert len(ctx._controls_stack) == 1

    # Push new container
    new_container = []
    ctx.push_container(new_container)
    assert ctx.current_container is new_container

    # Pop container
    popped = ctx.pop_container()
    assert popped is new_container
```

#### 1.3 Migrate Component Base Class

**Create Adapter Pattern for Backward Compatibility:**

```python
# ui_blocks.py (temporary during migration)
from .core.component import Component as NewComponent
from .core.context import RenderContext, CLIRenderContext, GUIRenderContext

class UiBlock(ABC):
    """DEPRECATED: Use core.component.Component instead.

    This class provides backward compatibility during migration.
    """

    @abstractmethod
    def show_cli(self, runner) -> None:
        """DEPRECATED: Implement render_cli() instead."""
        pass

    @abstractmethod
    def show_gui(self, runner) -> None:
        """DEPRECATED: Implement render_gui() instead."""
        pass

    # Adapter: calls old show_* methods from new render() method
    def render(self, context: RenderContext) -> None:
        """Adapter that calls legacy show_* methods."""
        if isinstance(context, CLIRenderContext):
            # Create fake runner for backward compat
            runner = _create_legacy_cli_runner(context)
            self.show_cli(runner)
        elif isinstance(context, GUIRenderContext):
            runner = _create_legacy_gui_runner(context)
            self.show_gui(runner)


# New components inherit from Component
class Text(Component):  # Not UiBlock
    def render_cli(self, context: CLIRenderContext):
        context.add_control(self.content)

    def render_gui(self, context: GUIRenderContext):
        import flet as ft
        context.add_control(ft.Text(self.content))
```

---

### Phase 2: Component Migration (Week 3-4)

#### 2.1 Migrate Simple Components

**Order:**
1. Text (simplest)
2. Md
3. Button
4. Link
5. TextInput

**Migration Pattern for Each Component:**

```python
# Before: ui_blocks.py
class Text(UiBlock):
    def show_cli(self, runner):
        print(self.content)

    def show_gui(self, runner):
        import flet as ft
        runner.add_to_output(ft.Text(self.content))

# After: components/simple.py
from ..core.component import Component
from ..core.context import CLIRenderContext, GUIRenderContext

class Text(Component):
    def __init__(self, content: str):
        self.content = content

    def render_cli(self, context: CLIRenderContext):
        context.add_control(self.content)

    def render_gui(self, context: GUIRenderContext):
        import flet as ft
        control = ft.Text(self.content)
        context.add_control(control)

    def to_text(self) -> str:
        return self.content

    def to_dict(self) -> dict:
        return {"type": "text", "content": self.content}
```

#### 2.2 Migrate Container Components

**Special Handling for Row, Column:**

```python
# components/layout.py
class Column(Component):
    def __init__(self, children: List[Component]):
        self.children = children

    def render_cli(self, context: CLIRenderContext):
        """Render children vertically."""
        for child in self.children:
            child.render(context)

    def render_gui(self, context: GUIRenderContext):
        """Create Flet Column with child controls."""
        import flet as ft

        # Create container for children
        child_controls = []

        # Render each child into temporary container
        with ContainerContext(context, child_controls):
            for child in self.children:
                child.render(context)

        # Create Flet Column with all child controls
        column = ft.Column(controls=child_controls, spacing=5)
        context.add_control(column)
```

#### 2.3 Migrate Table (Complex Component)

**Handle Progressive Rendering:**

```python
class Table(Component):
    def __init__(self, cols: List[str], data: List[List[Any]], title: str = ""):
        self.cols = cols
        self.data = data
        self.title = title
        self._gui_control: Optional['ft.DataTable'] = None
        self._context: Optional[GUIRenderContext] = None

    def render_gui(self, context: GUIRenderContext):
        """Render as Flet DataTable."""
        import flet as ft

        # Create DataTable
        self._gui_control = ft.DataTable(
            columns=[ft.DataColumn(ft.Text(col)) for col in self.cols],
            rows=[
                ft.DataRow(cells=[ft.DataCell(ft.Text(str(cell))) for cell in row])
                for row in self.data
            ]
        )

        self._context = context
        context.add_control(self._gui_control)

    def add_row(self, row: List[Any]):
        """Add row with auto-update in GUI."""
        self.data.append(row)

        # Update GUI if rendered
        if self._gui_control and self._context:
            import flet as ft
            new_row = ft.DataRow(
                cells=[ft.DataCell(ft.Text(str(cell))) for cell in row]
            )
            self._gui_control.rows.append(new_row)
            self._context.update_control(self._gui_control)

    # Context manager for progressive rendering
    def __enter__(self):
        return self

    def __exit__(self, *args):
        pass
```

---

### Phase 3: Runner Refactoring (Week 5-6)

#### 3.1 Update Runners to Use Context

**CLIRunner:**
```python
class CLIRunner(Runner):
    def __init__(self, app_spec: AppSpec, ui_app):
        self.app_spec = app_spec
        self.ui_app = ui_app
        self.context: Optional[CLIRenderContext] = None

    def execute_command(self, command_name: str, params: dict) -> ExecutionResult:
        """Execute command with CLI context."""
        # Find command
        command_spec = self._find_command(command_name)

        # Create CLI context
        output_buffer = StringIO()
        self.context = CLIRenderContext(output_buffer)

        # Execute in context
        with RenderContextManager(self.context):
            try:
                result = command_spec.callback(**params)
                exception = None
            except Exception as e:
                result = None
                exception = e

        # Get output
        output_text = output_buffer.getvalue()

        return ExecutionResult(
            result=result,
            exception=exception,
            output_text=output_text
        )
```

**GUIRunner:**
```python
class GUIRunner(Runner):
    def __init__(self, app_spec: AppSpec, ui_app):
        self.app_spec = app_spec
        self.ui_app = ui_app
        self.page: Optional[ft.Page] = None
        self.context: Optional[GUIRenderContext] = None

    async def execute_command(self, command_name: str, params: dict) -> ExecutionResult:
        """Execute command with GUI context."""
        command_spec = self._find_command(command_name)

        # Get output view for this command
        view = self._get_command_view(command_name)

        # Create GUI context pointing to output view
        self.context = GUIRenderContext(self.page, view.output_view)

        # Execute in context
        with RenderContextManager(self.context):
            try:
                result = await self._execute_with_strategy(command_spec, params)
                exception = None
            except Exception as e:
                result = None
                exception = e

        # Capture text output
        output_text = self.context.to_text()  # Convert controls to text

        return ExecutionResult(
            result=result,
            exception=exception,
            output_text=output_text
        )
```

#### 3.2 Extract Execution Strategies

```python
# runners/strategies.py
class ExecutionStrategy(ABC):
    @abstractmethod
    async def execute(
        self,
        command: CommandSpec,
        params: dict,
        context: RenderContext
    ) -> Any:
        """Execute command and return result."""
        pass


class SyncExecutionStrategy(ExecutionStrategy):
    async def execute(self, command: CommandSpec, params: dict, context: RenderContext) -> Any:
        """Execute synchronous command."""
        return command.callback(**params)


class AsyncExecutionStrategy(ExecutionStrategy):
    async def execute(self, command: CommandSpec, params: dict, context: RenderContext) -> Any:
        """Execute async command."""
        return await command.callback(**params)


class ThreadedExecutionStrategy(ExecutionStrategy):
    async def execute(self, command: CommandSpec, params: dict, context: RenderContext) -> Any:
        """Execute in background thread with real-time updates."""
        import asyncio
        from concurrent.futures import ThreadPoolExecutor

        def run_in_thread():
            return command.callback(**params)

        loop = asyncio.get_event_loop()
        with ThreadPoolExecutor() as executor:
            result = await loop.run_in_executor(executor, run_in_thread)

        return result


class ExecutionStrategyFactory:
    @staticmethod
    def get_strategy(command: CommandSpec) -> ExecutionStrategy:
        """Select appropriate execution strategy."""
        if command.ui_spec.long:
            return ThreadedExecutionStrategy()
        elif inspect.iscoroutinefunction(command.callback):
            return AsyncExecutionStrategy()
        return SyncExecutionStrategy()
```

---

### Phase 4: Update output.py (Week 7)

#### 4.1 Simplify ui() Function

```python
# output.py
from .core.context import get_current_context
from .core.component import Component
from .core.reactive import ReactiveComponent

def ui(component_or_value: Any = None) -> Component:
    """Present a component or value.

    Args:
        component_or_value: Component or value to display

    Returns:
        The component that was displayed
    """
    context = get_current_context()
    component = to_component(component_or_value)
    component.render(context)
    return component


def to_component(value: Any) -> Component:
    """Convert value to Component."""
    if isinstance(value, Component):
        return value
    if value is None:
        return Text("")
    if isinstance(value, str):
        return Md(value)
    return Text(str(value))


def dx(renderer: Callable[[], Component], *dependencies) -> ReactiveComponent:
    """Create reactive component.

    Args:
        renderer: Function returning a Component
        *dependencies: State objects to observe

    Returns:
        ReactiveComponent
    """
    return ReactiveComponent(renderer, *dependencies)


# Convenience functions
def text(value: str) -> Component:
    """Display plain text (not markdown)."""
    return ui(Text(value))


def md(markdown: str) -> Component:
    """Display markdown."""
    return ui(Md(markdown))
```

---

### Phase 5: Testing (Week 8)

#### 5.1 Unit Tests

```python
# tests/test_component.py
def test_text_component_cli():
    """Test Text component renders to CLI."""
    output = StringIO()
    context = CLIRenderContext(output)

    text = Text("Hello World")
    text.render(context)

    assert output.getvalue() == "Hello World\n"


def test_text_component_gui():
    """Test Text component renders to GUI."""
    page = Mock()
    output_view = Mock()
    output_view.controls = []

    context = GUIRenderContext(page, output_view)

    text = Text("Hello World")
    text.render(context)

    assert len(output_view.controls) == 1
    assert isinstance(output_view.controls[0], ft.Text)
    assert output_view.controls[0].value == "Hello World"


def test_reactive_component_updates():
    """Test ReactiveComponent refreshes on state change."""
    state = State(0)

    # Create reactive component
    reactive = dx(lambda: Text(f"Count: {state.value}"), state)

    # Render
    output = StringIO()
    context = CLIRenderContext(output)
    reactive.render(context)

    assert "Count: 0" in output.getvalue()

    # Change state
    state.set(1)

    # Should re-render
    assert "Count: 1" in output.getvalue()
```

#### 5.2 Integration Tests

```python
# tests/test_integration.py
def test_full_command_execution_cli():
    """Test complete command execution in CLI mode."""
    app = typer.Typer()

    @app.command()
    def greet(name: str):
        ui(f"# Hello {name}!")
        ui(Text("Welcome to the app"))

    ui_app = UiApp(app, title="Test")

    # Execute in CLI mode
    result = ui_app._execute_cli_command("greet", {"name": "Alice"})

    assert result.exception is None
    assert "HELLO ALICE!" in result.output_text
    assert "Welcome to the app" in result.output_text


def test_reactive_component_in_gui():
    """Test reactive component updates in GUI."""
    # ... test with mock Flet page
```

---

## Implementation Phases

### Phase 1: Foundation (Weeks 1-2)
- ✅ Create core module structure
- ✅ Implement RenderContext hierarchy
- ✅ Implement Component base class
- ✅ Implement ReactiveComponent
- ✅ Add comprehensive tests

### Phase 2: Component Migration (Weeks 3-4)
- ✅ Migrate simple components (Text, Md)
- ✅ Migrate interactive components (Button, Link, TextInput)
- ✅ Migrate container components (Row, Column)
- ✅ Migrate complex components (Table, Tabs)
- ✅ Add backward compatibility adapters

### Phase 3: Runner Refactoring (Weeks 5-6)
- ✅ Update CLIRunner to use RenderContext
- ✅ Update GUIRunner to use RenderContext
- ✅ Extract execution strategies
- ✅ Extract view builders
- ✅ Test runner refactoring

### Phase 4: API Update (Week 7)
- ✅ Simplify ui() function
- ✅ Update dx() implementation
- ✅ Remove global _current_runner
- ✅ Update all examples
- ✅ Update documentation

### Phase 5: Testing & Polish (Week 8)
- ✅ Comprehensive unit tests
- ✅ Integration tests
- ✅ Performance testing
- ✅ Documentation updates
- ✅ Migration guide

---

## Migration Guide

### For Library Users

#### Before (Current API):
```python
import typer
import typer_ui as tu
from typer_ui import ui, md, dx

typer_app = typer.Typer()
app = tu.UiApp(typer_app, title="My App")

@typer_app.command()
def show_data():
    ui("# Data")
    ui(tu.Table(cols=["A", "B"], data=[[1, 2]]))

    state = app.state(0)
    ui(dx(lambda: f"Count: {state.value}", state))
```

#### After (New API):
```python
import typer
import typer_ui as tu
from typer_ui import ui, text, md, dx

typer_app = typer.Typer()
app = tu.UiApp(typer_app, title="My App")

@typer_app.command()
def show_data():
    ui("# Data")  # Still works (string → Markdown)
    ui(tu.Table(cols=["A", "B"], data=[[1, 2]]))  # Still works

    state = app.state(0)
    # NOW: renderer must return Component, not string
    ui(dx(lambda: md(f"Count: {state.value}"), state))
    # OR use Text explicitly:
    ui(dx(lambda: Text(f"Count: {state.value}"), state))
```

**Key Changes:**
1. `dx()` renderer must return Component (not raw string)
2. Use `md()` or `Text()` inside dx() renderer
3. Everything else stays the same

### For Library Developers

#### Adding New Output Format:

```python
# 1. Create new RenderContext
class HTMLRenderContext(RenderContext[str]):
    """Context for rendering to HTML."""

    def __init__(self):
        super().__init__()
        self._html_parts = []

    def add_control(self, control: str):
        self._html_parts.append(control)

    def to_html(self) -> str:
        return "".join(self._html_parts)

# 2. Implement render_html() in components
class Text(Component):
    def render_html(self, context: HTMLRenderContext):
        html = f"<p>{self.content}</p>"
        context.add_control(html)

# 3. Create HTMLRunner
class HTMLRunner(Runner):
    def execute_command(self, command_name, params):
        context = HTMLRenderContext()
        with RenderContextManager(context):
            result = command.callback(**params)
        return context.to_html()
```

#### Adding New Component:

```python
# Just create a new file - no need to modify ui_blocks.py!
# components/custom.py
from typer_ui.core.component import Component
from typer_ui.core.context import CLIRenderContext, GUIRenderContext

class MyCustomComponent(Component):
    def __init__(self, value):
        self.value = value

    def render_cli(self, context: CLIRenderContext):
        context.add_control(f"[Custom: {self.value}]")

    def render_gui(self, context: GUIRenderContext):
        import flet as ft
        control = ft.Container(
            content=ft.Text(f"Custom: {self.value}"),
            border=ft.border.all(1, ft.colors.BLUE)
        )
        context.add_control(control)
```

---

## Risk Assessment

### High Risk
1. **Breaking changes to dx()** - Users must update renderer functions
   - **Mitigation:** Provide clear migration guide, deprecation warnings

2. **Performance impact** - Context management overhead
   - **Mitigation:** Benchmark before/after, optimize hot paths

### Medium Risk
3. **Backward compatibility** - Some internal APIs will change
   - **Mitigation:** Provide adapter classes during transition

4. **Testing coverage** - Need comprehensive tests
   - **Mitigation:** Write tests alongside refactoring

### Low Risk
5. **Documentation updates** - Need to update all docs
   - **Mitigation:** Update docs incrementally with code changes

---

## Success Criteria

### Technical
- ✅ All tests pass (unit + integration)
- ✅ No global state (eliminated _current_runner)
- ✅ Thread-safe execution
- ✅ Performance within 10% of current

### User Experience
- ✅ Clear migration path documented
- ✅ Examples updated and working
- ✅ Error messages improved
- ✅ Type hints complete

### Code Quality
- ✅ SOLID principles followed
- ✅ No god objects (files < 300 lines)
- ✅ Clear separation of concerns
- ✅ Easy to extend (new formats, components)

---

## Next Steps

1. **Review this proposal** - Get team feedback
2. **Create POC** - Implement Phase 1 as proof of concept
3. **Performance testing** - Benchmark context overhead
4. **Finalize plan** - Adjust based on POC results
5. **Begin implementation** - Start Phase 1

---

## Appendix: File Structure After Refactoring

```
typer_ui/
├── __init__.py                  # Public API exports
├── output.py                    # ui(), md(), dx() functions
├── ui_app.py                    # UiApp, UICommand
├── state.py                     # State management
├── specs.py                     # Data models
├── spec_builder.py              # Reflection
├── core/
│   ├── __init__.py
│   ├── context.py               # RenderContext hierarchy
│   ├── component.py             # Component base class
│   └── reactive.py              # ReactiveComponent
├── components/
│   ├── __init__.py
│   ├── simple.py                # Text, Md
│   ├── layout.py                # Row, Column
│   ├── data.py                  # Table
│   ├── interactive.py           # Button, Link, TextInput
│   └── composite.py             # Tabs, Tab
└── runners/
    ├── __init__.py
    ├── base.py                  # Runner ABC
    ├── cli_runner.py            # CLIRunner
    ├── gui_runner.py            # GUIRunner (refactored)
    ├── strategies.py            # Execution strategies
    └── builders.py              # View builders

# Deprecated (removed after migration):
# - ui_blocks.py (split into components/*)
```

**Total Lines Estimate:**
- Before: ~3500 lines
- After: ~4000 lines (more files, but smaller, focused modules)
- Average file size: ~150 lines (down from ~500)

---

## Conclusion

This refactoring addresses the critical architectural issues while maintaining a clear migration path. The context-based rendering architecture provides:

1. **Better separation of concerns** - Components focus on what to display, contexts handle how
2. **Easier extensibility** - Add new output formats without modifying components
3. **Improved testability** - No global state, dependency injection
4. **Type safety** - Generic contexts with proper type hints
5. **Better dx() design** - Returns proper Component instead of special wrapper

The refactoring is ambitious but achievable in 8 weeks with proper planning and testing.
