from typing import Protocol

from digital_twin.contracts.dtos.twin_baseline_dto import TwinBaselineDto


class IBaselineQueryRepository(Protocol):
    """베이스라인 화면 표출 및 통계 조회 전담 포트 (불변 DTO를 다룸)"""

    def find_by_id(self, baseline_id: str, company_id: str) -> TwinBaselineDto | None:
        """테넌시 격리 및 논리 삭제 필터링이 적용된 단건 조회"""

    # TODO
    # def get_detail_by_id(self, baseline_id: str) -> BaselineDetailDto | None:
    #     """화면 렌더링에 필요한 필드만 가볍게 조회한다."""
    #     ...

    # def list_by_company(self, company_id: str) -> list[BaselineSummaryDto]:
    #     """목록 조회를 위한 DTO 리스트를 반환한다."""
    #     ...
