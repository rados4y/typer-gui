"""Reactive state management for UI components."""

from typing import Any, Callable, Generic, List, Optional, Tuple, TypeVar

T = TypeVar('T')


class State(Generic[T]):
    """Reactive state container that triggers UI updates on change.

    When state value changes via set(), all registered observers (UI components)
    are notified and re-rendered automatically.

    Example:
        >>> counter = ui.state(0)
        >>> ui(lambda: tg.Text(f"Count: {counter.value}"), counter)
        >>> counter.set(counter.value + 1)  # Triggers re-render
    """

    def __init__(self, initial_value: T, runner: Any):
        """Initialize state with a value.

        Args:
            initial_value: Initial state value
            runner: Runner instance for triggering re-renders
        """
        self._value: T = initial_value
        self._runner = runner
        self._observers: List[Tuple[Callable, int]] = []  # (renderer, component_id)

    @property
    def value(self) -> T:
        """Get current state value.

        Returns:
            Current value
        """
        return self._value

    def set(self, new_value: T) -> None:
        """Update state value and notify observers.

        Only triggers re-render if value actually changed.

        Args:
            new_value: New state value
        """
        if self._value != new_value:
            self._value = new_value
            self._notify_observers()

    def _notify_observers(self) -> None:
        """Re-render all components that depend on this state."""
        for renderer, component_id in self._observers:
            # Re-execute renderer to get new component
            new_component = renderer()

            # Tell runner to update the component
            self._runner.update_reactive_component(component_id, new_component)

    def _add_observer(self, renderer: Callable, component_id: int) -> None:
        """Register a component as dependent on this state.

        Args:
            renderer: Function that returns a component
            component_id: Unique ID of the component to update
        """
        self._observers.append((renderer, component_id))

    def __repr__(self) -> str:
        """String representation for debugging."""
        return f"State({self._value})"
