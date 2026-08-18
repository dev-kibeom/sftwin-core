from abc import ABC, abstractmethod
from typing import Any, Generic, TypeVar

from shared.context.log_context import LogContext
from shared.enums.global_error_code_enum import GlobalErrorCode
from shared.exceptions.base_system_exception import BaseSystemException
from shared.logger.global_system_logger import GlobalSystemLogger

T = TypeVar("T")


class BaseSharedMemoryDriver(ABC, Generic[T]):
    """POSIX Shared Memory Zero-Copy 저수준 공통 드라이버"""

    def __init__(
        self,
        shm_fd: int,
        shm_ptr: Any,
        component_name: str = "BaseSharedMemoryDriver",
        system_logger: GlobalSystemLogger | None = None,
    ) -> None:
        self._shm_fd = shm_fd
        self._shm_ptr = shm_ptr
        self._system_logger = system_logger or GlobalSystemLogger(
            component_name=component_name
        )

    def write_to_shm(self, payload: T, trace_id: str = "TRC-SHM-WRITE") -> bool:
        log_ctx = LogContext(
            trace_id=trace_id,
            context={"shm_fd": self._shm_fd, "operation": "WRITE"},
        )

        self._validate_memory_mapping(log_ctx)

        self._system_logger.debug(
            "Writing payload to POSIX Shared Memory segment.", log_ctx=log_ctx
        )
        return self._do_write(payload)

    def read_from_shm(self, trace_id: str = "TRC-SHM-READ") -> T:
        log_ctx = LogContext(
            trace_id=trace_id,
            context={"shm_fd": self._shm_fd, "operation": "READ"},
        )

        self._validate_memory_mapping(log_ctx)

        self._system_logger.debug(
            "Reading payload from POSIX Shared Memory segment.", log_ctx=log_ctx
        )
        return self._do_read()

    @abstractmethod
    def _do_write(self, payload: T) -> bool:
        pass

    @abstractmethod
    def _do_read(self) -> T:
        pass

    def _validate_memory_mapping(self, log_ctx: LogContext) -> None:
        """shm_fd 및 shm_ptr 포인터 손상 여부를 조기 차단하여 Segfault 방지"""

        if self._shm_fd < 0 or self._shm_ptr is None:
            self._system_logger.error(
                f"SHM Descriptor Fault: shm_fd={self._shm_fd}, shm_ptr={self._shm_ptr}",
                log_ctx=log_ctx,
            )
            raise BaseSystemException(
                error_code=GlobalErrorCode.ERR_IPC_SHARED_MEMORY_ERROR,
                message="POSIX Shared Memory descriptor or pointer invalid. Access blocked to prevent segmentation fault.",
                status_code=500,
                details={
                    "shm_fd": self._shm_fd,
                    "shm_ptr_valid": self._shm_ptr is not None,
                },
            )
