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

### Layer 3: Runner (The "How")

- **Description**: Hosts the application in a specific environment (CLI, GUI). It is responsible for all environment-specific logic, including rendering, I/O capture, and command execution.
- **Key Modules & Classes**:
    - **`typer_ui.runners.base`**:
        - `Runner`: The abstract base class defining the common runner interface.
        - **Key Methods**:
            - `start()`: Begins the application environment (e.g., starts the Flet app).
            - `show(component)`: Renders a component by calling its channel-specific `show_*` method.
            - `update(component)`: Performs an in-place update of an already-rendered component.
            - `execute_command(name, **params)`: Captures stdout/stderr and runs the command's callback.
    - **`typer_ui.runners.cli_runner.CLIRunner`**: Executes the application in a standard terminal.
    - **`typer_ui.runners.gui_runner.GUIRunner`**: Runs the application in a Flet-based desktop window.

### Layer 4: Component (The "View")

- **Description**: Self-contained UI elements that know how to render themselves for different channels (CLI, GUI). This encapsulation makes it easy to define a new component in a single class.
- **Key Modules & Classes**:
    - **`typer_ui.ui_blocks`**: Contains all standard UI component classes.
        - `UiBlock`: The abstract base class for all components, with `show_cli()` and `show_gui()` methods.
        - `Container`: A `UiBlock` that supports progressive updates by calling `self._update()`.
        - `Text`, `Md`, `Table`, `Button`: Concrete component implementations.

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

This flow occurs when a UI component is first displayed during a command's execution. It involves the runner calling the component's channel-specific rendering method.
1.  `ui(component)` is called from the user's command function.
2.  This retrieves the active `runner` and calls `runner.show(component)`.
3.  The runner, knowing its own channel (e.g., GUI), invokes the corresponding method on the component: `component.show_gui(runner)`.
4.  The component creates the necessary Flet controls and uses `runner.add_to_output()` to add them to the main view.

### Progressive Update (e.g., `Table.add_row`)

This flow handles in-place updates for components that have already been rendered. It allows parts of the UI to change without a full redraw.
1.  A method that modifies a component's state is called, e.g., `my_table.add_row(...)`.
2.  The component updates its internal data and then calls its `self._update()` method.
3.  This call is forwarded to the runner that originally rendered it: `runner.update(self)`.
4.  The `GUIRunner` contains specific logic to efficiently update the component, such as modifying a Flet `DataTable`'s rows and refreshing the page.

## 4. How to Extend

### Adding a New UI Component

1.  Create a new class in `typer_ui/ui_blocks.py` that inherits from `UiBlock`.
2.  Define its data fields using `@dataclass`.
3.  Implement `show_cli(self, runner)` to render it in the terminal.
4.  Implement `show_gui(self, runner)` to render it using Flet controls.
5.  If the component needs to be updated after rendering, inherit from `Container` and call `self._update()` when its state changes.