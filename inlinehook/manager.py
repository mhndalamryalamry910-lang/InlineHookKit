"""Hook registry and lifecycle manager for InlineHookKit.

This module manages Hook objects and their lifecycle states.
It does not access real process memory or external programs.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Iterator

from .errors import (
    HookAlreadyInstalledError,
    HookNotInstalledError,
    ValidationError,
)
from .models import Hook, HookStatus


@dataclass(frozen=True)
class HookSummary:
    """Read-only summary of a registered hook."""

    name: str
    target: str
    replacement: str
    status: HookStatus
    is_installed: bool


class HookManager:
    """Manage registered hooks and their lifecycle states."""

    def __init__(self) -> None:
        """Create an empty hook manager."""
        self._hooks: dict[str, Hook] = {}

    @property
    def count(self) -> int:
        """Return the number of registered hooks."""
        return len(self._hooks)

    def register(self, hook: Hook) -> Hook:
        """Register a Hook object."""
        if not isinstance(hook, Hook):
            raise ValidationError(
                "Only Hook objects can be registered."
            )

        if hook.name in self._hooks:
            raise ValidationError(
                f"A hook named '{hook.name}' is already registered."
            )

        self._hooks[hook.name] = hook
        return hook

    def create(
        self,
        name: str,
        target: str,
        replacement: str,
    ) -> Hook:
        """Create and register a Hook object.

        Model ValueError exceptions are converted into the project's
        ValidationError type.
        """
        try:
            hook = Hook(
                name=name,
                target=target,
                replacement=replacement,
            )
        except ValueError as error:
            raise ValidationError(str(error)) from error

        return self.register(hook)

    def get(self, name: str) -> Hook:
        """Return a registered Hook by name."""
        self._validate_name(name)

        try:
            return self._hooks[name]
        except KeyError as error:
            raise ValidationError(
                f"No hook named '{name}' is registered."
            ) from error

    def find(self, name: str) -> Hook | None:
        """Return a registered Hook or None."""
        self._validate_name(name)
        return self._hooks.get(name)

    def contains(self, name: str) -> bool:
        """Return True if a Hook name is registered."""
        self._validate_name(name)
        return name in self._hooks

    def list_hooks(self) -> tuple[Hook, ...]:
        """Return all registered Hooks in registration order."""
        return tuple(self._hooks.values())

    def summaries(self) -> tuple[HookSummary, ...]:
        """Return summaries for all registered Hooks."""
        return tuple(
            HookSummary(
                name=hook.name,
                target=hook.target,
                replacement=hook.replacement,
                status=hook.status,
                is_installed=hook.is_installed,
            )
            for hook in self._hooks.values()
        )

    def install(
        self,
        name: str,
        original_bytes: bytes = b"",
    ) -> Hook:
        """Mark a registered Hook as installed."""
        hook = self.get(name)

        if hook.is_installed:
            raise HookAlreadyInstalledError(
                f"Hook '{name}' is already installed."
            )

        if not isinstance(original_bytes, bytes):
            raise ValidationError(
                "Original bytes must be a bytes object."
            )

        hook.mark_installed(original_bytes)
        return hook

    def remove(self, name: str) -> Hook:
        """Mark an installed Hook as removed."""
        hook = self.get(name)

        if not hook.is_installed:
            raise HookNotInstalledError(
                f"Hook '{name}' is not installed."
            )

        hook.mark_removed()
        return hook

    def fail(self, name: str, message: str) -> Hook:
        """Mark a registered Hook as failed."""
        hook = self.get(name)
        hook.mark_failed(message)
        return hook

    def reset(self, name: str) -> Hook:
        """Reset a Hook to its initial state."""
        hook = self.get(name)
        hook.reset()
        return hook

    def unregister(self, name: str) -> Hook:
        """Remove a non-installed Hook from the registry."""
        hook = self.get(name)

        if hook.is_installed:
            raise HookAlreadyInstalledError(
                f"Cannot unregister installed hook '{name}'. "
                "Remove it first."
            )

        del self._hooks[name]
        return hook

    def clear(self) -> None:
        """Remove all non-installed Hooks."""
        installed_hooks = [
            hook.name
            for hook in self._hooks.values()
            if hook.is_installed
        ]

        if installed_hooks:
            names = ", ".join(installed_hooks)
            raise HookAlreadyInstalledError(
                f"Cannot clear installed hooks: {names}."
            )

        self._hooks.clear()

    def installed_hooks(self) -> tuple[Hook, ...]:
        """Return all currently installed Hooks."""
        return tuple(
            hook
            for hook in self._hooks.values()
            if hook.is_installed
        )

    def __len__(self) -> int:
        """Return the number of registered Hooks."""
        return self.count

    def __contains__(self, name: object) -> bool:
        """Support checking a name with the in operator."""
        return (
            isinstance(name, str)
            and name in self._hooks
        )

    def __iter__(self) -> Iterator[Hook]:
        """Iterate over registered Hooks."""
        return iter(self._hooks.values())

    @staticmethod
    def _validate_name(name: str) -> None:
        """Validate a Hook name."""
        if not isinstance(name, str) or not name.strip():
            raise ValidationError(
                "Hook name must be a non-empty string."
            )
