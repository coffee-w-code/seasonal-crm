from datetime import timedelta

from django.db import transaction
from django.utils import timezone

from apps.accounts.models import UserTwoFactorAuth
from apps.accounts.security.recovery_codes import (
    consume_recovery_code,
)
from apps.accounts.security.two_factor import (
    decrypt_totp_secret,
)
from apps.accounts.security.totp import (
    get_valid_time_step,
)


MAX_FAILED_ATTEMPTS = 5
LOCKOUT_MINUTES = 10
SETUP_EXPIRATION_MINUTES = 10


def is_two_factor_locked(two_factor_auth):
    """
    Return True when the 2FA verifier is currently locked.
    """

    if not two_factor_auth.locked_until:
        return False

    if timezone.now() >= two_factor_auth.locked_until:
        two_factor_auth.locked_until = None
        two_factor_auth.failed_attempts = 0

        two_factor_auth.save(
            update_fields=[
                "locked_until",
                "failed_attempts",
                "updated_at",
            ]
        )

        return False

    return True


def register_failed_attempt(two_factor_auth):
    """
    Record a failed verification attempt and temporarily
    lock verification after the maximum number of failures.
    """

    two_factor_auth.failed_attempts += 1

    update_fields = [
        "failed_attempts",
        "updated_at",
    ]

    if (
        two_factor_auth.failed_attempts
        >= MAX_FAILED_ATTEMPTS
    ):
        two_factor_auth.locked_until = (
            timezone.now()
            + timedelta(minutes=LOCKOUT_MINUTES)
        )

        update_fields.append("locked_until")

    two_factor_auth.save(
        update_fields=update_fields
    )


def register_successful_attempt(
    two_factor_auth,
    time_step=None,
):
    """
    Reset failed-attempt tracking after successful
    verification.
    """

    two_factor_auth.failed_attempts = 0
    two_factor_auth.locked_until = None
    two_factor_auth.last_verified_at = timezone.now()

    update_fields = [
        "failed_attempts",
        "locked_until",
        "last_verified_at",
        "updated_at",
    ]

    if time_step is not None:
        two_factor_auth.last_used_time_step = time_step
        update_fields.append("last_used_time_step")

    two_factor_auth.save(
        update_fields=update_fields
    )


def _get_locked_two_factor_auth(two_factor_auth):
    """
    Reload and lock the 2FA row inside the current transaction.

    This prevents concurrent verification requests from
    modifying the same 2FA state at the same time.
    """

    return (
        UserTwoFactorAuth.objects
        .select_for_update()
        .get(pk=two_factor_auth.pk)
    )


@transaction.atomic
def verify_totp_for_user(
    two_factor_auth,
    submitted_code,
):
    """
    Verify a TOTP code for an enabled 2FA configuration.

    The 2FA row is locked during verification to prevent
    concurrent requests from bypassing replay protection
    or corrupting failed-attempt tracking.
    """

    two_factor_auth = _get_locked_two_factor_auth(
        two_factor_auth
    )

    if not two_factor_auth.is_enabled:
        return {
            "success": False,
            "reason": "TWO_FACTOR_DISABLED",
        }

    if is_two_factor_locked(two_factor_auth):
        return {
            "success": False,
            "reason": "TOO_MANY_ATTEMPTS",
        }

    try:
        secret = decrypt_totp_secret(
            two_factor_auth.encrypted_secret
        )
    except (RuntimeError, ValueError):
        return {
            "success": False,
            "reason": "CONFIGURATION_ERROR",
        }

    time_step = get_valid_time_step(
        secret,
        submitted_code,
    )

    if time_step is None:
        register_failed_attempt(two_factor_auth)

        return {
            "success": False,
            "reason": "INVALID_CODE",
        }

    if (
        two_factor_auth.last_used_time_step
        == time_step
    ):
        register_failed_attempt(two_factor_auth)

        return {
            "success": False,
            "reason": "CODE_ALREADY_USED",
        }

    register_successful_attempt(
        two_factor_auth,
        time_step=time_step,
    )

    return {
        "success": True,
        "method": "TOTP",
    }


