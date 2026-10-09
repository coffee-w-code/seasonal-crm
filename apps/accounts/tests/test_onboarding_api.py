from django.contrib.auth import get_user_model

from rest_framework.test import APITestCase

from apps.accounts.models import (
    BusinessMembership,
    UserBusinessContext,
)
from apps.tenants.models import Business


User = get_user_model()


class BusinessOnboardingAPITests(APITestCase):
    """
    Security and behavior tests for:

        POST /api/auth/onboarding/business/

    The endpoint creates the authenticated user's first business,
    assigns OWNER membership, and establishes the current business
    context.
    """

    def setUp(self):
        self.user = User.objects.create_user(
            username="onboarding_user",
            password="TestPassword123!",
        )

        self.other_user = User.objects.create_user(
            username="other_user",
            password="TestPassword123!",
        )

        self.url = "/api/auth/onboarding/business/"

    def authenticate(self):
        self.client.force_authenticate(
            user=self.user,
        )

    # ------------------------------------------------------------------
    # SUCCESS
    # ------------------------------------------------------------------

    def test_authenticated_user_can_create_first_business(self):
        self.authenticate()

        response = self.client.post(
            self.url,
            {
                "business_name": "Seasonal Fishing",
                "owner_name": "Test Owner",
                "phone_number": "9876543210",
                "email": "owner@example.com",
                "state_region": "Varanasi",
            },
            format="json",
        )

        self.assertEqual(
            response.status_code,
            201,
        )

        self.assertEqual(
            response.data["status"],
            "success",
        )

        self.assertEqual(
            response.data["message"],
            "Business created successfully.",
        )

        business = Business.objects.get(
            name="Seasonal Fishing",
        )

        self.assertEqual(
            response.data["business"]["id"],
            business.id,
        )

        self.assertEqual(
            response.data["business"]["name"],
            "Seasonal Fishing",
        )

        self.assertEqual(
            response.data["business"]["owner_name"],
            "Test Owner",
        )

    def test_created_business_has_owner_membership(self):
        self.authenticate()

        response = self.client.post(
            self.url,
            {
                "business_name": "Seasonal Fishing",
                "owner_name": "Test Owner",
            },
            format="json",
        )

        self.assertEqual(
            response.status_code,
            201,
        )

        business_id = response.data["business"]["id"]

        membership = BusinessMembership.objects.get(
            user=self.user,
            business_id=business_id,
        )

        self.assertEqual(
            membership.role,
            BusinessMembership.Role.OWNER,
        )

        self.assertTrue(
            membership.is_active,
        )

    def test_created_business_becomes_current_context(self):
        self.authenticate()

        response = self.client.post(
            self.url,
            {
                "business_name": "Seasonal Fishing",
                "owner_name": "Test Owner",
            },
            format="json",
        )

        self.assertEqual(
            response.status_code,
            201,
        )

        business_id = response.data["business"]["id"]

        context = UserBusinessContext.objects.get(
            user=self.user,
        )

        self.assertEqual(
            context.current_business_id,
            business_id,
        )

    # ------------------------------------------------------------------
    # AUTHENTICATION
    # ------------------------------------------------------------------

    def test_unauthenticated_user_cannot_create_business(self):
        response = self.client.post(
            self.url,
            {
                "business_name": "Unauthorized Business",
                "owner_name": "Unauthorized Owner",
            },
            format="json",
        )

        self.assertEqual(
            response.status_code,
            403,
        )

        self.assertFalse(
            Business.objects.filter(
                name="Unauthorized Business",
            ).exists(),
        )

    # ------------------------------------------------------------------
    # FIRST-ONBOARDING RESTRICTION
    # ------------------------------------------------------------------

    def test_user_cannot_create_second_business_through_onboarding(self):
        self.authenticate()

        first_response = self.client.post(
            self.url,
            {
                "business_name": "First Business",
                "owner_name": "Test Owner",
            },
            format="json",
        )

        self.assertEqual(
            first_response.status_code,
            201,
        )

        second_response = self.client.post(
            self.url,
            {
                "business_name": "Second Business",
                "owner_name": "Test Owner",
            },
            format="json",
        )

        self.assertEqual(
            second_response.status_code,
            400,
        )

        self.assertEqual(
            second_response.data["code"],
            "ONBOARDING_VALIDATION_ERROR",
        )

        self.assertFalse(
            Business.objects.filter(
                name="Second Business",
            ).exists(),
        )

        self.assertEqual(
            Business.objects.filter(
                memberships__user=self.user,
            ).count(),
            1,
        )

    # ------------------------------------------------------------------
    # VALIDATION
    # ------------------------------------------------------------------

    def test_missing_business_name_is_rejected(self):
        self.authenticate()

        response = self.client.post(
            self.url,
            {
                "owner_name": "Test Owner",
            },
            format="json",
        )

        self.assertEqual(
            response.status_code,
            400,
        )

        self.assertEqual(
            response.data["code"],
            "ONBOARDING_VALIDATION_ERROR",
        )

        self.assertEqual(
            Business.objects.count(),
            0,
        )

    def test_missing_owner_name_is_rejected(self):
        self.authenticate()

        response = self.client.post(
            self.url,
            {
                "business_name": "Seasonal Fishing",
            },
            format="json",
        )

        self.assertEqual(
            response.status_code,
            400,
        )

        self.assertEqual(
            response.data["code"],
            "ONBOARDING_VALIDATION_ERROR",
        )

        self.assertEqual(
            Business.objects.count(),
            0,
        )

    # ------------------------------------------------------------------
    # ROLE SECURITY
    # ------------------------------------------------------------------

    def test_client_cannot_choose_membership_role(self):
        self.authenticate()

        response = self.client.post(
            self.url,
            {
                "business_name": "Seasonal Fishing",
                "owner_name": "Test Owner",
                "role": "STAFF",
            },
            format="json",
        )

        self.assertEqual(
            response.status_code,
            201,
        )

        business_id = response.data["business"]["id"]

        membership = BusinessMembership.objects.get(
            user=self.user,
            business_id=business_id,
        )

        self.assertEqual(
            membership.role,
            BusinessMembership.Role.OWNER,
        )

    # ------------------------------------------------------------------
    # TENANT ISOLATION
    # ------------------------------------------------------------------

    def test_onboarding_does_not_create_membership_for_another_user(self):
        self.authenticate()

        response = self.client.post(
            self.url,
            {
                "business_name": "My Business",
                "owner_name": "Test Owner",
            },
            format="json",
        )

        self.assertEqual(
            response.status_code,
            201,
        )

        business_id = response.data["business"]["id"]

        self.assertTrue(
            BusinessMembership.objects.filter(
                user=self.user,
                business_id=business_id,
            ).exists()
        )

        self.assertFalse(
            BusinessMembership.objects.filter(
                user=self.other_user,
                business_id=business_id,
            ).exists()
        )

    # ------------------------------------------------------------------
    # INPUT NORMALIZATION
    # ------------------------------------------------------------------

    def test_business_and_owner_names_are_trimmed(self):
        self.authenticate()

        response = self.client.post(
            self.url,
            {
                "business_name": "   Seasonal Fishing   ",
                "owner_name": "   Test Owner   ",
            },
            format="json",
        )

        self.assertEqual(
            response.status_code,
            201,
        )

        business = Business.objects.get(
            id=response.data["business"]["id"],
        )

        self.assertEqual(
            business.name,
            "Seasonal Fishing",
        )

        self.assertEqual(
            business.owner_name,
            "Test Owner",
        )