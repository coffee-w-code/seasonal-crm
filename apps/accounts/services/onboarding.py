from django.contrib.auth import get_user_model
from django.db import transaction

from apps.accounts.models import (
    BusinessMembership,
    UserBusinessContext,
)
from apps.tenants.models import Business


User = get_user_model()


class OnboardingError(Exception):
    """
    Raised when account/business onboarding cannot be completed.
    """


@transaction.atomic
def create_business_owner(
    *,
    user,
    business_name,
    owner_name,
    phone_number="",
    email="",
    state_region="",
    gstin=None,
):
    """
    Create the authenticated user's first business.

    This operation is atomic:

        Business
            +
        OWNER membership
            +
        Current business context

    Either everything succeeds or the entire transaction rolls back.

    Security:
    - The user must already be authenticated.
    - A user can only complete initial onboarding once.
    - The OWNER role is assigned server-side.
    - The caller cannot choose the membership role.
    - The created membership belongs to the authenticated user.
    - Business ownership cannot be created for another user.
    """

    # ---------------------------------------------------------------
    # AUTHENTICATION
    # ---------------------------------------------------------------

    if not user or not user.is_authenticated:
        raise OnboardingError(
            "Authentication is required."
        )

    # ---------------------------------------------------------------
    # INITIAL ONBOARDING GUARD
    # ---------------------------------------------------------------
    #
    # Initial onboarding is only for users who do not already have
    # an active business membership.
    #
    # Additional businesses, if supported later, must use a separate
    # authorized business-creation workflow.
    #

    if BusinessMembership.objects.filter(
        user=user,
        is_active=True,
        business__is_active=True,
    ).exists():
        raise OnboardingError(
            "You already have a business."
        )

    # ---------------------------------------------------------------
    # NORMALIZE INPUT
    # ---------------------------------------------------------------

    business_name = (business_name or "").strip()
    owner_name = (owner_name or "").strip()
    phone_number = (phone_number or "").strip()
    email = (email or "").strip()
    state_region = (state_region or "").strip()

    if not business_name:
        raise OnboardingError(
            "Business name is required."
        )

    if not owner_name:
        raise OnboardingError(
            "Owner name is required."
        )

    # ---------------------------------------------------------------
    # CREATE BUSINESS
    # ---------------------------------------------------------------

    business = Business.objects.create(
        name=business_name,
        owner_name=owner_name,
        phone_number=phone_number,
        email=email,
        state_region=state_region,
        gstin=gstin,
        is_active=True,
    )

    # ---------------------------------------------------------------
    # CREATE OWNER MEMBERSHIP
    # ---------------------------------------------------------------
    #
    # IMPORTANT:
    # The role is assigned exclusively by the backend.
    # The client cannot choose OWNER / MANAGER / STAFF.
    #

    membership = BusinessMembership.objects.create(
        user=user,
        business=business,
        role=BusinessMembership.Role.OWNER,
        is_active=True,
    )

    # ---------------------------------------------------------------
    # CREATE CURRENT BUSINESS CONTEXT
    # ---------------------------------------------------------------

    UserBusinessContext.objects.create(
        user=user,
        current_business=business,
    )

    return business, membership