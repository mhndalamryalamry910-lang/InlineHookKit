import unittest

from inlinehook.models import Hook, HookStatus


class HookModelTests(unittest.TestCase):
    def test_hook_starts_not_installed(self):
        hook = Hook(
            name="demo",
            target="target_function",
            replacement="replacement_function",
        )

        self.assertEqual(hook.status, HookStatus.NOT_INSTALLED)
        self.assertFalse(hook.is_installed)

    def test_hook_can_be_marked_installed(self):
        hook = Hook("demo", "target", "replacement")

        hook.mark_installed(b"\x90\x90")

        self.assertEqual(hook.status, HookStatus.INSTALLED)
        self.assertTrue(hook.is_installed)
        self.assertEqual(hook.original_bytes, b"\x90\x90")
        self.assertIsNone(hook.error_message)

    def test_hook_can_be_removed(self):
        hook = Hook("demo", "target", "replacement")
        hook.mark_installed(b"\x90")

        hook.mark_removed()

        self.assertEqual(hook.status, HookStatus.REMOVED)
        self.assertFalse(hook.is_installed)

    def test_hook_can_fail(self):
        hook = Hook("demo", "target", "replacement")

        hook.mark_failed("Installation failed.")

        self.assertEqual(hook.status, HookStatus.FAILED)
        self.assertEqual(hook.error_message, "Installation failed.")

    def test_empty_name_is_rejected(self):
        with self.assertRaises(ValueError):
            Hook("", "target", "replacement")

    def test_empty_failure_message_is_rejected(self):
        hook = Hook("demo", "target", "replacement")

        with self.assertRaises(ValueError):
            hook.mark_failed("")


if __name__ == "__main__":
    unittest.main()
