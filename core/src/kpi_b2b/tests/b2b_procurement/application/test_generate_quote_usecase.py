from unittest.mock import MagicMock

import pytest
from kpi_b2b.b2b_procurement.application.generate_quote.generate_quote_usecase import (
    GenerateQuoteUseCase,
)
from kpi_b2b.contracts.dtos.b2b_quote_dto import B2bQuoteDto
from kpi_b2b.contracts.dtos.turnkey_quote_response_dto import (
    TurnkeyQuoteResponseDto,
)
from kpi_b2b.contracts.ports.outbound.i_procurement_command_repository import (
    IProcurementCommandRepository,
)
from kpi_b2b.contracts.ports.outbound.i_quote_idempotency_store import (
    IQuoteIdempotencyStore,
)
from kpi_b2b.contracts.ports.outbound.i_turnkey_quote_gateway import (
    ITurnkeyQuoteGateway,
)
from shared.context.user_context import UserContext
from shared.exceptions.base_system_exception import BaseSystemException
from shared.exceptions.global_error_code_enum import GlobalErrorCode
from shared.security.user_role_enum import UserRole


@pytest.fixture
def mock_gateway() -> MagicMock:
    return MagicMock(spec=ITurnkeyQuoteGateway)


@pytest.fixture
def mock_cache_store() -> MagicMock:
    return MagicMock(spec=IQuoteIdempotencyStore)


@pytest.fixture
def mock_command_repo() -> MagicMock:
    return MagicMock(spec=IProcurementCommandRepository)


@pytest.fixture
def usecase(
    mock_gateway: MagicMock,
    mock_cache_store: MagicMock,
    mock_command_repo: MagicMock,
) -> GenerateQuoteUseCase:
    return GenerateQuoteUseCase(
        gateway=mock_gateway,
        cache_store=mock_cache_store,
        command_repo=mock_command_repo,
    )


@pytest.fixture
def standard_context() -> UserContext:
    return UserContext(
        user_id="USER-123",
        username="kibeom_engineer",
        company_id="TEST-COMPANY-01",
        role=UserRole.FIELD_ENGINEER,
        accessible_factory_ids=["FACTORY-01"],
    )


def test_tc_happy_path_generate_quote(
    usecase: GenerateQuoteUseCase,
    mock_gateway: MagicMock,
    mock_cache_store: MagicMock,
    mock_command_repo: MagicMock,
    standard_context: UserContext,
):
    """[TC-정상] 턴키 견적 외부 연동, 저장소 영속화 및 캐시 갱신 검증"""
    mock_cache_store.find_cached_quote.return_value = None
    mock_gateway.request_turnkey_quote.return_value = TurnkeyQuoteResponseDto(
        total_estimated_price=150000.0,
        delivery_days_estimated=14,
    )

    result = usecase.execute(
        asset_ids=["CNC-01", "ROBOT-01"],
        ctx=standard_context,
        idempotency_key="IDEMP-KEY-123",
    )

    mock_gateway.request_turnkey_quote.assert_called_once_with(["CNC-01", "ROBOT-01"])
    mock_command_repo.save_quote.assert_called_once()
    mock_cache_store.save_cached_quote.assert_called_once()
    assert isinstance(result, B2bQuoteDto)
    assert result.quote_id.startswith("QT-")
    assert result.total_estimated_price == 150000.0
    assert result.delivery_days_estimated == 14
    assert result.status == "REQUESTED"


def test_tc_happy_path_idempotent_cached_quote(
    usecase: GenerateQuoteUseCase,
    mock_gateway: MagicMock,
    mock_cache_store: MagicMock,
    mock_command_repo: MagicMock,
    standard_context: UserContext,
):
    """[TC-정상] 동일 멱등키 존재 시 외부 Gateway 및 DB 미호출, 캐시 반환 검증"""
    cached_payload = {
        "quote_id": "QT-CACHED-01",
        "total_estimated_price": 80000.0,
        "delivery_days_estimated": 7,
        "status": "REQUESTED",
    }
    mock_cache_store.find_cached_quote.return_value = cached_payload

    result = usecase.execute(
        asset_ids=["CNC-01"],
        ctx=standard_context,
        idempotency_key="IDEMP-KEY-DUPLICATED",
    )

    mock_cache_store.find_cached_quote.assert_called_once_with("IDEMP-KEY-DUPLICATED")
    mock_gateway.request_turnkey_quote.assert_not_called()
    mock_command_repo.save_quote.assert_not_called()
    assert result.quote_id == "QT-CACHED-01"
    assert result.total_estimated_price == 80000.0


def test_tc_edge_case_empty_asset_ids(
    usecase: GenerateQuoteUseCase,
    mock_gateway: MagicMock,
    mock_command_repo: MagicMock,
    standard_context: UserContext,
):
    """[TC-예외] 빈 asset_ids 전달 시 조기 차단(Guard Clause) 검증"""
    with pytest.raises(BaseSystemException) as exc_info:
        usecase.execute(asset_ids=[], ctx=standard_context)

    assert exc_info.value.error_code == GlobalErrorCode.ERR_COMMON_INVALID_INPUT
    assert exc_info.value.status_code == 400
    mock_gateway.request_turnkey_quote.assert_not_called()
    mock_command_repo.save_quote.assert_not_called()
