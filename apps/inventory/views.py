from django.core.exceptions import PermissionDenied
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
import json

from apps.accounts.context import get_current_context

from .services.assistant import process_voice_onboarding

from .services.inventory_service import InventoryService, InventoryServiceError


from .services.reconciliation import (
    calculate_stock_discrepancy,
    commit_investigation_log,
)

@csrf_exempt
def test_voice_assistant(request):
    """
    Temporary endpoint for testing the voice assistant
    logic using text instead of realtime audio.
    """

    if request.method == "POST":
        try:
            data = json.loads(request.body)

            spoken_text = data.get("text")
            session_data = data.get("session")

            if not spoken_text:
                return JsonResponse(
                    {"error": "No text provided"},
                    status=400,
                )

            result = process_voice_onboarding(
                spoken_text,
                session_data,
            )

            return JsonResponse(result)

        except json.JSONDecodeError:
            return JsonResponse(
                {"error": "Invalid JSON body."},
                status=400,
            )

        except Exception as exc:
            return JsonResponse(
                {"error": str(exc)},
                status=500,
            )

    return JsonResponse(
        {
            "message": (
                "Please send a POST request with "
                "{'text': 'your hindi sentence here'}."
            )
        }
    )

def inventory_list_view(request):
    """
    Return inventory belonging to the authenticated user's business.
    """

    if request.method != "GET":
        return JsonResponse(
            {
                "status": "error",
                "message": "Only GET requests are allowed.",
            },
            status=405,
        )

    try:
        context = get_current_context(request.user)
        business = context.business
    except PermissionDenied as exc:
        return JsonResponse(
            {
                "status": "error",
                "code": "BUSINESS_CONTEXT_ERROR",
                "message": str(exc),
            },
            status=403,
        )

    inventory_items = InventoryService.list_inventory(
        business=business,
    )

    inventory = []

    for item in inventory_items:
        inventory.append(
            {
                "id": item.id,
                "product": {
                    "id": item.product.id,
                    "name": item.product.name,
                    "twine_number": item.product.twine_number,
                    "mesh_size": item.product.mesh_size,
                    "color": item.product.color,
                },
                "location": item.location,
                "quantity": item.quantity,
                "last_updated": item.last_updated.isoformat(),
            }
        )

    return JsonResponse(
        {
            "status": "success",
            "business": {
                "id": business.id,
                "name": business.name,
            },
            "inventory": inventory,
        }
    )

def movement_history_view(request):
    """
    Return stock movement history for the authenticated user's business.
    """

    if request.method != "GET":
        return JsonResponse(
            {
                "status": "error",
                "message": "Only GET requests are allowed.",
            },
            status=405,
        )

    try:
       context = get_current_context(request.user)
       business = context.business
    except PermissionDenied as exc:
        return JsonResponse(
            {
                "status": "error",
                "code": "BUSINESS_CONTEXT_ERROR",
                "message": str(exc),
            },
            status=403,
        )

    try:
        product_id = request.GET.get("product_id")
        limit = request.GET.get("limit", 50)

        if product_id:
            try:
                product_id = int(product_id)
            except (TypeError, ValueError):
                return JsonResponse(
                    {
                        "status": "error",
                        "code": "INVALID_PRODUCT_ID",
                        "message": "product_id must be a valid number.",
                    },
                    status=400,
                )
        else:
            product_id = None

        try:
            limit = int(limit)
        except (TypeError, ValueError):
            return JsonResponse(
                {
                    "status": "error",
                    "code": "INVALID_LIMIT",
                    "message": "limit must be a valid number.",
                },
                status=400,
            )

        movements = InventoryService.get_movement_history(
            business=business,
            product_id=product_id,
            limit=limit,
        )

        history = []

        for movement in movements:
            history.append(
                {
                    "id": movement.id,
                    "product": {
                        "id": movement.product.id,
                        "name": movement.product.name,
                        "twine_number": movement.product.twine_number,
                        "mesh_size": movement.product.mesh_size,
                        "color": movement.product.color,
                    },
                    "quantity": movement.quantity,
                    "movement_type": movement.movement_type,
                    "source_location": movement.source_location,
                    "destination_location": movement.destination_location,
                    "timestamp": movement.timestamp.isoformat(),
                    "notes": movement.notes or "",
                }
            )

        return JsonResponse(
            {
                "status": "success",
                "business": {
                    "id": business.id,
                    "name": business.name,
                },
                "movements": history,
            }
        )

    except InventoryServiceError as exc:
        return JsonResponse(
            {
                "status": "error",
                "code": "INVENTORY_ERROR",
                "message": str(exc),
            },
            status=400,
        )

    except ValueError as exc:
        return JsonResponse(
            {
                "status": "error",
                "code": "INVALID_REQUEST",
                "message": str(exc),
            },
            status=400,
        )

    except Exception as exc:
        return JsonResponse(
            {
                "status": "error",
                "code": "MOVEMENT_HISTORY_ERROR",
                "message": str(exc),
            },
            status=500,
        )

