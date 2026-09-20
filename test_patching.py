import unittest

from inlinehook.errors import (
    HookAlreadyInstalledError,
    HookNotInstalledError,
)
from inlinehook.memory import MemoryManager, MemoryPermission
from inlinehook.patching import Patch, PatchApplier, PatchState


class PatchingTests(unittest.TestCase):
    def create_applier(self):
        manager = MemoryManager()
        region = manager.allocate(
            8,
            {MemoryPermission.READ, MemoryPermission.WRITE},
        )
        region.write(b"ABCDEFGH")

        return region, PatchApplier(region)

    def test_patch_is_applied_and_verified(self):
        region, applier = self.create_applier()
        patch = Patch(offset=2, replacement=b"XYZ")

        applier.apply(patch)

        self.assertEqual(region.read(), b"ABXYZFGH")
        self.assertEqual(patch.state, PatchState.APPLIED)
        self.assertTrue(applier.verify_applied(patch))

    def test_patch_is_restored_and_verified(self):
        region, applier = self.create_applier()
        patch = Patch(offset=2, replacement=b"XYZ")

        applier.apply(patch)
        applier.restore(patch)

        self.assertEqual(region.read(), b"ABCDEFGH")
        self.assertEqual(patch.state, PatchState.RESTORED)
        self.assertTrue(applier.verify_restored(patch))

    def test_same_patch_cannot_be_applied_twice(self):
        _, applier = self.create_applier()
        patch = Patch(offset=0, replacement=b"XX")

        applier.apply(patch)

        with self.assertRaises(HookAlreadyInstalledError):
            applier.apply(patch)

    def test_unapplied_patch_cannot_be_restored(self):
        _, applier = self.create_applier()
        patch = Patch(offset=0, replacement=b"XX")

        with self.assertRaises(HookNotInstalledError):
            applier.restore(patch)

    def test_restore_all_restores_multiple_patches(self):
        region, applier = self.create_applier()
        first = Patch(offset=0, replacement=b"12")
        second = Patch(offset=4, replacement=b"XY")

        applier.apply(first)
        applier.apply(second)
        applier.restore_all()

        self.assertEqual(region.read(), b"ABCDEFGH")
        self.assertTrue(applier.verify_restored(first))
        self.assertTrue(applier.verify_restored(second))


if __name__ == "__main__":
    unittest.main()
