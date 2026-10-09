from io import BytesIO

from PIL import Image
from django.contrib.auth import get_user_model
from django.core.files.uploadedfile import SimpleUploadedFile
from rest_framework.test import APITestCase

from apps.accounts.models import UserProfile


User = get_user_model()


class AvatarAPITests(APITestCase):

    def setUp(self):
        self.user = User.objects.create_user(
            username="avatar_user",
            password="test-password",
            first_name="Shivani",
            last_name="Test",
            email="avatar@example.com",
        )

        self.client.force_authenticate(user=self.user)

    def create_image(self, image_format="PNG"):
        image = Image.new("RGB", (200, 200), "white")

        buffer = BytesIO()
        image.save(buffer, format=image_format)
        buffer.seek(0)

        extension = image_format.lower()

        if image_format == "JPEG":
            extension = "jpg"

        return SimpleUploadedFile(
            f"avatar.{extension}",
            buffer.read(),
            content_type=f"image/{'jpeg' if image_format == 'JPEG' else extension}",
        )

    def test_authenticated_user_can_upload_avatar(self):
        avatar = self.create_image()

        response = self.client.post(
            "/api/auth/profile/avatar/",
            {"avatar": avatar},
            format="multipart",
        )

        self.assertEqual(response.status_code, 200)

        profile = UserProfile.objects.get(user=self.user)

        self.assertTrue(profile.avatar)
        self.assertIn("avatar", response.data["user"])
        self.assertIsNotNone(response.data["user"]["avatar"])

    def test_authenticated_user_can_remove_avatar(self):
        avatar = self.create_image()

        upload_response = self.client.post(
            "/api/auth/profile/avatar/",
            {"avatar": avatar},
            format="multipart",
        )

        self.assertEqual(upload_response.status_code, 200)

        response = self.client.delete(
            "/api/auth/profile/avatar/"
        )

        self.assertEqual(response.status_code, 200)

        profile = UserProfile.objects.get(user=self.user)

        self.assertFalse(profile.avatar)
        self.assertIsNone(response.data["user"]["avatar"])

    def test_upload_requires_file(self):
        response = self.client.post(
            "/api/auth/profile/avatar/",
            {},
            format="multipart",
        )

        self.assertEqual(response.status_code, 400)
        self.assertEqual(
            response.data["code"],
            "AVATAR_REQUIRED",
        )

    def test_invalid_file_is_rejected(self):
        invalid_file = SimpleUploadedFile(
            "avatar.txt",
            b"This is not an image.",
            content_type="text/plain",
        )

        response = self.client.post(
            "/api/auth/profile/avatar/",
            {"avatar": invalid_file},
            format="multipart",
        )

        self.assertEqual(response.status_code, 400)
        self.assertEqual(
            response.data["code"],
            "INVALID_AVATAR",
        )

    def test_unsupported_image_format_is_rejected(self):
        avatar = SimpleUploadedFile(
            "avatar.bmp",
            b"fake bmp content",
            content_type="image/bmp",
        )

        response = self.client.post(
            "/api/auth/profile/avatar/",
            {"avatar": avatar},
            format="multipart",
        )

        self.assertEqual(response.status_code, 400)

    def test_unauthenticated_user_cannot_upload_avatar(self):
        self.client.force_authenticate(user=None)

        avatar = self.create_image()

        response = self.client.post(
            "/api/auth/profile/avatar/",
            {"avatar": avatar},
            format="multipart",
        )

        self.assertEqual(response.status_code, 403)

    def test_unauthenticated_user_cannot_remove_avatar(self):
        self.client.force_authenticate(user=None)

        response = self.client.delete(
            "/api/auth/profile/avatar/"
        )

        self.assertEqual(response.status_code, 403)