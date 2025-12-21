"""Base runner abstract class."""

from abc import ABC, abstractmethod
from typing import Any, Optional
from ..specs import AppSpec


class Runner(ABC):
    """Abstract base class for all runners.

    Runners host the application in specific environments (CLI, GUI, REST)
    and handle component rendering.
    """

    def __init__(self, app_spec: AppSpec):
        """Initialize runner with application specification.

        Args:
            app_spec: Immutable application specification
        """
        self.app_spec = app_spec

    @abstractmethod
    def start(self) -> None:
        """Boot the environment and start the runner.

        This method should initialize the environment (CLI process, Flet app, REST server).
        """
        pass

    @abstractmethod
    def show(self, component) -> None:
        """Show a component by calling its appropriate show method.

        Args:
            component: UiBlock component to display
        """
        pass

    @abstractmethod
    def execute_command(
        self,
        command_name: str,
        params: dict[str, Any]
    ) -> tuple[Any, Optional[Exception]]:
        """Execute a command callback with stdout/stderr capture.

        Args:
            command_name: Name of the command to execute
            params: Parameter values for the command

        Returns:
            Tuple of (result, exception). Exception is None if successful.
        """
        pass
