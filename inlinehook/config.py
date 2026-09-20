"""Configuration loading and validation for InlineHookKit."""

from __future__ import annotations

import logging
import tomllib
from dataclasses import dataclass
from pathlib import Path
from typing import Any

from .errors import ConfigurationError


@dataclass(frozen=True)
class ProjectConfig:
    """General project configuration."""

    name: str = "InlineHookKit"
    version: str = "0.1.0"


@dataclass(frozen=True)
class RuntimeConfig:
    """Runtime behavior configuration."""

    log_level: str = "WARNING"
    dry_run: bool = True
    state_file: str = ".inlinehook/state.json"


@dataclass(frozen=True)
class HookConfig:
    """Configuration describing a hook experiment."""

    name: str
    target: str
    replacement: str


@dataclass(frozen=True)
class AppConfig:
    """Complete validated application configuration."""

    project: ProjectConfig
    runtime: RuntimeConfig
    hook: HookConfig | None = None


_ALLOWED_LOG_LEVELS = {
    "DEBUG",
    "INFO",
    "WARNING",
    "ERROR",
    "CRITICAL",
}


def _require_table(
    data: dict[str, Any],
    section_name: str,
) -> dict[str, Any]:
    """Return a configuration section and ensure it is a TOML table."""
    section = data.get(section_name, {})

    if not isinstance(section, dict):
        raise ConfigurationError(
            f"Section [{section_name}] must be a TOML table."
        )

    return section


def _read_string(
    section: dict[str, Any],
    key: str,
    default: str | None = None,
    *,
    required: bool = False,
) -> str:
    """Read and validate a non-empty string value."""
    if required and key not in section:
        raise ConfigurationError(
            f"Missing required setting: {key}"
        )

    value = section.get(key, default)

    if not isinstance(value, str) or not value.strip():
        raise ConfigurationError(
            f"Setting '{key}' must be a non-empty string."
        )

    return value.strip()


def _read_boolean(
    section: dict[str, Any],
    key: str,
    default: bool,
) -> bool:
    """Read and validate a Boolean configuration value."""
    value = section.get(key, default)

    if not isinstance(value, bool):
        raise ConfigurationError(
            f"Setting '{key}' must be true or false."
        )

    return value


def load_config(path: str | Path) -> AppConfig:
    """Load and validate an InlineHookKit TOML configuration file."""
    config_path = Path(path)

    if not config_path.exists():
        raise ConfigurationError(
            f"Configuration file does not exist: {config_path}"
        )

    if not config_path.is_file():
        raise ConfigurationError(
            f"Configuration path is not a file: {config_path}"
        )

    try:
        with config_path.open("rb") as config_file:
            raw_data = tomllib.load(config_file)
    except tomllib.TOMLDecodeError as error:
        raise ConfigurationError(
            f"Invalid TOML configuration: {error}"
        ) from error
    except OSError as error:
        raise ConfigurationError(
            f"Cannot read configuration file: {error}"
        ) from error

    if not isinstance(raw_data, dict):
        raise ConfigurationError(
            "The configuration root must be a TOML table."
        )

    project_data = _require_table(raw_data, "project")
    runtime_data = _require_table(raw_data, "runtime")

    project = ProjectConfig(
        name=_read_string(
            project_data,
            "name",
            default="InlineHookKit",
        ),
        version=_read_string(
            project_data,
            "version",
            default="0.1.0",
        ),
    )

    log_level = _read_string(
        runtime_data,
        "log_level",
        default="WARNING",
    ).upper()

    if log_level not in _ALLOWED_LOG_LEVELS:
        allowed_values = ", ".join(sorted(_ALLOWED_LOG_LEVELS))
        raise ConfigurationError(
            f"Invalid log_level '{log_level}'. "
            f"Allowed values: {allowed_values}."
        )

    runtime = RuntimeConfig(
        log_level=log_level,
        dry_run=_read_boolean(
            runtime_data,
            "dry_run",
            default=True,
        ),
        state_file=_read_string(
            runtime_data,
            "state_file",
            default=".inlinehook/state.json",
        ),
    )

    hook_data = raw_data.get("hook")
    hook: HookConfig | None = None

    if hook_data is not None:
        if not isinstance(hook_data, dict):
            raise ConfigurationError(
                "Section [hook] must be a TOML table."
            )

        hook = HookConfig(
            name=_read_string(
                hook_data,
                "name",
                required=True,
            ),
            target=_read_string(
                hook_data,
                "target",
                required=True,
            ),
            replacement=_read_string(
                hook_data,
                "replacement",
                required=True,
            ),
        )

    config = AppConfig(
        project=project,
        runtime=runtime,
        hook=hook,
    )

    validate_config(config)

    return config


def validate_config(config: AppConfig) -> None:
    """Validate an already loaded application configuration."""
    if not config.project.name.strip():
        raise ConfigurationError(
            "Project name cannot be empty."
        )

    if not config.project.version.strip():
        raise ConfigurationError(
            "Project version cannot be empty."
        )

    if config.runtime.log_level not in _ALLOWED_LOG_LEVELS:
        raise ConfigurationError(
            f"Unsupported log level: {config.runtime.log_level}"
        )

    if not config.runtime.state_file.strip():
        raise ConfigurationError(
            "State file path cannot be empty."
        )

    if config.hook is not None:
        hook_values = (
            ("name", config.hook.name),
            ("target", config.hook.target),
            ("replacement", config.hook.replacement),
        )

        for field_name, value in hook_values:
            if not value.strip():
                raise ConfigurationError(
                    f"Hook field '{field_name}' cannot be empty."
                )


def get_logging_level(config: AppConfig) -> int:
    """Convert the configured log level to a logging constant."""
    return getattr(logging, config.runtime.log_level)