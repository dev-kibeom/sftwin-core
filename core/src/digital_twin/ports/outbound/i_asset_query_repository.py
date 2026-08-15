from typing import Protocol

from digital_twin.asset_library.domain.asset import Asset


class IAssetQueryRepository(Protocol):
    """단일 기기, 로봇 모델 조회 전담 아웃바운드 포트"""

    def find_by_id(self, asset_id: str) -> Asset | None: ...
