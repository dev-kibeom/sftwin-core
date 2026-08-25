from pathlib import Path

import pytest
from digital_twin.asset_library.domain.asset.asset import Asset
from digital_twin.asset_library.domain.asset.asset_type_enum import AssetType

from plugins.aas_persistence.adapters.asset_command_persistence_adapter import (
    AssetCommandPersistenceAdapter,
)
from plugins.aas_persistence.session.mysql_session_factory import MysqlSessionFactory


@pytest.fixture
def command_adapter(
    test_session_factory: MysqlSessionFactory, aas_storage_dir: Path
) -> AssetCommandPersistenceAdapter:
    return AssetCommandPersistenceAdapter(
        session_factory=test_session_factory,
        aas_storage_dir=aas_storage_dir,
    )


def test_save_persists_orm_and_physical_aas_file(
    command_adapter: AssetCommandPersistenceAdapter,
    sample_asset: Asset,
    aas_storage_dir: Path,
) -> None:
    # save() 호출 시 반환값은 None 확인
    result = command_adapter.save(sample_asset)
    assert result is None

    # 물리 AAS 파일 생성 검증
    expected_file = (
        aas_storage_dir / sample_asset.company_id / f"{sample_asset.asset_id}.json"
    )
    assert expected_file.exists()

    # load_by_id로 도메인 엔티티 복원 검증
    loaded_asset = command_adapter.load_by_id(sample_asset.asset_id)
    assert loaded_asset is not None
    assert loaded_asset.asset_id == sample_asset.asset_id
    assert loaded_asset.asset_name == sample_asset.asset_name
    assert loaded_asset.asset_type == AssetType.ROBOT
    assert loaded_asset.submodels == {"vendor": "Doosan"}


def test_delete_by_id_hard_deletes_record(
    command_adapter: AssetCommandPersistenceAdapter,
    sample_asset: Asset,
) -> None:
    command_adapter.save(sample_asset)

    # 물리 삭제 수행
    is_deleted = command_adapter.delete_by_id(sample_asset.asset_id)
    assert is_deleted is True

    # 삭제 후 재조회 시 None 반환
    assert command_adapter.load_by_id(sample_asset.asset_id) is None

    # 존재하지 않는 ID 삭제 시 False 반환
    assert command_adapter.delete_by_id("AST-NON-EXISTING") is False
