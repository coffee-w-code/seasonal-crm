from decimal import Decimal

from django.contrib.auth import get_user_model
from django.core.exceptions import PermissionDenied
from django.test import TestCase

from apps.accounts.models import (
    BusinessMembership,
    UserBusinessContext,
)
from apps.customers.models import Customer
from apps.inventory.models import Product, InventoryItem
from apps.tenants.models import Business

from apps.orders.models import Order, OrderItem, OrderNumberSequence
from apps.orders.services.order_service import (
    CustomerNotFoundError,
    InvalidOrderError,
    OrderService,
    ProductNotFoundError,
)


User = get_user_model()


class OrderServiceSecurityTests(TestCase):
    """
    Tests tenant isolation, validation, financial calculations,
    and order creation behavior.
    """

    def setUp(self):
        self.user_a = User.objects.create_user(
            username="business_a_user",
            password="StrongPassword123!",
        )

        self.user_b = User.objects.create_user(
            username="business_b_user",
            password="StrongPassword123!",
        )

        self.business_a = Business.objects.create(
            name="Business A",
            owner_name="Owner A",
        )

        self.business_b = Business.objects.create(
            name="Business B",
            owner_name="Owner B",
        )

        BusinessMembership.objects.create(
            user=self.user_a,
            business=self.business_a,
            role=BusinessMembership.Role.OWNER,
            is_active=True,
        )

        BusinessMembership.objects.create(
            user=self.user_b,
            business=self.business_b,
            role=BusinessMembership.Role.OWNER,
            is_active=True,
        )

        UserBusinessContext.objects.create(
            user=self.user_a,
            current_business=self.business_a,
        )

        UserBusinessContext.objects.create(
            user=self.user_b,
            current_business=self.business_b,
        )

        self.customer_a = Customer.objects.create(
            business=self.business_a,
            store_name="Customer A",
            owner_name="Customer Owner A",
            phone_number="9000000001",
            state_region="UP",
        )

        self.customer_b = Customer.objects.create(
            business=self.business_b,
            store_name="Customer B",
            owner_name="Customer Owner B",
            phone_number="9000000002",
            state_region="Bihar",
        )

        self.product_a = Product.objects.create(
            business=self.business_a,
            name="Product A",
            twine_number="210D",
            mesh_size="2 inch",
            color="Green",
        )

        self.product_b = Product.objects.create(
            business=self.business_b,
            name="Product B",
            twine_number="210D",
            mesh_size="2 inch",
            color="Blue",
        )

    # ------------------------------------------------------------------
    # AUTHENTICATION
    # ------------------------------------------------------------------

    def test_unauthenticated_user_cannot_create_order(self):
        from django.contrib.auth.models import AnonymousUser

        user = AnonymousUser()

        with self.assertRaises(InvalidOrderError):
            OrderService.create_draft_order(
                user=user,
                customer_id=self.customer_a.id,
                items=[
                    {
                       "product_id": self.product_a.id,
                       "quantity": 10,
                       "unit_price": "700.00",
                    }
               ],
            )

        self.assertEqual(Order.objects.count(), 0)
        self.assertEqual(OrderItem.objects.count(), 0)


    def test_user_without_business_membership_cannot_create_order(self):
        user = User.objects.create_user(
            username="no_business_user",
            password="StrongPassword123!",
        )

        with self.assertRaises(PermissionDenied):
            OrderService.create_draft_order(
                user=user,
                customer_id=self.customer_a.id,
                items=[
                    {
                        "product_id": self.product_a.id,
                        "quantity": 10,
                        "unit_price": "700.00",
                    }
                ],
            )

        self.assertEqual(Order.objects.count(), 0)

    # ------------------------------------------------------------------
    # BASIC ORDER CREATION
    # ------------------------------------------------------------------

    def test_user_can_create_order_for_own_business(self):
        order = OrderService.create_draft_order(
            user=self.user_a,
            customer_id=self.customer_a.id,
            items=[
                {
                    "product_id": self.product_a.id,
                    "quantity": 10,
                    "unit_price": "700.00",
                }
            ],
        )

        self.assertEqual(order.business, self.business_a)
        self.assertEqual(order.customer, self.customer_a)
        self.assertEqual(order.status, Order.Status.DRAFT)
        self.assertEqual(
            order.payment_status,
            Order.PaymentStatus.UNPAID,
        )

        self.assertEqual(
            order.subtotal,
            Decimal("7000.00"),
        )

        self.assertEqual(
            order.total,
            Decimal("7000.00"),
        )

        self.assertEqual(
            order.items.count(),
            1,
        )

    def test_order_can_contain_multiple_items(self):
        product_c = Product.objects.create(
            business=self.business_a,
            name="Product C",
            twine_number="300D",
            mesh_size="3 inch",
            color="White",
        )

        order = OrderService.create_draft_order(
            user=self.user_a,
            customer_id=self.customer_a.id,
            items=[
                {
                    "product_id": self.product_a.id,
                    "quantity": 10,
                    "unit_price": "700.00",
                },
                {
                    "product_id": product_c.id,
                    "quantity": 5,
                    "unit_price": "400.00",
                },
            ],
        )

        self.assertEqual(order.items.count(), 2)

        self.assertEqual(
            order.subtotal,
            Decimal("9000.00"),
        )

        self.assertEqual(
            order.total,
            Decimal("9000.00"),
        )

    # ------------------------------------------------------------------
    # TENANT ISOLATION
    # ------------------------------------------------------------------

    def test_user_cannot_use_customer_from_another_business(self):
        with self.assertRaises(CustomerNotFoundError):
            OrderService.create_draft_order(
                user=self.user_a,
                customer_id=self.customer_b.id,
                items=[
                    {
                        "product_id": self.product_a.id,
                        "quantity": 10,
                        "unit_price": "700.00",
                    }
                ],
            )

        self.assertEqual(Order.objects.count(), 0)
        self.assertEqual(OrderItem.objects.count(), 0)

    def test_user_cannot_use_product_from_another_business(self):
        with self.assertRaises(ProductNotFoundError):
            OrderService.create_draft_order(
                user=self.user_a,
                customer_id=self.customer_a.id,
                items=[
                    {
                        "product_id": self.product_b.id,
                        "quantity": 10,
                        "unit_price": "700.00",
                    }
                ],
            )

        self.assertEqual(Order.objects.count(), 0)
        self.assertEqual(OrderItem.objects.count(), 0)

    # ------------------------------------------------------------------
    # REQUIRED ORDER DATA
    # ------------------------------------------------------------------

    def test_empty_items_are_rejected(self):
        with self.assertRaises(InvalidOrderError):
            OrderService.create_draft_order(
                user=self.user_a,
                customer_id=self.customer_a.id,
                items=[],
            )

        self.assertEqual(Order.objects.count(), 0)

    def test_items_must_be_a_list(self):
        with self.assertRaises(InvalidOrderError):
            OrderService.create_draft_order(
                user=self.user_a,
                customer_id=self.customer_a.id,
                items={},
            )

        self.assertEqual(Order.objects.count(), 0)

    def test_item_must_be_an_object(self):
        with self.assertRaises(InvalidOrderError):
            OrderService.create_draft_order(
                user=self.user_a,
                customer_id=self.customer_a.id,
                items=["invalid item"],
            )

        self.assertEqual(Order.objects.count(), 0)

    def test_product_id_is_required(self):
        with self.assertRaises(InvalidOrderError):
            OrderService.create_draft_order(
                user=self.user_a,
                customer_id=self.customer_a.id,
                items=[
                    {
                        "quantity": 10,
                        "unit_price": "700.00",
                    }
                ],
            )

        self.assertEqual(Order.objects.count(), 0)

    def test_quantity_is_required(self):
        with self.assertRaises(InvalidOrderError):
            OrderService.create_draft_order(
                user=self.user_a,
                customer_id=self.customer_a.id,
                items=[
                    {
                        "product_id": self.product_a.id,
                        "unit_price": "700.00",
                    }
                ],
            )

        self.assertEqual(Order.objects.count(), 0)

    def test_unit_price_is_required(self):
        with self.assertRaises(InvalidOrderError):
            OrderService.create_draft_order(
                user=self.user_a,
                customer_id=self.customer_a.id,
                items=[
                    {
                        "product_id": self.product_a.id,
                        "quantity": 10,
                    }
                ],
            )

        self.assertEqual(Order.objects.count(), 0)

    # ------------------------------------------------------------------
    # QUANTITY VALIDATION
    # ------------------------------------------------------------------

    def test_zero_quantity_is_rejected(self):
        with self.assertRaises(InvalidOrderError):
            OrderService.create_draft_order(
                user=self.user_a,
                customer_id=self.customer_a.id,
                items=[
                    {
                        "product_id": self.product_a.id,
                        "quantity": 0,
                        "unit_price": "700.00",
                    }
                ],
            )

        self.assertEqual(Order.objects.count(), 0)
        self.assertEqual(OrderItem.objects.count(), 0)

    def test_negative_quantity_is_rejected(self):
        with self.assertRaises(InvalidOrderError):
            OrderService.create_draft_order(
                user=self.user_a,
                customer_id=self.customer_a.id,
                items=[
                    {
                        "product_id": self.product_a.id,
                        "quantity": -10,
                        "unit_price": "700.00",
                    }
                ],
            )

        self.assertEqual(Order.objects.count(), 0)
        self.assertEqual(OrderItem.objects.count(), 0)

    def test_non_numeric_quantity_is_rejected(self):
        with self.assertRaises(InvalidOrderError):
            OrderService.create_draft_order(
                user=self.user_a,
                customer_id=self.customer_a.id,
                items=[
                    {
                        "product_id": self.product_a.id,
                        "quantity": "ten",
                        "unit_price": "700.00",
                    }
                ],
            )

        self.assertEqual(Order.objects.count(), 0)

    # ------------------------------------------------------------------
    # MONEY VALIDATION
    # ------------------------------------------------------------------

    def test_negative_price_is_rejected(self):
        with self.assertRaises(InvalidOrderError):
            OrderService.create_draft_order(
                user=self.user_a,
                customer_id=self.customer_a.id,
                items=[
                    {
                        "product_id": self.product_a.id,
                        "quantity": 10,
                        "unit_price": "-700.00",
                    }
                ],
            )

        self.assertEqual(Order.objects.count(), 0)

    def test_negative_order_discount_is_rejected(self):
        with self.assertRaises(InvalidOrderError):
            OrderService.create_draft_order(
                user=self.user_a,
                customer_id=self.customer_a.id,
                items=[
                    {
                        "product_id": self.product_a.id,
                        "quantity": 10,
                        "unit_price": "700.00",
                    }
                ],
                discount="-1.00",
            )

        self.assertEqual(Order.objects.count(), 0)

    def test_negative_tax_is_rejected(self):
        with self.assertRaises(InvalidOrderError):
            OrderService.create_draft_order(
                user=self.user_a,
                customer_id=self.customer_a.id,
                items=[
                    {
                        "product_id": self.product_a.id,
                        "quantity": 10,
                        "unit_price": "700.00",
                    }
                ],
                tax="-1.00",
            )

        self.assertEqual(Order.objects.count(), 0)

    def test_invalid_monetary_value_is_rejected(self):
        with self.assertRaises(InvalidOrderError):
            OrderService.create_draft_order(
                user=self.user_a,
                customer_id=self.customer_a.id,
                items=[
                    {
                        "product_id": self.product_a.id,
                        "quantity": 10,
                        "unit_price": "not-a-price",
                    }
                ],
            )

        self.assertEqual(Order.objects.count(), 0)

    # ------------------------------------------------------------------
    # DISCOUNT VALIDATION
    # ------------------------------------------------------------------

    def test_item_discount_cannot_exceed_line_value(self):
        with self.assertRaises(InvalidOrderError):
            OrderService.create_draft_order(
                user=self.user_a,
                customer_id=self.customer_a.id,
                items=[
                    {
                        "product_id": self.product_a.id,
                        "quantity": 10,
                        "unit_price": "700.00",
                        "discount": "7001.00",
                    }
                ],
            )

        self.assertEqual(Order.objects.count(), 0)

    def test_order_discount_cannot_exceed_subtotal(self):
        with self.assertRaises(InvalidOrderError):
            OrderService.create_draft_order(
                user=self.user_a,
                customer_id=self.customer_a.id,
                items=[
                    {
                        "product_id": self.product_a.id,
                        "quantity": 10,
                        "unit_price": "700.00",
                    }
                ],
                discount="7001.00",
            )

        self.assertEqual(Order.objects.count(), 0)

    # ------------------------------------------------------------------
    # FINANCIAL CALCULATIONS
    # ------------------------------------------------------------------

    def test_item_discount_is_calculated_correctly(self):
        order = OrderService.create_draft_order(
            user=self.user_a,
            customer_id=self.customer_a.id,
            items=[
                {
                    "product_id": self.product_a.id,
                    "quantity": 10,
                    "unit_price": "700.00",
                    "discount": "500.00",
                }
            ],
        )

        item = order.items.first()

        self.assertEqual(
            item.line_total,
            Decimal("6500.00"),
        )

        self.assertEqual(
            order.subtotal,
            Decimal("6500.00"),
        )

        self.assertEqual(
            order.total,
            Decimal("6500.00"),
        )

    def test_order_discount_and_tax_are_calculated_correctly(self):
        order = OrderService.create_draft_order(
            user=self.user_a,
            customer_id=self.customer_a.id,
            items=[
                {
                    "product_id": self.product_a.id,
                    "quantity": 10,
                    "unit_price": "700.00",
                }
            ],
            discount="500.00",
            tax="1170.00",
        )

        self.assertEqual(
            order.subtotal,
            Decimal("7000.00"),
        )

        self.assertEqual(
            order.discount,
            Decimal("500.00"),
        )

        self.assertEqual(
            order.tax,
            Decimal("1170.00"),
        )

        self.assertEqual(
            order.total,
            Decimal("7670.00"),
        )

    # ------------------------------------------------------------------
    # INVENTORY SAFETY
    # ------------------------------------------------------------------

    def test_order_creation_does_not_modify_inventory(self):
        inventory = InventoryItem.objects.create(
            business=self.business_a,
            product=self.product_a,
            location="WAREHOUSE",
            quantity=100,
        )

        OrderService.create_draft_order(
            user=self.user_a,
            customer_id=self.customer_a.id,
            items=[
                {
                    "product_id": self.product_a.id,
                    "quantity": 10,
                    "unit_price": "700.00",
                }
            ],
        )

        inventory.refresh_from_db()

        self.assertEqual(
            inventory.quantity,
            100,
        )

    # ------------------------------------------------------------------
    # TRANSACTION SAFETY
    # ------------------------------------------------------------------

    def test_failed_order_does_not_leave_partial_records(self):
        with self.assertRaises(InvalidOrderError):
            OrderService.create_draft_order(
                user=self.user_a,
                customer_id=self.customer_a.id,
                items=[
                    {
                        "product_id": self.product_a.id,
                        "quantity": 10,
                        "unit_price": "700.00",
                    },
                    {
                        "product_id": self.product_a.id,
                        "quantity": 0,
                        "unit_price": "500.00",
                    },
                ],
            )

        self.assertEqual(Order.objects.count(), 0)
        self.assertEqual(OrderItem.objects.count(), 0)

    # ------------------------------------------------------------------
    # ORDER NUMBERING
    # ------------------------------------------------------------------

    def test_first_order_number_is_correct(self):
        order = OrderService.create_draft_order(
            user=self.user_a,
            customer_id=self.customer_a.id,
            items=[
                {
                    "product_id": self.product_a.id,
                    "quantity": 5,
                    "unit_price": "100.00",
                }
            ],
        )

        self.assertEqual(
            order.order_number,
            "ORD-000001",
        )

    def test_order_numbers_increment_within_business(self):
        order_one = OrderService.create_draft_order(
            user=self.user_a,
            customer_id=self.customer_a.id,
            items=[
                {
                    "product_id": self.product_a.id,
                    "quantity": 5,
                    "unit_price": "100.00",
                }
            ],
        )

        order_two = OrderService.create_draft_order(
            user=self.user_a,
            customer_id=self.customer_a.id,
            items=[
                {
                    "product_id": self.product_a.id,
                    "quantity": 5,
                    "unit_price": "100.00",
                }
            ],
        )

        self.assertEqual(
            order_one.order_number,
            "ORD-000001",
        )

        self.assertEqual(
            order_two.order_number,
            "ORD-000002",
        )

    def test_order_numbers_are_business_scoped(self):
        order_a = OrderService.create_draft_order(
            user=self.user_a,
            customer_id=self.customer_a.id,
            items=[
                {
                    "product_id": self.product_a.id,
                    "quantity": 5,
                    "unit_price": "100.00",
                }
            ],
        )

        order_b = OrderService.create_draft_order(
            user=self.user_b,
            customer_id=self.customer_b.id,
            items=[
                {
                    "product_id": self.product_b.id,
                    "quantity": 5,
                    "unit_price": "200.00",
                }
            ],
        )

        self.assertEqual(
            order_a.order_number,
            "ORD-000001",
        )

        self.assertEqual(
            order_b.order_number,
            "ORD-000001",
        )

    def test_order_number_sequence_starts_at_zero(self):
        self.assertFalse(
            OrderNumberSequence.objects.filter(
                business=self.business_a,
            ).exists()
        )

        order = OrderService.create_draft_order(
            user=self.user_a,
            customer_id=self.customer_a.id,
            items=[
                {
                    "product_id": self.product_a.id,
                    "quantity": 5,
                    "unit_price": "100.00",
                }
            ],
        )

        sequence = OrderNumberSequence.objects.get(
            business=self.business_a,
        )

        self.assertEqual(
            order.order_number,
            "ORD-000001",
        )

        self.assertEqual(
            sequence.last_number,
            1,
        )


    def test_order_number_sequence_increments(self):
        OrderService.create_draft_order(
            user=self.user_a,
            customer_id=self.customer_a.id,
            items=[
                {
                    "product_id": self.product_a.id,
                    "quantity": 5,
                    "unit_price": "100.00",
                }
            ],
        )

        OrderService.create_draft_order(
            user=self.user_a,
            customer_id=self.customer_a.id,
            items=[
                {
                    "product_id": self.product_a.id,
                    "quantity": 5,
                    "unit_price": "100.00",
                }
            ],
        )

        sequence = OrderNumberSequence.objects.get(
            business=self.business_a,
        )

        self.assertEqual(
            sequence.last_number,
            2,
        )


    def test_order_number_sequences_are_independent_per_business(self):
        OrderService.create_draft_order(
            user=self.user_a,
            customer_id=self.customer_a.id,
            items=[
                {
                    "product_id": self.product_a.id,
                    "quantity": 5,
                    "unit_price": "100.00",
                }
            ],
        )

        OrderService.create_draft_order(
            user=self.user_a,
            customer_id=self.customer_a.id,
            items=[
                {
                    "product_id": self.product_a.id,
                    "quantity": 5,
                    "unit_price": "100.00",
                }
            ],
        )

        OrderService.create_draft_order(
            user=self.user_b,
            customer_id=self.customer_b.id,
            items=[
                {
                    "product_id": self.product_b.id,
                    "quantity": 5,
                    "unit_price": "200.00",
                }
            ],
        )

        sequence_a = OrderNumberSequence.objects.get(
            business=self.business_a,
        )

        sequence_b = OrderNumberSequence.objects.get(
            business=self.business_b,
        )

        self.assertEqual(
            sequence_a.last_number,
            2,
        )

        self.assertEqual(
            sequence_b.last_number,
            1,
        )


    def test_failed_order_creation_rolls_back_order_number_sequence(self):
        with self.assertRaises(InvalidOrderError):
            OrderService.create_draft_order(
                user=self.user_a,
                customer_id=self.customer_a.id,
                items=[
                    {
                        "product_id": self.product_a.id,
                        "quantity": 0,
                        "unit_price": "100.00",
                    }
                ],
            )

        self.assertFalse(
            Order.objects.filter(
                business=self.business_a,
            ).exists()
        )

        self.assertFalse(
            OrderNumberSequence.objects.filter(
                business=self.business_a,
            ).exists()
        )

        order = OrderService.create_draft_order(
            user=self.user_a,
            customer_id=self.customer_a.id,
            items=[
                {
                    "product_id": self.product_a.id,
                    "quantity": 5,
                    "unit_price": "100.00",
                }
            ],
        )

        self.assertEqual(
            order.order_number,
            "ORD-000001",
        )

        sequence = OrderNumberSequence.objects.get(
            business=self.business_a,
        )

        self.assertEqual(
            sequence.last_number,
            1,
        )