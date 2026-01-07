"""Reactive state management - pure observable pattern."""

from typing import Callable, Generic, TypeVar

T = TypeVar('T')


class State(Generic[T]):
    """Observable state container that notifies observers on change.

    State is a simple observable value. When the value changes via set(),
    all registered observer callbacks are invoked. State doesn't know or
    care what observers do - it just notifies them.

    This follows the Observer pattern where State is the Subject and
    callbacks are Observers.

    Example:
        >>> counter = State(0)
        >>> counter.add_observer(lambda: print(f"Value is {counter.value}"))
        >>> counter.set(1)  # Prints: "Value is 1"
        >>> counter.set(5)  # Prints: "Value is 5"

    In UI context:
        >>> counter = ui.state(0)
        >>> ui(lambda: tg.Text(f"Count: {counter.value}"), counter)
        >>> counter.set(counter.value + 1)  # Triggers re-render
    """

    def __init__(self, initial_value: T):
        """Initialize state with a value.

        Args:
            initial_value: Initial state value
        """
        self._value: T = initial_value
        self._observers: list[Callable[[], None]] = []

    @property
    def value(self) -> T:
        """Get current state value.

        Returns:
            Current value
        """
        return self._value

    def set(self, new_value: T) -> None:
        """Update state value and notify observers.

        Only triggers notifications if value actually changed.

        Args:
            new_value: New state value
        """
        if self._value != new_value:
            self._value = new_value
            self._notify_observers()

    def _notify_observers(self) -> None:
        """Notify all observers that value has changed.

        Simply calls each observer callback. Observers are responsible
        for deciding what to do with the notification.
        """
        for observer_callback in self._observers:
            observer_callback()

    def add_observer(self, callback: Callable[[], None]) -> None:
        """Register an observer callback.

        The callback will be invoked whenever the state value changes.
        The callback receives no arguments - it can access the new value
        via the state's .value property if needed.

        Args:
            callback: Function to call when state changes
        """
        self._observers.append(callback)

    def remove_observer(self, callback: Callable[[], None]) -> None:
        """Unregister an observer callback.

        Args:
            callback: The callback to remove
        """
        if callback in self._observers:
            self._observers.remove(callback)

    def __repr__(self) -> str:
        """String representation for debugging."""
        return f"State({self._value})"
