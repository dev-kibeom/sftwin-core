"""
===============================================================================
[File Name] manage_asset_usecase.py
[Location ] /src/asset_twin/asset_library/application/manage_asset_usecase.py
[Description]
 - 자산 등록(register_asset) 및 단건 조회(get_asset)를 수행하는 무상태(Stateless) 유즈케이스.
===============================================================================
"""

from asset_twin.asset_library.domain.asset import Asset
from asset_twin.asset_library.ports.outbound.i_asset_command_repository import (
    IAssetCommandRepository,
)
from shared.dtos.asset_dto import AssetDto
from shared.enums.asset_type_enum import AssetTypeEnum
from shared.exceptions.base_exception import BaseSystemException
from shared.exceptions.error_codes import GlobalErrorCodes
from shared.logger.global_system_logger import GlobalSystemLogger
from shared.security.user_context import UserContext


class ManageAssetUseCase:
    """
    Stateless 애플리케이션 유즈케이스
    """

    def __init__(
        self,
        command_repository: IAssetCommandRepository,
        logger: GlobalSystemLogger | None = None,
    ) -> None:
        self._command_repository = command_repository
        self._logger = logger or GlobalSystemLogger(component_name="ManageAssetUseCase")

    def register_asset(self, asset_dto: AssetDto, ctx: UserContext) -> str:
        """
        신규 자산 동적 등록 오케스트레이션
        """
        self._logger.info(
            f"[ManageAssetUseCase] Registering asset '{asset_dto.asset_name}' by user '{ctx.user_id}'"
        )

        # Context Guard
        if not ctx or not ctx.company_id:
            self._logger.error(
                "[ManageAssetUseCase] UserContext or company_id missing in request"
            )
            raise BaseSystemException(
                error_code=GlobalErrorCodes.ERR_COMMON_INVALID_INPUT,
                message="UserContext with valid company_id is required.",
                status_code=400,
            )

        # AssetType Enum 파싱/검증
        try:
            asset_enum = AssetTypeEnum(asset_dto.asset_type)
        except ValueError as e:
            self._logger.warn(
                f"[ManageAssetUseCase] Invalid asset type: {asset_dto.asset_type}"
            )
            raise BaseSystemException(
                error_code=GlobalErrorCodes.ERR_TWIN_INVALID_SCHEMA,
                message=f"Invalid asset type '{asset_dto.asset_type}'.",
                status_code=400,
                details={"asset_type": asset_dto.asset_type},
            ) from e

        # 도메인 엔티티 생성 및 Audit 정보 주입
        domain_entity = Asset(
            asset_name=asset_dto.asset_name,
            asset_type=asset_enum,
            company_id=ctx.company_id,
            kinematics_metadata=asset_dto.kinematics_metadata or {},
            cad_file_path=asset_dto.cad_file_path,
            created_by=ctx.username,
            updated_by=ctx.username,
        )

        # Guard Clause: 도메인 스키마 검증
        domain_entity.validate_schema()

        # 저장소 영속화
        saved_entity = self._command_repository.save(domain_entity)
        self._logger.info(
            f"[ManageAssetUseCase] Asset successfully registered with ID: {saved_entity.asset_id}"
        )

        return saved_entity.asset_id

    def get_asset(self, asset_id: str, ctx: UserContext) -> AssetDto:
        """
        자산 단건 조회 및 Tenant Isolation 검증
        """
        self._logger.info(
            f"[ManageAssetUseCase] Fetching asset '{asset_id}' for company '{ctx.company_id}'"
        )

        entity = self._command_repository.find_by_id(asset_id)

        # Guard Clause: 자산 미존재 시 404 차단
        if not entity or entity.is_deleted:
            self._logger.warning(
                f"[ManageAssetUseCase] Asset not found or deleted: {asset_id}"
            )
            raise BaseSystemException(
                error_code=GlobalErrorCodes.ERR_TWIN_NOT_FOUND,
                message=f"Requested asset '{asset_id}' does not exist.",
                status_code=404,
            )

        # Guard Clause: 테넌트 격리 위반 시 404로 은닉 차단
        if entity.company_id != ctx.company_id:
            self._logger.warn(
                f"[ManageAssetUseCase] Tenant isolation violation: Asset company '{entity.company_id}' != Request company '{ctx.company_id}'"
            )
            raise BaseSystemException(
                error_code=GlobalErrorCodes.ERR_TWIN_NOT_FOUND,
                message=f"Requested asset '{asset_id}' does not exist.",
                status_code=404,
            )

        # Domain Entity -> DTO 변환
        return AssetDto(
            asset_id=entity.asset_id,
            asset_name=entity.asset_name,
            asset_type=entity.asset_type.value,
            cad_file_path=entity.cad_file_path,
            kinematics_metadata=entity.kinematics_metadata,
            created_at=entity.created_at,
        )
