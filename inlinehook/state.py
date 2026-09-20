"""Persistent state storage for the safe InlineHookKit simulation."""

from __future__ import annotations

import json
from dataclasses import dataclass
from pathlib import Path

from .errors import ConfigurationError


@dataclass(frozen=True)
class HookState:
    """Represent the persisted state of the simulated hook."""

    status: str = "not_installed"
    region_address: str | None = None
    patch_size: int | None = None
    verified: bool = False


class StateStore:
    """Read and write the simulated hook state to a JSON file."""

    def __init__(self, path: str | Path) -> None:
        self._path = Path(path)

    @property
    def path(self) -> Path:
        """Return the state file path."""
        return self._path

    def load(self) -> HookState:
        """Load the persisted state.

        A missing state file means that no hook is currently installed.
        """
        if not self._path.exists():
            return HookState()

        if not self._path.is_file():
            raise ConfigurationError(
                f"State path is not a file: {self._path}"
            )

        try:
            with self._path.open(
                "r",
                encoding="utf-8",
            ) as state_file:
                data = json.load(state_file)
        except json.JSONDecodeError as error:
            raise ConfigurationError(
                f"Invalid state file: {self._path}"
            ) from error
        except OSError as error:
            raise ConfigurationError(
                f"Cannot read state file: {error}"
            ) from error

        if not isinstance(data, dict):
            raise ConfigurationError(
                "The state file must contain a JSON object."
            )

        status = data.get("status", "not_installed")

        if not isinstance(status, str):
            raise ConfigurationError(
                "State 'status' must be a string."
            )

        region_address = data.get("region_address")

        if region_address is not None and not isinstance(
            region_address,
            str,
        ):
            raise ConfigurationError(
                "State 'region_address' must be a string or null."
            )

        patch_size = data.get("patch_size")

        if patch_size is not None and (
            not isinstance(patch_size, int) or patch_size < 0
        ):
            raise ConfigurationError(
                "State 'patch_size' must be a non-negative integer or null."
            )

        verified = data.get("verified", False)

        if not isinstance(verified, bool):
            raise ConfigurationError(
                "State 'verified' must be true or false."
            )

        return HookState(
            status=status,
            region_address=region_address,
            patch_size=patch_size,
            verified=verified,
        )

    def save(self, state: HookState) -> None:
        """Persist the simulated hook state."""
        self._path.parent.mkdir(
            parents=True,
            exist_ok=True,
        )

        data = {
            "status": state.status,
            "region_address": state.region_address,
            "patch_size": state.patch_size,
            "verified": state.verified,
        }

        try:
            with self._path.open(
                "w",
                encoding="utf-8",
            ) as state_file:
                json.dump(
                    data,
                    state_file,
                    indent=2,
                )
                state_file.write("\n")
        except OSError as error:
            raise ConfigurationError(
                f"Cannot write state file: {error}"
            ) from error

    def clear(self) -> None:
        """Remove the persisted state file."""
        try:
            if self._path.exists():
                self._path.unlink()
        except OSError as error:
            raise ConfigurationError(
                f"Cannot remove state file: {error}"
            ) from error