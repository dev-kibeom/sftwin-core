from digital_twin.asset_library.application.register_asset.register_asset_usecase import (
    RegisterAssetUseCase,
)
from digital_twin.ports.inbound.i_digital_twin_command_facade import (
    IDigitalTwinCommandFacade,
)
from digital_twin.twin_reconstruction.application.reconstruct_twin.reconstruct_twin_usecase import (
    RawFactoryDataDto,
    ReconstructTwinUseCase,
    TwinMetricsDto,
)
from shared.context.log_context import LogContext
from shared.context.user_context import UserContext
from shared.dtos.asset_dto import AssetDto
from shared.logger.global_system_logger import GlobalSystemLogger


class DigitalTwinCommandFacade(IDigitalTwinCommandFacade):
    """외부 컴포넌트 및 API 계층의 디지털 트윈 복각 명령을 유즈케이스로 연결하는 파사드"""

    def __init__(
        self,
        register_asset_uc: RegisterAssetUseCase,
        reconstruct_uc: ReconstructTwinUseCase,
        logger: GlobalSystemLogger | None = None,
    ) -> None:
        self._register_asset_uc = register_asset_uc
        self._reconstruct_uc = reconstruct_uc
        self._logger = logger or GlobalSystemLogger(
            component_name="DigitalTwinCommandFacade"
        )

    def register_asset(self, asset_dto: AssetDto, ctx: UserContext) -> str:
        return self._register_asset_uc.execute(asset_dto, ctx)

    def reconstruct_twin(
        self, raw_data: RawFactoryDataDto, ctx: UserContext | None = None
    ) -> TwinMetricsDto:
        effective_ctx = ctx or UserContext.create_system_context()

        log_ctx = LogContext(
            trace_id=getattr(effective_ctx, "trace_id", "TRC-DEFAULT"),
            context={
                "baseline_name": raw_data.baseline_name,
                "user_id": effective_ctx.user_id,
                "company_id": effective_ctx.company_id,
                "is_fallback_ctx": ctx is None,
            },
        )

        self._logger.debug(
            f"Facade routing reconstruct_twin: {raw_data.baseline_name}",
            log_ctx=log_ctx,
        )

        return self._reconstruct_uc.execute(raw_data, effective_ctx)
