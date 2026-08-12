"""
===============================================================================
[File Name] get_layout_usecase.py
[Location ] /src/asset_twin/twin_reconstruction/application/get_layout_usecase.py
[Description]
 - 3D 캔버스 공간 렌더링에 필요한 TwinBaseline 및 자산 매핑 데이터(좌표/회전 등)를
   조회하고 RBAC/Tenant Isolation 권한을 검증하는 무상태(Stateless) 유즈케이스입니다.
 - 외부 프레임워크 의존성을 최소화한 순수 읽기 전용(CQRS Read-Only) 서비스를 제공합니다.
===============================================================================
"""

from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from typing import Any

from src.shared.exceptions.base_exception import BaseSystemException
from src.shared.exceptions.error_codes import GlobalErrorCodes
from src.shared.logger.global_system_logger import GlobalSystemLogger
from src.shared.security.user_context import UserContext


@dataclass
class AssetMappingRenderingDto:
    """
    3D 공간 배치 자산 개별 렌더링 DTO
    """

    asset_id: str
    asset_name: str
    asset_type: str
    cad_file_path: str | None
    position_xyz_json: dict[str, float]
    rotation_q_json: dict[str, float]


@dataclass
class LayoutRenderingDto:
    """
    3D 가상 공장 레이아웃 통합 렌더링 DTO
    """

    baseline_id: str
    baseline_name: str
    company_id: str
    sync_error_rate: float
    sync_status: str
    asset_mappings: list[AssetMappingRenderingDto] = field(default_factory=list)


class ITwinQueryRepository(ABC):
    """
    읽기 전용 레이아웃 조회용 아웃바운드 포트 인터페이스 (DIP 준수)
    """

    @abstractmethod
    def find_baseline_with_mappings(self, baseline_id: str) -> dict[str, Any] | None:
        pass


class GetLayoutUseCase:
    """
    3D 레이아웃 렌더링 데이터 조회 무상태 유즈케이스
    """

    def __init__(
        self,
        query_repository: ITwinQueryRepository,
        logger: GlobalSystemLogger | None = None,
    ) -> None:
        self._query_repository = query_repository
        self._logger = logger or GlobalSystemLogger(component_name="GetLayoutUseCase")

    def execute(self, baseline_id: str, ctx: UserContext) -> LayoutRenderingDto:
        """
        3D 레이아웃 조회 및 RBAC/Tenant Isolation 권한 검증 오케스트레이션
        """
        self._logger.info(
            f"[GetLayoutUseCase] Fetching layout data for baseline_id='{baseline_id}' by user='{ctx.user_id}'"
        )

        # Context Guard
        if not ctx:
            self._logger.error("[GetLayoutUseCase] UserContext missing")
            raise BaseSystemException(
                error_code=GlobalErrorCodes.ERR_COMMON_INVALID_INPUT,
                message="UserContext is required for authorization.",
                status_code=400,
            )

        # 1. DB 조회 (읽기 전용 뷰 / 레포지토리)
        raw_data = self._query_repository.find_baseline_with_mappings(baseline_id)

        # Guard Clause 1: 데이터 미존재 시 404 차단
        if not raw_data:
            self._logger.warn(
                f"[GetLayoutUseCase] Baseline layout not found: '{baseline_id}'"
            )
            raise BaseSystemException(
                error_code=GlobalErrorCodes.ERR_TWIN_NOT_FOUND,
                message=f"Requested 3D baseline layout '{baseline_id}' does not exist.",
                status_code=404,
            )

        # Guard Clause 2: 권한 검증 (Tenant Isolation & accessible_factory_ids)
        owner_company_id = raw_data.get("company_id", "")
        if not self.verify_access_rights(baseline_id, owner_company_id, ctx):
            self._logger.warn(
                f"[GetLayoutUseCase] Access denied for baseline_id='{baseline_id}'. "
                f"Owner company='{owner_company_id}', Request company='{ctx.company_id}'"
            )
            # 보안 은닉을 위해 403 대신 404로 일괄 차단
            raise BaseSystemException(
                error_code=GlobalErrorCodes.ERR_TWIN_NOT_FOUND,
                message=f"Requested 3D baseline layout '{baseline_id}' does not exist.",
                status_code=404,
            )

        # 2. DTO 매핑 변환
        mappings_list: list[AssetMappingRenderingDto] = []
        for item in raw_data.get("asset_mappings", []):
            mappings_list.append(
                AssetMappingRenderingDto(
                    asset_id=item.get("asset_id", ""),
                    asset_name=item.get("asset_name", ""),
                    asset_type=item.get("asset_type", "UNKNOWN"),
                    cad_file_path=item.get("cad_file_path"),
                    position_xyz_json=item.get(
                        "position_xyz_json", {"x": 0.0, "y": 0.0, "z": 0.0}
                    ),
                    rotation_q_json=item.get(
                        "rotation_q_json", {"x": 0.0, "y": 0.0, "z": 0.0, "w": 1.0}
                    ),
                )
            )

        self._logger.info(
            f"[GetLayoutUseCase] Successfully assembled LayoutRenderingDto with {len(mappings_list)} asset mappings."
        )

        return LayoutRenderingDto(
            baseline_id=raw_data.get("baseline_id", baseline_id),
            baseline_name=raw_data.get("baseline_name", ""),
            company_id=owner_company_id,
            sync_error_rate=raw_data.get("sync_error_rate", 0.0),
            sync_status=raw_data.get("sync_status", "COMPLETED"),
            asset_mappings=mappings_list,
        )

    def verify_access_rights(
        self, baseline_id: str, owner_company_id: str, ctx: UserContext
    ) -> bool:
        """
        accessible_factory_ids 목록 포함 여부 또는 company_id 일치 여부 검증
        """
        # 1. accessible_factory_ids에 baseline_id가 직접 명시된 경우
        if ctx.accessible_factory_ids and baseline_id in ctx.accessible_factory_ids:
            return True

        # 2. 동일한 테넌트(company_id) 소유인 경우
        if owner_company_id and ctx.company_id and owner_company_id == ctx.company_id:
            return True

        return False
