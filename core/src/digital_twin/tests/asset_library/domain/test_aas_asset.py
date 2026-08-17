"""
===============================================================================
[File Name] test_aas_asset.py
[Location ] /tests/digital_twin/asset_library/domain/test_aas_asset.py
[Description] 도메인 엔티티 Asset 및 validate_schema() 단위 테스트
===============================================================================
"""

import pytest
from digital_twin.asset_library.domain.asset import Asset
from digital_twin.asset_library.domain.enums.asset_type_enum import AssetTypeEnum
from shared.enums.global_error_code_enum import GlobalErrorCodeEnum
from shared.exceptions.base_exception import BaseSystemException


def test_aas_asset_valid_schema():
    # Given
    asset = Asset(
        asset_name="Doosan_M1013_Robot",
        asset_type=AssetTypeEnum.ROBOT,
        company_id="TEST-COMPANY-01",
        kinematics_metadata={
            "degrees_of_freedom": 6,
            "dh_parameters": {"a": [0, -425, -392]},
        },
    )

    # When & Then
    assert asset.validate_schema() is True, "Valid Asset schema must return True"


def test_aas_asset_invalid_schema_missing_kinematics_keys():
    # Given
    asset = Asset(
        asset_name="Doosan_M1013_Robot",
        asset_type=AssetTypeEnum.ROBOT,
        company_id="TEST-COMPANY-01",
        kinematics_metadata={"invalid_key": "data"},  # missing degrees_of_freedom
    )

    # When & Then
    with pytest.raises(BaseSystemException) as exc_info:
        asset.validate_schema()

    assert exc_info.value.error_code == GlobalErrorCodeEnum.ERR_TWIN_INVALID_SCHEMA
    assert exc_info.value.status_code == 400
    assert "Missing required key" in exc_info.value.message
