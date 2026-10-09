from dataclasses import dataclass

from django.core.exceptions import PermissionDenied

from .models import BusinessMembership, UserBusinessContext


@dataclass(frozen=True)
class BusinessContext:
    """
    Immutable representation of the authenticated user's
    currently selected and authorized business context.

    This object is the single tenant-context contract used by
    application services, API views, realtime consumers, and
    AI tools.
    """

    business: object
    membership: BusinessMembership

    @property
    def business_id(self):
        return self.business.id

    @property
    def role(self):
        return self.membership.role


def _require_authenticated_user(user):
    """
    Ensure the supplied user is authenticated.
    """

    if not user or not user.is_authenticated:
        raise PermissionDenied(
            "Authentication is required."
        )


def get_business_membership(
    user,
    business=None,
    *,
    business_id=None,
):
    """
    Return the authenticated user's active membership
    for a specific business.

    This function is used when an operation intentionally
    targets a specific business.

    Security guarantees:
    - User must be authenticated.
    - Business must be active.
    - Membership must be active.
    - Authorization is always checked server-side.
    - No business is implicitly selected.
    """

    _require_authenticated_user(user)

    if business is not None and business_id is not None:
        raise ValueError(
            "Provide either business or business_id, not both."
        )

    if business is None and business_id is None:
        raise ValueError(
            "Either business or business_id must be provided."
        )

    membership_query = (
        BusinessMembership.objects
        .select_related("business")
        .filter(
            user=user,
            is_active=True,
            business__is_active=True,
        )
    )

    if business_id is not None:
        membership_query = membership_query.filter(
            business_id=business_id,
        )
    else:
        membership_query = membership_query.filter(
            business=business,
        )

    try:
        return membership_query.get()
    except BusinessMembership.DoesNotExist as exc:
        raise PermissionDenied(
            "You do not have access to this business."
        ) from exc


def get_current_context(user):
    """
    Resolve the authenticated user's complete tenant context.

    This is the PRIMARY tenant-context resolver.

    Every normal application operation that depends on the
    current business should ultimately use this function.

    Resolution chain:

        User
          ↓
        UserBusinessContext
          ↓
        current_business
          ↓
        BusinessMembership
          ↓
        BusinessContext

    Security guarantees:
    - User must be authenticated.
    - A current business must exist.
    - The current business must still be active.
    - The user must still have an active membership.
    - A stale or unauthorized context is rejected.
    """

    _require_authenticated_user(user)

    try:
        context = (
            UserBusinessContext.objects
            .select_related("current_business")
            .get(user=user)
        )
    except UserBusinessContext.DoesNotExist as exc:
        raise PermissionDenied(
            "No business has been selected."
        ) from exc

    business = context.current_business

    if business is None:
        raise PermissionDenied(
            "No business has been selected."
        )

    try:
        membership = get_business_membership(
            user=user,
            business=business,
        )
    except PermissionDenied as exc:
        raise PermissionDenied(
            "You no longer have access to the selected business."
        ) from exc

    return BusinessContext(
        business=business,
        membership=membership,
    )


def get_current_membership(user):
    """
    Return the authenticated user's active membership
    for the current business.

    Compatibility helper.

    New application code should generally prefer
    get_current_context() when both business and membership
    information may be required.
    """

    return get_current_context(user).membership


def get_current_business(user):
    """
    Return the authenticated user's current business.

    Compatibility/helper API for application code that only
    needs the Business instance.
    """

    return get_current_context(user).business


def set_current_business(user, business):
    """
    Set the authenticated user's current business.

    The business must be:
    - active
    - associated with an active membership for the user

    Authorization is performed before changing the context.

    Returns:
        BusinessMembership
    """

    _require_authenticated_user(user)

    membership = get_business_membership(
        user=user,
        business=business,
    )

    context, _ = UserBusinessContext.objects.get_or_create(
        user=user,
    )

    if context.current_business_id != membership.business_id:
        context.current_business = membership.business
        context.save(
            update_fields=[
                "current_business",
                "updated_at",
            ]
        )

    return membership.business
