import secrets

from django.contrib.auth.hashers import check_password, make_password
from django.utils import timezone

from apps.accounts.models import TwoFactorRecoveryCode


RECOVERY_CODE_COUNT = 10
RECOVERY_CODE_LENGTH = 10


def generate_recovery_code():
    """
    Generate a cryptographically secure recovery code.

    The plaintext code is returned only to the caller and
    must never be stored directly in the database.
    """

    alphabet = "ABCDEFGHJKLMNPQRSTUVWXYZ23456789"

    return "".join(
        secrets.choice(alphabet)
        for _ in range(RECOVERY_CODE_LENGTH)
    )


def generate_recovery_codes(count=RECOVERY_CODE_COUNT):
    """
    Generate a new set of plaintext recovery codes.
    """

    return [
        generate_recovery_code()
        for _ in range(count)
    ]


def store_recovery_codes(two_factor_auth, recovery_codes):
    """
    Replace existing recovery codes with hashed versions
    of the supplied plaintext codes.

    Plaintext codes are never persisted.
    """

    TwoFactorRecoveryCode.objects.filter(
        two_factor_auth=two_factor_auth,
    ).delete()

    recovery_code_objects = [
        TwoFactorRecoveryCode(
            two_factor_auth=two_factor_auth,
            code_hash=make_password(code),
        )
        for code in recovery_codes
    ]

    TwoFactorRecoveryCode.objects.bulk_create(
        recovery_code_objects
    )


def consume_recovery_code(two_factor_auth, submitted_code):
    """
    Verify and consume one unused recovery code.

    Returns True only when a valid unused recovery code
    is successfully consumed.
    """

    if not submitted_code:
        return False

    normalized_code = submitted_code.strip().upper()

    recovery_codes = TwoFactorRecoveryCode.objects.filter(
        two_factor_auth=two_factor_auth,
        used_at__isnull=True,
    )

    for recovery_code in recovery_codes:
        if check_password(
            normalized_code,
            recovery_code.code_hash,
        ):
            recovery_code.used_at = timezone.now()
            recovery_code.save(
                update_fields=["used_at"]
            )
            return True

    return False


def get_unused_recovery_code_count(two_factor_auth):
    """
    Return the number of unused recovery codes remaining.
    """

    return TwoFactorRecoveryCode.objects.filter(
        two_factor_auth=two_factor_auth,
        used_at__isnull=True,
    ).count()

def get_recovery_code_status(two_factor_auth):
    """
    Return recovery-code usage information.

    Plaintext recovery codes are never returned.
    """

    total_count = TwoFactorRecoveryCode.objects.filter(
        two_factor_auth=two_factor_auth,
    ).count()

    unused_count = TwoFactorRecoveryCode.objects.filter(
        two_factor_auth=two_factor_auth,
        used_at__isnull=True,
    ).count()

    return {
        "total": total_count,
        "unused": unused_count,
        "used": total_count - unused_count,
    }