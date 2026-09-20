"""Command-line interface for InlineHookKit."""

from __future__ import annotations

import argparse
import logging
from pathlib import Path
from typing import Any, Sequence

from .config import load_config
from .engine import EngineResult, create_engine
from .errors import InlineHookError


VERSION = "0.1.0"
LOGGER = logging.getLogger("inlinehook")


def configure_logging(level_name: str) -> None:
    """Configure application logging."""
    level = getattr(logging, level_name.upper(), None)

    if not isinstance(level, int):
        raise ValueError(f"Invalid log level: {level_name}")

    logging.basicConfig(
        level=level,
        format="%(levelname)s: %(message)s",
    )


def build_parser() -> argparse.ArgumentParser:
    """Build and return the command-line argument parser."""
    parser = argparse.ArgumentParser(
        prog="inlinehook",
        description=(
            "InlineHookKit - an educational tool for "
            "safe simulated inline-hook experiments."
        ),
    )

    parser.add_argument(
        "--version",
        action="version",
        version=f"%(prog)s {VERSION}",
    )

    parser.add_argument(
        "--config",
        metavar="PATH",
        default="config.toml",
        help="Path to the TOML configuration file. "
        "Default: config.toml",
    )

    parser.add_argument(
        "--log-level",
        choices=(
            "DEBUG",
            "INFO",
            "WARNING",
            "ERROR",
            "CRITICAL",
        ),
        default="WARNING",
        help="Set the logging level. Default: WARNING.",
    )

    subparsers = parser.add_subparsers(
        dest="command",
        title="commands",
        description="Available InlineHookKit commands",
    )

    subparsers.add_parser(
        "inspect",
        help="Inspect the configured hook.",
    )

    subparsers.add_parser(
        "install",
        help="Install the hook in the safe simulated environment.",
    )

    subparsers.add_parser(
        "remove",
        help="Remove the hook in the safe simulated environment.",
    )

    subparsers.add_parser(
        "status",
        help="Display the current hook status.",
    )

    return parser


def print_result(result: EngineResult) -> None:
    """Print an engine result in a readable format."""
    status = "SUCCESS" if result.success else "FAILED"

    print(f"[{status}] {result.operation}")
    print(result.message)

    if result.details:
        print("Details:")

        for key, value in result.details.items():
            print(f"  {key}: {value}")


def create_engine_from_config(
    config_path: str,
):
    """Load the configuration and create an application engine."""
    path = Path(config_path)

    if not path.exists():
        raise InlineHookError(
            f"Configuration file does not exist: {path}"
        )

    config = load_config(path)

    configure_logging(config.runtime.log_level)

    return create_engine(config)


def execute_command(args: argparse.Namespace) -> int:
    """Execute the selected CLI command."""
    if args.command is None:
        print(
            "No command selected. "
            "Use 'python main.py --help' for available commands."
        )
        return 0

    engine = create_engine_from_config(args.config)

    operations = {
        "inspect": engine.inspect,
        "install": engine.install,
        "remove": engine.remove,
        "status": engine.status,
    }

    operation = operations.get(args.command)

    if operation is None:
        raise InlineHookError(
            f"Unsupported command: {args.command}"
        )

    result = operation()
    print_result(result)

    return 0 if result.success else 1


def main(argv: Sequence[str] | None = None) -> int:
    """Run the CLI application and return an exit code."""
    parser = build_parser()
    args = parser.parse_args(argv)

    try:
        return execute_command(args)

    except InlineHookError as error:
        print(f"ERROR: {error}")
        return 1

    except ValueError as error:
        print(f"ERROR: {error}")
        return 1

    except OSError as error:
        print(f"ERROR: Operating-system error: {error}")
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
