from rest_framework import status
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response

from apps.accounts.services.onboarding import (
    OnboardingError,
    create_business_owner,
)


@api_view(["POST"])
@permission_classes([IsAuthenticated])
def create_business_view(request):
    """
    Create the authenticated user's first business.

    The authenticated user automatically becomes OWNER.

    The role is never accepted from the client.
    """

    try:
        business, membership = create_business_owner(
            user=request.user,
            business_name=request.data.get("business_name"),
            owner_name=request.data.get("owner_name"),
            phone_number=request.data.get(
                "phone_number",
                "",
            ),
            email=request.data.get(
                "email",
                "",
            ),
            state_region=request.data.get(
                "state_region",
                "",
            ),
            gstin=request.data.get(
                "gstin",
            ),
        )

    except OnboardingError as exc:
        return Response(
            {
                "status": "error",
                "code": "ONBOARDING_VALIDATION_ERROR",
                "message": str(exc),
            },
            status=status.HTTP_400_BAD_REQUEST,
        )

    return Response(
        {
            "status": "success",
            "message": "Business created successfully.",
            "business": {
                "id": business.id,
                "name": business.name,
                "owner_name": business.owner_name,
            },
            "membership": {
                "role": membership.role,
                "is_active": membership.is_active,
            },
        },
        status=status.HTTP_201_CREATED,
    )