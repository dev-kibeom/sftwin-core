from typing import Protocol

from digital_twin.asset_library.domain.asset.asset import Asset


class IAssetCommandRepository(Protocol):
    """단일 기기, 로봇 모델 영속화 전담 아웃바운드 포트"""

    def save(self, asset: Asset) -> Asset: ...

    def delete(self, asset_id: str) -> bool: ...
