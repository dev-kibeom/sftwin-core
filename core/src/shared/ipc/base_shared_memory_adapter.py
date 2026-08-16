from abc import ABC, abstractmethod
from typing import Any, Generic, TypeVar

from shared.enums.global_error_code_enum import GlobalErrorCodeEnum
from shared.exceptions.base_exception import BaseSystemException
from shared.logger.global_system_logger import GlobalSystemLogger

T = TypeVar("T")


class BaseSharedMemoryAdapter(ABC, Generic[T]):
    """POSIX Shared Memory Zero-Copy IPC 추상 기반 클래스"""

    def __init__(
        self, shm_fd: int, shm_ptr: Any, logger: GlobalSystemLogger | None = None
    ):
        self._shm_fd = shm_fd
        self._shm_ptr = shm_ptr
        self._logger = logger or GlobalSystemLogger(
            component_name="BaseSharedMemoryAdapter"
        )

    def write_to_shm(self, payload: T) -> bool:
        """
        Newspaper Structure: Zero-Copy Shared Memory 기록 인터페이스
        """
        self._validate_memory_mapping()
        self._logger.info("Writing payload to POSIX Shared Memory segment.")
        return self._do_write(payload)

    def read_from_shm(self) -> T:
        """
        Newspaper Structure: Zero-Copy Shared Memory 읽기 인터페이스
        """
        self._validate_memory_mapping()
        self._logger.info("Reading payload from POSIX Shared Memory segment.")
        return self._do_read()

    @abstractmethod
    def _do_write(self, payload: T) -> bool:
        """하위 구현체 실제 Write 연산"""
        pass

    @abstractmethod
    def _do_read(self) -> T:
        """하위 구현체 실제 Read 연산"""
        pass

    def _validate_memory_mapping(self) -> None:
        """
        Guard Clause: shm_fd 및 shm_ptr 포인터/디스크립터 손상 여부를 조기 차단하여
        Memory Segmentation Fault 발생을 방지합니다.

        Newspaper Structure: 메모리 매핑 검증 헬퍼
        """
        if self._shm_fd < 0 or self._shm_ptr is None:
            self._logger.error(
                f"SHM Descriptor Fault: shm_fd={self._shm_fd}, shm_ptr={self._shm_ptr}"
            )
            raise BaseSystemException(
                error_code=GlobalErrorCodeEnum.ERR_IPC_SHARED_MEMORY_ERROR,
                message="POSIX Shared Memory descriptor or pointer invalid. Access blocked to prevent segmentation fault.",
                status_code=500,
                details={
                    "shm_fd": self._shm_fd,
                    "shm_ptr_valid": self._shm_ptr is not None,
                },
            )
