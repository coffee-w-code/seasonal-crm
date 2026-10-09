from django.core.exceptions import PermissionDenied

from rest_framework import status
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response

from apps.accounts.context import (
    get_current_context,
    set_current_business,
)
from apps.accounts.models import BusinessMembership
from apps.tenants.models import Business


def _serialize_membership(membership):
    """
    Serialize a business membership for API responses.
    """

    return {
        "id": membership.business.id,
        "name": membership.business.name,
        "role": membership.role,
    }


def _serialize_context(context):
    """
    Serialize the currently active tenant context.
    """

    return {
        "business": {
            "id": context.business.id,
            "name": context.business.name,
        },
        "membership": {
            "role": context.membership.role,
            "is_active": context.membership.is_active,
        },
    }


@api_view(["GET"])
@permission_classes([IsAuthenticated])
def business_list_view(request):
    """
    Return all businesses accessible to the authenticated user.

    Also return the currently selected business context.

    The frontend should use this endpoint to initialize its
    global BusinessContext.
    """

    memberships = (
        BusinessMembership.objects
        .filter(
            user=request.user,
            is_active=True,
            business__is_active=True,
        )
        .select_related("business")
        .order_by(
            "business__name",
            "business__id",
        )
    )

    try:
        context = get_current_context(request.user)
    except PermissionDenied:
        context = None

    return Response(
        {
            "status": "success",
            "current_context": (
                _serialize_context(context)
                if context
                else None
            ),
            "businesses": [
                _serialize_membership(membership)
                for membership in memberships
            ],
        },
        status=status.HTTP_200_OK,
    )


@api_view(["GET"])
@permission_classes([IsAuthenticated])
def current_business_view(request):
    """
    Return the authenticated user's current tenant context.
    """

    try:
        context = get_current_context(request.user)
    except PermissionDenied as exc:
        return Response(
            {
                "status": "error",
                "code": "BUSINESS_CONTEXT_NOT_FOUND",
                "message": str(exc),
            },
            status=status.HTTP_403_FORBIDDEN,
        )

    return Response(
        {
            "status": "success",
            "current_context": _serialize_context(context),
        },
        status=status.HTTP_200_OK,
    )


@api_view(["POST"])
@permission_classes([IsAuthenticated])
def select_business_view(request):
    """
    Change the authenticated user's current business.

    The requested business ID is only an input.

    Authorization is always performed server-side through
    BusinessMembership before the context is changed.
    """

    business_id = request.data.get("business_id")

    if business_id is None:
        return Response(
            {
                "status": "error",
                "code": "MISSING_BUSINESS_ID",
                "message": "business_id is required.",
            },
            status=status.HTTP_400_BAD_REQUEST,
        )

    try:
        business_id = int(business_id)
    except (TypeError, ValueError):
        return Response(
            {
                "status": "error",
                "code": "INVALID_BUSINESS_ID",
                "message": "business_id must be a valid integer.",
            },
            status=status.HTTP_400_BAD_REQUEST,
        )

    try:
        business = (
            Business.objects
            .get(
                id=business_id,
                is_active=True,
            )
        )
    except Business.DoesNotExist:
        return Response(
            {
                "status": "error",
                "code": "BUSINESS_NOT_FOUND",
                "message": "Business was not found.",
            },
            status=status.HTTP_404_NOT_FOUND,
        )

    try:
        membership = set_current_business(
            user=request.user,
            business=business,
        )

        context = get_current_context(request.user)

    except PermissionDenied as exc:
        return Response(
            {
                "status": "error",
                "code": "BUSINESS_ACCESS_DENIED",
                "message": str(exc),
            },
            status=status.HTTP_403_FORBIDDEN,
        )

    return Response(
        {
            "status": "success",
            "message": "Business selected successfully.",
            "current_context": _serialize_context(context),
        },
        status=status.HTTP_200_OK,
    )