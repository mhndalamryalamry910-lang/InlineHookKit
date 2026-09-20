import tempfile
import unittest
from pathlib import Path

from inlinehook.config import load_config
from inlinehook.errors import ConfigurationError


VALID_CONFIG = """
[project]
name = "InlineHookKit"
version = "0.1.0"

[runtime]
log_level = "INFO"
dry_run = true

[hook]
name = "demo_hook"
target = "target_function"
replacement = "replacement_function"
"""


class ConfigTests(unittest.TestCase):
    def create_config_file(self, content: str) -> Path:
        temporary_file = tempfile.NamedTemporaryFile(
            mode="w",
            suffix=".toml",
            delete=False,
            encoding="utf-8",
        )
        temporary_file.write(content)
        temporary_file.close()

        self.addCleanup(
            lambda: Path(temporary_file.name).unlink(missing_ok=True)
        )

        return Path(temporary_file.name)

    def test_valid_config_is_loaded(self):
        path = self.create_config_file(VALID_CONFIG)

        config = load_config(path)

        self.assertEqual(config.project.name, "InlineHookKit")
        self.assertEqual(config.runtime.log_level, "INFO")
        self.assertTrue(config.runtime.dry_run)
        self.assertIsNotNone(config.hook)
        self.assertEqual(config.hook.name, "demo_hook")

    def test_missing_config_file_is_rejected(self):
        with self.assertRaises(ConfigurationError):
            load_config("missing_config_file.toml")

    def test_invalid_log_level_is_rejected(self):
        content = VALID_CONFIG.replace(
            'log_level = "INFO"',
            'log_level = "INVALID"',
        )
        path = self.create_config_file(content)

        with self.assertRaises(ConfigurationError):
            load_config(path)

    def test_invalid_boolean_is_rejected(self):
        content = VALID_CONFIG.replace(
            "dry_run = true",
            'dry_run = "yes"',
        )
        path = self.create_config_file(content)

        with self.assertRaises(ConfigurationError):
            load_config(path)

    def test_missing_required_hook_field_is_rejected(self):
        content = VALID_CONFIG.replace(
            'replacement = "replacement_function"',
            "",
        )
        path = self.create_config_file(content)

        with self.assertRaises(ConfigurationError):
            load_config(path)


if __name__ == "__main__":
    unittest.main()
