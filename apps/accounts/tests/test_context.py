from django.contrib.auth import get_user_model
from django.core.exceptions import PermissionDenied
from django.test import TestCase

from apps.accounts.context import (
    get_business_membership,
    get_current_business,
    get_current_membership,
    set_current_business,
)
from apps.accounts.models import (
    BusinessMembership,
    UserBusinessContext,
)
from apps.tenants.models import Business


User = get_user_model()


class CurrentBusinessContextTests(TestCase):
    """
    Security tests for the application's central business-context resolver.

    These tests verify:
    - authentication requirements
    - explicit business selection
    - active business validation
    - active membership validation
    - tenant isolation
    - safe business switching
    - protection against implicit business selection
    """

    def setUp(self):
        self.user = User.objects.create_user(
            username="testowner",
            password="TestPassword123!",
        )

        self.other_user = User.objects.create_user(
            username="otheruser",
            password="TestPassword123!",
        )

        self.business = Business.objects.create(
            name="Test Fishing Business",
            owner_name="Test Owner",
        )

        self.other_business = Business.objects.create(
            name="Other Business",
            owner_name="Other Owner",
        )

        self.membership = BusinessMembership.objects.create(
            user=self.user,
            business=self.business,
            role=BusinessMembership.Role.OWNER,
            is_active=True,
        )

        self.other_membership = BusinessMembership.objects.create(
            user=self.user,
            business=self.other_business,
            role=BusinessMembership.Role.OWNER,
            is_active=True,
        )

    # ------------------------------------------------------------------
    # AUTHENTICATION
    # ------------------------------------------------------------------

    def test_get_current_membership_requires_authentication(self):
        from django.contrib.auth.models import AnonymousUser

        user = AnonymousUser()

        with self.assertRaises(PermissionDenied):
            get_current_membership(user)

    def test_get_current_business_requires_authentication(self):
        from django.contrib.auth.models import AnonymousUser

        user = AnonymousUser()

        with self.assertRaises(PermissionDenied):
            get_current_business(user)

    def test_get_business_membership_requires_authentication(self):
        from django.contrib.auth.models import AnonymousUser

        user = AnonymousUser()

        with self.assertRaises(PermissionDenied):
            get_business_membership(
                user,
                self.business,
            )

    # ------------------------------------------------------------------
    # CURRENT BUSINESS SELECTION
    # ------------------------------------------------------------------

    def test_no_selected_business_is_rejected(self):
        with self.assertRaises(PermissionDenied):
            get_current_membership(self.user)

    def test_current_business_requires_explicit_selection(self):
        with self.assertRaises(PermissionDenied):
            get_current_business(self.user)

    def test_selected_business_is_returned(self):
        set_current_business(
            self.user,
            self.business,
        )

        result = get_current_business(self.user)

        self.assertEqual(
            result,
            self.business,
        )

    def test_selected_membership_is_returned(self):
        set_current_business(
            self.user,
            self.business,
        )

        result = get_current_membership(self.user)

        self.assertEqual(
            result,
            self.membership,
        )

    # ------------------------------------------------------------------
    # MEMBERSHIP SECURITY
    # ------------------------------------------------------------------

    def test_user_without_membership_cannot_get_current_business(self):
        user = User.objects.create_user(
            username="nomembership",
            password="TestPassword123!",
        )

        with self.assertRaises(PermissionDenied):
            get_current_business(user)

    def test_inactive_membership_is_rejected(self):
        set_current_business(
            self.user,
            self.business,
        )

        self.membership.is_active = False
        self.membership.save(update_fields=["is_active"])

        with self.assertRaises(PermissionDenied):
            get_current_business(self.user)

    def test_inactive_membership_cannot_be_selected(self):
        self.membership.is_active = False
        self.membership.save(update_fields=["is_active"])

        with self.assertRaises(PermissionDenied):
            set_current_business(
                self.user,
                self.business,
            )

    def test_user_cannot_access_business_without_membership(self):
        with self.assertRaises(PermissionDenied):
            get_business_membership(
                self.other_user,
                self.business,
            )

    # ------------------------------------------------------------------
    # BUSINESS SECURITY
    # ------------------------------------------------------------------

    def test_inactive_business_is_rejected(self):
        set_current_business(
            self.user,
            self.business,
        )

        self.business.is_active = False
        self.business.save(update_fields=["is_active"])

        with self.assertRaises(PermissionDenied):
            get_current_business(self.user)

    def test_inactive_business_cannot_be_selected(self):
        self.business.is_active = False
        self.business.save(update_fields=["is_active"])

        with self.assertRaises(PermissionDenied):
            set_current_business(
                self.user,
                self.business,
            )

    # ------------------------------------------------------------------
    # TENANT ISOLATION
    # ------------------------------------------------------------------

    def test_user_cannot_select_unrelated_business(self):
        unrelated_business = Business.objects.create(
            name="Unrelated Business",
            owner_name="Unrelated Owner",
        )

        with self.assertRaises(PermissionDenied):
            set_current_business(
                self.user,
                unrelated_business,
            )

    def test_selected_business_must_belong_to_current_user(self):
        UserBusinessContext.objects.create(
            user=self.user,
            current_business=self.other_business,
        )

        # The user actually has membership in other_business in this test
        # setup, so this should succeed.
        result = get_current_business(self.user)

        self.assertEqual(
            result,
            self.other_business,
        )

    # ------------------------------------------------------------------
    # BUSINESS SWITCHING
    # ------------------------------------------------------------------

    def test_user_can_switch_between_authorized_businesses(self):
        set_current_business(
            self.user,
            self.business,
        )

        self.assertEqual(
            get_current_business(self.user),
            self.business,
        )

        set_current_business(
            self.user,
            self.other_business,
        )

        self.assertEqual(
            get_current_business(self.user),
            self.other_business,
        )

    def test_switching_business_updates_existing_context(self):
        set_current_business(
            self.user,
            self.business,
        )

        set_current_business(
            self.user,
            self.other_business,
        )

        context = UserBusinessContext.objects.get(
            user=self.user,
        )

        self.assertEqual(
            context.current_business,
            self.other_business,
        )

    # ------------------------------------------------------------------
    # NO IMPLICIT BUSINESS SELECTION
    # ------------------------------------------------------------------

    def test_multiple_memberships_do_not_auto_select_business(self):
        """
        Having multiple memberships must never cause the application
        to silently choose the first business.
        """

        with self.assertRaises(PermissionDenied):
            get_current_business(self.user)

    def test_get_business_membership_returns_only_requested_business(self):
        result = get_business_membership(
            self.user,
            self.other_business,
        )

        self.assertEqual(
            result.business,
            self.other_business,
        )

        self.assertNotEqual(
            result.business,
            self.business,
        )

    # ------------------------------------------------------------------
    # CONTEXT PERSISTENCE
    # ------------------------------------------------------------------

    def test_set_current_business_creates_context(self):
        set_current_business(
            self.user,
            self.business,
        )

        self.assertTrue(
            UserBusinessContext.objects.filter(
                user=self.user,
                current_business=self.business,
            ).exists()
        )

    def test_set_current_business_returns_business(self):
        result = set_current_business(
            self.user,
            self.business,
        )

        self.assertEqual(
            result,
            self.business,
        )