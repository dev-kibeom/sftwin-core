from src.shared.security.jwt_token_provider import JwtTokenProvider
from src.shared.security.user_context import UserContext, UserRoleEnum


def test_jwt_token_provider_generate_and_verify():
    """JwtTokenProvider Access/Refresh 토큰 생성 및 검증 성공 사례"""
    # Given
    provider = JwtTokenProvider(secret_key="test-secret-key-32bytes-long-secret-key!")
    user_ctx = UserContext(
        user_id="usr-001",
        username="kibeom_engineer",
        company_id="COMP-A",
        role=UserRoleEnum.FIELD_ENGINEER,
    )

    # When
    access_token = provider.generate_access_token(user_ctx)
    refresh_token = provider.generate_refresh_token(user_ctx)
    verified_ctx = provider.verify_token(access_token)

    # Then
    assert access_token is not None
    assert refresh_token is not None
    assert verified_ctx.user_id == "usr-001"
    assert verified_ctx.company_id == "COMP-A"
    assert verified_ctx.role == UserRoleEnum.FIELD_ENGINEER
