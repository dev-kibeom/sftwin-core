from pathlib import Path

import pytest
from digital_twin.asset_library.domain.asset.asset import Asset
from digital_twin.asset_library.domain.asset.asset_type_enum import AssetType
from digital_twin.contracts.dtos.asset_dto import AssetFilterDto
from shared.exceptions.base_system_exception import BaseSystemException

from plugins.aas_persistence.adapters.asset_command_persistence_adapter import (
    AssetCommandPersistenceAdapter,
)
from plugins.aas_persistence.adapters.asset_query_persistence_adapter import (
    AssetQueryPersistenceAdapter,
)
from plugins.aas_persistence.session.mysql_session_factory import MysqlSessionFactory


@pytest.fixture
def asset_adapters(
    test_session_factory: MysqlSessionFactory, aas_storage_dir: Path
) -> tuple[AssetCommandPersistenceAdapter, AssetQueryPersistenceAdapter]:
    cmd = AssetCommandPersistenceAdapter(
        session_factory=test_session_factory, aas_storage_dir=aas_storage_dir
    )
    query = AssetQueryPersistenceAdapter(session_factory=test_session_factory)
    return cmd, query


def test_find_by_id_projects_dto_and_isolates_tenancy(
    asset_adapters: tuple[AssetCommandPersistenceAdapter, AssetQueryPersistenceAdapter],
) -> None:
    cmd, query = asset_adapters
    asset = Asset(
        asset_id="AST-QUERY-001",
        company_id="COMP-A",
        asset_name="Sorting Conveyor",
        asset_type=AssetType.CONVEYOR,
        kinematics_metadata={
            "degrees_of_freedom": 1,
            "dh_parameters": {"dof": 1},
            "dof": 1,
            "joints": [
                {
                    "name": "belt",
                    "type": "prismatic",
                    "min_limit": 0,
                    "max_limit": 100,
                }
            ],
        },
    )
    cmd.save(asset)

    dto = query.find_by_id(asset.asset_id, company_id="COMP-A")
    assert dto is not None
    assert dto.asset_id == "AST-QUERY-001"
    assert dto.asset_type == "CONVEYOR"
    assert isinstance(dto.created_at, str)

    assert query.find_by_id(asset.asset_id, company_id="COMP-OTHER") is None


def test_filter_and_count_queries(
    asset_adapters: tuple[AssetCommandPersistenceAdapter, AssetQueryPersistenceAdapter],
) -> None:
    cmd, query = asset_adapters
    for i in range(3):
        cmd.save(
            Asset(
                asset_id=f"AST-AMR-{i}",
                company_id="COMP-A",
                asset_name=f"AMR Bot {i}",
                asset_type=AssetType.AMR,
                kinematics_metadata={
                    "degrees_of_freedom": 2,
                    "dh_parameters": {"dof": 2},
                    "dof": 2,
                    "joints": [
                        {
                            "name": "w1",
                            "type": "continuous",
                            "min_limit": 0,
                            "max_limit": 0,
                        }
                    ],
                },
            )
        )

    filter_dto = AssetFilterDto(asset_type="AMR", limit=2, offset=0)
    items = query.list_by_filter(filter_dto, company_id="COMP-A")
    assert len(items) == 2

    count = query.count_by_filter(filter_dto, company_id="COMP-A")
    assert count == 3

    assert query.exists_by_id_and_company("AST-AMR-0", "COMP-A") is True
    assert query.exists_by_id_and_company("AST-AMR-0", "COMP-B") is False


def test_get_by_id_raises_not_found_exception(
    asset_adapters: tuple[AssetCommandPersistenceAdapter, AssetQueryPersistenceAdapter],
) -> None:
    _, query = asset_adapters
    with pytest.raises(BaseSystemException) as exc_info:
        query.get_by_id("AST-NONE", company_id="COMP-A")
    assert exc_info.value.status_code == 404
