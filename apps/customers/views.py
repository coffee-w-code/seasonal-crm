import json

from django.core.exceptions import PermissionDenied
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_protect
from django.views.decorators.http import (
    require_GET,
    require_http_methods,
    require_POST,
)

from apps.accounts.context import get_current_context

from .services.customer_service import (
    CustomerHasOrdersError,
    CustomerNotFoundError,
    CustomerService,
    CustomerServiceError,
    DuplicateCustomerError,
    InvalidCustomerError,
)


def _serialize_customer(customer):
    """
    Convert a Customer instance into a JSON-safe response.
    """

    return {
        "id": customer.id,
        "store_name": customer.store_name,
        "owner_name": customer.owner_name,
        "phone_number": customer.phone_number,
        "state_region": customer.state_region,
        "gstin": customer.gstin,
        "remaining_balance": str(customer.remaining_balance),
        "created_at": customer.created_at.isoformat(),
        "updated_at": customer.updated_at.isoformat(),
    }


def _authentication_required():
    return JsonResponse(
        {
            "status": "error",
            "code": "AUTHENTICATION_REQUIRED",
            "message": "Authentication is required.",
        },
        status=401,
    )


def _get_current_business(request):
    """
    Resolve the authenticated user's current business.

    The business is determined entirely by trusted backend context.
    The client cannot choose the business.
    """

    try:
        context = get_current_context(request.user)
        return context.business
    except (CustomerServiceError, PermissionDenied):
        raise


def _parse_json_body(request):
    """
    Parse and validate a JSON request body.
    """

    try:
        data = json.loads(request.body)
    except (json.JSONDecodeError, UnicodeDecodeError) as exc:
        raise InvalidCustomerError(
            "Request body must contain valid JSON."
        ) from exc

    if not isinstance(data, dict):
        raise InvalidCustomerError(
            "Request body must contain a JSON object."
        )

    return data


def _handle_service_error(exc):
    """
    Convert service-layer exceptions into stable API responses.
    """

    if isinstance(exc, CustomerNotFoundError):
        return JsonResponse(
            {
                "status": "error",
                "code": "CUSTOMER_NOT_FOUND",
                "message": str(exc),
            },
            status=404,
        )

    if isinstance(exc, DuplicateCustomerError):
        return JsonResponse(
            {
                "status": "error",
                "code": "DUPLICATE_CUSTOMER",
                "message": str(exc),
            },
            status=409,
        )

    if isinstance(exc, CustomerHasOrdersError):
        return JsonResponse(
            {
                "status": "error",
                "code": "CUSTOMER_HAS_ORDERS",
                "message": str(exc),
            },
            status=409,
        )

    if isinstance(exc, InvalidCustomerError):
        return JsonResponse(
            {
                "status": "error",
                "code": "INVALID_CUSTOMER",
                "message": str(exc),
            },
            status=400,
        )

    if isinstance(exc, PermissionDenied):
        return JsonResponse(
            {
                "status": "error",
                "code": "BUSINESS_ACCESS_DENIED",
                "message": "You do not have access to this business.",
            },
            status=403,
        )

    if isinstance(exc, CustomerServiceError):
        return JsonResponse(
            {
                "status": "error",
                "code": "CUSTOMER_OPERATION_FAILED",
                "message": str(exc),
            },
            status=400,
        )

    raise exc


def _get_business_or_response(request):
    """
    Resolve the current business and convert expected context
    failures into an API response.
    """

    try:
        return _get_current_business(request)
    except (
        CustomerServiceError,
        PermissionDenied,
    ) as exc:
        return _handle_service_error(exc)


@require_GET
def customer_list_view(request):
    """
    GET /customers/

    Optional:
        ?search=value
    """

    if not request.user.is_authenticated:
        return _authentication_required()

    business = _get_business_or_response(request)

    if isinstance(business, JsonResponse):
        return business

    try:
        customers = CustomerService.list_customers(
            business=business,
            search=request.GET.get("search"),
        )
    except Exception as exc:
        return _handle_service_error(exc)

    return JsonResponse(
        {
            "status": "success",
            "customers": [
                _serialize_customer(customer)
                for customer in customers
            ],
        },
        status=200,
    )


@require_POST
@csrf_protect
def customer_create_view(request):
    """
    POST /customers/create/
    """

    if not request.user.is_authenticated:
        return _authentication_required()

    business = _get_business_or_response(request)

    if isinstance(business, JsonResponse):
        return business

    try:
        data = _parse_json_body(request)

        allowed_fields = {
            "store_name",
            "owner_name",
            "phone_number",
            "state_region",
            "gstin",
        }

        unexpected_fields = set(data.keys()) - allowed_fields

        if unexpected_fields:
            raise InvalidCustomerError(
                "Unsupported field(s): "
                + ", ".join(sorted(unexpected_fields))
            )

        customer = CustomerService.create_customer(
            business=business,
            store_name=data.get("store_name"),
            owner_name=data.get("owner_name"),
            phone_number=data.get("phone_number"),
            state_region=data.get("state_region"),
            gstin=data.get("gstin"),
        )

    except Exception as exc:
        return _handle_service_error(exc)

    return JsonResponse(
        {
            "status": "success",
            "message": "Customer created successfully.",
            "customer": _serialize_customer(customer),
        },
        status=201,
    )


@require_GET
def customer_detail_view(request, customer_id):
    """
    GET /customers/<customer_id>/
    """

    if not request.user.is_authenticated:
        return _authentication_required()

    business = _get_business_or_response(request)

    if isinstance(business, JsonResponse):
        return business

    try:
        customer = CustomerService.get_customer(
            business=business,
            customer_id=customer_id,
        )
    except Exception as exc:
        return _handle_service_error(exc)

    return JsonResponse(
        {
            "status": "success",
            "customer": _serialize_customer(customer),
        },
        status=200,
    )


@require_http_methods(["PATCH", "PUT"])
@csrf_protect
def customer_update_view(request, customer_id):
    """
    PATCH/PUT /customers/<customer_id>/update/
    """

    if not request.user.is_authenticated:
        return _authentication_required()

    business = _get_business_or_response(request)

    if isinstance(business, JsonResponse):
        return business

    try:
        data = _parse_json_body(request)

        allowed_fields = {
            "store_name",
            "owner_name",
            "phone_number",
            "state_region",
            "gstin",
        }

        unexpected_fields = set(data.keys()) - allowed_fields

        if unexpected_fields:
            raise InvalidCustomerError(
                "Unsupported field(s): "
                + ", ".join(sorted(unexpected_fields))
            )

        customer = CustomerService.update_customer(
            business=business,
            customer_id=customer_id,
            store_name=data.get("store_name"),
            owner_name=data.get("owner_name"),
            phone_number=data.get("phone_number"),
            state_region=data.get("state_region"),
            gstin=data.get("gstin"),
        )

    except Exception as exc:
        return _handle_service_error(exc)

    return JsonResponse(
        {
            "status": "success",
            "message": "Customer updated successfully.",
            "customer": _serialize_customer(customer),
        },
        status=200,
    )


@require_http_methods(["DELETE"])
@csrf_protect
def customer_delete_view(request, customer_id):
    """
    DELETE /customers/<customer_id>/delete/
    """

    if not request.user.is_authenticated:
        return _authentication_required()

    business = _get_business_or_response(request)

    if isinstance(business, JsonResponse):
        return business

    try:
        CustomerService.delete_customer(
            business=business,
            customer_id=customer_id,
        )
    except Exception as exc:
        return _handle_service_error(exc)

    return JsonResponse(
        {
            "status": "success",
            "message": "Customer deleted successfully.",
        },
        status=200,
    )