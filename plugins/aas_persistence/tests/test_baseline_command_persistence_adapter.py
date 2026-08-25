import pytest
from digital_twin.twin_reconstruction.domain.twin_baseline.twin_baseline import (
    TwinBaseline,
)
from digital_twin.twin_reconstruction.domain.twin_baseline.twin_sync_status_enum import (
    TwinSyncStatus,
)

from plugins.aas_persistence.adapters.baseline_command_persistence_adapter import (
    BaselineCommandPersistenceAdapter,
)
from plugins.aas_persistence.adapters.baseline_query_persistence_adapter import (
    BaselineQueryPersistenceAdapter,
)
from plugins.aas_persistence.session.mysql_session_factory import MysqlSessionFactory


@pytest.fixture
def baseline_adapters(
    test_session_factory: MysqlSessionFactory,
) -> tuple[BaselineCommandPersistenceAdapter, BaselineQueryPersistenceAdapter]:
    cmd = BaselineCommandPersistenceAdapter(session_factory=test_session_factory)
    query = BaselineQueryPersistenceAdapter(session_factory=test_session_factory)
    return cmd, query


def test_baseline_crud_and_query_flow(
    baseline_adapters: tuple[
        BaselineCommandPersistenceAdapter, BaselineQueryPersistenceAdapter
    ],
    sample_baseline: TwinBaseline,
) -> None:
    cmd_adapter, query_adapter = baseline_adapters

    # 1. 저장 (save -> None)
    cmd_adapter.save(sample_baseline)

    # 2. Command 측 도메인 엔티티 로드
    loaded = cmd_adapter.load_by_id(sample_baseline.baseline_id)
    assert loaded is not None
    assert loaded.sync_error_rate == 2.5
    assert loaded.sync_status == TwinSyncStatus.COMPLETED

    # 3. Query 측 DTO 단건 조회
    dto = query_adapter.find_by_id(
        sample_baseline.baseline_id, company_id=sample_baseline.company_id
    )
    assert dto is not None
    assert dto.baseline_name == "Factory 1 Baseline"
    assert dto.sync_status == "COMPLETED"

    # 4. 물리 삭제 및 삭제 확인
    assert cmd_adapter.delete_by_id(sample_baseline.baseline_id) is True
    assert (
        query_adapter.find_by_id(
            sample_baseline.baseline_id, company_id=sample_baseline.company_id
        )
        is None
    )
