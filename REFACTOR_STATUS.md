# Event-Driven Async Architecture Refactor - Status

## Overview

Implementing a complete architectural refactor as specified in SPEC.md to separate:
- **Definition Layer**: Immutable specs (AppSpec, CommandSpec, ParamSpec)
- **Controller Layer**: Async event-emitting UIApp
- **Runner Layer**: CLI/GUI/REST runners that handle presentation
- **Event Contract**: Ordered, deterministic events between controller and runners

## Completed ✅

### 1. Event System (`events.py`)
- Base `Event` class with timestamp and event_id
- Lifecycle events: `CommandSelected`, `CommandStarted`, `CommandFinished`
- Output events: `TextEmitted`, `BlockEmitted`
- Container events: `ContainerStarted`, `ContainerEnded`
- Error events: `ErrorRaised`, `ValidationError`

### 2. Immutable Specifications (`specs.py`)
- `ParamType` enum
- `ParamSpec` - frozen dataclass for parameters
- `CommandUiSpec` - GUI options (is_button, is_long, is_auto_exec)
- `CommandSpec` - frozen dataclass for commands
- `AppSpec` - frozen dataclass for application

### 3. Runner Architecture
- **`runners/base.py`**: Abstract `Runner` base class
  - `start()` - Boot environment
  - `execute_command()` - Execute with stdout/stderr capture
  - `handle_event()` - Process events
  - Event subscription/unsubscription

- **`runners/cli_runner.py`**: CLI execution
  - Direct command execution
  - stdout/stderr capture
  - Event handling (print to console)

- **`runners/gui_runner.py`**: Flet GUI
  - Flet page building
  - Real-time/buffered output
  - Event handling (update GUI)
  - Container stack for nested UI blocks

### 4. Async UIApp Controller (`ui_app.py`)
- Completely rewritten as async controller
- Event queue and processing loop
- Session state (current command, execution history)
- Intent-style API:
  - `select_command(name)`
  - `run_command(**kwargs)`
  - `include_command(name, **kwargs)`
  - `clear()`
- Event emission: `emit_event()`, `subscribe()`, `unsubscribe()`
- `UICommand` wrapper class with async methods

### 5. Async UI Blocks (`ui_blocks.py`)
- Async `present()` method
- Async context manager for `RowContext`
- Event emission via `UiContext.render()`
- Container events for row/grid/column
- Backward compatibility with sync context managers
- `UiOutput` methods updated for async

### 6. Core Reflection (`core.py`)
- Updated to build `AppSpec` instead of `GuiApp`
- `build_app_spec()` as new primary function
- `build_gui_model()` kept as deprecated alias
- Legacy `GuiCommandOptions` → `CommandUiSpec` conversion

### 7. Git Commit
✅ Committed with message: "Implement event-driven async architecture refactor (WIP)"

## Pending ⏳

### High Priority

1. **`ui.py`** - Update entry point
   - Keep `Ui` class API mostly compatible
   - Update internals to use new runners
   - Handle async execution properly
   - Update `command()` method for new UICommand

2. **`flet_ui.py`** - Migrate to new GUIRunner
   - Replace `TyperGUI` with runner-based approach
   - `create_flet_app()` should use GUIRunner
   - Event subscription and handling

3. **`runner.py`** - Update for CLIRunner
   - Replace with new CLIRunner
   - Or deprecate if redundant

4. **`__init__.py`** - Update exports
   - Export new classes (AppSpec, CommandSpec, etc.)
   - Export runners
   - Keep backward compatibility where possible

5. **`types.py`** - Deprecate or remove
   - Old types (GuiApp, GuiCommand, GuiParam) no longer used
   - May need to keep for backward compatibility

### Medium Priority

6. **Examples** - Update all examples
   - `01_basic_typer_to_gui.py`
   - `02_arguments_and_output.py`
   - `03_ui_blocks.py`
   - `04_customizations.py`
   - Handle async command methods
   - Test with new architecture

7. **Testing**
   - Basic smoke tests
   - Test CLI mode
   - Test GUI mode
   - Test event flow
   - Test async execution

### Low Priority

8. **Documentation**
   - Update README.md if API changed
   - Migration guide for existing users
   - Update examples README

9. **Cleanup**
   - Remove deprecated code
   - Clean up imports
   - Update type hints

## Architecture Summary

```
┌─────────────┐
│  Definition │  AppSpec, CommandSpec, ParamSpec (immutable)
│    Layer    │
└──────┬──────┘
       │
       ↓
┌─────────────┐
│ Controller  │  UIApp (async, event-emitting)
│    Layer    │  - select_command()
└──────┬──────┘  - run_command()
       │         - Events: CommandStarted, BlockEmitted, etc.
       │
       ↓ Events
┌─────────────┐
│   Runner    │  CLIRunner / GUIRunner / RESTRunner
│    Layer    │  - execute_command() → stdout/stderr capture
└─────────────┘  - handle_event() → print / render / serialize
```

## Key Design Decisions

1. **Big Bang Refactor**: No backward compatibility during transition
2. **Async Throughout**: UIApp, UICommand, UI blocks all async
3. **Event-Driven**: Clean separation via events
4. **ContainerStarted/ContainerEnded**: For row/grid/column lifecycle
5. **Frozen Dataclasses**: Immutable specs
6. **Single Event Queue**: Thread-safe async queue in UIApp

## Breaking Changes

- `UICommand.run()` is now async (was sync)
- `UICommand.include()` is now async
- `UICommand.select()` is now async
- UI blocks `.present()` is now async (sync fallback provided)
- `UiContext` requires `ui_app` reference
- `RowContext` is async context manager (sync support via fallback)
- `GuiApp`, `GuiCommand`, `GuiParam` replaced with `AppSpec`, `CommandSpec`, `ParamSpec`

## Next Steps

1. Complete `ui.py` update
2. Update `flet_ui.py` to use GUIRunner
3. Update `runner.py` for CLIRunner
4. Update `__init__.py` exports
5. Fix one example end-to-end
6. Test and iterate
7. Update remaining examples
8. Documentation

## Notes

- This refactor touches almost every file in the project
- Examples will not work until integration is complete
- Consider creating a feature branch if not already on one
- May want to keep old code temporarily for reference
