"""Custom exception hierarchy for InlineHookKit."""

from __future__ import annotations


class InlineHookError(Exception):
    """Base class for all expected InlineHookKit errors."""

    default_message = "An InlineHookKit error occurred."

    def __init__(self, message: str | None = None) -> None:
        """Create an error with a readable message."""
        super().__init__(message or self.default_message)


class ConfigurationError(InlineHookError):
    """Raised when application configuration is missing or invalid."""

    default_message = "The configuration is invalid."


class ValidationError(InlineHookError):
    """Raised when user input or project data is invalid."""

    default_message = "The provided data is invalid."


class PlatformNotSupportedError(InlineHookError):
    """Raised when the current operating system is unsupported."""

    default_message = "The current platform is not supported."


class ArchitectureNotSupportedError(InlineHookError):
    """Raised when the current CPU architecture is unsupported."""

    default_message = "The current architecture is not supported."


class PermissionDeniedError(InlineHookError):
    """Raised when the operation lacks the required permissions."""

    default_message = "The operation requires permissions that are not available."


class MemoryOperationError(InlineHookError):
    """Raised when a safe memory operation cannot be completed."""

    default_message = "The memory operation could not be completed."


class PatchError(InlineHookError):
    """Raised when preparing or validating a patch fails."""

    default_message = "The patch operation could not be completed."


class HookError(InlineHookError):
    """Base class for hook lifecycle errors."""

    default_message = "The hook operation could not be completed."


class HookAlreadyInstalledError(HookError):
    """Raised when installing a hook that is already installed."""

    default_message = "The hook is already installed."


class HookNotInstalledError(HookError):
    """Raised when removing or using a hook that is not installed."""

    default_message = "The hook is not installed."


class HookInstallationError(HookError):
    """Raised when hook installation fails."""

    default_message = "The hook could not be installed."


class HookRemovalError(HookError):
    """Raised when hook removal fails."""

    default_message = "The hook could not be removed."


class BackendUnavailableError(InlineHookError):
    """Raised when a required operating-system backend is unavailable."""

    default_message = "The required system backend is unavailable."


class OutputError(InlineHookError):
    """Raised when writing output or reports fails."""

    default_message = "The output could not be written."
