"""
===============================================================================
[File Name] asset_twin_command_impl.py
[Location ] /src/asset_twin/facades/asset_twin_command_impl.py
[Description]
 - AssetTwinCommandFacade 인터페이스를 구현하여 타 컴포넌트나 API 계층의 디지털 트윈 복각 명령을
   유즈케이스로 연결하는 단일 진입점 파사드입니다.
===============================================================================
"""

from abc import ABC, abstractmethod

from src.asset_twin.twin_reconstruction.application.reconstruct_twin_usecase import (
    RawDataDto,
    ReconstructTwinUseCase,
    TwinMetricsDto,
)
from src.shared.logging.global_system_logger import GlobalSystemLogger
from src.shared.security.user_context import UserContext


class AssetTwinCommandFacade(ABC):
    """
    명령 전용 파사드 인터페이스
    """

    @abstractmethod
    def reconstruct_twin(
        self, raw_data: RawDataDto, ctx: UserContext | None = None
    ) -> TwinMetricsDto:
        pass


class AssetTwinCommandImpl(AssetTwinCommandFacade):
    """
    AssetTwinCommandFacade 구현체
    """

    def __init__(
        self,
        reconstruct_uc: ReconstructTwinUseCase,
        logger: GlobalSystemLogger | None = None,
    ) -> None:
        self._reconstruct_uc = reconstruct_uc
        self._logger = logger or GlobalSystemLogger(
            component_name="AssetTwinCommandImpl"
        )

    def reconstruct_twin(
        self, raw_data: RawDataDto, ctx: UserContext | None = None
    ) -> TwinMetricsDto:
        self._logger.info(
            f"[AssetTwinCommandImpl] Delegate reconstruct_twin for '{raw_data.baseline_name}'"
        )
        if ctx is None:
            ctx = UserContext.create_system_context()
        return self._reconstruct_uc.execute(raw_data, ctx)
