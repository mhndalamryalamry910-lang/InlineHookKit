"""Unit tests for the InlineHookKit command-line interface."""

import io
import tempfile
import unittest
from contextlib import redirect_stdout
from pathlib import Path

from inlinehook.cli import main


class CliTests(unittest.TestCase):
    """Test the main CLI commands and error handling."""

    def setUp(self) -> None:
        """Create an isolated configuration for each test."""
        self.temp_directory = tempfile.TemporaryDirectory()

        temp_path = Path(self.temp_directory.name)

        self.config_path = temp_path / "config.toml"
        self.state_path = temp_path / "state.json"

        self.config_path.write_text(
            f"""
[project]
name = "InlineHookKit"
version = "0.1.0"

[runtime]
log_level = "INFO"
dry_run = true
state_file = "{self.state_path.as_posix()}"

[hook]
name = "demo_hook"
target = "target_function"
replacement = "replacement_function"
""".strip()
            + "\n",
            encoding="utf-8",
        )

    def tearDown(self) -> None:
        """Remove the isolated test environment."""
        self.temp_directory.cleanup()

    def run_cli(self, *arguments: str) -> tuple[int, str]:
        """Run the CLI and capture its output and exit code."""
        output = io.StringIO()

        with redirect_stdout(output):
            try:
                exit_code = main(list(arguments))
            except SystemExit as error:
                exit_code = (
                    error.code
                    if isinstance(error.code, int)
                    else 1
                )

        return exit_code, output.getvalue()

    def test_help_command(self) -> None:
        """The help option displays usage information."""
        exit_code, output = self.run_cli("--help")

        self.assertEqual(exit_code, 0)
        self.assertIn("InlineHookKit", output)
        self.assertIn("install", output)
        self.assertIn("status", output)

    def test_version_command(self) -> None:
        """The version option displays the application version."""
        exit_code, output = self.run_cli("--version")

        self.assertEqual(exit_code, 0)
        self.assertIn("inlinehook 0.1.0", output)

    def test_inspect_command(self) -> None:
        """The inspect command reads and displays hook configuration."""
        exit_code, output = self.run_cli(
            "--config",
            str(self.config_path),
            "inspect",
        )

        self.assertEqual(exit_code, 0)
        self.assertIn("[SUCCESS] inspect", output)
        self.assertIn("demo_hook", output)

    def test_install_command(self) -> None:
        """The install command runs the simulated installation."""
        exit_code, output = self.run_cli(
            "--config",
            str(self.config_path),
            "install",
        )

        self.assertEqual(exit_code, 0)
        self.assertIn("[SUCCESS] install", output)
        self.assertIn("simulated", output)

    def test_status_starts_not_installed_in_new_process_context(
        self,
    ) -> None:
        """A new engine reports the hook as not installed."""
        exit_code, output = self.run_cli(
            "--config",
            str(self.config_path),
            "status",
        )

        self.assertEqual(exit_code, 0)
        self.assertIn("[SUCCESS] status", output)
        self.assertIn("not_installed", output)

    def test_missing_config_returns_error(self) -> None:
        """A missing configuration file returns an error code."""
        exit_code, output = self.run_cli(
            "--config",
            "missing.toml",
            "inspect",
        )

        self.assertEqual(exit_code, 1)
        self.assertIn("ERROR:", output)


if __name__ == "__main__":
    unittest.main()