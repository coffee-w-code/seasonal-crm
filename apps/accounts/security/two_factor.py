from cryptography.fernet import Fernet, InvalidToken
from django.conf import settings


def _get_fernet():
    """
    Return the Fernet encryption service used for
    protecting TOTP secrets at rest.
    """

    key = settings.TWO_FACTOR_ENCRYPTION_KEY

    if not key:
        raise RuntimeError(
            "TWO_FACTOR_ENCRYPTION_KEY is not configured."
        )

    try:
        return Fernet(key.encode())
    except (ValueError, TypeError) as exc:
        raise RuntimeError(
            "TWO_FACTOR_ENCRYPTION_KEY is invalid."
        ) from exc


def encrypt_totp_secret(secret):
    """
    Encrypt a TOTP secret before storing it in the database.
    """

    if not secret:
        raise ValueError("TOTP secret cannot be empty.")

    fernet = _get_fernet()

    return fernet.encrypt(
        secret.encode("utf-8")
    ).decode("utf-8")


def decrypt_totp_secret(encrypted_secret):
    """
    Decrypt a stored TOTP secret.
    """

    if not encrypted_secret:
        raise ValueError(
            "Encrypted TOTP secret cannot be empty."
        )

    fernet = _get_fernet()

    try:
        return fernet.decrypt(
            encrypted_secret.encode("utf-8")
        ).decode("utf-8")
    except InvalidToken as exc:
        raise RuntimeError(
            "Unable to decrypt the stored TOTP secret."
        ) from exc