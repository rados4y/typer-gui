# Typer-GUI Technical Specification

This document defines the full technical specification for implementing the `typer-gui` Python library. It is intended for direct consumption by an AI coding assistant such as Claude Code.

---

## Goal

Build a Python library called **`typer-gui`** that automatically generates a desktop GUI for existing **Typer** CLI applications, using **Flet** as the GUI framework.

Developers should be able to:

- Keep their existing Typer-based CLI code unchanged, or almost unchanged.
- Add a very small integration layer (one or two functions) to expose a GUI.
- Run something like `python my_app.py --gui` or a small bootstrap script, and get a Flet-based GUI that mirrors their Typer commands and options.

The library should aim to be **simple to integrate**, **robust**, and **extensible**.

---

## Core Requirements

### 1. Project structure

Create a proper Python package structure, for example:

- `typer_gui/`

  - `__init__.py`
  - `core.py` # Reflection & mapping from Typer app to GUI model
  - `flet_ui.py` # All Flet-specific GUI construction
  - `runner.py` # Helper entrypoints (e.g., run_gui(app))
  - `types.py` # Shared dataclasses / types for GUI models

- `examples/`

  - `basic_typer_app.py`
  - `basic_gui_runner.py`

- `pyproject.toml` or `setup.cfg` + `setup.py`
- `README.md`
- `LICENSE` (use MIT)

Use type hints everywhere and make the library ready for publishing on PyPI.

Runtime dependencies:

- `typer` (for CLI integration)
- `flet` (for the GUI)

Development tooling (not imported in library code and not required at runtime):

- `uv` for creating and managing the virtual environment / installing dependencies
- a test runner such as `pytest` for unit tests

`uv` MUST NOT be added as a runtime dependency of `typer-gui` and MUST NOT be imported anywhere in the library modules. It is only an optional tool for developers working on this project.

---

### 2. Typer integration API

Expose a **minimal public API** for developers, for example in `typer_gui.__init__`:

```python
from .runner import run_gui
from .core import build_gui_model

__all__ = ["run_gui", "build_gui_model"]
```

#### `run_gui(app, *, title=None, description=None)`

- `app`: a `typer.Typer` instance.
- `title`: optional window title override.
- `description`: optional text to show at the top of the GUI.

Behavior:

- Reflect the provided `Typer` app (commands, params, help text).
- Start a Flet application that shows a window with:

  - Left pane: list of commands.
  - Right pane: a dynamic form for the selected command.
  - Bottom area: log / output console.

#### `build_gui_model(app)`

- Introspects a `typer.Typer` app and returns a structured representation of:

  - Commands
  - Arguments / options (names, types, defaults, help text, required flags)

- This should be independent of Flet, so it can be reused or tested.
- Use dataclasses in `types.py`, e.g. `GuiApp`, `GuiCommand`, `GuiParam`.

The Typer app should **not** need to change; the library must rely on Typer’s own metadata (commands, params, annotations, defaults, etc.). Also support nested Typer apps (subcommands) if reasonably possible.

---

### 3. Reflection of Typer apps

Implement logic in `core.py` that:

1. Accepts a `typer.Typer` instance.
2. Iterates through its registered commands.
3. For each command, gathers:

   - Name (CLI name and function name)
   - Help text / short help
   - Parameters:

     - Name(s) and CLI flags
     - Annotation type (`str`, `int`, `float`, `bool`, `Enum`, etc.)
     - Default value if any
     - Required vs optional
     - Help text

4. Builds a `GuiApp` model with `GuiCommand` and `GuiParam` entries.

Handle at least these param types:

- `str`
- `int`
- `float`
- `bool`
- `Enum`

You may start with these basic types, but design the code so it can be extended later to support:

- `Path`
- `datetime`
- lists / multiple values

If something is unsupported, the GUI can either:

- Hide that parameter and show a warning in the console, or
- Render a generic text field.

---

### 4. Mapping CLI params to Flet controls

In `flet_ui.py`, implement mapping from `GuiParam` types to Flet controls:

- `str` → `TextField`
- `int` → `TextField` with numeric input mode and validation
- `float` → `TextField` with numeric/decimal validation
- `bool` → `Checkbox` or `Switch`
- `Enum` → `Dropdown` with options

