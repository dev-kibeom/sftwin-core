import pytest
from digital_twin.asset_library.domain.asset.asset import Asset
from shared.enums.asset_type_enum import AssetType


def test_aas_asset_valid_schema():
    # Given & When: 유효한 스키마로 인스턴스화 성공 검증
    asset = Asset(
        asset_name="Doosan_M1013_Robot",
        asset_type=AssetType.ROBOT,
        company_id="TEST-COMPANY-01",
        kinematics_metadata={
            "degrees_of_freedom": 6,
            "dh_parameters": {"a": [0, -425, -392]},
        },
    )

    # Then
    assert asset.asset_name == "Doosan_M1013_Robot"
    assert asset.asset_type == AssetType.ROBOT
    assert asset.company_id == "TEST-COMPANY-01"
    assert asset.is_deleted is False


def test_aas_asset_invalid_schema_missing_kinematics_keys():
    # Given & When & Then: 필수 키 누락 시 객체 생성 단계에서 ValueError 발생 검증
    with pytest.raises(ValueError) as exc_info:
        Asset(
            asset_name="Doosan_M1013_Robot",
            asset_type=AssetType.ROBOT,
            company_id="TEST-COMPANY-01",
            kinematics_metadata={"invalid_key": "data"},  # degrees_of_freedom 누락
        )

    assert "Missing required key in kinematics_metadata: 'degrees_of_freedom'" in str(
        exc_info.value
    )
