from datetime import datetime

from src.shared.dtos.global_response_dto import GlobalResponseDto


def test_tc_shared_01_hp01_success_response_creation():
    """TC-SHARED-01-HP01: GlobalResponseDto 성공 응답 생성 검증"""
    # Given
    payload = {"user_id": "usr-1234", "username": "kibeom"}
    msg = "User profile retrieved successfully."
    trace_id = "TRC-test1234"

    # When
    response = GlobalResponseDto.success_response(
        data=payload, message=msg, trace_id=trace_id
    )

    # Then
    assert response.success is True, "성공 여부는 True여야 합니다."
    assert response.code == "SUCCESS", "코드 값은 'SUCCESS'여야 합니다."
    assert response.message == msg, "설정한 메시지와 일치해야 합니다."
    assert response.data == payload, "전달한 payload와 일치해야 합니다."
    assert response.trace_id == trace_id, "trace_id가 정상 설정되어야 합니다."

    # Verify ISO-8601 timestamp
    parsed_time = datetime.fromisoformat(response.timestamp)
    assert parsed_time is not None, "Timestamp는 유효한 ISO-8601 포맷이어야 합니다."


def test_error_response_creation():
    """GlobalResponseDto 에러 응답 정적 팩토리 메서드 검증"""
    # Given
    code = "ERR_SHARED_UNAUTHORIZED"
    msg = "Unauthorized access."
    details = {"reason": "Expired Token"}
    trace_id = "TRC-err1234"

    # When
    response = GlobalResponseDto.error_response(
        code=code, message=msg, data=details, trace_id=trace_id
    )

    # Then
    assert response.success is False, "성공 여부는 False여야 합니다."
    assert response.code == code, f"코드 값은 {code}여야 합니다."
    assert response.message == msg, "메시지가 일치해야 합니다."
    assert response.data == details, "상세 에러 내역이 전달되어야 합니다."
    assert response.trace_id == trace_id, "trace_id가 전달되어야 합니다."
