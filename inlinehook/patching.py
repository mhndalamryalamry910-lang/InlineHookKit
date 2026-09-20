"""Safe simulated patching for InlineHookKit.

This module applies temporary byte patches only to the simulated
MemoryRegion provided by inlinehook.memory. It does not modify another
process or real operating-system memory.
"""

from __future__ import annotations

from dataclasses import dataclass
from enum import Enum

from .errors import (
    HookAlreadyInstalledError,
    HookNotInstalledError,
    PatchError,
    ValidationError,
)
from .memory import MemoryPermission, MemoryRegion


class PatchState(Enum):
    """Possible states of a simulated patch."""

    NOT_APPLIED = "not_applied"
    APPLIED = "applied"
    RESTORED = "restored"
    FAILED = "failed"


@dataclass
class Patch:
    """Describe a temporary byte patch within a memory region."""

    offset: int
    replacement: bytes
    original: bytes = b""
    state: PatchState = PatchState.NOT_APPLIED
    error_message: str | None = None

    def __post_init__(self) -> None:
        """Validate patch values after object creation."""
        if self.offset < 0:
            raise ValidationError(
                "Patch offset cannot be negative."
            )

        if not isinstance(self.replacement, bytes):
            raise ValidationError(
                "Patch replacement must be a bytes object."
            )

        if not self.replacement:
            raise ValidationError(
                "Patch replacement cannot be empty."
            )

    @property
    def size(self) -> int:
        """Return the number of bytes changed by this patch."""
        return len(self.replacement)

    @property
    def is_applied(self) -> bool:
        """Return True when the patch is currently applied."""
        return self.state is PatchState.APPLIED


class PatchApplier:
    """Apply and restore patches in a simulated memory region."""

    def __init__(self, region: MemoryRegion) -> None:
        """Create a patch applier for one simulated memory region."""
        self._region = region
        self._patches: list[Patch] = []

    @property
    def region(self) -> MemoryRegion:
        """Return the memory region managed by this applier."""
        return self._region

    @property
    def patches(self) -> tuple[Patch, ...]:
        """Return all patches known to this applier."""
        return tuple(self._patches)

    def apply(self, patch: Patch) -> None:
        """Apply one patch and save the original bytes."""
        if patch.is_applied:
            raise HookAlreadyInstalledError(
                "The patch is already applied."
            )

        if MemoryPermission.READ not in self._region.permissions:
            raise PatchError(
                "The target region must have READ permission "
                "before applying a patch."
            )

        if MemoryPermission.WRITE not in self._region.permissions:
            raise PatchError(
                "The target region must have WRITE permission "
                "before applying a patch."
            )

        try:
            original = self._region.read(
                offset=patch.offset,
                length=patch.size,
            )

            self._region.write(
                patch.replacement,
                offset=patch.offset,
            )

            patch.original = original
            patch.state = PatchState.APPLIED
            patch.error_message = None

            if patch not in self._patches:
                self._patches.append(patch)

        except Exception as error:
            patch.state = PatchState.FAILED
            patch.error_message = str(error)

            raise PatchError(
                f"Could not apply patch: {error}"
            ) from error

    def restore(self, patch: Patch) -> None:
        """Restore the original bytes saved by an applied patch."""
        if not patch.is_applied:
            raise HookNotInstalledError(
                "The patch is not currently applied."
            )

        if not patch.original:
            raise PatchError(
                "The patch has no original bytes to restore."
            )

        try:
            self._region.write(
                patch.original,
                offset=patch.offset,
            )

            patch.state = PatchState.RESTORED
            patch.error_message = None

        except Exception as error:
            patch.state = PatchState.FAILED
            patch.error_message = str(error)

            raise PatchError(
                f"Could not restore patch: {error}"
            ) from error

    def restore_all(self) -> None:
        """Restore every currently applied patch."""
        applied_patches = [
            patch for patch in self._patches
            if patch.is_applied
        ]

        for patch in reversed(applied_patches):
            self.restore(patch)

    def remove_restored(self) -> None:
        """Remove patch records that have already been restored."""
        self._patches = [
            patch for patch in self._patches
            if patch.state is PatchState.APPLIED
        ]

    def verify_applied(self, patch: Patch) -> bool:
        """Verify that the replacement bytes are present."""
        if not patch.is_applied:
            return False

        current = self._region.read(
            offset=patch.offset,
            length=patch.size,
        )

        return current == patch.replacement

    def verify_restored(self, patch: Patch) -> bool:
        """Verify that the original bytes are present again."""
        if not patch.original:
            return False

        current = self._region.read(
            offset=patch.offset,
            length=len(patch.original),
        )

        return current == patch.original
