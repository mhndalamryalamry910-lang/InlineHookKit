"""Application engine that connects InlineHookKit components.

This engine currently runs in a safe simulated environment.
It does not modify real operating-system or external-process memory.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from .config import AppConfig
from .errors import (
    HookAlreadyInstalledError,
    HookNotInstalledError,
    ValidationError,
)
from .memory import MemoryManager, MemoryPermission, MemoryRegion
from .models import Hook
from .patching import Patch, PatchApplier
from .state import HookState, StateStore


@dataclass(frozen=True)
class EngineResult:
    """Represent the result of an engine operation."""

    success: bool
    operation: str
    message: str
    details: dict[str, Any]


class HookEngine:
    """Coordinate configuration, hook models, memory, patching, and state."""

    def __init__(self, config: AppConfig) -> None:
        """Create a hook engine using validated application settings."""
        self._config = config
        self._memory_manager = MemoryManager()
        self._region: MemoryRegion | None = None
        self._patch: Patch | None = None
        self._patch_applier: PatchApplier | None = None
        self._hook: Hook | None = None

        self._state_store = StateStore(
            config.runtime.state_file
        )

        if config.hook is not None:
            self._hook = Hook(
                name=config.hook.name,
                target=config.hook.target,
                replacement=config.hook.replacement,
            )

            self._restore_persisted_state()

    @property
    def config(self) -> AppConfig:
        """Return the configuration used by the engine."""
        return self._config

    @property
    def hook(self) -> Hook | None:
        """Return the configured hook model."""
        return self._hook

    def _restore_persisted_state(self) -> None:
        """Restore the simulated lifecycle state from persistent storage."""
        if self._hook is None:
            return

        state = self._state_store.load()

        if state.status == "installed":
            self._hook.mark_installed()

        elif state.status == "removed":
            self._hook.mark_removed()

    def _save_state(
        self,
        *,
        status: str,
        region_address: str | None = None,
        patch_size: int | None = None,
        verified: bool = False,
    ) -> None:
        """Save the current simulated lifecycle state."""
        self._state_store.save(
            HookState(
                status=status,
                region_address=region_address,
                patch_size=patch_size,
                verified=verified,
            )
        )

    def inspect(self) -> EngineResult:
        """Inspect the configured hook without applying any patch."""
        if self._hook is None:
            return EngineResult(
                success=False,
                operation="inspect",
                message="No hook is configured.",
                details={},
            )

        return EngineResult(
            success=True,
            operation="inspect",
            message="Hook configuration inspected successfully.",
            details={
                "name": self._hook.name,
                "target": self._hook.target,
                "replacement": self._hook.replacement,
                "status": self._hook.status.value,
                "dry_run": self._config.runtime.dry_run,
            },
        )

    def install(self) -> EngineResult:
        """Install a safe simulated patch for the configured hook."""
        if self._hook is None:
            raise ValidationError(
                "Cannot install a hook because no hook is configured."
            )

        if self._hook.is_installed:
            raise HookAlreadyInstalledError(
                f"Hook '{self._hook.name}' is already installed."
            )

        if not self._config.runtime.dry_run:
            raise ValidationError(
                "Real memory operations are not implemented. "
                "Set runtime.dry_run = true."
            )

        # The following bytes are intentionally simulated test data.
        original_bytes = b"ORIGINAL"
        replacement_bytes = b"HOOK----"

        self._region = self._memory_manager.allocate(
            size=len(original_bytes),
            permissions={
                MemoryPermission.READ,
                MemoryPermission.WRITE,
            },
        )

        self._region.write(original_bytes)

        self._patch = Patch(
            offset=0,
            replacement=replacement_bytes,
        )

        self._patch_applier = PatchApplier(self._region)
        self._patch_applier.apply(self._patch)

        self._hook.mark_installed(
            original_bytes=self._patch.original,
        )

        verified = self._patch_applier.verify_applied(
            self._patch
        )

        self._save_state(
            status="installed",
            region_address=hex(self._region.address),
            patch_size=self._patch.size,
            verified=verified,
        )

        return EngineResult(
            success=True,
            operation="install",
            message=(
                f"Hook '{self._hook.name}' was installed "
                "in the simulated environment."
            ),
            details={
                "hook_name": self._hook.name,
                "status": self._hook.status.value,
                "simulated": True,
                "region_address": hex(self._region.address),
                "patch_size": self._patch.size,
                "verified": verified,
            },
        )

    def remove(self) -> EngineResult:
        """Remove the simulated patch and restore the original bytes."""
        if self._hook is None:
            raise ValidationError(
                "Cannot remove a hook because no hook is configured."
            )

        if not self._hook.is_installed:
            raise HookNotInstalledError(
                f"Hook '{self._hook.name}' is not installed."
            )

        # Same-process removal:
        # restore the actual simulated memory region.
        if self._patch is not None and self._patch_applier is not None:
            self._patch_applier.restore(self._patch)

            restored = self._patch_applier.verify_restored(
                self._patch
            )

            if not restored:
                raise ValidationError(
                    "The simulated patch could not be verified "
                    "after restoration."
                )

        else:
            # Different-process removal:
            # there is no real external memory to restore.
            # We only update the persistent simulation state.
            restored = True

        self._hook.mark_removed()

        if self._region is not None:
            self._memory_manager.release(
                self._region.address
            )

        self._region = None
        self._patch = None
        self._patch_applier = None

        self._save_state(
            status="removed",
            verified=restored,
        )

        return EngineResult(
            success=True,
            operation="remove",
            message=(
                f"Hook '{self._hook.name}' was removed "
                "and the original bytes were restored."
            ),
            details={
                "hook_name": self._hook.name,
                "status": self._hook.status.value,
                "restored": restored,
                "simulated": True,
            },
        )

    def status(self) -> EngineResult:
        """Return the current simulated and persisted hook status."""
        if self._hook is None:
            return EngineResult(
                success=False,
                operation="status",
                message="No hook is configured.",
                details={
                    "status": "not_configured",
                },
            )

        state = self._state_store.load()

        details: dict[str, Any] = {
            "hook_name": self._hook.name,
            "target": self._hook.target,
            "replacement": self._hook.replacement,
            "status": self._hook.status.value,
            "simulated": True,
        }

        if state.region_address is not None:
            details["region_address"] = state.region_address

        if state.patch_size is not None:
            details["patch_size"] = state.patch_size

        details["verified"] = state.verified

        # These fields describe the actual in-memory simulation
        # when the current process performed the installation.
        if self._region is not None:
            details["region_size"] = self._region.size

        if self._patch is not None:
            details["patch_state"] = self._patch.state.value

        return EngineResult(
            success=True,
            operation="status",
            message="Hook status retrieved successfully.",
            details=details,
        )


def create_engine(config: AppConfig) -> HookEngine:
    """Create a HookEngine from validated application configuration."""
    return HookEngine(config)