For each parameter:

- Use the Typer help text (if present) as `hint_text` or helper text.
- Show default values in the controls.
- Mark required parameters clearly (e.g. with a `*` in label).

We want a simple, clean layout. For example:

- Top: optional description text and app title.
- Left: `ListView` or `NavigationRail` with commands.
- Right: for the chosen command:

  - A vertical list of form fields for each parameter.
  - A “Run” button.

- Bottom: an output area that shows:

  - Standard output of the command.
  - Standard error, if possible, styled differently.

You can assume a desktop usage first (typical window size like 900x600).

---

### 5. Running commands from GUI

When the user clicks **Run** on a command form:

1. Validate and parse the form values into proper Python types.
2. Call the underlying Typer command function **directly**, not via subprocess, to avoid re-parsing.
3. Capture output:

   - Simple option: temporarily redirect `stdout`/`stderr` using `io.StringIO` and context managers, then display it in the GUI.

4. Errors (exceptions) should be:

   - Shown in the output area with a clear error prefix.
   - Logged to console as well.

We are fine if the library is initially single-threaded as long as it doesn’t block Flet’s UI completely. If needed, offload the command execution to a background thread and update the UI via Flet’s recommended mechanisms.

---

### 6. Example usage

Create one or two small example apps under `examples/` to show intended usage.

#### `examples/basic_typer_app.py`

- A simple `typer.Typer()` app with a couple of commands, e.g.:

  - `greet(name: str, excited: bool = False)`
  - `add(a: int, b: int)`

#### `examples/basic_gui_runner.py`

An example of running the GUI for the Typer app:

```python
import typer
from typer_gui import run_gui

from basic_typer_app import app

if __name__ == "__main__":
    run_gui(app, title="Typer Demo GUI", description="Simple demo of typer-gui.")
```

Make sure this actually works when run (assuming Flet is installed).

---

### 7. Flet integration details

- Use Flet’s `flet.app()` or `flet.app(target=main)` entry style.
- Keep all Flet-specific details inside `flet_ui.py` and `runner.py`.
- `run_gui(app, ...)` should:

  - Build the GUI model using `build_gui_model(app)`.
  - Start Flet with a `main(page: flet.Page)` function that:

    - Builds the layout.
    - Binds events (e.g. command selection, Run button).
    - Updates the form when a different command is selected.

Design the Flet code to be:

- Clear and readable.
- Organized into smaller functions/components for clarity (e.g. functions that create the command list, create the form, create the output panel).

---

### 8. Error handling and edge cases

- If the Typer app has **no commands**, show a message in the GUI instead of failing.
- If a parameter type is unsupported, mark it clearly in the form (e.g. disabled field with a message).
- Validate numeric fields and show a message if parsing fails instead of crashing.
- Gracefully handle exceptions thrown by command functions.

---

### 9. Testing and quality

- Use type hints everywhere and make the code compatible with `mypy` (at least in principle).
- Add a few unit tests for the reflection logic in `core.py` (e.g., how commands and params are converted to GUI models).
- Make the public API small and clear.

---

### 10. Documentation (README)

Produce a concise `README.md` that includes:

- What `typer-gui` is.
- Installation instructions, including:

  - Standard `pip`-based installation, e.g. `pip install typer-gui` (and mentioning that `flet` and `typer` will be installed as dependencies if not already present).
  - Optional example of using `uv` for local development setup, e.g. `uv venv` followed by `uv pip install -e .` or `uv pip install typer-gui flet typer`.

`uv` should be presented as an optional development convenience, not as a required dependency for library users.

- A minimal example of a Typer app and how to launch the GUI.
- A screenshot placeholder section for the GUI (you can just describe it in text).

---

### 11. Implementation style

- Use modern Python (3.10+).
- Prefer dataclasses for the GUI model.
- Keep each module focused and cohesive.
- Code should be clean, readable, and structured as if it were going to be open-sourced.

---

## Deliverables

1. The full source tree for the `typer-gui` library as described above.
2. At least one working example that I can run locally to see the GUI.
3. Basic tests for the reflection logic.

Implement all of this now.
