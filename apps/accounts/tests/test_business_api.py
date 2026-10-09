from django.contrib.auth import get_user_model

from rest_framework.test import APITestCase

from apps.accounts.models import (
    BusinessMembership,
    UserBusinessContext,
)
from apps.tenants.models import Business


User = get_user_model()


class BusinessContextAPITests(APITestCase):
    """
    Tests for the global business / tenant-context API.

    These tests verify that:
    - users only see businesses they can access
    - current business is correctly returned
    - authorized business switching works
    - unauthorized switching is rejected
    - inactive memberships are rejected
    - inactive businesses are rejected
    """

    def setUp(self):
        self.user = User.objects.create_user(
            username="business_context_user",
            password="test-password",
        )

        self.other_user = User.objects.create_user(
            username="other_business_user",
            password="test-password",
        )

        self.business_a = Business.objects.create(
            name="Business A",
            is_active=True,
        )

        self.business_b = Business.objects.create(
            name="Business B",
            is_active=True,
        )

        self.business_c = Business.objects.create(
            name="Business C",
            is_active=True,
        )

        BusinessMembership.objects.create(
            user=self.user,
            business=self.business_a,
            role=BusinessMembership.Role.OWNER,
            is_active=True,
        )

        BusinessMembership.objects.create(
            user=self.user,
            business=self.business_b,
            role=BusinessMembership.Role.MANAGER,
            is_active=True,
        )

        BusinessMembership.objects.create(
            user=self.other_user,
            business=self.business_c,
            role=BusinessMembership.Role.OWNER,
            is_active=True,
        )

        UserBusinessContext.objects.create(
            user=self.user,
            current_business=self.business_a,
        )

    def authenticate(self):
        self.client.force_authenticate(
            user=self.user,
        )

    def test_business_list_returns_only_accessible_businesses(self):
        """
        A user must only receive businesses for which they have
        an active membership.
        """

        self.authenticate()

        response = self.client.get(
            "/api/auth/businesses/",
        )

        self.assertEqual(
            response.status_code,
            200,
        )

        self.assertEqual(
            response.data["status"],
            "success",
        )

        business_ids = {
            business["id"]
            for business in response.data["businesses"]
        }

        self.assertEqual(
            business_ids,
            {
                self.business_a.id,
                self.business_b.id,
            },
        )

        self.assertNotIn(
            self.business_c.id,
            business_ids,
        )

    def test_business_list_returns_current_context(self):
        """
        The business list endpoint must return the user's
        currently selected business.
        """

        self.authenticate()

        response = self.client.get(
            "/api/auth/businesses/",
        )

        self.assertEqual(
            response.status_code,
            200,
        )

        current_context = response.data["current_context"]

        self.assertIsNotNone(
            current_context,
        )

        self.assertEqual(
            current_context["business"]["id"],
            self.business_a.id,
        )

        self.assertEqual(
            current_context["membership"]["role"],
            BusinessMembership.Role.OWNER,
        )

    def test_current_business_endpoint_returns_context(self):
        """
        The current-business endpoint must return the complete
        active tenant context.
        """

        self.authenticate()

        response = self.client.get(
            "/api/auth/businesses/current/",
        )

        self.assertEqual(
            response.status_code,
            200,
        )

        self.assertEqual(
            response.data["status"],
            "success",
        )

        context = response.data["current_context"]

        self.assertEqual(
            context["business"]["id"],
            self.business_a.id,
        )

        self.assertEqual(
            context["membership"]["role"],
            BusinessMembership.Role.OWNER,
        )

    def test_authorized_user_can_switch_business(self):
        """
        A user can switch to another business when they have
        an active membership for it.
        """

        self.authenticate()

        response = self.client.post(
            "/api/auth/businesses/select/",
            {
                "business_id": self.business_b.id,
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
            response.data["current_context"]["business"]["id"],
            self.business_b.id,
        )

        context = UserBusinessContext.objects.get(
            user=self.user,
        )

        self.assertEqual(
            context.current_business_id,
            self.business_b.id,
        )

    def test_user_cannot_switch_to_unauthorized_business(self):
        """
        A user must not be able to select a business for which
        they have no membership.
        """

        self.authenticate()

        response = self.client.post(
            "/api/auth/businesses/select/",
            {
                "business_id": self.business_c.id,
            },
            format="json",
        )

        self.assertEqual(
            response.status_code,
            403,
        )

        self.assertEqual(
            response.data["code"],
            "BUSINESS_ACCESS_DENIED",
        )

        context = UserBusinessContext.objects.get(
            user=self.user,
        )

        self.assertEqual(
            context.current_business_id,
            self.business_a.id,
        )

    def test_inactive_membership_cannot_be_selected(self):
        """
        An inactive membership must immediately prevent switching
        to that business.
        """

        membership = BusinessMembership.objects.get(
            user=self.user,
            business=self.business_b,
        )

        membership.is_active = False
        membership.save(
            update_fields=["is_active"],
        )

        self.authenticate()

        response = self.client.post(
            "/api/auth/businesses/select/",
            {
                "business_id": self.business_b.id,
            },
            format="json",
        )

        self.assertEqual(
            response.status_code,
            403,
        )

        self.assertEqual(
            response.data["code"],
            "BUSINESS_ACCESS_DENIED",
        )

    def test_inactive_business_cannot_be_selected(self):
        """
        An inactive business must not be selectable even when
        the user has an active membership.
        """

        self.business_b.is_active = False
        self.business_b.save(
            update_fields=["is_active"],
        )

        self.authenticate()

        response = self.client.post(
            "/api/auth/businesses/select/",
            {
                "business_id": self.business_b.id,
            },
            format="json",
        )

        self.assertEqual(
            response.status_code,
            404,
        )

        self.assertEqual(
            response.data["code"],
            "BUSINESS_NOT_FOUND",
        )

    def test_missing_business_id_is_rejected(self):
        """
        A business switch request must contain business_id.
        """

        self.authenticate()

        response = self.client.post(
            "/api/auth/businesses/select/",
            {},
            format="json",
        )

        self.assertEqual(
            response.status_code,
            400,
        )

        self.assertEqual(
            response.data["code"],
            "MISSING_BUSINESS_ID",
        )

    def test_invalid_business_id_is_rejected(self):
        """
        business_id must be a valid integer.
        """

        self.authenticate()

        response = self.client.post(
            "/api/auth/businesses/select/",
            {
                "business_id": "not-a-number",
            },
            format="json",
        )

        self.assertEqual(
            response.status_code,
            400,
        )

        self.assertEqual(
            response.data["code"],
            "INVALID_BUSINESS_ID",
        )

    def test_unauthenticated_user_cannot_access_businesses(self):
        """
        Business context APIs require authentication.
        """

        response = self.client.get(
            "/api/auth/businesses/",
        )

        self.assertEqual(
            response.status_code,
            403,
        )

    def test_switch_persists_across_requests(self):
        """
        After switching, subsequent requests must resolve the
        newly selected business.
        """

        self.authenticate()

        switch_response = self.client.post(
            "/api/auth/businesses/select/",
            {
                "business_id": self.business_b.id,
            },
            format="json",
        )

        self.assertEqual(
            switch_response.status_code,
            200,
        )

        current_response = self.client.get(
            "/api/auth/businesses/current/",
        )

        self.assertEqual(
            current_response.status_code,
            200,
        )

        self.assertEqual(
            current_response.data["current_context"]["business"]["id"],
            self.business_b.id,
        )