@transaction.atomic
def verify_totp_setup_for_user(
    two_factor_auth,
    submitted_code,
):
    """
    Verify the TOTP code during 2FA setup.

    Setup must be completed within the configured
    expiration period.

    The 2FA row is locked during verification to prevent
    concurrent requests from bypassing replay protection.
    """

    two_factor_auth = _get_locked_two_factor_auth(
        two_factor_auth
    )

    if two_factor_auth.is_enabled:
        return {
            "success": False,
            "reason": "TWO_FACTOR_ALREADY_ENABLED",
        }

    if not two_factor_auth.setup_started_at:
        return {
            "success": False,
            "reason": "TWO_FACTOR_SETUP_NOT_STARTED",
        }

    setup_expires_at = (
        two_factor_auth.setup_started_at
        + timedelta(minutes=SETUP_EXPIRATION_MINUTES)
    )

    if timezone.now() >= setup_expires_at:
        return {
            "success": False,
            "reason": "TWO_FACTOR_SETUP_EXPIRED",
        }

    if is_two_factor_locked(two_factor_auth):
        return {
            "success": False,
            "reason": "TOO_MANY_ATTEMPTS",
        }

    try:
        secret = decrypt_totp_secret(
            two_factor_auth.encrypted_secret
        )
    except (RuntimeError, ValueError):
        return {
            "success": False,
            "reason": "CONFIGURATION_ERROR",
        }

    time_step = get_valid_time_step(
        secret,
        submitted_code,
    )

    if time_step is None:
        register_failed_attempt(two_factor_auth)

        return {
            "success": False,
            "reason": "INVALID_CODE",
        }

    if (
        two_factor_auth.pending_last_used_time_step
        == time_step
    ):
        register_failed_attempt(two_factor_auth)

        return {
            "success": False,
            "reason": "CODE_ALREADY_USED",
        }

    two_factor_auth.pending_last_used_time_step = time_step
    two_factor_auth.failed_attempts = 0
    two_factor_auth.locked_until = None
    two_factor_auth.last_verified_at = timezone.now()

    two_factor_auth.save(
        update_fields=[
            "pending_last_used_time_step",
            "failed_attempts",
            "locked_until",
            "last_verified_at",
            "updated_at",
        ]
    )

    return {
        "success": True,
        "method": "TOTP_SETUP",
    }

@transaction.atomic
def verify_totp_authenticator_change_for_user(
    two_factor_auth,
    submitted_code,
):
    """
    Verify the TOTP code for a pending authenticator replacement.

    The currently active authenticator remains unchanged until
    the pending authenticator is successfully verified.

    The 2FA row is locked during verification to prevent
    concurrent requests from bypassing replay protection
    or corrupting failed-attempt tracking.
    """

    two_factor_auth = _get_locked_two_factor_auth(
        two_factor_auth
    )

    if not two_factor_auth.is_enabled:
        return {
            "success": False,
            "reason": "TWO_FACTOR_DISABLED",
        }

    if not two_factor_auth.pending_encrypted_secret:
        return {
            "success": False,
            "reason": "TWO_FACTOR_CHANGE_NOT_STARTED",
        }

    if not two_factor_auth.pending_setup_started_at:
        return {
            "success": False,
            "reason": "TWO_FACTOR_CHANGE_NOT_STARTED",
        }

    setup_expires_at = (
        two_factor_auth.pending_setup_started_at
        + timedelta(minutes=SETUP_EXPIRATION_MINUTES)
    )

    if timezone.now() >= setup_expires_at:
        return {
            "success": False,
            "reason": "TWO_FACTOR_CHANGE_EXPIRED",
        }

    if is_two_factor_locked(two_factor_auth):
        return {
            "success": False,
            "reason": "TOO_MANY_ATTEMPTS",
        }

    try:
        secret = decrypt_totp_secret(
            two_factor_auth.pending_encrypted_secret
        )
    except (RuntimeError, ValueError):
        return {
            "success": False,
            "reason": "CONFIGURATION_ERROR",
        }

    time_step = get_valid_time_step(
        secret,
        submitted_code,
    )

    if time_step is None:
        register_failed_attempt(two_factor_auth)

        return {
            "success": False,
            "reason": "INVALID_CODE",
        }

    if (
        two_factor_auth.pending_last_used_time_step
        == time_step
    ):
        register_failed_attempt(two_factor_auth)

        return {
            "success": False,
            "reason": "CODE_ALREADY_USED",
        }

    two_factor_auth.pending_last_used_time_step = time_step
    two_factor_auth.failed_attempts = 0
    two_factor_auth.locked_until = None
    two_factor_auth.last_verified_at = timezone.now()

    two_factor_auth.save(
        update_fields=[
            "pending_last_used_time_step",
            "failed_attempts",
            "locked_until",
            "last_verified_at",
            "updated_at",
        ]
    )

    return {
        "success": True,
        "method": "TOTP_AUTHENTICATOR_CHANGE",
    }


@transaction.atomic
def verify_recovery_code_for_user(
    two_factor_auth,
    submitted_code,
):
    """
    Verify and consume a recovery code.

    The 2FA row is locked during verification to prevent
    concurrent requests from bypassing failed-attempt tracking.
    """

    two_factor_auth = _get_locked_two_factor_auth(
        two_factor_auth
    )

    if not two_factor_auth.is_enabled:
        return {
            "success": False,
            "reason": "TWO_FACTOR_DISABLED",
        }

    if is_two_factor_locked(two_factor_auth):
        return {
            "success": False,
            "reason": "TOO_MANY_ATTEMPTS",
        }

    if not consume_recovery_code(
        two_factor_auth,
        submitted_code,
    ):
        register_failed_attempt(two_factor_auth)

        return {
            "success": False,
            "reason": "INVALID_RECOVERY_CODE",
        }

    register_successful_attempt(
        two_factor_auth
    )

    return {
        "success": True,
        "method": "RECOVERY_CODE",
    }