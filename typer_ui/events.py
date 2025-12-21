"""Event system for UIApp - presentation-agnostic events."""

import time
import uuid
from dataclasses import dataclass, field
from typing import Any, Optional
from abc import ABC


@dataclass
class Event(ABC):
    """Base class for all events."""
    timestamp: float = field(default_factory=time.time, kw_only=True)
    event_id: str = field(default_factory=lambda: str(uuid.uuid4()), kw_only=True)


# === Lifecycle Events ===

@dataclass
class CommandSelected(Event):
    """Emitted when a command is selected."""
    command_name: str


@dataclass
class CommandStarted(Event):
    """Emitted when command execution starts."""
    command_name: str
    params: dict


@dataclass
class CommandFinished(Event):
    """Emitted when command execution completes."""
    command_name: str
    result: Any
    success: bool
    duration: float
    error: Optional[Exception] = None


# === Output Events ===

@dataclass
class TextEmitted(Event):
    """Emitted when text is printed to stdout/stderr."""
    text: str
    stream: str  # "stdout" or "stderr"


@dataclass
class BlockEmitted(Event):
    """Emitted when a UI block is presented."""
    block: Any  # UiBlock type (avoid circular import)


# === Container Events ===

@dataclass
class ContainerStarted(Event):
    """Emitted when entering a container context (row, grid, etc.)."""
    container_type: str  # "row", "grid", "column", "tabs"
    container_id: str
    params: dict = field(default_factory=dict)


@dataclass
class ContainerEnded(Event):
    """Emitted when exiting a container context."""
    container_id: str


# === Error Events ===

@dataclass
class ErrorRaised(Event):
    """Emitted when an error occurs."""
    exception: Exception
    traceback: str
    context: str  # "validation", "execution", "rendering"
    severity: str = "error"  # "warning", "error", "critical"


# === Validation Events ===

@dataclass
class ValidationError(Event):
    """Emitted when parameter validation fails."""
    param_name: str
    message: str
    value: Any
