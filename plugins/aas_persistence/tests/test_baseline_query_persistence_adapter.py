import pytest
from digital_twin.twin_reconstruction.domain.twin_baseline.twin_baseline import (
    TwinBaseline,
)

from plugins.aas_persistence.adapters.baseline_command_persistence_adapter import (
    BaselineCommandPersistenceAdapter,
)
from plugins.aas_persistence.adapters.baseline_query_persistence_adapter import (
    BaselineQueryPersistenceAdapter,
)
from plugins.aas_persistence.session.mysql_session_factory import MysqlSessionFactory


@pytest.fixture
def query_adapter(
    test_session_factory: MysqlSessionFactory,
) -> BaselineQueryPersistenceAdapter:
    return BaselineQueryPersistenceAdapter(session_factory=test_session_factory)


@pytest.fixture
def command_adapter(
    test_session_factory: MysqlSessionFactory,
) -> BaselineCommandPersistenceAdapter:
    return BaselineCommandPersistenceAdapter(session_factory=test_session_factory)


def test_find_by_id_returns_dto_and_isolates_company(
    command_adapter: BaselineCommandPersistenceAdapter,
    query_adapter: BaselineQueryPersistenceAdapter,
    sample_baseline: TwinBaseline,
) -> None:
    command_adapter.save(sample_baseline)

    # 동일 테넌시 조회 성공 (TwinBaselineDto 반환 확인)
    dto = query_adapter.find_by_id(
        baseline_id=sample_baseline.baseline_id,
        company_id=sample_baseline.company_id,
    )
    assert dto is not None
    assert dto.baseline_id == sample_baseline.baseline_id
    assert dto.baseline_name == sample_baseline.baseline_name
    assert dto.sync_error_rate == sample_baseline.sync_error_rate
    assert dto.sync_status == "COMPLETED"  # Enum이 아닌 str 확인
    assert dto.company_id == "COMP-A"

    # 타 테넌시 조회 시 None 반환 (IDOR 차단 확인)
    other_tenant_dto = query_adapter.find_by_id(
        baseline_id=sample_baseline.baseline_id,
        company_id="COMP-OTHER",
    )
    assert other_tenant_dto is None


def test_find_by_id_returns_none_for_non_existing(
    query_adapter: BaselineQueryPersistenceAdapter,
) -> None:
    result = query_adapter.find_by_id(
        baseline_id="BASE-NON-EXISTING",
        company_id="COMP-A",
    )
    assert result is None


def test_exists_by_id_and_company(
    command_adapter: BaselineCommandPersistenceAdapter,
    query_adapter: BaselineQueryPersistenceAdapter,
    sample_baseline: TwinBaseline,
) -> None:
    command_adapter.save(sample_baseline)

    # 테넌시 일치 시 True
    assert (
        query_adapter.exists_by_id_and_company(
            baseline_id=sample_baseline.baseline_id,
            company_id="COMP-A",
        )
        is True
    )

    # 테넌시 불일치 시 False
    assert (
        query_adapter.exists_by_id_and_company(
            baseline_id=sample_baseline.baseline_id,
            company_id="COMP-B",
        )
        is False
    )

    # 미존재 식별자 조회 시 False
    assert (
        query_adapter.exists_by_id_and_company(
            baseline_id="BASE-UNKNOWN",
            company_id="COMP-A",
        )
        is False
    )


def test_find_by_id_filters_soft_deleted_baseline(
    command_adapter: BaselineCommandPersistenceAdapter,
    query_adapter: BaselineQueryPersistenceAdapter,
    sample_baseline: TwinBaseline,
) -> None:
    # 소프트 삭제 상태로 저장
    sample_baseline.soft_delete(modifier_user_id="USER-TEST")
    command_adapter.save(sample_baseline)

    # is_deleted=True 인 데이터는 조회되지 않아야 함
    dto = query_adapter.find_by_id(
        baseline_id=sample_baseline.baseline_id,
        company_id=sample_baseline.company_id,
    )
    assert dto is None

    exists = query_adapter.exists_by_id_and_company(
        baseline_id=sample_baseline.baseline_id,
        company_id=sample_baseline.company_id,
    )
    assert exists is False
