import base64
import logging
import os
from cryptography.fernet import Fernet, InvalidToken
from src.shared.exceptions.base_exception import EncryptionFailedException

logger = logging.getLogger("sftwin.shared.security.aes256")


class Aes256EncryptionService:
    """AES-256 규격 양방향 암복호화 무상태 서비스"""

    def __init__(self, secret_key: str = None):
        if not secret_key:
            secret_key = os.getenv("AES256_SECRET_KEY")

        if not secret_key:
            # Fallback 32-byte url-safe base64 key generation for dev/testing
            secret_key = Fernet.generate_key().decode()

        try:
            self._fernet = Fernet(
                secret_key.encode() if isinstance(secret_key, str) else secret_key
            )
        except Exception as exc:
            logger.error(f"[Aes256EncryptionService] Key initialization failed: {exc}")
            raise EncryptionFailedException(
                message="Invalid encryption key configuration.",
                details={"error": str(exc)},
            )

    def encrypt(self, plain_text: str) -> str:
        """평문 문자열을 AES-256 알고리즘으로 암호화하여 Base64 문자열로 반환"""
        if not plain_text:
            return ""
        try:
            cipher_bytes = self._fernet.encrypt(plain_text.encode("utf-8"))
            logger.info(
                "[Aes256EncryptionService] Plaintext encryption completed successfully."
            )
            return cipher_bytes.decode("utf-8")
        except Exception as exc:
            logger.error(f"[Aes256EncryptionService] Encryption failed: {exc}")
            raise EncryptionFailedException(
                message="Failed to encrypt input plaintext.",
                details={"error": str(exc)},
            )

    def decrypt(self, cipher_text: str) -> str:
        """Base64 암호문 문자열을 복호화하여 원본 평문으로 복원"""
        if not cipher_text:
            return ""
        try:
            plain_bytes = self._fernet.decrypt(cipher_text.encode("utf-8"))
            logger.info(
                "[Aes256EncryptionService] Ciphertext decryption completed successfully."
            )
            return plain_bytes.decode("utf-8")
        except (InvalidToken, Exception) as exc:
            logger.error(f"[Aes256EncryptionService] Decryption failed: {exc}")
            raise EncryptionFailedException(
                message="Failed to decrypt input ciphertext. Key mismatch or corrupted payload.",
                details={"error": str(exc)},
            )
