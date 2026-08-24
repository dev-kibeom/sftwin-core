from digital_twin.asset_library.domain.asset.asset import Asset
from digital_twin.dtos.asset_dto import AssetDto
from digital_twin.ports.outbound.i_asset_command_repository import (
    IAssetCommandRepository,
)
from shared.context.user_context import UserContext
from shared.exceptions.base_system_exception import BaseSystemException
from shared.exceptions.global_error_code_enum import GlobalErrorCode
from shared.logger.global_system_logger import GlobalSystemLogger
from shared.security.context_guard import require_user_context


class RegisterAssetUseCase:
    """신규 자산 등록 비즈니스 로직을 오케스트레이션하는 유스케이스"""

    def __init__(
        self,
        command_repo: IAssetCommandRepository,
        system_logger: GlobalSystemLogger | None = None,
    ) -> None:
        self._command_repo = command_repo
        self._system_logger = system_logger or GlobalSystemLogger(
            component_name="RegisterAssetUseCase"
        )

    @require_user_context
    def execute(self, asset_dto: AssetDto, ctx: UserContext) -> str:
        # 1. DTO 언패킹 및 Domain Entity 생성 (검증 실패 시 표준 예외로 변환)
        try:
            asset = Asset(
                asset_name=asset_dto.asset_name,
                asset_type=asset_dto.asset_type,
                company_id=ctx.company_id,
                kinematics_metadata=asset_dto.kinematics_metadata or {},
                cad_file_path=asset_dto.cad_file_path,
                created_by=ctx.user_id,
                updated_by=ctx.user_id,
            )
        except ValueError as e:
            raise BaseSystemException.from_error_code(
                GlobalErrorCode.ERR_TWIN_INVALID_SCHEMA,
                custom_message=str(e),
                details={"asset_name": asset_dto.asset_name},
            ) from e

        # 2. 영속화 포트 호출 (실패 시 예외 체이닝 및 상위 전파)
        saved_entity = self._command_repo.save(asset)

        # 3. 비즈니스 마일스톤 성공 로깅
        self._system_logger.info(
            f"Asset '{saved_entity.asset_id}' registered successfully",
            extra={
                "asset_id": saved_entity.asset_id,
                "asset_name": saved_entity.asset_name,
            },
        )

        return saved_entity.asset_id
