"""
===============================================================================
[File Name] i_asset_twin_command_facade.py
[Location ] /src/asset_twin/ports/inbound/i_asset_twin_command_facade.py
[Description]
 - AssetTwin 컴포넌트의 데이터 명령 전용(CQRS Write-Only) 추상 파사드 포트 인터페이스입니다.
===============================================================================
"""

from abc import ABC, abstractmethod

from asset_twin.twin_reconstruction.application.reconstruct_twin.reconstruct_twin_usecase import (
    RawDataDto,
    TwinMetricsDto,
)
from shared.security.user_context import UserContext


class AssetTwinCommandFacade(ABC):
    """
    명령 전용 파사드 인터페이스
    """

    @abstractmethod
    def reconstruct_twin(
        self, raw_data: RawDataDto, ctx: UserContext | None = None
    ) -> TwinMetricsDto:
        pass
