"""
@file test_generate_quote.py
@description B2B 마켓플레이스 턴키 견적 요청 (GenerateQuoteUseCase) 및 파사드(ProcurementCommandFacadeImpl) 단위 테스트
"""

from unittest.mock import MagicMock, patch

import pytest

from src.kpi_b2b.b2b_procurement.application.generate_quote_usecase import (
    GenerateQuoteUseCase,
)
from src.kpi_b2b.b2b_procurement.domain.b2b_quote import B2bQuoteStatusEnum
from src.kpi_b2b.facades.procurement_command_facade import ProcurementCommandFacadeImpl
from src.shared.enums.user_role_enum import UserRoleEnum
from src.shared.exceptions.base_exception import BaseSystemException
from src.shared.security.user_context import UserContext


@pytest.fixture
def mock_b2b_adapter():
    """외부 B2B 마켓플레이스 API 통신 어댑터 모킹"""
    return MagicMock()


@pytest.fixture
def mock_mysql_repo():
    """MySQL DB 영속화 어댑터 모킹"""
    return MagicMock()


@pytest.fixture
def mock_redis_adapter():
    """멱등성 보장용 Redis 캐시 어댑터 모킹"""
    return MagicMock()


@pytest.fixture
def target_system(mock_b2b_adapter, mock_mysql_repo, mock_redis_adapter):
    """테스트 대상 시스템(Facade & UseCase) 셋업 및 전역 로거 패치"""
    with (
        patch(
            "src.kpi_b2b.b2b_procurement.application.generate_quote_usecase.GlobalSystemLogger"
        ),
        patch("src.kpi_b2b.facades.procurement_command_facade.GlobalSystemLogger"),
    ):
        usecase = GenerateQuoteUseCase(
            b2b_adapter=mock_b2b_adapter, mysql_repo=mock_mysql_repo
        )
        facade = ProcurementCommandFacadeImpl(
            generate_quote_uc=usecase, redis_adapter=mock_redis_adapter
        )

        yield facade, mock_b2b_adapter, mock_mysql_repo, mock_redis_adapter


class TestGenerateQuote:
    @pytest.fixture
    def valid_ctx(self):
        """정상적인 권한을 가진 UserContext 픽스처"""
        return UserContext(
            user_id="USR-100",
            username="factory_manager_a",
            company_id="TENANT_A",
            role=UserRoleEnum.FACTORY_MANAGER,
        )

    def test_generate_quote_happy_path_cache_miss(self, target_system, valid_ctx):
        """TC-정상 (Happy Path): Cache Miss 시 외부 API를 호출하고 엔티티 생성 후 캐싱하는지 검증"""
        facade, mock_b2b, mock_db, mock_redis = target_system

        # Given
        asset_ids = ["ASSET-001", "ASSET-002"]
        idempotency_key = "IDEMP-KEY-12345"

        mock_redis.get_cached_quote.return_value = None  # Cache Miss
        mock_b2b.request_turnkey_quote.return_value = {
            "total_estimated_price": 150000.0,
            "delivery_days_estimated": 14,
        }

        # When
        result_dto = facade.generate_quote(
            asset_ids=asset_ids, idempotency_key=idempotency_key, ctx=valid_ctx
        )

        # Then
        # 1. B2B API 호출 여부 검증
        mock_b2b.request_turnkey_quote.assert_called_once_with(asset_ids)

        # 2. DB 영속화 호출 검증
        mock_db.save.assert_called_once()
        saved_entity = mock_db.save.call_args[0][0]
        assert saved_entity.status == B2bQuoteStatusEnum.REQUESTED
        assert saved_entity.total_estimated_price == 150000.0
        assert saved_entity.delivery_days_estimated == 14

        # 3. Redis 캐싱 호출 및 DTO 반환 검증
        mock_redis.set_cached_quote.assert_called_once()
        assert result_dto.quote_id.startswith("QT-")
        assert result_dto.status == B2bQuoteStatusEnum.REQUESTED.value

    def test_generate_quote_happy_path_cache_hit(self, target_system, valid_ctx):
        """TC-정상 (Idempotency): Cache Hit 시 외부 연동 없이 즉시 캐시된 응답 반환 검증"""
        facade, mock_b2b, mock_db, mock_redis = target_system

        # Given
        asset_ids = ["ASSET-001"]
        idempotency_key = "IDEMP-KEY-DUPLICATE"

        cached_response = {
            "quote_id": "QT-CACHED-001",
            "total_estimated_price": 50000.0,
            "status": "REQUESTED",
            "delivery_days_estimated": 7,
        }
        mock_redis.get_cached_quote.return_value = cached_response  # Cache Hit

        # When
        result_dto = facade.generate_quote(
            asset_ids=asset_ids, idempotency_key=idempotency_key, ctx=valid_ctx
        )

        # Then
        # 외부 API 및 DB 영속화가 절대 호출되지 않아야 함
        mock_b2b.request_turnkey_quote.assert_not_called()
        mock_db.save.assert_not_called()

        # 캐시된 결과가 그대로 반환되어야 함
        assert result_dto.quote_id == "QT-CACHED-001"
        assert result_dto.total_estimated_price == 50000.0

    def test_generate_quote_invalid_schema(self, target_system, valid_ctx):
        """TC-예외 (Edge Case): 외부 B2B API가 필수 필드를 누락한 응답을 줄 때 422 에러 발생 검증"""
        facade, mock_b2b, mock_db, mock_redis = target_system

        # Given
        asset_ids = ["ASSET-003"]
        idempotency_key = "IDEMP-KEY-INVALID"

        mock_redis.get_cached_quote.return_value = None
        mock_b2b.request_turnkey_quote.return_value = {
            "total_estimated_price": 10000.0
            # delivery_days_estimated 누락
        }

        # When & Then
        with pytest.raises(BaseSystemException) as exc_info:
            facade.generate_quote(
                asset_ids=asset_ids, idempotency_key=idempotency_key, ctx=valid_ctx
            )

        assert exc_info.value.error_code == "ERR_B2B_INVALID_QUOTE"
        assert exc_info.value.status_code == 422
        mock_db.save.assert_not_called()  # 비정상 데이터 영속화 차단 확인

    def test_generate_quote_api_failure(self, target_system, valid_ctx):
        """TC-에러 (Error Handling): 외부 B2B API 통신 지연/타임아웃 시 502 에러로 안전하게 래핑 검증"""
        facade, mock_b2b, mock_db, mock_redis = target_system

        # Given
        asset_ids = ["ASSET-004"]
        idempotency_key = "IDEMP-KEY-TIMEOUT"

        mock_redis.get_cached_quote.return_value = None
        mock_b2b.request_turnkey_quote.side_effect = Exception(
            "requests.exceptions.Timeout"
        )

        # When & Then
        with pytest.raises(BaseSystemException) as exc_info:
            facade.generate_quote(
                asset_ids=asset_ids, idempotency_key=idempotency_key, ctx=valid_ctx
            )

        assert exc_info.value.error_code == "ERR_B2B_API_FAILURE"
        assert exc_info.value.status_code == 502
        assert "공급망 연결이 지연되고 있습니다" in exc_info.value.message
        mock_db.save.assert_not_called()
