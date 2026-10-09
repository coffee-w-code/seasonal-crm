from datetime import timedelta

import pyotp

from django.contrib.auth import get_user_model
from django.utils import timezone

from rest_framework.test import APITestCase

from apps.accounts.models import (
    SecurityEvent,
    TwoFactorRecoveryCode,
    UserSession,
    UserTwoFactorAuth,
)
from apps.accounts.security.recovery_codes import (
    generate_recovery_codes,
    store_recovery_codes,
)
from apps.accounts.security.two_factor import (
    encrypt_totp_secret,
)


User = get_user_model()


class LoginAPITests(APITestCase):
    def setUp(self):
        self.user = User.objects.create_user(
            username="logintest",
            password="StrongPassword123!",
        )

        self.login_url = "/api/auth/login/"
        self.two_factor_login_url = "/api/auth/login/2fa/"

    def enable_two_factor(self):
        secret = pyotp.random_base32()

        two_factor_auth = UserTwoFactorAuth.objects.create(
            user=self.user,
            encrypted_secret=encrypt_totp_secret(secret),
            is_enabled=True,
            enabled_at=timezone.now(),
        )

        return two_factor_auth, secret

    def test_login_without_2fa_succeeds(self):
        response = self.client.post(
            self.login_url,
            {
                "username": "logintest",
                "password": "StrongPassword123!",
            },
            format="json",
        )

        self.assertEqual(response.status_code, 200)
        self.assertEqual(
            response.json()["status"],
            "success",
        )

        self.assertEqual(
            response.json()["user"]["username"],
            "logintest",
        )

        self.assertTrue(
            response.wsgi_request.user.is_authenticated
        )

        self.assertEqual(
            UserSession.objects.filter(
                user=self.user,
                revoked_at__isnull=True,
            ).count(),
            1,
        )

        self.assertEqual(
            SecurityEvent.objects.filter(
                user=self.user,
                event_type=SecurityEvent.EventType.LOGIN,
            ).count(),
            1,
        )

    def test_wrong_password_does_not_start_2fa(self):
        self.enable_two_factor()

        response = self.client.post(
            self.login_url,
            {
                "username": "logintest",
                "password": "WrongPassword123!",
            },
            format="json",
        )

        self.assertEqual(response.status_code, 401)
        self.assertEqual(
            response.json()["code"],
            "INVALID_CREDENTIALS",
        )

        self.assertIsNone(
            self.client.session.get(
                "pending_2fa_user_id"
            )
        )

        self.assertEqual(
            UserSession.objects.filter(
                user=self.user
            ).count(),
            0,
        )

        self.assertEqual(
            SecurityEvent.objects.filter(
                user=self.user
            ).count(),
            0,
        )

    def test_correct_password_with_2fa_returns_2fa_required(self):
        self.enable_two_factor()

        response = self.client.post(
            self.login_url,
            {
                "username": "logintest",
                "password": "StrongPassword123!",
            },
            format="json",
        )

        self.assertEqual(response.status_code, 200)
        self.assertEqual(
            response.json()["status"],
            "2fa_required",
        )
        self.assertEqual(
            response.json()["code"],
            "TWO_FACTOR_REQUIRED",
        )

        self.assertFalse(
            response.wsgi_request.user.is_authenticated
        )

        session = self.client.session

        self.assertEqual(
            session.get("pending_2fa_user_id"),
            self.user.id,
        )

        self.assertIsNotNone(
            session.get("pending_2fa_started_at")
        )

        self.assertEqual(
            UserSession.objects.filter(
                user=self.user
            ).count(),
            0,
        )

        self.assertEqual(
            SecurityEvent.objects.filter(
                user=self.user
            ).count(),
            0,
        )

    def test_invalid_totp_does_not_complete_login(self):
        self.enable_two_factor()

        response = self.client.post(
            self.login_url,
            {
                "username": "logintest",
                "password": "StrongPassword123!",
            },
            format="json",
        )

        self.assertEqual(
            response.json()["code"],
            "TWO_FACTOR_REQUIRED",
        )

        response = self.client.post(
            self.two_factor_login_url,
            {
                "method": "TOTP",
                "code": "000000",
            },
            format="json",
        )

        self.assertEqual(response.status_code, 400)
        self.assertEqual(
            response.json()["code"],
            "INVALID_CODE",
        )

        self.assertFalse(
            response.wsgi_request.user.is_authenticated
        )

        self.assertIsNotNone(
            self.client.session.get(
                "pending_2fa_user_id"
            )
        )

        two_factor_auth = (
            UserTwoFactorAuth.objects.get(
                user=self.user
            )
        )

        self.assertEqual(
            two_factor_auth.failed_attempts,
            1,
        )

        self.assertEqual(
            UserSession.objects.filter(
                user=self.user
            ).count(),
            0,
        )

        self.assertEqual(
            SecurityEvent.objects.filter(
                user=self.user
            ).count(),
            0,
        )

    def test_valid_totp_completes_login(self):
        two_factor_auth, secret = self.enable_two_factor()

        response = self.client.post(
            self.login_url,
            {
                "username": "logintest",
                "password": "StrongPassword123!",
            },
            format="json",
        )

        self.assertEqual(
            response.json()["status"],
            "2fa_required",
        )

        code = pyotp.TOTP(secret).now()

        response = self.client.post(
            self.two_factor_login_url,
            {
                "method": "TOTP",
                "code": code,
            },
            format="json",
        )

        self.assertEqual(response.status_code, 200)
        self.assertEqual(
            response.json()["status"],
            "success",
        )

        self.assertTrue(
            response.wsgi_request.user.is_authenticated
        )

        session = self.client.session

        self.assertIsNone(
            session.get("pending_2fa_user_id")
        )

        self.assertIsNone(
            session.get("pending_2fa_started_at")
        )

        self.assertEqual(
            UserSession.objects.filter(
                user=self.user,
                revoked_at__isnull=True,
            ).count(),
            1,
        )

        self.assertEqual(
            SecurityEvent.objects.filter(
                user=self.user,
                event_type=SecurityEvent.EventType.LOGIN,
            ).count(),
            1,
        )

        two_factor_auth.refresh_from_db()

        self.assertEqual(
            two_factor_auth.failed_attempts,
            0,
        )

        self.assertIsNotNone(
            two_factor_auth.last_verified_at
        )

    def test_recovery_code_completes_login(self):
        two_factor_auth, _ = self.enable_two_factor()

        recovery_codes = generate_recovery_codes()

        store_recovery_codes(
            two_factor_auth,
            recovery_codes,
        )

        response = self.client.post(
            self.login_url,
            {
                "username": "logintest",
                "password": "StrongPassword123!",
            },
            format="json",
        )

        self.assertEqual(
            response.json()["status"],
            "2fa_required",
        )

        recovery_code = recovery_codes[0]

        response = self.client.post(
            self.two_factor_login_url,
            {
                "method": "RECOVERY_CODE",
                "code": recovery_code,
            },
            format="json",
        )

        self.assertEqual(response.status_code, 200)
        self.assertEqual(
            response.json()["status"],
            "success",
        )

        self.assertTrue(
            response.wsgi_request.user.is_authenticated
        )

        used_count = (
            TwoFactorRecoveryCode.objects.filter(
                two_factor_auth=two_factor_auth,
                used_at__isnull=False,
            ).count()
        )

        self.assertEqual(
            used_count,
            1,
        )

        self.assertEqual(
            UserSession.objects.filter(
                user=self.user,
                revoked_at__isnull=True,
            ).count(),
            1,
        )

        self.assertEqual(
            SecurityEvent.objects.filter(
                user=self.user,
                event_type=SecurityEvent.EventType.LOGIN,
            ).count(),
            1,
        )

    def test_recovery_code_cannot_be_reused(self):
        two_factor_auth, _ = self.enable_two_factor()

        recovery_codes = generate_recovery_codes()

        store_recovery_codes(
            two_factor_auth,
            recovery_codes,
        )

        response = self.client.post(
            self.login_url,
            {
                "username": "logintest",
                "password": "StrongPassword123!",
            },
            format="json",
        )

        self.assertEqual(
            response.json()["status"],
            "2fa_required",
        )

        recovery_code = recovery_codes[0]

        response = self.client.post(
            self.two_factor_login_url,
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

        self.client.logout()

        response = self.client.post(
            self.login_url,
            {
                "username": "logintest",
                "password": "StrongPassword123!",
            },
            format="json",
        )

        self.assertEqual(
            response.json()["status"],
            "2fa_required",
        )

        response = self.client.post(
            self.two_factor_login_url,
            {
                "method": "RECOVERY_CODE",
                "code": recovery_code,
            },
            format="json",
        )

        self.assertEqual(response.status_code, 400)
        self.assertEqual(
            response.json()["code"],
            "INVALID_RECOVERY_CODE",
        )

    def test_expired_pending_2fa_is_rejected(self):
        self.enable_two_factor()

        response = self.client.post(
            self.login_url,
            {
                "username": "logintest",
                "password": "StrongPassword123!",
            },
            format="json",
        )

        self.assertEqual(
            response.json()["status"],
            "2fa_required",
        )

        session = self.client.session

        session["pending_2fa_started_at"] = (
            timezone.now().timestamp()
            - 301
        )

        session.save()

        response = self.client.post(
            self.two_factor_login_url,
            {
                "method": "TOTP",
                "code": "123456",
            },
            format="json",
        )

        self.assertEqual(response.status_code, 400)
        self.assertEqual(
            response.json()["code"],
            "TWO_FACTOR_LOGIN_EXPIRED",
        )

        session = self.client.session

        self.assertIsNone(
            session.get("pending_2fa_user_id")
        )

        self.assertIsNone(
            session.get("pending_2fa_started_at")
        )

        self.assertEqual(
            UserSession.objects.filter(
                user=self.user
            ).count(),
            0,
        )

    def test_missing_pending_2fa_is_rejected(self):
        response = self.client.post(
            self.two_factor_login_url,
            {
                "method": "TOTP",
                "code": "123456",
            },
            format="json",
        )

        self.assertEqual(response.status_code, 400)
        self.assertEqual(
            response.json()["code"],
            "TWO_FACTOR_LOGIN_REQUIRED",
        )

        self.assertFalse(
            response.wsgi_request.user.is_authenticated
        )

    def test_invalid_2fa_method_is_rejected(self):
        self.enable_two_factor()

        response = self.client.post(
            self.login_url,
            {
                "username": "logintest",
                "password": "StrongPassword123!",
            },
            format="json",
        )

        self.assertEqual(
            response.json()["status"],
            "2fa_required",
        )

        response = self.client.post(
            self.two_factor_login_url,
            {
                "method": "SMS",
                "code": "123456",
            },
            format="json",
        )

        self.assertEqual(response.status_code, 400)
        self.assertEqual(
            response.json()["code"],
            "INVALID_2FA_METHOD",
        )

    def test_missing_2fa_code_is_rejected(self):
        self.enable_two_factor()

        response = self.client.post(
            self.login_url,
            {
                "username": "logintest",
                "password": "StrongPassword123!",
            },
            format="json",
        )

        self.assertEqual(
            response.json()["status"],
            "2fa_required",
        )

        response = self.client.post(
            self.two_factor_login_url,
            {
                "method": "TOTP",
            },
            format="json",
        )

        self.assertEqual(response.status_code, 400)
        self.assertEqual(
            response.json()["code"],
            "MISSING_2FA_CODE",
        )
