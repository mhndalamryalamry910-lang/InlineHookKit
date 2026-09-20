"""Unit tests for the InlineHookKit HookManager."""

import unittest

from inlinehook.errors import (
    HookAlreadyInstalledError,
    HookNotInstalledError,
    ValidationError,
)
from inlinehook.manager import HookManager, HookSummary
from inlinehook.models import Hook, HookStatus


class HookManagerTests(unittest.TestCase):
    """Test HookManager registration and lifecycle operations."""

    def setUp(self) -> None:
        """Create a new manager before each test."""
        self.manager = HookManager()

    def create_demo_hook(self, name: str = "demo") -> Hook:
        """Create and register a test hook."""
        return self.manager.create(
            name=name,
            target="target_function",
            replacement="replacement_function",
        )

    def test_manager_starts_empty(self) -> None:
        self.assertEqual(self.manager.count, 0)
        self.assertEqual(len(self.manager), 0)
        self.assertEqual(self.manager.list_hooks(), ())
        self.assertEqual(self.manager.installed_hooks(), ())

    def test_create_registers_hook(self) -> None:
        hook = self.create_demo_hook()

        self.assertIsInstance(hook, Hook)
        self.assertEqual(hook.name, "demo")
        self.assertEqual(self.manager.count, 1)
        self.assertTrue(self.manager.contains("demo"))
        self.assertIn("demo", self.manager)

    def test_register_accepts_hook_object(self) -> None:
        hook = Hook(
            name="registered",
            target="target",
            replacement="replacement",
        )

        result = self.manager.register(hook)

        self.assertIs(result, hook)
        self.assertIs(self.manager.get("registered"), hook)

    def test_register_rejects_duplicate_name(self) -> None:
        self.create_demo_hook()

        duplicate = Hook(
            name="demo",
            target="another_target",
            replacement="another_replacement",
        )

        with self.assertRaises(ValidationError):
            self.manager.register(duplicate)

    def test_register_rejects_non_hook_object(self) -> None:
        with self.assertRaises(ValidationError):
            self.manager.register("not a hook")  # type: ignore[arg-type]

    def test_get_returns_registered_hook(self) -> None:
        hook = self.create_demo_hook()

        self.assertIs(self.manager.get("demo"), hook)

    def test_get_unknown_hook_raises_error(self) -> None:
        with self.assertRaises(ValidationError):
            self.manager.get("missing")

    def test_find_returns_hook_or_none(self) -> None:
        hook = self.create_demo_hook()

        self.assertIs(self.manager.find("demo"), hook)
        self.assertIsNone(self.manager.find("missing"))

    def test_contains_returns_correct_result(self) -> None:
        self.create_demo_hook()

        self.assertTrue(self.manager.contains("demo"))
        self.assertFalse(self.manager.contains("missing"))

    def test_list_hooks_preserves_registration_order(self) -> None:
        first = self.create_demo_hook("first")
        second = self.create_demo_hook("second")

        self.assertEqual(
            self.manager.list_hooks(),
            (first, second),
        )

    def test_manager_is_iterable(self) -> None:
        first = self.create_demo_hook("first")
        second = self.create_demo_hook("second")

        self.assertEqual(
            tuple(self.manager),
            (first, second),
        )

    def test_summaries_returns_hook_summaries(self) -> None:
        self.create_demo_hook()

        summaries = self.manager.summaries()

        self.assertEqual(len(summaries), 1)
        self.assertIsInstance(summaries[0], HookSummary)
        self.assertEqual(summaries[0].name, "demo")
        self.assertEqual(
            summaries[0].status,
            HookStatus.NOT_INSTALLED,
        )
        self.assertFalse(summaries[0].is_installed)

    def test_install_marks_hook_as_installed(self) -> None:
        hook = self.create_demo_hook()

        result = self.manager.install("demo", b"ORIGINAL")

        self.assertIs(result, hook)
        self.assertEqual(hook.status, HookStatus.INSTALLED)
        self.assertTrue(hook.is_installed)
        self.assertEqual(hook.original_bytes, b"ORIGINAL")

    def test_install_without_original_bytes_is_supported(self) -> None:
        hook = self.create_demo_hook()

        self.manager.install("demo")

        self.assertEqual(hook.status, HookStatus.INSTALLED)
        self.assertEqual(hook.original_bytes, b"")

    def test_install_rejects_invalid_original_bytes(self) -> None:
        self.create_demo_hook()

        with self.assertRaises(ValidationError):
            self.manager.install(
                "demo",
                "invalid bytes",  # type: ignore[arg-type]
            )

    def test_installing_twice_raises_error(self) -> None:
        self.create_demo_hook()
        self.manager.install("demo")

        with self.assertRaises(HookAlreadyInstalledError):
            self.manager.install("demo")

    def test_install_unknown_hook_raises_error(self) -> None:
        with self.assertRaises(ValidationError):
            self.manager.install("missing")

    def test_remove_marks_hook_as_removed(self) -> None:
        hook = self.create_demo_hook()
        self.manager.install("demo")

        result = self.manager.remove("demo")

        self.assertIs(result, hook)
        self.assertEqual(hook.status, HookStatus.REMOVED)
        self.assertFalse(hook.is_installed)

    def test_removing_uninstalled_hook_raises_error(self) -> None:
        self.create_demo_hook()

        with self.assertRaises(HookNotInstalledError):
            self.manager.remove("demo")

    def test_remove_unknown_hook_raises_error(self) -> None:
        with self.assertRaises(ValidationError):
            self.manager.remove("missing")

    def test_fail_marks_hook_as_failed(self) -> None:
        hook = self.create_demo_hook()

        result = self.manager.fail(
            "demo",
            "Simulated installation failure.",
        )

        self.assertIs(result, hook)
        self.assertEqual(hook.status, HookStatus.FAILED)
        self.assertEqual(
            hook.error_message,
            "Simulated installation failure.",
        )

    def test_reset_returns_hook_to_initial_state(self) -> None:
        hook = self.create_demo_hook()

        self.manager.install("demo", b"ORIGINAL")
        result = self.manager.reset("demo")

        self.assertIs(result, hook)
        self.assertEqual(hook.status, HookStatus.NOT_INSTALLED)
        self.assertFalse(hook.is_installed)
        self.assertEqual(hook.original_bytes, b"")
        self.assertIsNone(hook.error_message)

    def test_installed_hooks_returns_only_installed_hooks(self) -> None:
        self.create_demo_hook("first")
        self.create_demo_hook("second")
        self.manager.install("first")

        result = self.manager.installed_hooks()

        self.assertEqual(len(result), 1)
        self.assertEqual(result[0].name, "first")

    def test_unregister_removes_non_installed_hook(self) -> None:
        hook = self.create_demo_hook()

        result = self.manager.unregister("demo")

        self.assertIs(result, hook)
        self.assertEqual(self.manager.count, 0)
        self.assertFalse(self.manager.contains("demo"))

    def test_unregister_installed_hook_is_rejected(self) -> None:
        self.create_demo_hook()
        self.manager.install("demo")

        with self.assertRaises(HookAlreadyInstalledError):
            self.manager.unregister("demo")

    def test_unregister_unknown_hook_raises_error(self) -> None:
        with self.assertRaises(ValidationError):
            self.manager.unregister("missing")

    def test_clear_removes_all_non_installed_hooks(self) -> None:
        self.create_demo_hook("first")
        self.create_demo_hook("second")

        self.manager.clear()

        self.assertEqual(self.manager.count, 0)
        self.assertEqual(self.manager.list_hooks(), ())

    def test_clear_installed_hooks_is_rejected(self) -> None:
        self.create_demo_hook("first")
        self.create_demo_hook("second")
        self.manager.install("first")

        with self.assertRaises(HookAlreadyInstalledError):
            self.manager.clear()

        self.assertEqual(self.manager.count, 2)

    def test_empty_name_is_rejected(self) -> None:
        with self.assertRaises(ValidationError):
            self.manager.create(
                name="",
                target="target",
                replacement="replacement",
            )

    def test_invalid_name_argument_is_rejected(self) -> None:
        with self.assertRaises(ValidationError):
            self.manager.get("")

        with self.assertRaises(ValidationError):
            self.manager.find(" ")

        with self.assertRaises(ValidationError):
            self.manager.contains("")

    def test_multiple_hooks_have_independent_states(self) -> None:
        first = self.create_demo_hook("first")
        second = self.create_demo_hook("second")

        self.manager.install("first")
        self.manager.remove("first")

        self.assertEqual(first.status, HookStatus.REMOVED)
        self.assertEqual(
            second.status,
            HookStatus.NOT_INSTALLED,
        )

    def test_summaries_reflect_current_state(self) -> None:
        self.create_demo_hook()
        self.manager.install("demo")

        summaries = self.manager.summaries()

        self.assertEqual(
            summaries[0].status,
            HookStatus.INSTALLED,
        )
        self.assertTrue(summaries[0].is_installed)


if __name__ == "__main__":
    unittest.main()
