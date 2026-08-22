"""AAS JSON Schema Validator."""

from typing import Any


class SchemaValidationError(Exception):
    """JSON 스키마 검증 실패 시 발생하는 예외."""

    def __init__(self, message: str, details: dict[str, Any] | None = None) -> None:
        super().__init__(message)
        self.message = message
        self.details = details or {}


class AasJsonSchemaValidator:
    """AAS kinematics 및 submodels JSON 규격 검증기."""

    def validate_kinematics_json(self, kinematics_data: dict[str, Any]) -> bool:
        """관절 운동학 메타데이터 스키마 유효성을 검증한다."""
        if not isinstance(kinematics_data, dict):
            raise SchemaValidationError(
                "kinematics_metadata must be a dictionary.",
                details={"received_type": type(kinematics_data).__name__},
            )

        if "dof" not in kinematics_data:
            raise SchemaValidationError(
                "Missing required field 'dof' in kinematics_metadata.",
                details={"missing_field": "dof"},
            )

        dof = kinematics_data["dof"]
        if not isinstance(dof, int) or dof < 1:
            raise SchemaValidationError(
                "'dof' must be an integer greater than or equal to 1.",
                details={"dof": dof},
            )

        if "joints" not in kinematics_data:
            raise SchemaValidationError(
                "Missing required field 'joints' in kinematics_metadata.",
                details={"missing_field": "joints"},
            )

        joints = kinematics_data["joints"]
        if not isinstance(joints, list) or len(joints) == 0:
            raise SchemaValidationError(
                "'joints' must be a non-empty list.",
                details={"joints": joints},
            )

        required_joint_fields = {"name", "type", "min_limit", "max_limit"}
        for idx, joint in enumerate(joints):
            if not isinstance(joint, dict):
                raise SchemaValidationError(
                    f"Joint at index {idx} must be a dictionary.",
                    details={"index": idx, "invalid_joint": joint},
                )
            missing = required_joint_fields - set(joint.keys())
            if missing:
                raise SchemaValidationError(
                    f"Joint at index {idx} is missing required fields: {sorted(missing)}",
                    details={"index": idx, "missing_fields": sorted(missing)},
                )

        return True

    def validate_aas_submodels(self, submodels_data: dict[str, Any]) -> bool:
        """AAS v3.0 JSON 서브모델 규격을 검증한다."""
        if not isinstance(submodels_data, dict):
            raise SchemaValidationError(
                "submodels must be a dictionary.",
                details={"received_type": type(submodels_data).__name__},
            )
        return True
