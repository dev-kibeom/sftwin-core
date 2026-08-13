"""
===============================================================================
[File Name] i_asset_twin_query_facade.py
[Location ] /src/asset_twin/ports/inbound/i_asset_twin_query_facade.py
[Description]
 - AssetTwin 컴포넌트의 데이터 조회 전용(CQRS Read-Only) 추상 파사드 포트 인터페이스입니다.
===============================================================================
"""

from abc import ABC, abstractmethod

from asset_twin.twin_reconstruction.application.get_layout.get_layout_usecase import (
    LayoutRenderingDto,
)
from shared.dtos.asset_dto import AssetDto
from shared.security.user_context import UserContext


class AssetTwinQueryFacade(ABC):
    """
    조회 전용 파사드 추상 인터페이스 (CQRS 적용)
    """

    @abstractmethod
    def get_asset_info(self, asset_id: str, ctx: UserContext | None = None) -> AssetDto:
        """
        자산 단건 메타데이터 조회
        """
        pass

    @abstractmethod
    def get_layout_data(
        self, baseline_id: str, ctx: UserContext | None = None
    ) -> LayoutRenderingDto:
        """
        3D 캔버스 렌더링용 가상 공장 레이아웃 및 좌표 데이터 조회
        """
        pass
