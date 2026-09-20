"""Unit tests for InlineHookKit persistent state storage."""

import json
import tempfile
import unittest
from pathlib import Path

from inlinehook.errors import ConfigurationError
from inlinehook.state import HookState, StateStore


class StateStoreTests(unittest.TestCase):
    """Test loading, saving, validating, and clearing state."""

    def setUp(self) -> None:
        """Create an isolated temporary directory."""
        self.temp_directory = tempfile.TemporaryDirectory()
        self.state_path = (
            Path(self.temp_directory.name)
            / "state.json"
        )
        self.store = StateStore(self.state_path)

    def tearDown(self) -> None:
        """Remove the temporary directory."""
        self.temp_directory.cleanup()

    def test_missing_file_returns_default_state(self) -> None:
        """A missing state file returns the default state."""
        state = self.store.load()

        self.assertEqual(
            state,
            HookState(),
        )

    def test_save_and_load_state(self) -> None:
        """A saved state can be loaded again."""
        expected = HookState(
            status="installed",
            region_address="0x10000000",
            patch_size=8,
            verified=True,
        )

        self.store.save(expected)

        actual = self.store.load()

        self.assertEqual(actual, expected)

    def test_save_creates_parent_directory(self) -> None:
        """Saving creates missing parent directories."""
        nested_path = (
            Path(self.temp_directory.name)
            / "nested"
            / "state.json"
        )

        store = StateStore(nested_path)
        state = HookState(status="installed")

        store.save(state)

        self.assertTrue(nested_path.is_file())
        self.assertEqual(store.load(), state)

    def test_clear_removes_state_file(self) -> None:
        """Clear removes the persisted state file."""
        self.store.save(
            HookState(status="installed")
        )

        self.assertTrue(self.state_path.exists())

        self.store.clear()

        self.assertFalse(self.state_path.exists())
        self.assertEqual(
            self.store.load(),
            HookState(),
        )

    def test_clear_missing_file_is_safe(self) -> None:
        """Clearing a missing state file does not fail."""
        self.store.clear()

        self.assertFalse(self.state_path.exists())

    def test_invalid_json_is_rejected(self) -> None:
        """Invalid JSON raises ConfigurationError."""
        self.state_path.write_text(
            "{invalid json",
            encoding="utf-8",
        )

        with self.assertRaises(ConfigurationError):
            self.store.load()

    def test_non_object_json_is_rejected(self) -> None:
        """A JSON value other than an object is rejected."""
        self.state_path.write_text(
            "[]",
            encoding="utf-8",
        )

        with self.assertRaises(ConfigurationError):
            self.store.load()

    def test_invalid_status_type_is_rejected(self) -> None:
        """A non-string status is rejected."""
        self._write_json(
            {
                "status": 123,
            }
        )

        with self.assertRaises(ConfigurationError):
            self.store.load()

    def test_invalid_region_address_type_is_rejected(
        self,
    ) -> None:
        """A non-string region address is rejected."""
        self._write_json(
            {
                "status": "installed",
                "region_address": 123,
            }
        )

        with self.assertRaises(ConfigurationError):
            self.store.load()

    def test_invalid_patch_size_type_is_rejected(
        self,
    ) -> None:
        """A non-integer patch size is rejected."""
        self._write_json(
            {
                "status": "installed",
                "patch_size": "8",
            }
        )

        with self.assertRaises(ConfigurationError):
            self.store.load()

    def test_negative_patch_size_is_rejected(self) -> None:
        """A negative patch size is rejected."""
        self._write_json(
            {
                "status": "installed",
                "patch_size": -1,
            }
        )

        with self.assertRaises(ConfigurationError):
            self.store.load()

    def test_invalid_verified_type_is_rejected(self) -> None:
        """A non-Boolean verified value is rejected."""
        self._write_json(
            {
                "status": "installed",
                "verified": "true",
            }
        )

        with self.assertRaises(ConfigurationError):
            self.store.load()

    def test_path_property_returns_state_path(self) -> None:
        """The path property returns the configured path."""
        self.assertEqual(
            self.store.path,
            self.state_path,
        )

    def _write_json(self, data: dict) -> None:
        """Write test JSON data directly to the state file."""
        self.state_path.write_text(
            json.dumps(data),
            encoding="utf-8",
        )


if __name__ == "__main__":
    unittest.main()