from typing import Protocol

from digital_twin.contracts.dtos.asset_dto import AssetDto


class IAssetQueryRepository(Protocol):
    """단일 기기, 로봇 모델 조회 전담 아웃바운드 포트"""

    def find_by_id(self, asset_id: str, company_id: str) -> AssetDto | None:
        """테넌시 격리가 적용된 단건 조회"""


#   def list_by_company(
#       self, company_id: str, limit: int = 50, offset: int = 0
#   ) -> list[AssetSummaryDto]:
#     """목록 조회"""
#     ...
