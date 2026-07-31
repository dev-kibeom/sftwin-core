"""
Unit Test Specification for BaseSharedMemoryAdapter (TC-ADP-03, TC-ADP-05)
"""


import pytest

from src.shared.exceptions.base_exception import BaseSystemException
from src.shared.exceptions.error_codes import GlobalErrorCodes
from src.shared.ipc.base_shared_memory_adapter import BaseSharedMemoryAdapter


class ConcreteMuJoCoIpcAdapter(BaseSharedMemoryAdapter[bytes]):
    """테스트용 Concrete Shared Memory IPC Adapter"""

    def __init__(self, shm_fd: int, shm_ptr: object):
        super().__init__(shm_fd, shm_ptr)
        self._buffer = b""

    def _do_write(self, payload: bytes) -> bool:
        self._buffer = payload
        return True

    def _do_read(self) -> bytes:
        return self._buffer


# TC-ADP-03: Happy Path - POSIX Shared Memory Zero-Copy Read/Write 검증
def test_tc_adp_03_shm_read_write_success():
    dummy_ptr = object()
    adapter = ConcreteMuJoCoIpcAdapter(shm_fd=3, shm_ptr=dummy_ptr)

    payload = b"MOTION_STATE_VECTOR_3D"
    write_success = adapter.write_to_shm(payload)
    read_payload = adapter.read_from_shm()

    assert write_success is True
    assert read_payload == payload, (
        "Read binary payload must exactly match written payload."
    )


# TC-ADP-05: Edge Case - SHM 포인터 손상시 Guard Clause 차단 및 예외 검증
def test_tc_adp_05_shm_pointer_fault_guard_clause():
    # shm_fd = -1 및 shm_ptr = None (메모리 매핑 손상)
    adapter = ConcreteMuJoCoIpcAdapter(shm_fd=-1, shm_ptr=None)

    with pytest.raises(BaseSystemException) as exc_info:
        adapter.write_to_shm(b"CORRUPTED_PAYLOAD")

    assert exc_info.value.error_code == GlobalErrorCodes.ERR_SHARED_INTERNAL_ERROR
    assert exc_info.value.status_code == 500
    assert "POSIX Shared Memory descriptor or pointer invalid" in exc_info.value.message
