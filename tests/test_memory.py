import unittest

from inlinehook.errors import (
    MemoryOperationError,
    PermissionDeniedError,
    ValidationError,
)
from inlinehook.memory import MemoryManager, MemoryPermission


class MemoryTests(unittest.TestCase):
    def test_allocate_and_write_read_region(self):
        manager = MemoryManager()
        region = manager.allocate(
            16,
            {MemoryPermission.READ, MemoryPermission.WRITE},
        )

        region.write(b"HELLO")

        self.assertEqual(region.read(0, 5), b"HELLO")
        self.assertEqual(region.size, 16)

    def test_read_only_region_rejects_write(self):
        manager = MemoryManager()
        region = manager.allocate(8, {MemoryPermission.READ})

        with self.assertRaises(PermissionDeniedError):
            region.write(b"X")

    def test_write_only_region_rejects_read(self):
        manager = MemoryManager()
        region = manager.allocate(8, {MemoryPermission.WRITE})

        with self.assertRaises(PermissionDeniedError):
            region.read()

    def test_negative_size_is_rejected(self):
        manager = MemoryManager()

        with self.assertRaises(ValidationError):
            manager.allocate(-1)

    def test_out_of_range_access_is_rejected(self):
        manager = MemoryManager()
        region = manager.allocate(
            4,
            {MemoryPermission.READ, MemoryPermission.WRITE},
        )

        with self.assertRaises(MemoryOperationError):
            region.read(3, 5)

    def test_release_removes_region(self):
        manager = MemoryManager()
        region = manager.allocate(8)

        manager.release(region.address)

        self.assertEqual(manager.regions, ())

    def test_find_region_by_address(self):
        manager = MemoryManager()
        region = manager.allocate(8)

        found = manager.find_region(region.address + 2, 2)

        self.assertIs(found, region)


if __name__ == "__main__":
    unittest.main()
