import pytest
from cryptography.fernet import Fernet

from src.shared.exceptions.base_exception import EncryptionFailedException
from src.shared.security.aes256_encryption_service import Aes256EncryptionService


def test_tc_shared_03_hp01_aes256_encrypt_decrypt_success():
    """TC-SHARED-03-HP01: 평문 데이터를 암복호화했을 때 원본이 복원되는지 검증"""
    # Given
    key = Fernet.generate_key().decode()
    service = Aes256EncryptionService(secret_key=key)
    plain_text = "SecretPassword123!"

    # When
    cipher_text = service.encrypt(plain_text)
    decrypted_text = service.decrypt(cipher_text)

    # Then
    assert cipher_text != plain_text, "암호문은 평문과 상이해야 합니다."
    assert decrypted_text == plain_text, "복호화 결과는 최초 평문과 동일해야 합니다."


def test_aes256_decryption_failure():
    """잘못된 암호문 복호화 시 EncryptionFailedException 예외 발생 검증"""
    # Given
    key = Fernet.generate_key().decode()
    service = Aes256EncryptionService(secret_key=key)
    invalid_cipher = "InvalidCorruptedCipherText"

    # When & Then
    with pytest.raises(EncryptionFailedException) as exc_info:
        service.decrypt(invalid_cipher)

    assert exc_info.value.status_code == 500
    assert exc_info.value.error_code == "ERR_SHARED_ENCRYPTION_FAILED"
