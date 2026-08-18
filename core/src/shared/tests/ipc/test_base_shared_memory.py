import pytest
from shared.enums.global_error_code_enum import GlobalErrorCode
from shared.exceptions.base_exception import BaseSystemException
from shared.ipc.base_shared_memory_driver import BaseSharedMemoryDriver


class ConcreteSharedMemoryDriver(BaseSharedMemoryDriver[bytes]):
    """추상 메서드 _do_write, _do_read 구현용 테스트 더블"""

    def __init__(self, shm_fd: int, shm_ptr: object):
        super().__init__(shm_fd, shm_ptr)
        self._buffer = b""

    def _do_write(self, payload: bytes) -> bool:
        self._buffer = payload
        return True

    def _do_read(self) -> bytes:
        return self._buffer


@pytest.fixture
def valid_shm_driver():
    """정상 매핑 상태의 SHM 드라이버 Fixture"""
    dummy_ptr = object()
    return ConcreteSharedMemoryDriver(shm_fd=3, shm_ptr=dummy_ptr)


# TC-SHM-01: Happy Path - POSIX Shared Memory Zero-Copy Read/Write 검증
def test_shm_read_write_success(valid_shm_driver):
    payload = b"MOTION_STATE_VECTOR_3D"

    write_success = valid_shm_driver.write_to_shm(payload, trace_id="TRC-SHM-001")
    read_payload = valid_shm_driver.read_from_shm(trace_id="TRC-SHM-002")

    assert write_success is True
    assert read_payload == payload


# TC-SHM-02: Edge Case - SHM 포인터/디스크립터 손상 시 Guard Clause 차단 검증
def test_shm_pointer_fault_guard_clause():
    corrupted_driver = ConcreteSharedMemoryDriver(shm_fd=-1, shm_ptr=None)

    with pytest.raises(BaseSystemException) as exc_info:
        corrupted_driver.write_to_shm(b"CORRUPTED_PAYLOAD")

    assert exc_info.value.error_code == GlobalErrorCode.ERR_IPC_SHARED_MEMORY_ERROR
    assert exc_info.value.status_code == 500
    assert "POSIX Shared Memory descriptor or pointer invalid" in exc_info.value.message
