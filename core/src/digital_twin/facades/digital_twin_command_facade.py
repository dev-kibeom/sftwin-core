from digital_twin.asset_library.application.register_asset.register_asset_usecase import (
    RegisterAssetUseCase,
)
from digital_twin.contracts.dtos.asset_dto import AssetDto
from digital_twin.contracts.ports.inbound.i_digital_twin_command_facade import (
    IDigitalTwinCommandFacade,
)
from digital_twin.twin_reconstruction.application.reconstruct_twin.raw_factory_data_dto import (
    RawFactoryDataDto,
)
from digital_twin.twin_reconstruction.application.reconstruct_twin.reconstruct_twin_usecase import (
    ReconstructTwinUseCase,
)
from digital_twin.twin_reconstruction.application.reconstruct_twin.twin_metrics_dto import (
    TwinMetricsDto,
)
from shared.context.user_context import UserContext
from shared.security.context_guard import require_permission
from shared.security.user_role_enum import UserRole


class DigitalTwinCommandFacade(IDigitalTwinCommandFacade):
    """외부 및 타 Bounded Context 요청을 유스케이스로 단순 라우팅하는 Thin Facade"""

    def __init__(
        self,
        register_asset_uc: RegisterAssetUseCase,
        reconstruct_uc: ReconstructTwinUseCase,
    ) -> None:
        self._register_asset_uc = register_asset_uc
        self._reconstruct_uc = reconstruct_uc

    @require_permission(UserRole.FIELD_ENGINEER, "TWIN_REGISTER_ASSET")
    def register_asset(self, asset_dto: AssetDto, ctx: UserContext) -> str:
        return self._register_asset_uc.execute(asset_dto, ctx)

    @require_permission(UserRole.FACTORY_MANAGER, "TWIN_RECONSTRUCT")
    def reconstruct_twin(
        self, raw_data: RawFactoryDataDto, ctx: UserContext
    ) -> TwinMetricsDto:
        return self._reconstruct_uc.execute(raw_data, ctx)
