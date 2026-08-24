from unittest.mock import MagicMock

import pytest
from digital_twin.contracts.dtos.twin_baseline_dto import TwinBaselineDto
from digital_twin.contracts.ports.outbound.i_baseline_query_repository import (
    IBaselineQueryRepository,
)
from digital_twin.twin_reconstruction.application.get_layout.get_layout_usecase import (
    GetLayoutUseCase,
    LayoutRenderDto,
    LayoutRenderMapper,
)
from shared.context.user_context import UserContext
from shared.exceptions.base_system_exception import BaseSystemException
from shared.exceptions.global_error_code_enum import GlobalErrorCode
from shared.security.user_role_enum import UserRole


@pytest.fixture
def mock_query_repo() -> MagicMock:
    return MagicMock(spec=IBaselineQueryRepository)


@pytest.fixture
def mock_mapper() -> MagicMock:
    return MagicMock(spec=LayoutRenderMapper)


@pytest.fixture
def usecase(
    mock_query_repo: MagicMock,
    mock_mapper: MagicMock,
) -> GetLayoutUseCase:
    return GetLayoutUseCase(query_repo=mock_query_repo, mapper=mock_mapper)


@pytest.fixture
def standard_context() -> UserContext:
    return UserContext(
        user_id="USER-123",
        username="kibeom_engineer",
        company_id="TEST-COMPANY-01",
        role=UserRole.FIELD_ENGINEER,
        accessible_factory_ids=["FACTORY-01"],
    )


def test_tc_happy_path_get_layout(
    usecase: GetLayoutUseCase,
    mock_query_repo: MagicMock,
    mock_mapper: MagicMock,
    standard_context: UserContext,
):
    """[TC-정상] 레포지토리 단건 조회 후 Mapper로 전달되어 Render DTO가 반환되는지 검증"""
    # Given
    mock_baseline = MagicMock(spec=TwinBaselineDto)
    mock_render_dto = LayoutRenderDto(
        baseline_id="BASE-01",
        baseline_name="Factory Layout",
        company_id="TEST-COMPANY-01",
        sync_error_rate=0.05,
        sync_status="COMPLETED",
        asset_mappings=(),
    )
    mock_query_repo.find_by_id.return_value = mock_baseline
    mock_mapper.to_render_dto.return_value = mock_render_dto

    # When
    result = usecase.execute("BASE-01", standard_context)

    # Then
    mock_query_repo.find_by_id.assert_called_once_with(
        baseline_id="BASE-01",
        company_id="TEST-COMPANY-01",
    )
    mock_mapper.to_render_dto.assert_called_once_with(mock_baseline)
    assert result == mock_render_dto


def test_tc_error_handling_baseline_not_found(
    usecase: GetLayoutUseCase,
    mock_query_repo: MagicMock,
    mock_mapper: MagicMock,
    standard_context: UserContext,
):
    """
    [TC-예외] DB에 해당 baseline_id가 존재하지 않을 때 404 NOT_FOUND 반환 검증
    """
    # Given
    mock_query_repo.find_by_id.return_value = None

    # When & Then
    with pytest.raises(BaseSystemException) as exc_info:
        usecase.execute(baseline_id="NON-EXISTENT-BASE", ctx=standard_context)

    # 요청된 ID와 호출자의 company_id로 조회를 시도했는지 검증
    mock_query_repo.find_by_id.assert_called_once_with(
        baseline_id="NON-EXISTENT-BASE",
        company_id="TEST-COMPANY-01",
    )
    assert exc_info.value.error_code == GlobalErrorCode.ERR_TWIN_NOT_FOUND
    assert exc_info.value.status_code == 404
    mock_mapper.to_render_dto.assert_not_called()


def test_tc_edge_case_unauthorized_isolation_violation(
    usecase: GetLayoutUseCase,
    mock_query_repo: MagicMock,
    mock_mapper: MagicMock,
    standard_context: UserContext,
):
    """
    [TC-예외] 타사 베이스라인 ID를 요청하더라도 컨텍스트의 company_id로 조회하여
    타사 리소스 접근을 차단하고 404 NOT_FOUND로 은닉하는지 검증 (IDOR 방어)
    """
    # Given: 타사 테넌트의 ID를 알더라도 Repository는 사용자 테넌트 필터에 걸려 None 반환
    target_foreign_baseline_id = "OTHER-COMPANY-BASE-99"
    mock_query_repo.find_by_id.return_value = None

    # When & Then
    with pytest.raises(BaseSystemException) as exc_info:
        usecase.execute(
            baseline_id=target_foreign_baseline_id,
            ctx=standard_context,
        )

    # Repository 호출 시 공격 대상 ID와 함께 '요청자의 company_id'가 반드시 바인딩되었는지 단언
    mock_query_repo.find_by_id.assert_called_once_with(
        baseline_id=target_foreign_baseline_id,
        company_id=standard_context.company_id,
    )
    assert exc_info.value.error_code == GlobalErrorCode.ERR_TWIN_NOT_FOUND
    assert exc_info.value.status_code == 404
    mock_mapper.to_render_dto.assert_not_called()
