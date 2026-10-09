from django.contrib.auth import get_user_model
from rest_framework.test import APITestCase

User = get_user_model()


class ChangePasswordAPITests(APITestCase):
    def setUp(self):
        self.user = User.objects.create_user(
            username="passwordtest",
            password="OldPassword123!",
        )

        self.client.force_authenticate(user=self.user)

    def test_change_password_successfully(self):
        response = self.client.post(
            "/api/auth/change-password/",
            {
                "current_password": "OldPassword123!",
                "new_password": "NewPassword456!",
                "confirm_password": "NewPassword456!",
            },
            format="json",
        )

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.data["status"], "success")

        self.user.refresh_from_db()

        self.assertTrue(
            self.user.check_password("NewPassword456!")
        )

    def test_current_password_is_required(self):
        response = self.client.post(
            "/api/auth/change-password/",
            {
                "new_password": "NewPassword456!",
                "confirm_password": "NewPassword456!",
            },
            format="json",
        )

        self.assertEqual(response.status_code, 400)
        self.assertEqual(
            response.data["code"],
            "CURRENT_PASSWORD_REQUIRED",
        )

    def test_new_password_is_required(self):
        response = self.client.post(
            "/api/auth/change-password/",
            {
                "current_password": "OldPassword123!",
                "confirm_password": "NewPassword456!",
            },
            format="json",
        )

        self.assertEqual(response.status_code, 400)
        self.assertEqual(
            response.data["code"],
            "NEW_PASSWORD_REQUIRED",
        )

    def test_confirm_password_is_required(self):
        response = self.client.post(
            "/api/auth/change-password/",
            {
                "current_password": "OldPassword123!",
                "new_password": "NewPassword456!",
            },
            format="json",
        )

        self.assertEqual(response.status_code, 400)
        self.assertEqual(
            response.data["code"],
            "CONFIRM_PASSWORD_REQUIRED",
        )

    def test_current_password_must_be_correct(self):
        response = self.client.post(
            "/api/auth/change-password/",
            {
                "current_password": "WrongPassword123!",
                "new_password": "NewPassword456!",
                "confirm_password": "NewPassword456!",
            },
            format="json",
        )

        self.assertEqual(response.status_code, 400)
        self.assertEqual(
            response.data["code"],
            "INVALID_CURRENT_PASSWORD",
        )

    def test_new_passwords_must_match(self):
        response = self.client.post(
            "/api/auth/change-password/",
            {
                "current_password": "OldPassword123!",
                "new_password": "NewPassword456!",
                "confirm_password": "DifferentPassword789!",
            },
            format="json",
        )

        self.assertEqual(response.status_code, 400)
        self.assertEqual(
            response.data["code"],
            "PASSWORD_MISMATCH",
        )

    def test_new_password_cannot_be_same_as_current_password(self):
        response = self.client.post(
            "/api/auth/change-password/",
            {
                "current_password": "OldPassword123!",
                "new_password": "OldPassword123!",
                "confirm_password": "OldPassword123!",
            },
            format="json",
        )

        self.assertEqual(response.status_code, 400)
        self.assertEqual(
            response.data["code"],
            "PASSWORD_UNCHANGED",
        )

    def test_new_password_must_pass_django_password_validators(self):
        response = self.client.post(
            "/api/auth/change-password/",
            {
                "current_password": "OldPassword123!",
                "new_password": "short",
                "confirm_password": "short",
            },
            format="json",
        )

        self.assertEqual(response.status_code, 400)
        self.assertEqual(
            response.data["code"],
            "INVALID_NEW_PASSWORD",
        )

    def test_unauthenticated_user_cannot_change_password(self):
        self.client.force_authenticate(user=None)

        response = self.client.post(
            "/api/auth/change-password/",
            {
                "current_password": "OldPassword123!",
                "new_password": "NewPassword456!",
                "confirm_password": "NewPassword456!",
            },
            format="json",
        )

        self.assertEqual(response.status_code, 403)