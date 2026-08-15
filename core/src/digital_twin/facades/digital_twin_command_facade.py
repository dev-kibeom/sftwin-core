from digital_twin.ports.inbound.i_digital_twin_command_facade import (
    IDigitalTwinCommandFacade,
)
from digital_twin.twin_reconstruction.application.reconstruct_twin.reconstruct_twin_usecase import (
    RawFactoryDataDto,
    ReconstructTwinUseCase,
    TwinMetricsDto,
)
from shared.logger.system_logger.global_system_logger import GlobalSystemLogger
from shared.security.user_context import UserContext


class DigitalTwinCommandFacade(IDigitalTwinCommandFacade):
    """타 컴포넌트나 API 계층의 디지털 트윈 복각 명령을
    유즈케이스로 연결하는 파사드 구현체"""

    def __init__(
        self,
        reconstruct_uc: ReconstructTwinUseCase,
        logger: GlobalSystemLogger | None = None,
    ) -> None:
        self._reconstruct_uc = reconstruct_uc
        self._logger = logger or GlobalSystemLogger(
            component_name="DigitalTwinCommandFacade"
        )

    def reconstruct_twin(
        self, raw_data: RawFactoryDataDto, ctx: UserContext | None = None
    ) -> TwinMetricsDto:
        self._logger.info(f"reconstruct_twin for '{raw_data.baseline_name}'")

        if ctx is None:
            ctx = UserContext.create_system_context()
        return self._reconstruct_uc.execute(raw_data, ctx)
