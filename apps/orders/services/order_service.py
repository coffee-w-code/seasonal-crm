from decimal import Decimal, ROUND_HALF_UP

from django.db import transaction

from apps.accounts.context import get_current_context
from apps.customers.models import Customer
from apps.inventory.models import Product

from ..models import Order, OrderItem, OrderNumberSequence


class OrderServiceError(Exception):
    """Base exception for order service errors."""


class CustomerNotFoundError(OrderServiceError):
    """Customer does not exist within the current business."""


class ProductNotFoundError(OrderServiceError):
    """Product does not exist within the current business."""


class InvalidOrderError(OrderServiceError):
    """Order data is invalid."""


class OrderService:
    """
    Business logic for creating and managing customer orders.

    All operations are explicitly scoped to the authenticated
    user's current business.
    """

    MONEY_PLACES = Decimal("0.01")

    @staticmethod
    def _money(value):
        """
        Convert a value to Decimal and round it to two decimal places.
        """

        try:
            value = Decimal(str(value))
        except (TypeError, ValueError, ArithmeticError) as exc:
            raise InvalidOrderError(
                "Invalid monetary value."
            ) from exc

        return value.quantize(
            OrderService.MONEY_PLACES,
            rounding=ROUND_HALF_UP,
        )

    @staticmethod
    def _validate_non_negative_money(value, field_name):
        value = OrderService._money(value)

        if value < Decimal("0.00"):
            raise InvalidOrderError(
                f"{field_name} cannot be negative."
            )

        return value

    @staticmethod
    def _get_next_order_number(business):
        """
        Generate the next customer-facing order number.

        The sequence row is locked by the surrounding database
        transaction, preventing concurrent requests for the same
        business from generating duplicate numbers.
        """

        sequence, _ = (
            OrderNumberSequence.objects
            .select_for_update()
            .get_or_create(
                business=business,
                defaults={"last_number": 0},
            )
        )

        sequence.last_number += 1

        sequence.save(
            update_fields=[
                "last_number",
                "updated_at",
            ]
        )

        return f"ORD-{sequence.last_number:06d}"

    @staticmethod
    def _get_customer(business, customer_id):
        """
        Resolve a customer strictly inside the current business.
        """

        try:
            return Customer.objects.get(
                id=customer_id,
                business=business,
            )

        except Customer.DoesNotExist as exc:
            raise CustomerNotFoundError(
                "Customer was not found in the current business."
            ) from exc

    @staticmethod
    def _get_product(business, product_id):
        """
        Resolve a product strictly inside the current business.
        """

        try:
            return Product.objects.get(
                id=product_id,
                business=business,
            )

        except Product.DoesNotExist as exc:
            raise ProductNotFoundError(
                "Product was not found in the current business."
            ) from exc

    @classmethod
    @transaction.atomic
    def create_draft_order(
        cls,
        *,
        user,
        customer_id,
        items,
        discount=Decimal("0.00"),
        tax=Decimal("0.00"),
        notes="",
    ):
        """
        Create a new DRAFT order.

        Every call creates a NEW order.

        Orders are NOT merged together, even when the same
        customer places multiple orders.

        The customer's remaining_balance is increased by
        the total of this new unpaid order.
        """

        # ---------------------------------------------------------
        # 1. Authentication
        # ---------------------------------------------------------

        if not user or not user.is_authenticated:
            raise InvalidOrderError(
                "Authentication is required."
            )

        # ---------------------------------------------------------
        # 2. Validate items
        # ---------------------------------------------------------

        if not isinstance(items, list) or not items:
            raise InvalidOrderError(
                "An order must contain at least one item."
            )

        # ---------------------------------------------------------
        # 3. Get current business context
        # ---------------------------------------------------------

        context = get_current_context(user)

        if not context or not context.business:
            raise InvalidOrderError(
                "No current business selected."
            )

        business = context.business

        # ---------------------------------------------------------
        # 4. Get customer inside current business
        # ---------------------------------------------------------

        customer = cls._get_customer(
            business=business,
            customer_id=customer_id,
        )

        # ---------------------------------------------------------
        # 5. Validate order-level discount
        # ---------------------------------------------------------

        order_discount = cls._validate_non_negative_money(
            discount,
            "Order discount",
        )

        # ---------------------------------------------------------
        # 6. Validate tax
        # ---------------------------------------------------------

        order_tax = cls._validate_non_negative_money(
            tax,
            "Order tax",
        )

        # ---------------------------------------------------------
        # 7. Create a NEW order
        # ---------------------------------------------------------

        order = Order.objects.create(
            business=business,
            customer=customer,
            order_number=cls._get_next_order_number(business),
            status=Order.Status.DRAFT,
            payment_status=Order.PaymentStatus.UNPAID,
            subtotal=Decimal("0.00"),
            discount=order_discount,
            tax=order_tax,
            total=Decimal("0.00"),
            notes=notes or "",
            created_by=user,
        )

        # ---------------------------------------------------------
        # 8. Process order items
        # ---------------------------------------------------------

        subtotal = Decimal("0.00")

        for item_data in items:

            # -----------------------------------------------------
            # Validate item structure
            # -----------------------------------------------------

            if not isinstance(item_data, dict):
                raise InvalidOrderError(
                    "Each order item must be an object."
                )

            # -----------------------------------------------------
            # Product ID
            # -----------------------------------------------------

            product_id = item_data.get("product_id")

            if product_id is None:
                raise InvalidOrderError(
                    "Each item requires a product_id."
                )

            # -----------------------------------------------------
            # Quantity
            # -----------------------------------------------------

            quantity = item_data.get("quantity")

            if quantity is None:
                raise InvalidOrderError(
                    "Each item requires a quantity."
                )

            try:
                quantity = int(quantity)

            except (TypeError, ValueError) as exc:
                raise InvalidOrderError(
                    "Quantity must be a whole number."
                ) from exc

            if quantity <= 0:
                raise InvalidOrderError(
                    "Quantity must be greater than zero."
                )

            # -----------------------------------------------------
            # Unit price
            # -----------------------------------------------------

            unit_price = item_data.get("unit_price")

            if unit_price is None:
                raise InvalidOrderError(
                    "Each item requires a unit_price."
                )

            price = cls._validate_non_negative_money(
                unit_price,
                "Unit price",
            )

            # -----------------------------------------------------
            # Item discount
            # -----------------------------------------------------

            item_discount = cls._validate_non_negative_money(
                item_data.get(
                    "discount",
                    Decimal("0.00"),
                ),
                "Item discount",
            )

            # -----------------------------------------------------
            # Get product inside current business
            # -----------------------------------------------------

            product = cls._get_product(
                business=business,
                product_id=product_id,
            )

            # -----------------------------------------------------
            # Calculate line total
            # -----------------------------------------------------

            gross_line_total = (
                price * Decimal(quantity)
            )

            if item_discount > gross_line_total:
                raise InvalidOrderError(
                    "Item discount cannot exceed the line value."
                )

            line_total = cls._money(
                gross_line_total - item_discount
            )

            # -----------------------------------------------------
            # Add to subtotal
            # -----------------------------------------------------

            subtotal += line_total

            # -----------------------------------------------------
            # Create OrderItem
            # -----------------------------------------------------

            OrderItem.objects.create(
                order=order,
                product=product,
                quantity=quantity,
                unit_price=price,
                discount=item_discount,
                line_total=line_total,
            )

        # ---------------------------------------------------------
        # 9. Normalize subtotal
        # ---------------------------------------------------------

        subtotal = cls._money(subtotal)

        # ---------------------------------------------------------
        # 10. Validate order discount
        # ---------------------------------------------------------

        if order_discount > subtotal:
            raise InvalidOrderError(
                "Order discount cannot exceed the subtotal."
            )

        # ---------------------------------------------------------
        # 11. Calculate final total
        # ---------------------------------------------------------

        taxable_amount = cls._money(
            subtotal - order_discount
        )

        total = cls._money(
            taxable_amount + order_tax
        )

        # ---------------------------------------------------------
        # 12. Update order totals
        # ---------------------------------------------------------

        order.subtotal = subtotal
        order.total = total

        order.save(
            update_fields=[
                "subtotal",
                "total",
                "updated_at",
            ]
        )

        # ---------------------------------------------------------
        # 13. Add this NEW order's amount to Customer Due
        # ---------------------------------------------------------

        customer.remaining_balance = (
            customer.remaining_balance + total
        )

        customer.save(
            update_fields=[
                "remaining_balance",
                "updated_at",
            ]
        )

        # ---------------------------------------------------------
        # 14. Return the newly created order
        # ---------------------------------------------------------

        return order