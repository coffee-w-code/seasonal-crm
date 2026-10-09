import json
from datetime import timedelta
from unittest.mock import patch

import pyotp

from django.contrib.auth import get_user_model
from django.utils import timezone

from rest_framework.test import APITestCase

from apps.accounts.models import (
    TwoFactorRecoveryCode,
    UserTwoFactorAuth,
)
from apps.accounts.security.two_factor import (
    decrypt_totp_secret,
)


User = get_user_model()


class TwoFactorAPITests(APITestCase):
    def setUp(self):
        self.user = User.objects.create_user(
            username="twofactortest",
            password="StrongPassword123!",
        )

        self.client.force_authenticate(
            user=self.user
        )

    def start_setup(self):
        return self.client.post(
            "/api/auth/2fa/setup/",
            {
                "current_password": "StrongPassword123!",
            },
            format="json",
        )

    def test_unauthenticated_user_cannot_access_status(self):
        self.client.force_authenticate(user=None)

        response = self.client.get(
            "/api/auth/2fa/"
        )

        self.assertEqual(response.status_code, 403)

    def test_unauthenticated_user_cannot_start_setup(self):
        self.client.force_authenticate(user=None)

        response = self.client.post(
            "/api/auth/2fa/setup/",
            {
                "current_password": "StrongPassword123!",
            },
            format="json",
        )

        self.assertEqual(response.status_code, 403)

    def test_unauthenticated_user_cannot_verify_setup(self):
        self.client.force_authenticate(user=None)

        response = self.client.post(
            "/api/auth/2fa/setup/verify/",
            {
                "code": "123456",
            },
            format="json",
        )

        self.assertEqual(response.status_code, 403)

    def test_status_returns_disabled_when_2fa_is_not_configured(self):
        response = self.client.get(
            "/api/auth/2fa/"
        )

        self.assertEqual(response.status_code, 200)
        self.assertEqual(
            response.data["status"],
            "success",
        )
        self.assertFalse(
            response.data["enabled"]
        )
        self.assertFalse(
            response.data["setup_in_progress"]
        )

    def test_current_password_is_required_for_setup(self):
        response = self.client.post(
            "/api/auth/2fa/setup/",
            {},
            format="json",
        )

        self.assertEqual(response.status_code, 400)
        self.assertEqual(
            response.data["code"],
            "CURRENT_PASSWORD_REQUIRED",
        )

    def test_invalid_current_password_is_rejected(self):
        response = self.client.post(
            "/api/auth/2fa/setup/",
            {
                "current_password": "WrongPassword123!",
            },
            format="json",
        )

        self.assertEqual(response.status_code, 400)
        self.assertEqual(
            response.data["code"],
            "INVALID_CURRENT_PASSWORD",
        )

    def test_setup_generates_secret_and_provisioning_uri(self):
        response = self.start_setup()

        self.assertEqual(response.status_code, 200)
        self.assertEqual(
            response.data["status"],
            "success",
        )
        self.assertFalse(
            response.data["enabled"]
        )

        self.assertIn(
            "secret",
            response.data,
        )
        self.assertIn(
            "provisioning_uri",
            response.data,
        )

        secret = response.data["secret"]

        self.assertTrue(
            pyotp.TOTP(secret).verify(
                pyotp.TOTP(secret).now()
            )
        )

        self.assertTrue(
            response.data["provisioning_uri"].startswith(
                "otpauth://totp/"
            )
        )

    def test_totp_secret_is_stored_encrypted(self):
        response = self.start_setup()

        self.assertEqual(response.status_code, 200)

        plaintext_secret = response.data["secret"]

        two_factor_auth = (
            UserTwoFactorAuth.objects.get(
                user=self.user
            )
        )

        self.assertNotEqual(
            two_factor_auth.encrypted_secret,
            plaintext_secret,
        )

        decrypted_secret = decrypt_totp_secret(
            two_factor_auth.encrypted_secret
        )

        self.assertEqual(
            decrypted_secret,
            plaintext_secret,
        )

    def test_status_reports_setup_in_progress(self):
        response = self.start_setup()

        self.assertEqual(response.status_code, 200)

        response = self.client.get(
            "/api/auth/2fa/"
        )

        self.assertEqual(response.status_code, 200)
        self.assertFalse(
            response.data["enabled"]
        )
        self.assertTrue(
            response.data["setup_in_progress"]
        )

    def test_valid_totp_enables_2fa(self):
        setup_response = self.start_setup()

        self.assertEqual(
            setup_response.status_code,
            200,
        )

        secret = setup_response.data["secret"]

        code = pyotp.TOTP(secret).now()

        response = self.client.post(
            "/api/auth/2fa/setup/verify/",
            {
                "code": code,
            },
            format="json",
        )

        self.assertEqual(
            response.status_code,
            200,
        )
        self.assertEqual(
            response.data["status"],
            "success",
        )
        self.assertTrue(
            response.data["enabled"]
        )

        self.assertEqual(
            len(response.data["recovery_codes"]),
            10,
        )

        two_factor_auth = (
            UserTwoFactorAuth.objects.get(
                user=self.user
            )
        )

        self.assertTrue(
            two_factor_auth.is_enabled
        )
        self.assertIsNotNone(
            two_factor_auth.enabled_at
        )

        self.assertEqual(
            TwoFactorRecoveryCode.objects.filter(
                two_factor_auth=two_factor_auth,
                used_at__isnull=True,
            ).count(),
            10,
        )

    def test_invalid_totp_code_is_rejected(self):
        self.start_setup()

        response = self.client.post(
            "/api/auth/2fa/setup/verify/",
            {
                "code": "000000",
            },
            format="json",
        )

        self.assertEqual(
            response.status_code,
            400,
        )
        self.assertEqual(
            response.data["code"],
            "INVALID_CODE",
        )

        two_factor_auth = (
            UserTwoFactorAuth.objects.get(
                user=self.user
            )
        )

        self.assertFalse(
            two_factor_auth.is_enabled
        )
        self.assertEqual(
            two_factor_auth.failed_attempts,
            1,
        )

    def test_same_totp_code_cannot_be_used_twice(self):
        setup_response = self.start_setup()

        secret = setup_response.data["secret"]
        code = pyotp.TOTP(secret).now()

        first_response = self.client.post(
            "/api/auth/2fa/setup/verify/",
            {
                "code": code,
            },
            format="json",
        )

        self.assertEqual(
            first_response.status_code,
            200,
        )

        # Disable 2FA again so that the setup verifier
        # cannot reject the second request merely because
        # 2FA is already enabled.
        two_factor_auth = (
            UserTwoFactorAuth.objects.get(
                user=self.user
            )
        )

        two_factor_auth.is_enabled = False
        two_factor_auth.enabled_at = None
        two_factor_auth.save(
            update_fields=[
                "is_enabled",
                "enabled_at",
                "updated_at",
            ]
        )

        second_response = self.client.post(
            "/api/auth/2fa/setup/verify/",
            {
                "code": code,
            },
            format="json",
        )

        self.assertEqual(
            second_response.status_code,
            400,
        )
        self.assertEqual(
            second_response.data["code"],
            "CODE_ALREADY_USED",
        )

    def test_setup_expiration_is_enforced(self):
        self.start_setup()

        two_factor_auth = (
            UserTwoFactorAuth.objects.get(
                user=self.user
            )
        )

        two_factor_auth.setup_started_at = (
            timezone.now()
            - timedelta(minutes=11)
        )

        two_factor_auth.save(
            update_fields=[
                "setup_started_at",
                "updated_at",
            ]
        )

        response = self.client.post(
            "/api/auth/2fa/setup/verify/",
            {
                "code": "123456",
            },
            format="json",
        )

        self.assertEqual(
            response.status_code,
            400,
        )
        self.assertEqual(
            response.data["code"],
            "TWO_FACTOR_SETUP_EXPIRED",
        )

    def test_setup_verification_locks_after_too_many_failures(self):
        self.start_setup()

        for _ in range(5):
            response = self.client.post(
                "/api/auth/2fa/setup/verify/",
                {
                    "code": "000000",
                },
                format="json",
            )

        self.assertEqual(
            response.status_code,
            400,
        )
        self.assertEqual(
            response.data["code"],
            "INVALID_CODE",
        )

        two_factor_auth = (
            UserTwoFactorAuth.objects.get(
                user=self.user
            )
        )

        self.assertEqual(
            two_factor_auth.failed_attempts,
            5,
        )
        self.assertIsNotNone(
            two_factor_auth.locked_until
        )

        response = self.client.post(
            "/api/auth/2fa/setup/verify/",
            {
                "code": "000000",
            },
            format="json",
        )

        self.assertEqual(
            response.status_code,
            400,
        )
        self.assertEqual(
            response.data["code"],
            "TOO_MANY_ATTEMPTS",
        )

    def test_status_does_not_expose_secret_or_recovery_codes(self):
        setup_response = self.start_setup()

        self.assertEqual(
            setup_response.status_code,
            200,
        )

        response = self.client.get(
            "/api/auth/2fa/"
        )

        self.assertEqual(
            response.status_code,
            200,
        )

        self.assertNotIn(
            "secret",
            response.data,
        )
        self.assertNotIn(
            "provisioning_uri",
            response.data,
        )
        self.assertNotIn(
            "recovery_codes",
            response.data,
        )

    def test_cannot_start_setup_when_2fa_is_already_enabled(self):
        setup_response = self.start_setup()

        secret = setup_response.data["secret"]
        code = pyotp.TOTP(secret).now()

        verify_response = self.client.post(
            "/api/auth/2fa/setup/verify/",
            {
                "code": code,
            },
            format="json",
        )

        self.assertEqual(
            verify_response.status_code,
            200,
        )

        response = self.start_setup()

        self.assertEqual(
            response.status_code,
            400,
        )
        self.assertEqual(
            response.data["code"],
            "TWO_FACTOR_ALREADY_ENABLED",
        )

    def enable_2fa(self):
        """
        Helper to enable 2FA and return the generated
        authenticator secret and recovery codes.
        """

        setup_response = self.start_setup()

        self.assertEqual(
            setup_response.status_code,
            200,
        )

        secret = setup_response.data["secret"]

        verify_response = self.client.post(
            "/api/auth/2fa/setup/verify/",
            {
                "code": pyotp.TOTP(secret).now(),
            },
            format="json",
        )

        self.assertEqual(
            verify_response.status_code,
            200,
        )

        return (
            secret,
            verify_response.data["recovery_codes"],
        )

    def start_2fa_login(self):
        """
        Start the real login flow for a user with 2FA enabled.

        The production login endpoint creates the temporary
        pending-2FA session required by /api/auth/login/2fa/.
        """

        self.client.force_authenticate(user=None)

        response = self.client.post(
            "/api/auth/login/",
            {
                "username": "twofactortest",
                "password": "StrongPassword123!",
            },
            format="json",
        )

        self.assertEqual(
            response.status_code,
            200,
        )

        response_data = json.loads(
            response.content
        )

        self.assertEqual(
            response_data["status"],
            "2fa_required",
        )

        self.assertEqual(
            response_data["code"],
            "TWO_FACTOR_REQUIRED",
        )

        return response


    def test_recovery_code_status_requires_2fa(self):
        response = self.client.get(
            "/api/auth/2fa/recovery-codes/"
        )

        self.assertEqual(
            response.status_code,
            400,
        )

        self.assertEqual(
            response.data["code"],
            "TWO_FACTOR_NOT_ENABLED",
        )


    def test_recovery_code_status_returns_usage_counts(self):
        self.enable_2fa()

        response = self.client.get(
            "/api/auth/2fa/recovery-codes/"
        )

        self.assertEqual(
            response.status_code,
            200,
        )

        self.assertEqual(
            response.data["status"],
            "success",
        )

        self.assertEqual(
            response.data["total"],
            10,
        )

        self.assertEqual(
            response.data["unused"],
            10,
        )

        self.assertEqual(
            response.data["used"],
            0,
        )

        self.assertNotIn(
            "recovery_codes",
            response.data,
        )


    def test_recovery_code_can_be_consumed_once(self):
        _, recovery_codes = self.enable_2fa()

        recovery_code = recovery_codes[0]

        self.start_2fa_login()

        response = self.client.post(
            "/api/auth/login/2fa/",
            {
                "method": "RECOVERY_CODE",
                "code": recovery_code,
            },
            format="json",
        )

        self.assertEqual(
            response.status_code,
            200,
        )

        two_factor_auth = (
            UserTwoFactorAuth.objects.get(
                user=self.user
            )
        )

        self.assertEqual(
            TwoFactorRecoveryCode.objects.filter(
                two_factor_auth=two_factor_auth,
                used_at__isnull=True,
            ).count(),
            9,
        )

        self.assertEqual(
            TwoFactorRecoveryCode.objects.filter(
                two_factor_auth=two_factor_auth,
                used_at__isnull=False,
            ).count(),
            1,
        )


    def test_used_recovery_code_cannot_be_used_again(self):
        _, recovery_codes = self.enable_2fa()

        recovery_code = recovery_codes[0]

        self.start_2fa_login()

        first_response = self.client.post(
            "/api/auth/login/2fa/",
            {
                "method": "RECOVERY_CODE",
                "code": recovery_code,
            },
            format="json",
        )

        self.assertEqual(
            first_response.status_code,
            200,
        )

        # A successful 2FA verification consumes the
        # pending challenge, so start a new login attempt.
        self.start_2fa_login()

        second_response = self.client.post(
            "/api/auth/login/2fa/",
            {
                "method": "RECOVERY_CODE",
                "code": recovery_code,
            },
            format="json",
        )

        self.assertEqual(
            second_response.status_code,
            400,
        )

        second_response_data = json.loads(
            second_response.content
        )

        self.assertEqual(
            second_response_data["code"],
            "INVALID_RECOVERY_CODE",
        )


    def test_invalid_recovery_code_is_rejected(self):
        self.enable_2fa()

        self.start_2fa_login()

        response = self.client.post(
            "/api/auth/login/2fa/",
            {
                "method": "RECOVERY_CODE",
                "code": "INVALIDCODE",
            },
            format="json",
        )

        self.assertEqual(
            response.status_code,
            400,
        )

        response_data = json.loads(response.content)

        self.assertEqual(
            response_data["code"],
            "INVALID_RECOVERY_CODE",
        )


    def test_recovery_code_regeneration_requires_current_password(self):
        secret, _ = self.enable_2fa()

        response = self.client.post(
            "/api/auth/2fa/recovery-codes/regenerate/",
            {
                "method": "TOTP",
                "code": pyotp.TOTP(secret).now(),
            },
            format="json",
        )

        self.assertEqual(
            response.status_code,
            400,
        )

        self.assertEqual(
            response.data["code"],
            "CURRENT_PASSWORD_REQUIRED",
        )


    def test_recovery_code_regeneration_rejects_wrong_password(self):
        secret, _ = self.enable_2fa()

        response = self.client.post(
            "/api/auth/2fa/recovery-codes/regenerate/",
            {
                "current_password": "WrongPassword123!",
                "method": "TOTP",
                "code": pyotp.TOTP(secret).now(),
            },
            format="json",
        )

        self.assertEqual(
            response.status_code,
            400,
        )

        self.assertEqual(
            response.data["code"],
            "INVALID_CURRENT_PASSWORD",
        )


    def test_recovery_code_regeneration_requires_valid_2fa_method(self):
        self.enable_2fa()

        response = self.client.post(
            "/api/auth/2fa/recovery-codes/regenerate/",
            {
                "current_password": "StrongPassword123!",
                "method": "INVALID",
                "code": "123456",
            },
            format="json",
        )

        self.assertEqual(
            response.status_code,
            400,
        )

        self.assertEqual(
            response.data["code"],
            "INVALID_2FA_METHOD",
        )


    def test_recovery_code_regeneration_returns_new_codes(self):
        _, old_codes = self.enable_2fa()

        response = self.client.post(
            "/api/auth/2fa/recovery-codes/regenerate/",
            {
                "current_password": "StrongPassword123!",
                "method": "RECOVERY_CODE",
                "code": old_codes[0],
            },
            format="json",
        )

        self.assertEqual(
            response.status_code,
            200,
        )

        self.assertEqual(
            response.data["status"],
            "success",
        )

        new_codes = response.data["recovery_codes"]

        self.assertEqual(
            len(new_codes),
            10,
        )

        self.assertNotEqual(
            new_codes,
            old_codes,
        )


    def test_old_recovery_codes_are_invalid_after_regeneration(self):
        _, old_codes = self.enable_2fa()

        response = self.client.post(
            "/api/auth/2fa/recovery-codes/regenerate/",
            {
                "current_password": "StrongPassword123!",
                "method": "RECOVERY_CODE",
                "code": old_codes[1],
            },
            format="json",
        )

        self.assertEqual(
            response.status_code,
            200,
        )

        old_code = old_codes[0]

        self.start_2fa_login()

        response = self.client.post(
            "/api/auth/login/2fa/",
            {
                "method": "RECOVERY_CODE",
                "code": old_code,
            },
            format="json",
        )

        self.assertEqual(
            response.status_code,
            400,
        )

        response_data = json.loads(response.content)

        self.assertEqual(
            response_data["code"],
            "INVALID_RECOVERY_CODE",
        )


    def test_recovery_code_regeneration_updates_status(self):
        _, old_codes = self.enable_2fa()

        response = self.client.post(
            "/api/auth/2fa/recovery-codes/regenerate/",
            {
                "current_password": "StrongPassword123!",
                "method": "RECOVERY_CODE",
                "code": old_codes[0],
            },
            format="json",
        )

        self.assertEqual(
            response.status_code,
            200,
        )

        response = self.client.get(
            "/api/auth/2fa/recovery-codes/"
        )

        self.assertEqual(
            response.status_code,
            200,
        )

        self.assertEqual(
            response.data["total"],
            10,
        )

        self.assertEqual(
            response.data["unused"],
            10,
        )

        self.assertEqual(
            response.data["used"],
            0,
        )

    # ------------------------------------------------------------------
    # Authenticator change
    # ------------------------------------------------------------------

    def test_authenticator_change_requires_current_password(self):
        self.enable_2fa()

        response = self.client.post(
            "/api/auth/2fa/authenticator/change/",
            {
                "method": "TOTP",
                "code": "123456",
            },
            format="json",
        )

        self.assertEqual(
            response.status_code,
            400,
        )

        self.assertEqual(
            response.data["code"],
            "CURRENT_PASSWORD_REQUIRED",
        )


    def test_authenticator_change_rejects_wrong_current_password(self):
        secret, _ = self.enable_2fa()

        response = self.client.post(
            "/api/auth/2fa/authenticator/change/",
            {
                "current_password": "WrongPassword123!",
                "method": "TOTP",
                "code": pyotp.TOTP(secret).now(),
            },
            format="json",
        )

        self.assertEqual(
            response.status_code,
            400,
        )

        self.assertEqual(
            response.data["code"],
            "INVALID_CURRENT_PASSWORD",
        )


    def test_authenticator_change_requires_2fa_to_be_enabled(self):
        response = self.client.post(
            "/api/auth/2fa/authenticator/change/",
            {
                "current_password": "StrongPassword123!",
                "method": "TOTP",
                "code": "123456",
            },
            format="json",
        )

        self.assertEqual(
            response.status_code,
            400,
        )

        self.assertEqual(
            response.data["code"],
            "TWO_FACTOR_NOT_ENABLED",
        )


    def test_authenticator_change_rejects_invalid_method(self):
        self.enable_2fa()

        response = self.client.post(
            "/api/auth/2fa/authenticator/change/",
            {
                "current_password": "StrongPassword123!",
                "method": "INVALID",
                "code": "123456",
            },
            format="json",
        )

        self.assertEqual(
            response.status_code,
            400,
        )

        self.assertEqual(
            response.data["code"],
            "INVALID_2FA_METHOD",
        )


    def test_authenticator_change_can_be_authorized_with_current_totp(self):
        secret, _ = self.enable_2fa()

        response = self.client.post(
            "/api/auth/2fa/authenticator/change/",
            {
                "current_password": "StrongPassword123!",
                "method": "TOTP",
                "code": pyotp.TOTP(secret).now(),
            },
            format="json",
        )

        self.assertEqual(
            response.status_code,
            200,
        )

        self.assertEqual(
            response.data["status"],
            "success",
        )

        self.assertIn(
            "secret",
            response.data,
        )

        self.assertIn(
            "provisioning_uri",
            response.data,
        )


    def test_authenticator_change_can_be_authorized_with_recovery_code(self):
        _, recovery_codes = self.enable_2fa()

        response = self.client.post(
            "/api/auth/2fa/authenticator/change/",
            {
                "current_password": "StrongPassword123!",
                "method": "RECOVERY_CODE",
                "code": recovery_codes[0],
            },
            format="json",
        )

        self.assertEqual(
            response.status_code,
            200,
        )

        self.assertEqual(
            response.data["status"],
            "success",
        )

        self.assertIn(
            "secret",
            response.data,
        )

        two_factor_auth = (
            UserTwoFactorAuth.objects.get(
                user=self.user
            )
        )

        self.assertEqual(
            TwoFactorRecoveryCode.objects.filter(
                two_factor_auth=two_factor_auth,
                used_at__isnull=True,
            ).count(),
            9,
        )


    def test_new_authenticator_is_stored_as_pending(self):
        old_secret, _ = self.enable_2fa()

        response = self.client.post(
            "/api/auth/2fa/authenticator/change/",
            {
                "current_password": "StrongPassword123!",
                "method": "TOTP",
                "code": pyotp.TOTP(old_secret).now(),
            },
            format="json",
        )

        self.assertEqual(
            response.status_code,
            200,
        )

        new_secret = response.data["secret"]

        self.assertNotEqual(
            old_secret,
            new_secret,
        )

        two_factor_auth = (
            UserTwoFactorAuth.objects.get(
                user=self.user
            )
        )

        self.assertTrue(
            two_factor_auth.is_enabled
        )

        self.assertEqual(
            decrypt_totp_secret(
                two_factor_auth.encrypted_secret
            ),
            old_secret,
        )

        self.assertEqual(
            decrypt_totp_secret(
                two_factor_auth.pending_encrypted_secret
            ),
            new_secret,
        )

        self.assertIsNotNone(
            two_factor_auth.pending_setup_started_at
        )


    def test_current_authenticator_remains_active_until_new_one_is_verified(self):
        old_secret, _ = self.enable_2fa()

        response = self.client.post(
            "/api/auth/2fa/authenticator/change/",
            {
                "current_password": "StrongPassword123!",
                "method": "TOTP",
                "code": pyotp.TOTP(old_secret).now(),
            },
            format="json",
        )

        self.assertEqual(
            response.status_code,
            200,
        )

        new_secret = response.data["secret"]

        two_factor_auth = (
            UserTwoFactorAuth.objects.get(
                user=self.user
            )
        )

        self.assertEqual(
            decrypt_totp_secret(
                two_factor_auth.encrypted_secret
            ),
            old_secret,
        )

        self.assertNotEqual(
            decrypt_totp_secret(
                two_factor_auth.encrypted_secret
            ),
            new_secret,
        )


    def test_authenticator_change_requires_new_authenticator_verification(self):
        old_secret, _ = self.enable_2fa()

        start_response = self.client.post(
            "/api/auth/2fa/authenticator/change/",
            {
                "current_password": "StrongPassword123!",
                "method": "TOTP",
                "code": pyotp.TOTP(old_secret).now(),
            },
            format="json",
        )

        self.assertEqual(
            start_response.status_code,
            200,
        )

        two_factor_auth = (
            UserTwoFactorAuth.objects.get(
                user=self.user
            )
        )

        self.assertEqual(
            decrypt_totp_secret(
                two_factor_auth.encrypted_secret
            ),
            old_secret,
        )

        self.assertIsNotNone(
            two_factor_auth.pending_encrypted_secret
        )


    def test_authenticator_change_rejects_invalid_new_totp(self):
        old_secret, _ = self.enable_2fa()

        start_response = self.client.post(
            "/api/auth/2fa/authenticator/change/",
            {
                "current_password": "StrongPassword123!",
                "method": "TOTP",
                "code": pyotp.TOTP(old_secret).now(),
            },
            format="json",
        )

        self.assertEqual(
            start_response.status_code,
            200,
        )

        response = self.client.post(
            "/api/auth/2fa/authenticator/change/verify/",
            {
                "code": "000000",
            },
            format="json",
        )

        self.assertEqual(
            response.status_code,
            400,
        )

        self.assertEqual(
            response.data["code"],
            "INVALID_CODE",
        )


    def test_authenticator_change_expiration_is_enforced(self):
        old_secret, _ = self.enable_2fa()

        start_response = self.client.post(
            "/api/auth/2fa/authenticator/change/",
            {
                "current_password": "StrongPassword123!",
                "method": "TOTP",
                "code": pyotp.TOTP(old_secret).now(),
            },
            format="json",
        )

        self.assertEqual(
            start_response.status_code,
            200,
        )

        two_factor_auth = (
            UserTwoFactorAuth.objects.get(
                user=self.user
            )
        )

        two_factor_auth.pending_setup_started_at = (
            timezone.now()
            - timedelta(minutes=11)
        )

        two_factor_auth.save(
            update_fields=[
                "pending_setup_started_at",
                "updated_at",
            ]
        )

        response = self.client.post(
            "/api/auth/2fa/authenticator/change/verify/",
            {
                "code": "123456",
            },
            format="json",
        )

        self.assertEqual(
            response.status_code,
            400,
        )

        self.assertEqual(
            response.data["code"],
            "TWO_FACTOR_CHANGE_EXPIRED",
        )


    def test_authenticator_change_verification_locks_after_too_many_failures(self):
        old_secret, _ = self.enable_2fa()

        start_response = self.client.post(
            "/api/auth/2fa/authenticator/change/",
            {
                "current_password": "StrongPassword123!",
                "method": "TOTP",
                "code": pyotp.TOTP(old_secret).now(),
            },
            format="json",
        )

        self.assertEqual(
            start_response.status_code,
            200,
        )

        for _ in range(5):
            response = self.client.post(
                "/api/auth/2fa/authenticator/change/verify/",
                {
                    "code": "000000",
                },
                format="json",
            )

        self.assertEqual(
            response.status_code,
            400,
        )

        self.assertEqual(
            response.data["code"],
            "INVALID_CODE",
        )

        two_factor_auth = (
            UserTwoFactorAuth.objects.get(
                user=self.user
            )
        )

        self.assertEqual(
            two_factor_auth.failed_attempts,
            5,
        )

        self.assertIsNotNone(
            two_factor_auth.locked_until
        )

        response = self.client.post(
            "/api/auth/2fa/authenticator/change/verify/",
            {
                "code": "000000",
            },
            format="json",
        )

        self.assertEqual(
            response.status_code,
            400,
        )

        self.assertEqual(
            response.data["code"],
            "TOO_MANY_ATTEMPTS",
        )


    def test_authenticator_change_verification_promotes_new_secret(self):
        old_secret, _ = self.enable_2fa()

        start_response = self.client.post(
            "/api/auth/2fa/authenticator/change/",
            {
                "current_password": "StrongPassword123!",
                "method": "TOTP",
                "code": pyotp.TOTP(old_secret).now(),
            },
            format="json",
        )

        self.assertEqual(
            start_response.status_code,
            200,
        )

        new_secret = start_response.data["secret"]

        verify_response = self.client.post(
            "/api/auth/2fa/authenticator/change/verify/",
            {
                "code": pyotp.TOTP(new_secret).now(),
            },
            format="json",
        )

        self.assertEqual(
            verify_response.status_code,
            200,
        )

        self.assertEqual(
            verify_response.data["status"],
            "success",
        )

        two_factor_auth = (
            UserTwoFactorAuth.objects.get(
                user=self.user
            )
        )

        self.assertEqual(
            decrypt_totp_secret(
                two_factor_auth.encrypted_secret
            ),
            new_secret,
        )

        self.assertIsNone(
            two_factor_auth.pending_encrypted_secret
        )

        self.assertIsNone(
            two_factor_auth.pending_setup_started_at
        )

        self.assertIsNone(
            two_factor_auth.pending_last_used_time_step
        )


    def test_authenticator_change_records_security_event(self):
        old_secret, _ = self.enable_2fa()

        start_response = self.client.post(
            "/api/auth/2fa/authenticator/change/",
            {
                "current_password": "StrongPassword123!",
                "method": "TOTP",
                "code": pyotp.TOTP(old_secret).now(),
            },
            format="json",
        )

        self.assertEqual(
            start_response.status_code,
            200,
        )

        new_secret = start_response.data["secret"]

        verify_response = self.client.post(
            "/api/auth/2fa/authenticator/change/verify/",
            {
                "code": pyotp.TOTP(new_secret).now(),
            },
            format="json",
        )

        self.assertEqual(
            verify_response.status_code,
            200,
        )

        from apps.accounts.models import SecurityEvent

        self.assertTrue(
            SecurityEvent.objects.filter(
                user=self.user,
                event_type=(
                    SecurityEvent.EventType
                    .TWO_FACTOR_AUTHENTICATOR_CHANGED
                ),
            ).exists()
        )

    def test_disable_2fa_with_valid_totp(self):
        secret, _ = self.enable_2fa()

        response = self.client.post(
            "/api/auth/2fa/disable/",
            {
                "current_password": "StrongPassword123!",
                "method": "TOTP",
                "code": pyotp.TOTP(secret).now(),
            },
            format="json",
        )

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.data["status"], "success")
        self.assertFalse(response.data["enabled"])

        two_factor_auth = UserTwoFactorAuth.objects.get(
            user=self.user
        )

        self.assertFalse(two_factor_auth.is_enabled)
        self.assertEqual(two_factor_auth.encrypted_secret, "")
        self.assertIsNone(two_factor_auth.pending_encrypted_secret)

        self.assertEqual(
            TwoFactorRecoveryCode.objects.filter(
                two_factor_auth=two_factor_auth
            ).count(),
            0,
        )

    def test_disable_2fa_with_valid_recovery_code(self):
        _, recovery_codes = self.enable_2fa()

        response = self.client.post(
            "/api/auth/2fa/disable/",
            {
                "current_password": "StrongPassword123!",
                "method": "RECOVERY_CODE",
                "code": recovery_codes[0],
            },
            format="json",
        )

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.data["status"], "success")
        self.assertFalse(response.data["enabled"])

        two_factor_auth = UserTwoFactorAuth.objects.get(
            user=self.user
        )

        self.assertFalse(two_factor_auth.is_enabled)

        self.assertEqual(
            TwoFactorRecoveryCode.objects.filter(
                two_factor_auth=two_factor_auth
            ).count(),
            0,
        )

    def test_disable_2fa_rejects_wrong_current_password(self):
        secret, _ = self.enable_2fa()

        response = self.client.post(
            "/api/auth/2fa/disable/",
            {
                "current_password": "WrongPassword123!",
                "method": "TOTP",
                "code": pyotp.TOTP(secret).now(),
            },
            format="json",
        )

        self.assertEqual(response.status_code, 400)
        self.assertEqual(
            response.data["code"],
            "INVALID_CURRENT_PASSWORD",
        )

        two_factor_auth = UserTwoFactorAuth.objects.get(
            user=self.user
        )

        self.assertTrue(two_factor_auth.is_enabled)

    def test_disable_2fa_rejects_invalid_totp(self):
        self.enable_2fa()

        response = self.client.post(
            "/api/auth/2fa/disable/",
            {
                "current_password": "StrongPassword123!",
                "method": "TOTP",
                "code": "000000",
            },
            format="json",
        )

        self.assertEqual(response.status_code, 400)
        self.assertEqual(
            response.data["code"],
            "INVALID_CODE",
        )

        two_factor_auth = UserTwoFactorAuth.objects.get(
            user=self.user
        )

        self.assertTrue(two_factor_auth.is_enabled)

    def test_disable_2fa_requires_enabled_2fa(self):
        response = self.client.post(
            "/api/auth/2fa/disable/",
            {
                "current_password": "StrongPassword123!",
                "method": "TOTP",
                "code": "123456",
            },
            format="json",
        )

        self.assertEqual(response.status_code, 400)
        self.assertEqual(
            response.data["code"],
            "TWO_FACTOR_NOT_ENABLED",
        )

    def test_disable_2fa_records_security_event(self):
        from apps.accounts.models import SecurityEvent

        secret, _ = self.enable_2fa()

        response = self.client.post(
            "/api/auth/2fa/disable/",
            {
                "current_password": "StrongPassword123!",
                "method": "TOTP",
                "code": pyotp.TOTP(secret).now(),
            },
            format="json",
        )

        self.assertEqual(response.status_code, 200)

        self.assertTrue(
            SecurityEvent.objects.filter(
                user=self.user,
                event_type=SecurityEvent.EventType.TWO_FACTOR_DISABLED,
            ).exists()
        )
