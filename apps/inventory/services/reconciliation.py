from django.db import transaction

from apps.inventory.models import (
    InventoryItem,
    Product,
    StockAudit,
    StockMovement,
)
from apps.tenants.models import Business


def calculate_stock_discrepancy(
    business: Business,
    product_id: int,
    location: str,
    actual_count: int,
) -> dict:
    """
    Compare physical stock against the system quantity
    for a specific business.

    This operation is read-only.
    It does not modify the database.
    """

    # ---------------------------------------------------------
    # 1. Validate physical stock count
    # ---------------------------------------------------------

    if actual_count is None or actual_count < 0:
        return {
            "status": "error",
            "code": "INVALID_STOCK_COUNT",
            "message": "Physical stock count cannot be negative.",
        }

    # ---------------------------------------------------------
    # 2. Validate business
    # ---------------------------------------------------------

    if not isinstance(business, Business):
        return {
            "status": "error",
            "code": "INVALID_BUSINESS",
            "message": "A valid business is required.",
        }

    # ---------------------------------------------------------
    # 3. Find product belonging to this business
    # ---------------------------------------------------------

    try:
        product = Product.objects.get(
            pk=product_id,
            business=business,
        )
    except Product.DoesNotExist:
        return {
            "status": "error",
            "code": "PRODUCT_NOT_FOUND",
            "message": (
                f"Product with ID {product_id} "
                f"does not exist for this business."
            ),
        }

    # ---------------------------------------------------------
    # 4. Find inventory belonging to this business
    # ---------------------------------------------------------

    try:
        stock_record = InventoryItem.objects.get(
            business=business,
            product=product,
            location=location,
        )
    except InventoryItem.DoesNotExist:
        return {
            "status": "error",
            "code": "INVENTORY_RECORD_NOT_FOUND",
            "message": (
                f"No inventory record exists for "
                f"{product.name} at {location}."
            ),
        }

    # ---------------------------------------------------------
    # 5. Calculate discrepancy
    # ---------------------------------------------------------

    expected_count = stock_record.quantity
    difference = actual_count - expected_count

    # ---------------------------------------------------------
    # 6. Perfect match
    # ---------------------------------------------------------

    if difference == 0:
        return {
            "status": "PERFECT_MATCH",
            "expected": expected_count,
            "actual": actual_count,
            "difference": 0,
            "message": (
                "Stock matches the system record perfectly. "
                "No discrepancy detected."
            ),
        }

    # ---------------------------------------------------------
    # 7. Determine discrepancy status
    # ---------------------------------------------------------

    status = (
        "WARNING_SHORTAGE"
        if difference < 0
        else "SURPLUS_UNEXPLAINED"
    )

    return {
        "status": status,
        "expected": expected_count,
        "actual": actual_count,
        "difference": difference,
        "message": (
            f"⚠️ Layer 4 Alert: "
            f"{abs(difference)} units unaccounted for "
            f"at {location}."
        ),
    }


def commit_investigation_log(
    business: Business,
    product_id: int,
    location: str,
    actual: int,
    selected_reason: str,
    notes: str | None = None,
) -> dict:
    """
    Commit a completed inventory reconciliation
    for a specific business.

    The operation:

    1. Validates the physical count.
    2. Locks the inventory record.
    3. Creates a permanent StockAudit.
    4. Creates a traceable adjustment movement.
    5. Updates inventory to the verified quantity.

    All database changes succeed or fail together.
    """

    # ---------------------------------------------------------
    # 1. Validate physical count
    # ---------------------------------------------------------

    if actual is None or actual < 0:
        return {
            "status": "error",
            "code": "INVALID_STOCK_COUNT",
            "message": "Physical stock count cannot be negative.",
        }

    # ---------------------------------------------------------
    # 2. Validate business
    # ---------------------------------------------------------

    if not isinstance(business, Business):
        return {
            "status": "error",
            "code": "INVALID_BUSINESS",
            "message": "A valid business is required.",
        }

    # ---------------------------------------------------------
    # 3. Find product belonging to this business
    # ---------------------------------------------------------

    try:
        product = Product.objects.get(
            pk=product_id,
            business=business,
        )
    except Product.DoesNotExist:
        return {
            "status": "error",
            "code": "PRODUCT_NOT_FOUND",
            "message": (
                f"Product with ID {product_id} "
                f"does not exist for this business."
            ),
        }

    # ---------------------------------------------------------
    # 4. Atomic inventory transaction
    # ---------------------------------------------------------

    with transaction.atomic():

        try:
            stock = (
                InventoryItem.objects
                .select_for_update()
                .get(
                    business=business,
                    product=product,
                    location=location,
                )
            )

        except InventoryItem.DoesNotExist:
            return {
                "status": "error",
                "code": "INVENTORY_NOT_FOUND",
                "message": "Inventory record not found.",
            }

        # -----------------------------------------------------
        # 5. Calculate discrepancy
        # -----------------------------------------------------

        expected = stock.quantity
        difference = actual - expected

        # -----------------------------------------------------
        # 6. Nothing to reconcile
        # -----------------------------------------------------

        if difference == 0:
            return {
                "status": "error",
                "code": "NO_DISCREPANCY",
                "message": "No discrepancy to commit.",
            }

        # -----------------------------------------------------
        # 7. Create permanent audit record
        # -----------------------------------------------------

        audit = StockAudit.objects.create(
            business=business,
            product=product,
            location=location,
            expected_quantity=expected,
            actual_quantity=actual,
            difference=difference,
            reason=selected_reason,
            owner_notes=notes,
        )

        # -----------------------------------------------------
        # 8. Create adjustment movement
        # -----------------------------------------------------

        StockMovement.objects.create(
            business=business,
            product=product,
            quantity=abs(difference),
            movement_type="ADJUSTMENT",
            source_location=location,
            destination_location=location,
            notes=(
                f"Audit #{audit.pk}: "
                f"{difference:+d} units; "
                f"{selected_reason}."
            ),
        )

        # -----------------------------------------------------
        # 9. Update inventory
        # -----------------------------------------------------

        stock.quantity = actual

        stock.save(
            update_fields=["quantity", "last_updated"]
        )

    # ---------------------------------------------------------
    # 10. Return successful result
    # ---------------------------------------------------------

    return {
        "status": "success",
        "message": (
            f"Inventory reconciled to {actual} units."
        ),
        "audit_id": audit.pk,
        "expected": expected,
        "actual": actual,
        "difference": difference,
    }