"""
===============================================================================
[File Name] test_asset_twin_query_impl.py
[Location ] /tests/asset_twin/facades/test_asset_twin_query_impl.py
[Description] AssetTwinQueryImpl 파사드 위임 및 기능 단위 테스트
===============================================================================
"""

from unittest.mock import MagicMock

from src.asset_twin.asset_library.application.manage_asset_usecase import (
    ManageAssetUseCase,
)
from src.asset_twin.facades.asset_twin_query_impl import AssetTwinQueryImpl
from src.asset_twin.twin_reconstruction.application.get_layout_usecase import (
    GetLayoutUseCase,
    LayoutRenderingDto,
)
from src.shared.enums.user_role_enum import UserRoleEnum
from src.shared.security.user_context import UserContext


def test_facade_get_layout_data_delegation():
    # Given
    mock_manage_uc = MagicMock(spec=ManageAssetUseCase)
    mock_get_layout_uc = MagicMock(spec=GetLayoutUseCase)

    expected_dto = LayoutRenderingDto(
        baseline_id="BASE-TWIN-001",
        baseline_name="Factory_1",
        company_id="TEST-COMPANY-01",
        sync_error_rate=1.0,
        sync_status="COMPLETED",
        asset_mappings=[],
    )
    mock_get_layout_uc.execute.return_value = expected_dto

    facade = AssetTwinQueryImpl(
        manage_asset_uc=mock_manage_uc, get_layout_uc=mock_get_layout_uc
    )

    ctx = UserContext(
        user_id="USER-123",
        username="kibeom_engineer",
        company_id="TEST-COMPANY-01",
        role=UserRoleEnum.CREATOR,
        accessible_factory_ids=["BASE-TWIN-001"],
    )

    # When
    result = facade.get_layout_data("BASE-TWIN-001", ctx)

    # Then
    assert result.baseline_id == "BASE-TWIN-001"
    assert mock_get_layout_uc.execute.call_count == 1
