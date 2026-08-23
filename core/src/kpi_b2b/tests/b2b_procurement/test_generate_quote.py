from unittest.mock import MagicMock

import pytest
from kpi_b2b.b2b_procurement.application.generate_quote.generate_quote_usecase import (
    GenerateQuoteUseCase,
)
from kpi_b2b.b2b_procurement.domain.b2b_quote.b2b_quote_status_enum import (
    B2bQuoteStatus,
)
from kpi_b2b.facades.procurement_command_facade import ProcurementCommandFacade
from kpi_b2b.ports.outbound.i_procurement_command_repository import (
    IProcurementCommandRepository,
)
from kpi_b2b.ports.outbound.i_quote_idempotency_store import (
    IQuoteIdempotencyStore,
)
from kpi_b2b.ports.outbound.i_turnkey_quote_gateway import (
    ITurnkeyQuoteGateway,
)
from shared.context.user_context import UserContext
from shared.exceptions.global_error_code_enum import GlobalErrorCode
from shared.security.user_role_enum import UserRole
from shared.exceptions.base_system_exception import BaseSystemException


@pytest.fixture
def target_system():
    mock_gateway = MagicMock(spec=ITurnkeyQuoteGateway)
    mock_cache_store = MagicMock(spec=IQuoteIdempotencyStore)
    mock_command_repo = MagicMock(spec=IProcurementCommandRepository)
    mock_session_uc = MagicMock()
    mock_prod_order_uc = MagicMock()
    mock_rbac = MagicMock()
    mock_logger = MagicMock()

    usecase = GenerateQuoteUseCase(
        gateway=mock_gateway,
        cache_store=mock_cache_store,
        command_repo=mock_command_repo,
        system_logger=mock_logger,
    )
    facade = ProcurementCommandFacade(
        generate_quote_uc=usecase,
        create_expert_session_uc=mock_session_uc,
        process_production_order_uc=mock_prod_order_uc,
        rbac_manager=mock_rbac,
    )
    return facade, mock_gateway, mock_cache_store, mock_command_repo


@pytest.fixture
def valid_ctx():
    return UserContext(
        user_id="USR-100",
        username="factory_manager_a",
        company_id="TENANT_A",
        role=UserRole.FACTORY_MANAGER,
    )


def test_generate_quote_happy_path_cache_miss(target_system, valid_ctx):
    facade, mock_gateway, mock_cache, mock_cmd_repo = target_system
    asset_ids = ["ASSET-001", "ASSET-002"]
    idempotency_key = "IDEMP-KEY-12345"

    mock_cache.find_cached_quote.return_value = None
    mock_gateway.request_turnkey_quote.return_value = {
        "total_estimated_price": 150000.0,
        "delivery_days_estimated": 14,
    }

    result_dto = facade.generate_quote(
        asset_ids=asset_ids, idempotency_key=idempotency_key, ctx=valid_ctx
    )

    mock_gateway.request_turnkey_quote.assert_called_once_with(asset_ids)
    mock_cmd_repo.save_quote.assert_called_once()
    mock_cache.save_cached_quote.assert_called_once()
    assert result_dto.status == B2bQuoteStatus.REQUESTED.value
    assert result_dto.total_estimated_price == 150000.0


def test_generate_quote_happy_path_cache_hit(target_system, valid_ctx):
    facade, mock_gateway, mock_cache, mock_cmd_repo = target_system
    asset_ids = ["ASSET-001"]
    idempotency_key = "IDEMP-KEY-DUPLICATE"

    cached_response = {
        "quote_id": "QT-CACHED-001",
        "total_estimated_price": 50000.0,
        "status": "REQUESTED",
        "delivery_days_estimated": 7,
    }
    mock_cache.find_cached_quote.return_value = cached_response

    result_dto = facade.generate_quote(
        asset_ids=asset_ids, idempotency_key=idempotency_key, ctx=valid_ctx
    )

    mock_gateway.request_turnkey_quote.assert_not_called()
    mock_cmd_repo.save_quote.assert_not_called()
    assert result_dto.quote_id == "QT-CACHED-001"


def test_generate_quote_invalid_schema(target_system, valid_ctx):
    facade, mock_gateway, mock_cache, mock_cmd_repo = target_system
    asset_ids = ["ASSET-003"]
    idempotency_key = "IDEMP-KEY-INVALID"

    mock_cache.find_cached_quote.return_value = None
    mock_gateway.request_turnkey_quote.return_value = {"total_estimated_price": 10000.0}

    with pytest.raises(BaseSystemException) as exc_info:
        facade.generate_quote(
            asset_ids=asset_ids, idempotency_key=idempotency_key, ctx=valid_ctx
        )

    assert exc_info.value.error_code == GlobalErrorCode.ERR_B2B_INVALID_QUOTE
    assert exc_info.value.status_code == 422
    mock_cmd_repo.save_quote.assert_not_called()


def test_generate_quote_api_failure(target_system, valid_ctx):
    facade, mock_gateway, mock_cache, mock_cmd_repo = target_system
    asset_ids = ["ASSET-004"]
    idempotency_key = "IDEMP-KEY-TIMEOUT"

    mock_cache.find_cached_quote.return_value = None
    mock_gateway.request_turnkey_quote.side_effect = Exception("Timeout")

    with pytest.raises(BaseSystemException) as exc_info:
        facade.generate_quote(
            asset_ids=asset_ids, idempotency_key=idempotency_key, ctx=valid_ctx
        )

    assert exc_info.value.error_code == GlobalErrorCode.ERR_B2B_API_FAILURE
    assert exc_info.value.status_code == 502
    mock_cmd_repo.save_quote.assert_not_called()
