from pathlib import Path

from dotenv import load_dotenv

BASE_DIR = Path(__file__).resolve().parent
ENV_LOCAL_PATH = BASE_DIR / "infra" / ".env.local"
if ENV_LOCAL_PATH.exists():
    load_dotenv(ENV_LOCAL_PATH)

from digital_twin.asset_library.application.get_asset.get_asset_usecase import (
    GetAssetUseCase,
)
from digital_twin.asset_library.application.register_asset.register_asset_usecase import (
    RegisterAssetUseCase,
)
from digital_twin.contracts.ports.inbound.i_digital_twin_command_facade import (
    IDigitalTwinCommandFacade,
)
from digital_twin.contracts.ports.inbound.i_digital_twin_query_facade import (
    IDigitalTwinQueryFacade,
)
from digital_twin.facades.digital_twin_command_facade import DigitalTwinCommandFacade
from digital_twin.facades.digital_twin_query_facade import DigitalTwinQueryFacade
from digital_twin.twin_reconstruction.application.calibrate_dynamics.calibrate_dynamics_usecase import (
    CalibrateDynamicsUseCase,
)
from digital_twin.twin_reconstruction.application.get_layout.get_layout_usecase import (
    GetLayoutUseCase,
)
from digital_twin.twin_reconstruction.application.reconstruct_twin.reconstruct_twin_usecase import (
    ReconstructTwinUseCase,
)

from plugins.aas_persistence.adapters.asset_query_persistence_adapter import (
    AssetPersistenceAdapter,
)
from plugins.aas_persistence.adapters.baseline_query_persistence_adapter import (
    BaselinePersistenceAdapter,
)
from plugins.aas_persistence.session.mysql_session_factory import (
    MysqlSessionFactory,
)
from plugins.kamp_sensor_parser.adapters.kamp_data_adapter import KampDataAdapter


class InfraContainer:
    def __init__(self) -> None:
        self.session_factory = MysqlSessionFactory()
        # 공통 Redis, EventBus 등이 있다면 여기에 초기화


class DigitalTwinContainer:
    def __init__(self, infra: InfraContainer) -> None:
        self._asset_adapter = AssetPersistenceAdapter(
            session_factory=infra.session_factory,
            aas_storage_dir=str(BASE_DIR / "data" / "assets" / "aas"),
        )
        self._baseline_adapter = BaselinePersistenceAdapter(
            session_factory=infra.session_factory
        )
        self._sensor_parser = KampDataAdapter()

    def get_command_facade(self) -> IDigitalTwinCommandFacade:
        return DigitalTwinCommandFacade(
            register_asset_uc=RegisterAssetUseCase(command_repo=self._asset_adapter),
            reconstruct_uc=ReconstructTwinUseCase(
                sensor_parser=self._sensor_parser,
                command_repo=self._baseline_adapter,
            ),
            calibrate_dynamics_uc=CalibrateDynamicsUseCase(),
        )

    def get_query_facade(self) -> IDigitalTwinQueryFacade:
        return DigitalTwinQueryFacade(
            get_asset_uc=GetAssetUseCase(query_repo=self._asset_adapter),
            get_layout_uc=GetLayoutUseCase(query_repo=self._baseline_adapter),
        )


class SimulationContainer:
    def __init__(self, infra: InfraContainer) -> None:
        # 시뮬레이션용 어댑터 초기화 및 파사드 제공
        pass
