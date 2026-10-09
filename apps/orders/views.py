import json

from django.core.exceptions import PermissionDenied
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_protect
from django.views.decorators.http import require_GET, require_POST

from apps.accounts.context import get_current_context

from .models import Order
from .services.order_service import (
    CustomerNotFoundError,
    InvalidOrderError,
    OrderService,
    ProductNotFoundError,
)


def _serialize_order(order):
    """
    Convert an Order into a JSON-safe dictionary.

    This serializer is intentionally shared by the
    detail and create endpoints.
    """

    items = []

    for item in order.items.all():
        items.append(
            {
                "id": item.id,
                "product": {
                    "id": item.product.id,
                    "name": item.product.name,
                },
                "quantity": item.quantity,
                "unit_price": str(item.unit_price),
                "discount": str(item.discount),
                "line_total": str(item.line_total),
            }
        )

    return {
        "id": order.id,
        "order_number": order.order_number,
        "customer": {
            "id": order.customer.id,
            "store_name": order.customer.store_name,
            "owner_name": order.customer.owner_name,
        },
        "status": order.status,
        "payment_status": order.payment_status,
        "subtotal": str(order.subtotal),
        "discount": str(order.discount),
        "tax": str(order.tax),
        "total": str(order.total),
        "notes": order.notes,
        "created_by": order.created_by.username,
        "created_at": order.created_at.isoformat(),
        "updated_at": order.updated_at.isoformat(),
        "items": items,
    }


@require_POST
@csrf_protect
def create_order_view(request):
    """
    Create a new DRAFT order.

    Business ownership is determined from the authenticated
    user's explicitly selected current business.

    The client is never allowed to provide the business ID.
    """

    if not request.user.is_authenticated:
        return JsonResponse(
            {
                "status": "error",
                "code": "AUTHENTICATION_REQUIRED",
                "message": "Authentication is required.",
            },
            status=401,
        )

    try:
        data = json.loads(request.body)
    except (json.JSONDecodeError, UnicodeDecodeError):
        return JsonResponse(
            {
                "status": "error",
                "code": "INVALID_JSON",
                "message": "Request body must contain valid JSON.",
            },
            status=400,
        )

    if not isinstance(data, dict):
        return JsonResponse(
            {
                "status": "error",
                "code": "INVALID_REQUEST",
                "message": "Request body must be a JSON object.",
            },
            status=400,
        )

    customer_id = data.get("customer_id")
    items = data.get("items")

    if customer_id is None:
        return JsonResponse(
            {
                "status": "error",
                "code": "MISSING_CUSTOMER",
                "message": "customer_id is required.",
            },
            status=400,
        )

    if items is None:
        return JsonResponse(
            {
                "status": "error",
                "code": "MISSING_ITEMS",
                "message": "items is required.",
            },
            status=400,
        )

    try:
        order = OrderService.create_draft_order(
            user=request.user,
            customer_id=customer_id,
            items=items,
            discount=data.get("discount", "0.00"),
            tax=data.get("tax", "0.00"),
            notes=data.get("notes", ""),
        )

    except PermissionDenied as exc:
        return JsonResponse(
            {
                "status": "error",
                "code": "BUSINESS_CONTEXT_ERROR",
                "message": str(exc),
            },
            status=403,
        )

    except CustomerNotFoundError as exc:
        return JsonResponse(
            {
                "status": "error",
                "code": "CUSTOMER_NOT_FOUND",
                "message": str(exc),
            },
            status=404,
        )

    except ProductNotFoundError as exc:
        return JsonResponse(
            {
                "status": "error",
                "code": "PRODUCT_NOT_FOUND",
                "message": str(exc),
            },
            status=404,
        )

    except InvalidOrderError as exc:
        return JsonResponse(
            {
                "status": "error",
                "code": "INVALID_ORDER",
                "message": str(exc),
            },
            status=400,
        )

    return JsonResponse(
        {
            "status": "success",
            "message": "Order created successfully.",
            "order": _serialize_order(order),
        },
        status=201,
    )


@require_GET
def order_list_view(request):
    """
    Return orders belonging only to the authenticated
    user's current business.
    """

    if not request.user.is_authenticated:
        return JsonResponse(
            {
                "status": "error",
                "code": "AUTHENTICATION_REQUIRED",
                "message": "Authentication is required.",
            },
            status=401,
        )

    try:
        context = get_current_context(request.user)
        business = context.business
    except PermissionDenied as exc:
        return JsonResponse(
            {
                "status": "error",
                "code": "BUSINESS_NOT_FOUND",
                "message": str(exc),
            },
            status=403,
        )

    orders = (
        Order.objects
        .filter(business=business)
        .select_related("customer", "created_by")
        .prefetch_related("items__product")
    )

    return JsonResponse(
        {
            "status": "success",
            "orders": [
                _serialize_order(order)
                for order in orders
            ],
        },
        status=200,
    )


@require_GET
def order_detail_view(request, order_id):
    """
    Return one order only if it belongs to the
    authenticated user's current business.
    """

    if not request.user.is_authenticated:
        return JsonResponse(
            {
                "status": "error",
                "code": "AUTHENTICATION_REQUIRED",
                "message": "Authentication is required.",
            },
            status=401,
        )

    try:
        context = get_current_context(request.user)
        business = context.business
    except PermissionDenied as exc:
        return JsonResponse(
            {
                "status": "error",
                "code": "BUSINESS_NOT_FOUND",
                "message": str(exc),
            },
            status=403,
        )

    try:
        order = (
            Order.objects
            .select_related("customer", "created_by")
            .prefetch_related("items__product")
            .get(
                id=order_id,
                business=business,
            )
        )
    except Order.DoesNotExist:
        return JsonResponse(
            {
                "status": "error",
                "code": "ORDER_NOT_FOUND",
                "message": "Order was not found in the current business.",
            },
            status=404,
        )

    return JsonResponse(
        {
            "status": "success",
            "order": _serialize_order(order),
        },
        status=200,
    )