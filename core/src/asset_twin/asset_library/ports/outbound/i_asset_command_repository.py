# core/src/asset_twin/asset_library/ports/outbound/i_asset_command_repository.py
from abc import ABC, abstractmethod

from asset_twin.asset_library.domain.asset import Asset


class IAssetCommandRepository(ABC):
    """
    순수 자산(Asset) CUD 전담 아웃바운드 포트
    """

    @abstractmethod
    def find_by_id(self, entity_id: str) -> Asset | None:
        pass

    @abstractmethod
    def save(self, entity: Asset) -> Asset:
        pass

    @abstractmethod
    def delete(self, entity_id: str) -> bool:
        pass
