"""
@file test_generate_quote.py
@description B2B 견적 발주 단위 테스트 (RBAC 모듈 인자 동기화)
"""

from unittest.mock import MagicMock, patch

import pytest
from shared.enums.user_role_enum import UserRoleEnum
from shared.exceptions.base_exception import BaseSystemException
from shared.security.user_context import UserContext

from kpi_b2b.b2b_procurement.application.generate_quote.generate_quote_usecase import (
    GenerateQuoteUseCase,
)
from kpi_b2b.b2b_procurement.domain.b2b_quote import B2bQuoteStatusEnum
from kpi_b2b.facades.procurement_command_facade import ProcurementCommandFacadeImpl


@pytest.fixture
def target_system():
    mock_b2b = MagicMock()
    mock_db = MagicMock()
    mock_redis = MagicMock()
    mock_mirroring_uc = MagicMock()
    mock_rbac = MagicMock()

    with (
        patch(
            "kpi_b2b.b2b_procurement.application.generate_quote.generate_quote_usecase.GlobalSystemLogger"
        ),
        patch("kpi_b2b.facades.procurement_command_facade.GlobalSystemLogger"),
    ):
        usecase = GenerateQuoteUseCase(b2b_adapter=mock_b2b, mysql_repo=mock_db)
        facade = ProcurementCommandFacadeImpl(
            generate_quote_uc=usecase,
            mirroring_uc=mock_mirroring_uc,
            redis_adapter=mock_redis,
            rbac_manager=mock_rbac,
            baseline_repo=MagicMock(),
        )
        yield facade, mock_b2b, mock_db, mock_redis


class TestGenerateQuote:
    @pytest.fixture
    def valid_ctx(self):
        return UserContext(
            user_id="USR-100",
            username="factory_manager_a",
            company_id="TENANT_A",
            role=UserRoleEnum.FACTORY_MANAGER,
        )

    def test_generate_quote_happy_path_cache_miss(self, target_system, valid_ctx):
        facade, mock_b2b, mock_db, mock_redis = target_system
        asset_ids = ["ASSET-001", "ASSET-002"]
        idempotency_key = "IDEMP-KEY-12345"

        mock_redis.get_cached_quote.return_value = None
        mock_b2b.request_turnkey_quote.return_value = {
            "total_estimated_price": 150000.0,
            "delivery_days_estimated": 14,
        }

        result_dto = facade.generate_quote(
            asset_ids=asset_ids, idempotency_key=idempotency_key, ctx=valid_ctx
        )

        mock_b2b.request_turnkey_quote.assert_called_once_with(asset_ids)
        mock_db.save.assert_called_once()
        mock_redis.set_cached_quote.assert_called_once()
        assert result_dto.status == B2bQuoteStatusEnum.REQUESTED.value

    def test_generate_quote_happy_path_cache_hit(self, target_system, valid_ctx):
        facade, mock_b2b, mock_db, mock_redis = target_system
        asset_ids = ["ASSET-001"]
        idempotency_key = "IDEMP-KEY-DUPLICATE"

        cached_response = {
            "quote_id": "QT-CACHED-001",
            "total_estimated_price": 50000.0,
            "status": "REQUESTED",
            "delivery_days_estimated": 7,
        }
        mock_redis.get_cached_quote.return_value = cached_response

        result_dto = facade.generate_quote(
            asset_ids=asset_ids, idempotency_key=idempotency_key, ctx=valid_ctx
        )

        mock_b2b.request_turnkey_quote.assert_not_called()
        mock_db.save.assert_not_called()
        assert result_dto.quote_id == "QT-CACHED-001"

    def test_generate_quote_invalid_schema(self, target_system, valid_ctx):
        facade, mock_b2b, mock_db, mock_redis = target_system
        asset_ids = ["ASSET-003"]
        idempotency_key = "IDEMP-KEY-INVALID"

        mock_redis.get_cached_quote.return_value = None
        mock_b2b.request_turnkey_quote.return_value = {"total_estimated_price": 10000.0}

        with pytest.raises(BaseSystemException) as exc_info:
            facade.generate_quote(
                asset_ids=asset_ids, idempotency_key=idempotency_key, ctx=valid_ctx
            )

        assert exc_info.value.error_code == "ERR_B2B_INVALID_QUOTE"
        assert exc_info.value.status_code == 422
        mock_db.save.assert_not_called()

    def test_generate_quote_api_failure(self, target_system, valid_ctx):
        facade, mock_b2b, mock_db, mock_redis = target_system
        asset_ids = ["ASSET-004"]
        idempotency_key = "IDEMP-KEY-TIMEOUT"

        mock_redis.get_cached_quote.return_value = None
        mock_b2b.request_turnkey_quote.side_effect = Exception("Timeout")

        with pytest.raises(BaseSystemException) as exc_info:
            facade.generate_quote(
                asset_ids=asset_ids, idempotency_key=idempotency_key, ctx=valid_ctx
            )

        assert exc_info.value.error_code == "ERR_B2B_API_FAILURE"
        assert exc_info.value.status_code == 502
        mock_db.save.assert_not_called()
