"""Safe memory-region management for InlineHookKit.

This module currently provides an in-process simulation layer.
It does not access or modify another process's memory.
"""

from __future__ import annotations

from dataclasses import dataclass
from enum import Enum

from .errors import (
    MemoryOperationError,
    PermissionDeniedError,
    ValidationError,
)


class MemoryPermission(Enum):
    """Permissions that may be assigned to a simulated memory region."""

    READ = "r"
    WRITE = "w"
    EXECUTE = "x"


@dataclass(frozen=True)
class MemoryRegionInfo:
    """Descriptive information about a simulated memory region."""

    address: int
    size: int
    permissions: frozenset[MemoryPermission]
    allocated: bool = True


class MemoryRegion:
    """Represent an isolated, simulated memory region."""

    def __init__(
        self,
        address: int,
        size: int,
        permissions: frozenset[MemoryPermission],
    ) -> None:
        """Create a validated simulated memory region."""
        if address < 0:
            raise ValidationError("Memory address cannot be negative.")

        if size <= 0:
            raise ValidationError("Memory region size must be greater than zero.")

        if not permissions:
            raise ValidationError(
                "A memory region must have at least one permission."
            )

        self._info = MemoryRegionInfo(
            address=address,
            size=size,
            permissions=permissions,
        )
        self._data = bytearray(size)

    @property
    def address(self) -> int:
        """Return the simulated starting address."""
        return self._info.address

    @property
    def size(self) -> int:
        """Return the region size in bytes."""
        return self._info.size

    @property
    def permissions(self) -> frozenset[MemoryPermission]:
        """Return the current region permissions."""
        return self._info.permissions

    @property
    def info(self) -> MemoryRegionInfo:
        """Return immutable metadata describing this region."""
        return self._info

    def _validate_range(self, offset: int, length: int) -> None:
        """Validate an offset and length within the region."""
        if offset < 0:
            raise ValidationError("Memory offset cannot be negative.")

        if length < 0:
            raise ValidationError("Memory length cannot be negative.")

        if offset + length > self.size:
            raise MemoryOperationError(
                "The requested range is outside the memory region."
            )

    def read(self, offset: int = 0, length: int | None = None) -> bytes:
        """Read bytes from the region when READ permission is available."""
        if MemoryPermission.READ not in self.permissions:
            raise PermissionDeniedError(
                "The memory region does not have READ permission."
            )

        if length is None:
            length = self.size - offset

        self._validate_range(offset, length)
        return bytes(self._data[offset : offset + length])

    def write(self, data: bytes, offset: int = 0) -> None:
        """Write bytes to the region when WRITE permission is available."""
        if MemoryPermission.WRITE not in self.permissions:
            raise PermissionDeniedError(
                "The memory region does not have WRITE permission."
            )

        if not isinstance(data, bytes):
            raise ValidationError("Memory data must be a bytes object.")

        self._validate_range(offset, len(data))
        self._data[offset : offset + len(data)] = data

    def contains(self, address: int, length: int = 1) -> bool:
        """Return whether an address range is inside this region."""
        if length <= 0:
            return False

        region_end = self.address + self.size
        requested_end = address + length

        return (
            self.address <= address
            and requested_end <= region_end
        )


class MemoryManager:
    """Manage isolated simulated memory regions."""

    def __init__(self, base_address: int = 0x10000000) -> None:
        """Create an empty manager with a deterministic base address."""
        if base_address < 0:
            raise ValidationError(
                "Base address cannot be negative."
            )

        self._next_address = base_address
        self._regions: dict[int, MemoryRegion] = {}

    @property
    def regions(self) -> tuple[MemoryRegionInfo, ...]:
        """Return metadata for all currently allocated regions."""
        return tuple(
            region.info for region in self._regions.values()
        )

    def allocate(
        self,
        size: int,
        permissions: set[MemoryPermission] | None = None,
    ) -> MemoryRegion:
        """Allocate a simulated region and return it."""
        if size <= 0:
            raise ValidationError(
                "Allocation size must be greater than zero."
            )

        selected_permissions = permissions or {
            MemoryPermission.READ,
            MemoryPermission.WRITE,
        }

        frozen_permissions = frozenset(selected_permissions)

        region = MemoryRegion(
            address=self._next_address,
            size=size,
            permissions=frozen_permissions,
        )

        self._regions[region.address] = region

        # Leave a gap between simulated regions to make boundary errors
        # easier to detect during testing.
        self._next_address += size + 0x1000

        return region

    def get_region(self, address: int) -> MemoryRegion:
        """Return the region that starts at the specified address."""
        try:
            return self._regions[address]
        except KeyError as error:
            raise MemoryOperationError(
                f"No allocated region starts at address 0x{address:X}."
            ) from error

    def find_region(
        self,
        address: int,
        length: int = 1,
    ) -> MemoryRegion:
        """Find a region containing the requested address range."""
        for region in self._regions.values():
            if region.contains(address, length):
                return region

        raise MemoryOperationError(
            f"No allocated region contains address range "
            f"0x{address:X} - 0x{address + length:X}."
        )

    def release(self, address: int) -> None:
        """Release a simulated region by its starting address."""
        if address not in self._regions:
            raise MemoryOperationError(
                f"Cannot release unknown region at 0x{address:X}."
            )

        del self._regions[address]

    def release_all(self) -> None:
        """Release all simulated memory regions."""
        self._regions.clear()
