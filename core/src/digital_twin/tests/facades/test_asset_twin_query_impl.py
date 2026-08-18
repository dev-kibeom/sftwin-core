"""
===============================================================================
[File Name] test_digital_twin_query_impl.py
[Location ] /tests/digital_twin/facades/test_digital_twin_query_impl.py
[Description] AssetTwinQueryImpl 파사드 위임 및 기능 단위 테스트
===============================================================================
"""

from unittest.mock import MagicMock

from digital_twin.asset_library.application.get_asset.get_asset_usecase import (
    GetAssetUseCase,
)
from digital_twin.facades.digital_twin_query_facade import DigitalTwinQueryFacade
from digital_twin.twin_reconstruction.application.get_layout.get_layout_usecase import (
    GetLayoutUseCase,
    LayoutRenderDto,
)
from shared.context.user_context import UserContext
from shared.enums.user_role_enum import UserRole


def test_facade_get_layout_data_delegation():
    # Given
    mock_get_asset_uc = MagicMock(spec=GetAssetUseCase)
    mock_get_layout_uc = MagicMock(spec=GetLayoutUseCase)

    expected_dto = LayoutRenderDto(
        baseline_id="BASE-TWIN-001",
        baseline_name="Factory_1",
        company_id="TEST-COMPANY-01",
        sync_error_rate=1.0,
        sync_status="COMPLETED",
        asset_mappings=[],
    )
    mock_get_layout_uc.execute.return_value = expected_dto

    facade = DigitalTwinQueryFacade(
        get_asset_uc=mock_get_asset_uc, get_layout_uc=mock_get_layout_uc
    )

    ctx = UserContext(
        user_id="USER-123",
        username="kibeom_engineer",
        company_id="TEST-COMPANY-01",
        role=UserRole.CREATOR,
        accessible_factory_ids=["BASE-TWIN-001"],
    )

    # When
    result = facade.get_layout_data("BASE-TWIN-001", ctx)

    # Then
    assert result.baseline_id == "BASE-TWIN-001"
    assert mock_get_layout_uc.execute.call_count == 1
