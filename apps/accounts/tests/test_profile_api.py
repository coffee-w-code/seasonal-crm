from django.contrib.auth import get_user_model

from rest_framework.test import APITestCase


User = get_user_model()


class ProfileAPITests(APITestCase):
    """
    Tests for the authenticated user's profile API.

    These tests verify that:
    - authenticated users can retrieve their profile
    - profile fields can be updated
    - username remains read-only
    - invalid data is rejected
    - unauthenticated users cannot access the profile API
    """

    def setUp(self):
        self.user = User.objects.create_user(
            username="profile_user",
            password="test-password",
            first_name="Shivani",
            last_name="Test",
            email="shivani@example.com",
        )

    def authenticate(self):
        self.client.force_authenticate(
            user=self.user,
        )

    def test_authenticated_user_can_get_profile(self):
        """
        An authenticated user can retrieve their profile information.
        """

        self.authenticate()

        response = self.client.get(
            "/api/auth/profile/",
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
            response.data["user"]["username"],
            "profile_user",
        )

        self.assertEqual(
            response.data["user"]["first_name"],
            "Shivani",
        )

        self.assertEqual(
            response.data["user"]["last_name"],
            "Test",
        )

        self.assertEqual(
            response.data["user"]["email"],
            "shivani@example.com",
        )

    def test_authenticated_user_can_update_profile(self):
        """
        An authenticated user can update their editable profile fields.
        """

        self.authenticate()

        response = self.client.put(
            "/api/auth/profile/",
            {
                "first_name": "New",
                "last_name": "Name",
                "email": "new@example.com",
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

        self.assertEqual(
            response.data["user"]["first_name"],
            "New",
        )

        self.assertEqual(
            response.data["user"]["last_name"],
            "Name",
        )

        self.assertEqual(
            response.data["user"]["email"],
            "new@example.com",
        )

        self.user.refresh_from_db()

        self.assertEqual(
            self.user.first_name,
            "New",
        )

        self.assertEqual(
            self.user.last_name,
            "Name",
        )

        self.assertEqual(
            self.user.email,
            "new@example.com",
        )

    def test_username_cannot_be_changed(self):
        """
        Username must remain read-only through the profile API.
        """

        self.authenticate()

        response = self.client.put(
            "/api/auth/profile/",
            {
                "username": "changed_username",
                "first_name": "Updated",
                "last_name": "User",
                "email": "updated@example.com",
            },
            format="json",
        )

        self.assertEqual(
            response.status_code,
            200,
        )

        self.user.refresh_from_db()

        self.assertEqual(
            self.user.username,
            "profile_user",
        )

        self.assertEqual(
            response.data["user"]["username"],
            "profile_user",
        )

    def test_invalid_email_is_rejected(self):
        """
        An invalid email address must be rejected.
        """

        self.authenticate()

        response = self.client.put(
            "/api/auth/profile/",
            {
                "first_name": "Shivani",
                "last_name": "Test",
                "email": "not-an-email",
            },
            format="json",
        )

        self.assertEqual(
            response.status_code,
            400,
        )

        self.assertEqual(
            response.data["code"],
            "INVALID_EMAIL",
        )

    def test_unauthenticated_user_cannot_access_profile(self):
        """
        Profile APIs require authentication.
        """

        response = self.client.get(
            "/api/auth/profile/",
        )

        self.assertEqual(
            response.status_code,
            403,
        )

    def test_unauthenticated_user_cannot_update_profile(self):
        """
        Unauthenticated users cannot modify profile information.
        """

        response = self.client.put(
            "/api/auth/profile/",
            {
                "first_name": "Hacker",
                "last_name": "User",
                "email": "hacker@example.com",
            },
            format="json",
        )

        self.assertEqual(
            response.status_code,
            403,
        )