from abc import ABC, abstractmethod
from typing import Any, Generic, TypeVar

from shared.context.log_context import LogContext
from shared.exceptions.base_system_exception import BaseSystemException
from shared.exceptions.global_error_code_enum import GlobalErrorCode
from shared.logger.global_system_logger import GlobalSystemLogger

T = TypeVar("T")


class BaseSharedMemoryDriver(ABC, Generic[T]):
    """POSIX Shared Memory Zero-Copy 저수준 공통 드라이버"""

    def __init__(
        self,
        shm_fd: int,
        shm_ptr: Any,
        shm_size: int = 0,
        component_name: str = "BaseSharedMemoryDriver",
        system_logger: GlobalSystemLogger | None = None,
    ) -> None:
        self._shm_fd = shm_fd
        self._shm_ptr = shm_ptr
        self._shm_size = shm_size
        self._system_logger = system_logger or GlobalSystemLogger(
            component_name=component_name
        )

    def write_to_shm(self, payload: T, trace_id: str = "TRC-SHM-WRITE") -> bool:
        """POSIX Shared Memory 영역에 페이로드 쓰기 (무결성 검증 및 예외 변환 포함)"""
        log_ctx = LogContext(
            trace_id=trace_id,
            context={
                "shm_fd": self._shm_fd,
                "operation": "WRITE",
                "shm_size": self._shm_size,
            },
        )

        self._validate_memory_mapping(log_ctx)

        try:
            self._acquire_lock()
            try:
                self._system_logger.debug(
                    "Writing payload to POSIX Shared Memory segment.", log_ctx=log_ctx
                )
                return self._do_write(payload)
            finally:
                self._release_lock()
        except BaseSystemException:
            raise
        except Exception as exc:
            self._system_logger.error(
                f"SHM Write Operation Failed: {str(exc)}",
                log_ctx=log_ctx,
            )
            raise BaseSystemException(
                error_code=GlobalErrorCode.ERR_IPC_SHARED_MEMORY_ERROR,
                message=f"POSIX Shared Memory write failed: {str(exc)}",
                status_code=500,
                details={
                    "shm_fd": self._shm_fd,
                    "operation": "WRITE",
                    "error": str(exc),
                },
            ) from exc

    def read_from_shm(self, trace_id: str = "TRC-SHM-READ") -> T:
        """POSIX Shared Memory 영역에서 페이로드 읽기 (무결성 검증 및 예외 변환 포함)"""
        log_ctx = LogContext(
            trace_id=trace_id,
            context={
                "shm_fd": self._shm_fd,
                "operation": "READ",
                "shm_size": self._shm_size,
            },
        )

        self._validate_memory_mapping(log_ctx)

        try:
            self._acquire_lock()
            try:
                self._system_logger.debug(
                    "Reading payload from POSIX Shared Memory segment.", log_ctx=log_ctx
                )
                return self._do_read()
            finally:
                self._release_lock()
        except BaseSystemException:
            raise
        except Exception as exc:
            self._system_logger.error(
                f"SHM Read Operation Failed: {str(exc)}",
                log_ctx=log_ctx,
            )
            raise BaseSystemException(
                error_code=GlobalErrorCode.ERR_IPC_SHARED_MEMORY_ERROR,
                message=f"POSIX Shared Memory read failed: {str(exc)}",
                status_code=500,
                details={
                    "shm_fd": self._shm_fd,
                    "operation": "READ",
                    "error": str(exc),
                },
            ) from exc

    @abstractmethod
    def _do_write(self, payload: T) -> bool:
        """실제 바이트 복사 또는 C-타입 매핑 쓰기 구현"""
        pass

    @abstractmethod
    def _do_read(self) -> T:
        """실제 바이트 복사 또는 C-타입 매핑 읽기 구현"""
        pass

    def _acquire_lock(self) -> None:
        """세마포어/뮤텍스 락 획득 (서브클래스에서 동기화 방식에 맞게 오버라이딩 가능)"""
        pass

    def _release_lock(self) -> None:
        """세마포어/뮤텍스 락 해제 (서브클래스에서 동기화 방식에 맞게 오버라이딩 가능)"""
        pass

    def _validate_memory_mapping(self, log_ctx: LogContext) -> None:
        """shm_fd, shm_ptr 및 버퍼 크기 손상 여부를 조기 차단하여 Segfault 방지"""
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

        if self._shm_size < 0:
            self._system_logger.error(
                f"Invalid SHM buffer size configured: shm_size={self._shm_size}",
                log_ctx=log_ctx,
            )
            raise BaseSystemException(
                error_code=GlobalErrorCode.ERR_IPC_SHARED_MEMORY_ERROR,
                message="Configured POSIX Shared Memory segment size cannot be negative.",
                status_code=500,
                details={"shm_size": self._shm_size},
            )
