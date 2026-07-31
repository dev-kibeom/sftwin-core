"""
===============================================================================
[File Name] asset_twin_command_impl.py
[Location ] /src/asset_twin/facades/asset_twin_command_impl.py
[Description]
 - AssetTwinCommandFacade 인터페이스를 구현하여 타 컴포넌트나 API 계층의 디지털 트윈 복각 명령을
   유즈케이스로 연결하는 단일 진입점 파사드입니다.
===============================================================================
"""

import logging

from src.asset_twin.twin_reconstruction.application.reconstruct_twin_usecase import (
    RawDataDto,
    ReconstructTwinUseCase,
    TwinMetricsDto,
)
from src.shared.enums.user_role_enum import UserRoleEnum
from src.shared.security.user_context import UserContext

logger = logging.getLogger("asset_twin.facades.command_impl")


class AssetTwinCommandFacade:
    """
    명령 전용 파사드 인터페이스
    """

    def reconstruct_twin(
        self, raw_data: RawDataDto, ctx: UserContext | None = None
    ) -> TwinMetricsDto:
        raise NotImplementedError()


class AssetTwinCommandImpl(AssetTwinCommandFacade):
    """
    AssetTwinCommandFacade 구현체
    """

    def __init__(self, reconstruct_uc: ReconstructTwinUseCase) -> None:
        self._reconstruct_uc = reconstruct_uc

    def reconstruct_twin(
        self, raw_data: RawDataDto, ctx: UserContext | None = None
    ) -> TwinMetricsDto:
        logger.info(
            f"[AssetTwinCommandImpl] Delegate reconstruct_twin for '{raw_data.baseline_name}'"
        )
        if ctx is None:
            ctx = UserContext(
                user_id="SYSTEM",
                username="system",
                company_id="SYSTEM_PUBLIC",
                role=UserRoleEnum.SYSTEM_ADMIN,
                accessible_factory_ids=[],
            )
        return self._reconstruct_uc.execute(raw_data, ctx)
