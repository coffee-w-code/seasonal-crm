import time

import pyotp


TOTP_INTERVAL = 30
TOTP_DIGITS = 6
TOTP_VALID_WINDOW = 1


def generate_totp_secret():
    """
    Generate a cryptographically secure TOTP secret.
    """

    return pyotp.random_base32()


def build_totp(secret):
    """
    Create a TOTP instance for a secret.
    """

    return pyotp.TOTP(
        secret,
        digits=TOTP_DIGITS,
        interval=TOTP_INTERVAL,
    )


def generate_provisioning_uri(secret, username):
    """
    Generate the otpauth URI used by authenticator
    applications.
    """

    totp = build_totp(secret)

    return totp.provisioning_uri(
        name=username,
        issuer_name="Seasonal CRM",
    )


def get_current_time_step():
    """
    Return the current server TOTP time-step.
    """

    return int(time.time() // TOTP_INTERVAL)


def get_valid_time_step(secret, code):
    """
    Return the exact TOTP time-step represented by a
    valid code.

    The verification window allows one step of clock
    drift in either direction.
    """

    if not isinstance(code, str):
        return None

    normalized_code = code.strip()

    if (
        not normalized_code.isdigit()
        or len(normalized_code) != TOTP_DIGITS
    ):
        return None

    totp = build_totp(secret)

    current_time_step = get_current_time_step()

    for offset in range(
        -TOTP_VALID_WINDOW,
        TOTP_VALID_WINDOW + 1,
    ):
        time_step = current_time_step + offset

        if totp.at(time_step * TOTP_INTERVAL) == normalized_code:
            return time_step

    return None


def verify_totp_code(secret, code):
    """
    Return True when the supplied code is valid.
    """

    return get_valid_time_step(secret, code) is not None