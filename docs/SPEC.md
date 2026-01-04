# Typer-GUI Advanced Developer Guide

This document provides a concise overview of the Typer-GUI library's architecture and design, intended for developers looking to extend its functionality.

## 1. Purpose & Core Principle

- **Purpose**: To automatically create a GUI or CLI from a Typer application, enabling rich, interactive outputs with minimal code changes.
- **Core Principle**: **Component-centric design and simplicity.** The architecture is optimized for easily creating and adding new UI components. Control flow is based on direct method calls rather than complex event systems.

## 2. Architecture Layers & Key Code

The library is divided into four distinct layers. The public-facing API, `typer_ui.ui.Ui`, acts as a facade that coordinates these layers.

### Layer 1: Definition (The "What")

- **Description**: A static, serializable representation of the Typer application, generated at startup. It contains no execution logic.
- **Key Modules & Classes**:
    - **`typer_ui.spec_builder`**: Introspects the `typer.Typer` app to create the `AppSpec`.
    - **`typer_ui.specs`**: Contains the dataclasses for this layer.
        - `AppSpec`: Holds the entire application structure.
        - `CommandSpec`: Defines a single command, its parameters, and callback.
        - `ParamSpec`: Defines a single parameter's type, default, and help text.

### Layer 2: Controller (The "State")

- **Description**: Manages the application's session state and orchestrates command execution. It is presentation-agnostic and has no knowledge of the final UI framework being used.
- **Key Modules & Classes**:
    - **`typer_ui.ui_app`**:
        - `UIApp`: The central controller. It owns the `AppSpec` and tracks the current command.
        - **Key Methods**:
            - `select_command(name)`: Sets the active command.
            - `run_command(**kwargs)`: Executes the current command's callback via the runner.
            - `include_command(name, **kwargs)`: Executes another command inline without changing the primary selection.

### Layer 3: Runner Context (The "How")

- **Description**: Provides environment-specific context for rendering UI components. Uses stack-based architecture for lazy evaluation and observer pattern for real-time updates.
- **Key Modules & Classes**:
    - **`typer_ui.context`**:
        - `UIRunnerCtx`: Abstract base class with stack-based architecture.
        - `UiStack`: List subclass with internal observer pattern for append notifications.
        - **Key Methods**:
            - `ui(component)`: Simply appends UIBlockType to current stack (lazy evaluation).
            - `build_child(parent, child)`: Handles all complexity of building different content types.
            - `_new_ui_stack()`: Context manager for save/restore stack pattern.
    - **`typer_ui.runners.cli_context.CLIRunnerCtx`**: CLI-specific context using Rich library.
    - **`typer_ui.runners.gui_context.GUIRunnerCtx`**: GUI-specific context using Flet library.
    - **`typer_ui.runners.gui_runner.GUIRunner`**: Orchestrates GUI execution and manages Flet page.
    - **`typer_ui.runners.cli_runner.CLIRunner`**: Orchestrates CLI execution with stdout/stderr capture.

### Layer 4: Component (The "View")

- **Description**: Self-contained UI elements that know how to build themselves for different channels (CLI, GUI). Components maintain parent-child hierarchy and context references.
- **Key Modules & Classes**:
    - **`typer_ui.ui_blocks`**: Contains all standard UI component classes.
        - `UiBlock`: The abstract base class for all components.
        - **Key Methods**:
            - `build_cli(ctx)`: Build and return Rich renderable for CLI.
            - `build_gui(ctx)`: Build and return Flet control for GUI.
            - `add_child(child)`: Establish parent-child relationship.
        - **Key Attributes**:
            - `_parent`: Reference to parent component.
            - `_children`: List of child components.
            - `_ctx`: Reference to UIRunnerCtx.
            - `_flet_control`: Reference to built Flet control (GUI only).
        - `Container`: A `UiBlock` that supports progressive updates via `_update()`.
        - `Text`, `Md`, `Table`, `Row`, `Column`, `Button`: Concrete component implementations.

## 3. Execution Flows

### GUI Application Startup Flow

This flow describes how the GUI application is initialized and launched. It begins when the developer calls the main entrypoint function without the `--cli` flag.
1.  `ui.app()` is called, which determines the mode is GUI.
2.  `spec_builder.build_app_spec()` introspects the `typer.Typer` instance to create a static `AppSpec` model.
3.  `create_flet_app()` is called, which initializes the `GUIRunner` with the `AppSpec`.
4.  `ft.app(target=...)` starts the Flet application, which in turn calls the `GUIRunner.build(page)` method to construct the user interface.

### CLI Application Startup Flow

This flow describes how the application runs when invoked with the `--cli` flag. It bypasses all GUI components and executes directly in the terminal.
1.  `ui.app()` is called and detects the `--cli` argument.
2.  The `--cli` argument is removed from `sys.argv` so Typer can parse the remaining arguments correctly.
3.  `spec_builder.build_app_spec()` creates the `AppSpec`, and a `CLIRunner` is initialized.
4.  `set_current_runner()` globally registers the `CLIRunner` instance.
5.  The original `typer_app()` is invoked, which proceeds to execute the command specified on the command line.

### Initial Component Rendering

This flow occurs when a UI component is first displayed during a command's execution. Uses stack-based lazy evaluation.
1.  `ui(component)` is called from the user's command function.
2.  `ui()` retrieves the current `UIRunnerCtx.instance()` and calls `ctx.ui(component)`.
3.  `ctx.ui()` simply appends the component to `_current_stack` (lazy evaluation - not built yet).
4.  After command execution completes, the runner iterates through the stack.
5.  For each item, runner calls `ctx.build_child(root, item)` which:
    - Detects component type (str → Md, UIBlock → build, callable → execute)
    - Calls `component.build_gui(ctx)` or `component.build_cli(ctx)` as appropriate
    - Establishes parent-child relationship via `parent.add_child(child)`
    - Stores context reference `child._ctx = ctx`
    - Returns built control (ft.Control for GUI, RenderableType for CLI)
6.  Built controls are added to the output view and page is updated.

### Progressive Update (e.g., `Table.add_row`)

This flow handles in-place updates for components that have already been rendered. Components use stored context to update themselves.
1.  A method that modifies a component's state is called, e.g., `my_table.add_row(...)`.
2.  The component updates its internal data structure (e.g., `self.data.append(row)`).
3.  The component uses stored references to update:
    - Calls `self._ctx.build_child(self, cell)` to build new cell controls
    - Appends built controls to `self._flet_control` (e.g., table rows)
4.  The component calls `self._update()` which triggers `self._ctx.page.update()` to refresh the display.
5.  For long-running tasks, observers are notified immediately via UiStack's observer pattern.

## 4. How to Extend

### Adding a New UI Component

1.  Create a new class in `typer_ui/ui_blocks.py` that inherits from `UiBlock`.
2.  Define its data fields using `@dataclass`.
3.  Implement `build_cli(self, ctx) -> RenderableType` to build Rich renderable for terminal.
4.  Implement `build_gui(self, ctx) -> ft.Control` to build Flet control for GUI.
5.  Store context and control references:
    - Set `self._ctx = ctx` to access context later
    - Set `self._flet_control = control` to enable progressive updates
6.  If the component needs progressive updates, inherit from `Container` and call `self._update()` when state changes.
7.  For container components, use `ctx.build_child(self, child)` to build children uniformly.