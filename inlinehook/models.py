"""Data models used by InlineHookKit."""

from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum
from typing import Optional


class HookStatus(Enum):
    """Possible lifecycle states of a hook."""

    NOT_INSTALLED = "not_installed"
    INSTALLED = "installed"
    REMOVED = "removed"
    FAILED = "failed"


@dataclass
class Hook:
    """Represent the configuration and current state of one hook."""

    name: str
    target: str
    replacement: str
    status: HookStatus = HookStatus.NOT_INSTALLED
    original_bytes: bytes = field(default=b"")
    error_message: Optional[str] = None

    def __post_init__(self) -> None:
        """Validate the required hook fields after object creation."""
        if not self.name.strip():
            raise ValueError("Hook name cannot be empty.")

        if not self.target.strip():
            raise ValueError("Hook target cannot be empty.")

        if not self.replacement.strip():
            raise ValueError("Hook replacement cannot be empty.")

    @property
    def is_installed(self) -> bool:
        """Return True when this hook is currently installed."""
        return self.status is HookStatus.INSTALLED

    def mark_installed(self, original_bytes: bytes = b"") -> None:
        """Mark the hook as installed and optionally save original bytes."""
        self.status = HookStatus.INSTALLED
        self.original_bytes = original_bytes
        self.error_message = None

    def mark_removed(self) -> None:
        """Mark the hook as removed."""
        self.status = HookStatus.REMOVED
        self.error_message = None

    def mark_failed(self, message: str) -> None:
        """Mark the hook as failed and store a readable error message."""
        if not message.strip():
            raise ValueError("Failure message cannot be empty.")

        self.status = HookStatus.FAILED
        self.error_message = message

    def reset(self) -> None:
        """Return the hook to its initial not-installed state."""
        self.status = HookStatus.NOT_INSTALLED
        self.original_bytes = b""
        self.error_message = None
