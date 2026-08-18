from typing import Protocol


class IProcurementQueryRepository(Protocol):
    """B2B 조달 도메인 순수 데이터 조회(R) 포트"""

    def get_production_order_by_id(self, baseline_id: str) -> str | None: ...

    def get_baseline_owner(self, baseline_id: str) -> str | None: ...