def stock_move_view(request):
    """
    Receive, transfer, or dispatch stock for the authenticated user's
    currently selected business.

    HTTP concerns stay in this view.
    Inventory business rules are delegated to InventoryService.
    """

    if request.method != "POST":
        return JsonResponse(
            {
                "status": "error",
                "message": "Only POST requests are allowed.",
            },
            status=405,
        )

    try:
        context = get_current_context(request.user)
        business = context.business
    except PermissionDenied as exc:
        return JsonResponse(
            {
                "status": "error",
                "code": "BUSINESS_CONTEXT_ERROR",
                "message": str(exc),
            },
            status=403,
        )

    try:
        data = json.loads(request.body)

        product_id = data.get("product_id")
        quantity = data.get("quantity")
        source = data.get("source")
        destination = data.get("destination")
        notes = data.get("notes")

        if (
            product_id is None
            or quantity is None
            or not source
            or not destination
        ):
            return JsonResponse(
                {
                    "status": "error",
                    "code": "MISSING_FIELDS",
                    "message": (
                        "product_id, quantity, source, "
                        "and destination are required."
                    ),
                },
                status=400,
            )

        try:
            product_id = int(product_id)
        except (TypeError, ValueError):
            return JsonResponse(
                {
                    "status": "error",
                    "code": "INVALID_PRODUCT_ID",
                    "message": "product_id must be a valid number.",
                },
                status=400,
            )

        try:
            quantity = int(quantity)
        except (TypeError, ValueError):
            return JsonResponse(
                {
                    "status": "error",
                    "code": "INVALID_QUANTITY",
                    "message": "Quantity must be a valid number.",
                },
                status=400,
            )

        source = source.strip().upper()
        destination = destination.strip().upper()

        # ---------------------------------------------------------
        # EXTERNAL -> INTERNAL = RECEIVE
        # ---------------------------------------------------------

        if source == "EXTERNAL":
            result = InventoryService.receive(
                business=business,
                product_id=product_id,
                quantity=quantity,
                destination_location=destination,
                notes=notes,
            )

        # ---------------------------------------------------------
        # INTERNAL -> EXTERNAL = DISPATCH
        # ---------------------------------------------------------

        elif destination == "EXTERNAL":
            result = InventoryService.dispatch(
                business=business,
                product_id=product_id,
                quantity=quantity,
                source_location=source,
                notes=notes,
            )

        # ---------------------------------------------------------
        # INTERNAL -> INTERNAL = TRANSFER
        # ---------------------------------------------------------

        else:
            result = InventoryService.transfer(
                business=business,
                product_id=product_id,
                quantity=quantity,
                source_location=source,
                destination_location=destination,
                notes=notes,
            )

        return JsonResponse(
            {
                "status": "success",
                "message": (
                    f"Successfully moved {result.quantity} units of "
                    f"{result.product_name}."
                ),
                "movement_type": result.movement_type,
                "log_id": result.movement_id,
            },
            status=200,
        )

    except InventoryServiceError as exc:
        return JsonResponse(
            {
                "status": "error",
                "code": "INVENTORY_ERROR",
                "message": str(exc),
            },
            status=400,
        )

    except json.JSONDecodeError:
        return JsonResponse(
            {
                "status": "error",
                "code": "INVALID_JSON",
                "message": "Invalid JSON body.",
            },
            status=400,
        )

    except Exception as exc:
        return JsonResponse(
            {
                "status": "error",
                "code": "STOCK_MOVE_ERROR",
                "message": str(exc),
            },
            status=500,
        )

def audit_check_view(request):
    if request.method != "POST":
        return JsonResponse(
            {
                "status": "error",
                "message": (
                    "Send a POST request to check a physical stock count."
                ),
            },
            status=405,
        )

    try:
        context = get_current_context(request.user)
        business = context.business
    except PermissionDenied as exc:
        return JsonResponse(
            {
                "status": "error",
                "code": "BUSINESS_CONTEXT_ERROR",
                "message": str(exc),
            },
            status=403,
        )

    try:
        data = json.loads(request.body)

        result = calculate_stock_discrepancy(
            business=business,
            product_id=data.get("product_id"),
            location=data.get("location"),
            actual_count=data.get("actual_count"),
        )

        return JsonResponse(result)

    except (json.JSONDecodeError, TypeError, ValueError):
        return JsonResponse(
            {
                "status": "error",
                "code": "INVALID_REQUEST",
                "message": "Invalid request data.",
            },
            status=400,
        )

def audit_commit_view(request):
    if request.method != "POST":
        return JsonResponse(
            {
                "status": "error",
                "message": "Send a POST request to commit an investigation.",
            },
            status=405,
        )

    try:
        context = get_current_context(request.user)
        business = context.business
    except PermissionDenied as exc:
        return JsonResponse(
            {
                "status": "error",
                "code": "BUSINESS_CONTEXT_ERROR",
                "message": str(exc),
            },
            status=403,
        )

    try:
        data = json.loads(request.body)

        result = commit_investigation_log(
            business=business,
            product_id=data.get("product_id"),
            location=data.get("location"),
            actual=data.get("actual"),
            selected_reason=data.get("selected_reason"),
            notes=data.get("notes"),
        )

        return JsonResponse(result)

    except (json.JSONDecodeError, TypeError, ValueError):
        return JsonResponse(
            {
                "status": "error",
                "code": "INVALID_REQUEST",
                "message": "Invalid request data.",
            },
            status=400,
        )