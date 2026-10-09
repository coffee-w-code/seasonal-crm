from django.contrib.auth import get_user_model
from django.test import TestCase

from apps.accounts.models import (
    BusinessMembership,
    UserBusinessContext,
)
from apps.accounts.services.onboarding import (
    OnboardingError,
    create_business_owner,
)
from apps.tenants.models import Business


User = get_user_model()


class BusinessOnboardingServiceTests(TestCase):
    """
    Security and business-logic tests for initial onboarding.
    """

    def setUp(self):
        self.user = User.objects.create_user(
            username="newowner",
            password="TestPassword123!",
        )

    # ------------------------------------------------------------------
    # SUCCESS
    # ------------------------------------------------------------------

    def test_first_business_is_created_successfully(self):
        business, membership = create_business_owner(
            user=self.user,
            business_name="Seasonal Fishing",
            owner_name="Test Owner",
            phone_number="9876543210",
            email="owner@example.com",
            state_region="Varanasi",
        )

        self.assertIsNotNone(business)
        self.assertIsNotNone(membership)

        self.assertEqual(
            business.name,
            "Seasonal Fishing",
        )

        self.assertEqual(
            membership.user,
            self.user,
        )

        self.assertEqual(
            membership.business,
            business,
        )

        self.assertEqual(
            membership.role,
            BusinessMembership.Role.OWNER,
        )

        self.assertTrue(
            membership.is_active,
        )

    def test_first_business_becomes_current_business(self):
        business, _ = create_business_owner(
            user=self.user,
            business_name="Seasonal Fishing",
            owner_name="Test Owner",
        )

        context = UserBusinessContext.objects.get(
            user=self.user,
        )

        self.assertEqual(
            context.current_business,
            business,
        )

    def test_first_business_is_active(self):
        business, _ = create_business_owner(
            user=self.user,
            business_name="Seasonal Fishing",
            owner_name="Test Owner",
        )

        self.assertTrue(
            business.is_active,
        )

    # ------------------------------------------------------------------
    # OWNER SECURITY
    # ------------------------------------------------------------------

    def test_client_cannot_choose_membership_role(self):
        """
        The service API does not accept a role argument.

        Ownership is determined entirely by the backend.
        """

        business, membership = create_business_owner(
            user=self.user,
            business_name="Seasonal Fishing",
            owner_name="Test Owner",
        )

        self.assertEqual(
            membership.role,
            BusinessMembership.Role.OWNER,
        )

    # ------------------------------------------------------------------
    # FIRST-ONBOARDING RESTRICTION
    # ------------------------------------------------------------------

    def test_user_cannot_complete_initial_onboarding_twice(self):
        create_business_owner(
            user=self.user,
            business_name="First Business",
            owner_name="Test Owner",
        )

        with self.assertRaises(OnboardingError):
            create_business_owner(
                user=self.user,
                business_name="Second Business",
                owner_name="Test Owner",
            )

        self.assertEqual(
            Business.objects.filter(
                name="First Business",
            ).count(),
            1,
        )

        self.assertFalse(
            Business.objects.filter(
                name="Second Business",
            ).exists(),
        )

    # ------------------------------------------------------------------
    # VALIDATION
    # ------------------------------------------------------------------

    def test_business_name_is_required(self):
        with self.assertRaises(OnboardingError):
            create_business_owner(
                user=self.user,
                business_name="",
                owner_name="Test Owner",
            )

        self.assertEqual(
            Business.objects.count(),
            0,
        )

    def test_owner_name_is_required(self):
        with self.assertRaises(OnboardingError):
            create_business_owner(
                user=self.user,
                business_name="Seasonal Fishing",
                owner_name="",
            )

        self.assertEqual(
            Business.objects.count(),
            0,
        )

    # ------------------------------------------------------------------
    # AUTHENTICATION
    # ------------------------------------------------------------------

    def test_unauthenticated_user_is_rejected(self):
        from django.contrib.auth.models import AnonymousUser

        user = AnonymousUser()

        with self.assertRaises(OnboardingError):
            create_business_owner(
                user=user,
                business_name="Seasonal Fishing",
                owner_name="Test Owner",
            )

        self.assertEqual(
            Business.objects.count(),
            0,
        )

    # ------------------------------------------------------------------
    # TRANSACTIONAL INTEGRITY
    # ------------------------------------------------------------------

    def test_existing_membership_prevents_second_business(self):
        existing_business = Business.objects.create(
            name="Existing Business",
            owner_name="Existing Owner",
        )

        BusinessMembership.objects.create(
            user=self.user,
            business=existing_business,
            role=BusinessMembership.Role.OWNER,
            is_active=True,
        )

        with self.assertRaises(OnboardingError):
            create_business_owner(
                user=self.user,
                business_name="Another Business",
                owner_name="Test Owner",
            )

        self.assertEqual(
            Business.objects.count(),
            1,
        )

    def test_existing_business_owner_cannot_complete_onboarding_again(self):
        """
        A user who already has an active business must not be able
        to create another business through initial onboarding.
        """

        existing_business = Business.objects.create(
            name="Existing Business",
            owner_name="Existing Owner",
            is_active=True,
        )

        BusinessMembership.objects.create(
            user=self.user,
            business=existing_business,
            role=BusinessMembership.Role.OWNER,
            is_active=True,
        )

        with self.assertRaises(OnboardingError) as context:
            create_business_owner(
                user=self.user,
                business_name="Second Business",
                owner_name="Test Owner",
            )

        self.assertEqual(
            str(context.exception),
            "You already have a business.",
        )

        self.assertFalse(
            Business.objects.filter(
                name="Second Business",
            ).exists()
        )

        self.assertFalse(
            BusinessMembership.objects.filter(
                user=self.user,
                business__name="Second Business",
            ).exists()
        )