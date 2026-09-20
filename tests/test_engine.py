"""Unit tests for the InlineHookKit application engine."""

import tempfile
import unittest
from dataclasses import replace
from pathlib import Path

from inlinehook.config import load_config
from inlinehook.engine import create_engine
from inlinehook.errors import (
    HookAlreadyInstalledError,
    HookNotInstalledError,
    ValidationError,
)


class EngineTests(unittest.TestCase):
    """Test the lifecycle and behavior of HookEngine."""

    def setUp(self) -> None:
        """Create a fresh engine and isolated state file."""
        self.config = load_config("config.toml")

        self.temp_directory = tempfile.TemporaryDirectory()

        runtime = replace(
            self.config.runtime,
            state_file=str(
                Path(self.temp_directory.name)
                / "state.json"
            ),
        )

        self.config = replace(
            self.config,
            runtime=runtime,
        )

        self.engine = create_engine(self.config)

    def tearDown(self) -> None:
        """Remove the temporary state directory."""
        self.temp_directory.cleanup()

    def test_inspect_returns_hook_configuration(self) -> None:
        """The inspect operation returns the configured hook details."""
        result = self.engine.inspect()

        self.assertTrue(result.success)
        self.assertEqual(result.operation, "inspect")
        self.assertEqual(result.details["name"], "demo_hook")
        self.assertEqual(
            result.details["target"],
            "target_function",
        )
        self.assertEqual(
            result.details["replacement"],
            "replacement_function",
        )
        self.assertEqual(
            result.details["status"],
            "not_installed",
        )

    def test_install_status_and_remove_lifecycle(self) -> None:
        """A hook can be installed, inspected, and removed."""
        install_result = self.engine.install()

        self.assertTrue(install_result.success)
        self.assertEqual(
            install_result.operation,
            "install",
        )
        self.assertEqual(
            install_result.details["status"],
            "installed",
        )
        self.assertTrue(
            install_result.details["simulated"],
        )
        self.assertTrue(
            install_result.details["verified"],
        )

        status_result = self.engine.status()

        self.assertTrue(status_result.success)
        self.assertEqual(
            status_result.details["status"],
            "installed",
        )
        self.assertEqual(
            status_result.details["patch_state"],
            "applied",
        )

        remove_result = self.engine.remove()

        self.assertTrue(remove_result.success)
        self.assertEqual(
            remove_result.operation,
            "remove",
        )
        self.assertEqual(
            remove_result.details["status"],
            "removed",
        )
        self.assertTrue(
            remove_result.details["restored"],
        )

        final_status = self.engine.status()

        self.assertTrue(final_status.success)
        self.assertEqual(
            final_status.details["status"],
            "removed",
        )

    def test_remove_before_install_fails(self) -> None:
        """Removing an uninstalled hook raises the correct error."""
        with self.assertRaises(HookNotInstalledError):
            self.engine.remove()

    def test_install_twice_fails(self) -> None:
        """Installing the same hook twice raises the correct error."""
        self.engine.install()

        with self.assertRaises(HookAlreadyInstalledError):
            self.engine.install()

    def test_real_mode_is_rejected(self) -> None:
        """Real memory mode is rejected because it is not implemented."""
        runtime = replace(
            self.config.runtime,
            dry_run=False,
        )

        config = replace(
            self.config,
            runtime=runtime,
        )

        engine = create_engine(config)

        with self.assertRaises(ValidationError):
            engine.install()

    def test_status_before_install_is_not_installed(self) -> None:
        """A new engine reports the hook as not installed."""
        result = self.engine.status()

        self.assertTrue(result.success)
        self.assertEqual(
            result.details["status"],
            "not_installed",
        )

    def test_install_result_contains_simulation_details(self) -> None:
        """Installation returns details about the simulated patch."""
        result = self.engine.install()

        self.assertIn(
            "region_address",
            result.details,
        )
        self.assertIn(
            "patch_size",
            result.details,
        )
        self.assertEqual(
            result.details["patch_size"],
            8,
        )

    def test_remove_restores_original_bytes(self) -> None:
        """Removing the hook reports that original bytes were restored."""
        self.engine.install()

        result = self.engine.remove()

        self.assertTrue(result.success)
        self.assertTrue(result.details["restored"])
        self.assertEqual(
            result.details["status"],
            "removed",
        )

    def test_state_persists_between_engine_instances(self) -> None:
        """Installed state survives creation of a new engine."""
        install_result = self.engine.install()

        self.assertEqual(
            install_result.details["status"],
            "installed",
        )

        new_engine = create_engine(self.config)

        result = new_engine.status()

        self.assertTrue(result.success)
        self.assertEqual(
            result.details["status"],
            "installed",
        )
        self.assertTrue(
            result.details["verified"],
        )

    def test_persisted_state_can_be_removed(self) -> None:
        """A persisted installation can be removed by a new engine."""
        self.engine.install()

        new_engine = create_engine(self.config)

        result = new_engine.remove()

        self.assertTrue(result.success)
        self.assertEqual(
            result.details["status"],
            "removed",
        )
        self.assertTrue(
            result.details["restored"],
        )


if __name__ == "__main__":
    unittest.main()