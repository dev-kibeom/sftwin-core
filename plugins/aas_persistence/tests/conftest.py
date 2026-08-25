from pathlib import Path

import pytest
from digital_twin.asset_library.domain.asset.asset import Asset
from digital_twin.asset_library.domain.asset.asset_type_enum import AssetType
from digital_twin.twin_reconstruction.domain.twin_baseline.twin_baseline import (
    TwinBaseline,
)
from digital_twin.twin_reconstruction.domain.twin_baseline.twin_sync_status_enum import (
    TwinSyncStatus,
)

from plugins.aas_persistence.models.asset_orm_model import Base
from plugins.aas_persistence.session.mysql_session_factory import MysqlSessionFactory


@pytest.fixture
def test_session_factory(tmp_path: Path) -> MysqlSessionFactory:
    sqlite_db = f"sqlite:///{tmp_path / 'test.db'}"
    factory = MysqlSessionFactory(db_url=sqlite_db)
    Base.metadata.create_all(factory._engine)
    return factory


@pytest.fixture
def aas_storage_dir(tmp_path: Path) -> Path:
    storage = tmp_path / "aas_storage"
    storage.mkdir(parents=True, exist_ok=True)
    return storage


@pytest.fixture
def sample_asset() -> Asset:
    return Asset(
        asset_id="AST-TEST-001",
        company_id="COMP-A",
        asset_name="Test Robot Arm",
        asset_type=AssetType.ROBOT,
        kinematics_metadata={
            "degrees_of_freedom": 6,
            "dh_parameters": {"dof": 6},
            "dof": 6,
            "joints": [
                {
                    "name": "j1",
                    "type": "revolute",
                    "min_limit": -180,
                    "max_limit": 180,
                }
            ],
        },
        cad_file_path="/cad/arm.step",
        submodels={"vendor": "Doosan"},
    )


@pytest.fixture
def sample_baseline() -> TwinBaseline:
    return TwinBaseline(
        baseline_id="BASE-TEST-001",
        company_id="COMP-A",
        baseline_name="Factory 1 Baseline",
        sync_error_rate=2.5,
        sync_status=TwinSyncStatus.COMPLETED,
        raw_sensor_summary={"mean_deviation": 0.025, "max_tolerance": 1.0},
    )
