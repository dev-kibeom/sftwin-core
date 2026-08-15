"""
@file test_generate_quote.py
@description B2B 견적 발주 단위 테스트 (CQRS 포트 및 Facade 규격 동기화)
"""

from unittest.mock import MagicMock, patch

import pytest
from kpi_b2b.b2b_procurement.application.generate_quote.generate_quote_usecase import (
    GenerateQuoteUseCase,
)
from kpi_b2b.b2b_procurement.domain.b2b_quote import B2bQuoteStatusEnum
from kpi_b2b.facades.procurement_command_facade import ProcurementCommandFacade
from kpi_b2b.ports.outbound.i_procurement_command_repository import (
    IProcurementCommandRepository,
)
from kpi_b2b.ports.outbound.i_procurement_query_repository import (
    IProcurementQueryRepository,
)
from shared.enums.user_role_enum import UserRoleEnum
from shared.exceptions.base_exception import BaseSystemException
from shared.exceptions.error_codes import GlobalErrorCodes
from shared.security.user_context import UserContext


@pytest.fixture
def target_system():
    mock_command_repo = MagicMock(spec=IProcurementCommandRepository)
    mock_query_repo = MagicMock(spec=IProcurementQueryRepository)
    mock_mirroring_uc = MagicMock()
    mock_rbac = MagicMock()

    with (
        patch(
            "kpi_b2b.b2b_procurement.application.generate_quote.generate_quote_usecase.GlobalSystemLogger"
        ),
        patch("kpi_b2b.facades.procurement_command_facade.GlobalSystemLogger"),
    ):
        usecase = GenerateQuoteUseCase(command_repo=mock_command_repo)
        facade = ProcurementCommandFacade(
            generate_quote_uc=usecase,
            mirroring_uc=mock_mirroring_uc,
            command_repo=mock_command_repo,
            query_repo=mock_query_repo,
            rbac_manager=mock_rbac,
        )
        yield facade, mock_command_repo, mock_query_repo


@pytest.fixture
def valid_ctx():
    return UserContext(
        user_id="USR-100",
        username="factory_manager_a",
        company_id="TENANT_A",
        role=UserRoleEnum.FACTORY_MANAGER,
    )


def test_generate_quote_happy_path_cache_miss(target_system, valid_ctx):
    facade, mock_cmd_repo, mock_qry_repo = target_system
    asset_ids = ["ASSET-001", "ASSET-002"]
    idempotency_key = "IDEMP-KEY-12345"

    mock_qry_repo.find_cached_quote.return_value = None
    mock_cmd_repo.request_turnkey_quote.return_value = {
        "total_estimated_price": 150000.0,
        "delivery_days_estimated": 14,
    }

    result_dto = facade.generate_quote(
        asset_ids=asset_ids, idempotency_key=idempotency_key, ctx=valid_ctx
    )

    mock_cmd_repo.request_turnkey_quote.assert_called_once_with(asset_ids)
    mock_cmd_repo.save_quote.assert_called_once()
    mock_cmd_repo.save_cached_quote.assert_called_once()
    assert result_dto.status == B2bQuoteStatusEnum.REQUESTED.value


def test_generate_quote_happy_path_cache_hit(target_system, valid_ctx):
    facade, mock_cmd_repo, mock_qry_repo = target_system
    asset_ids = ["ASSET-001"]
    idempotency_key = "IDEMP-KEY-DUPLICATE"

    cached_response = {
        "quote_id": "QT-CACHED-001",
        "total_estimated_price": 50000.0,
        "status": "REQUESTED",
        "delivery_days_estimated": 7,
    }
    mock_qry_repo.find_cached_quote.return_value = cached_response

    result_dto = facade.generate_quote(
        asset_ids=asset_ids, idempotency_key=idempotency_key, ctx=valid_ctx
    )

    mock_cmd_repo.request_turnkey_quote.assert_not_called()
    mock_cmd_repo.save_quote.assert_not_called()
    assert result_dto.quote_id == "QT-CACHED-001"


def test_generate_quote_invalid_schema(target_system, valid_ctx):
    facade, mock_cmd_repo, mock_qry_repo = target_system
    asset_ids = ["ASSET-003"]
    idempotency_key = "IDEMP-KEY-INVALID"

    mock_qry_repo.find_cached_quote.return_value = None
    mock_cmd_repo.request_turnkey_quote.return_value = {
        "total_estimated_price": 10000.0
    }

    with pytest.raises(BaseSystemException) as exc_info:
        facade.generate_quote(
            asset_ids=asset_ids, idempotency_key=idempotency_key, ctx=valid_ctx
        )

    assert exc_info.value.error_code == GlobalErrorCodes.ERR_B2B_INVALID_QUOTE
    assert exc_info.value.status_code == 422
    mock_cmd_repo.save_quote.assert_not_called()


def test_generate_quote_api_failure(target_system, valid_ctx):
    facade, mock_cmd_repo, mock_qry_repo = target_system
    asset_ids = ["ASSET-004"]
    idempotency_key = "IDEMP-KEY-TIMEOUT"

    mock_qry_repo.find_cached_quote.return_value = None
    mock_cmd_repo.request_turnkey_quote.side_effect = Exception("Timeout")

    with pytest.raises(BaseSystemException) as exc_info:
        facade.generate_quote(
            asset_ids=asset_ids, idempotency_key=idempotency_key, ctx=valid_ctx
        )

    assert exc_info.value.error_code == GlobalErrorCodes.ERR_B2B_API_FAILURE
    assert exc_info.value.status_code == 502
    mock_cmd_repo.save_quote.assert_not_called()
