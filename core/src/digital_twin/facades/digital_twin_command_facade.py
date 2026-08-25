from digital_twin.asset_library.application.register_asset.register_asset_usecase import (
    RegisterAssetUseCase,
)
from digital_twin.contracts.dtos.asset_dto import AssetDto
from digital_twin.contracts.dtos.calibrate_dynamics_dto import (
    CalibrateDynamicsRequestDto,
    CalibrateDynamicsResponseDto,
)
from digital_twin.contracts.ports.inbound.i_digital_twin_command_facade import (
    IDigitalTwinCommandFacade,
)
from digital_twin.twin_reconstruction.application.calibrate_dynamics.calibrate_dynamics_usecase import (
    CalibrateDynamicsUseCase,
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
    """자산 등록, 트윈 재구성 및 동역학 캘리브레이션을 중계하는 Facade"""

    def __init__(
        self,
        register_asset_uc: RegisterAssetUseCase,
        reconstruct_uc: ReconstructTwinUseCase,
        calibrate_dynamics_uc: CalibrateDynamicsUseCase,
    ) -> None:
        self._register_asset_uc = register_asset_uc
        self._reconstruct_uc = reconstruct_uc
        self._calibrate_dynamics_uc = calibrate_dynamics_uc

    @require_permission(UserRole.FIELD_ENGINEER, "TWIN_REGISTER_ASSET")
    def register_asset(self, asset_dto: AssetDto, ctx: UserContext) -> str:
        return self._register_asset_uc.execute(asset_dto, ctx)

    @require_permission(UserRole.FACTORY_MANAGER, "TWIN_RECONSTRUCT")
    def reconstruct_twin(
        self, raw_data: RawFactoryDataDto, ctx: UserContext
    ) -> TwinMetricsDto:
        return self._reconstruct_uc.execute(raw_data, ctx)

    @require_permission(UserRole.FIELD_ENGINEER, "TWIN_CALIBRATE_DYNAMICS")
    def calibrate_dynamics(
        self, request_dto: CalibrateDynamicsRequestDto, ctx: UserContext
    ) -> CalibrateDynamicsResponseDto:
        return self._calibrate_dynamics_uc.execute(request_dto, ctx)
