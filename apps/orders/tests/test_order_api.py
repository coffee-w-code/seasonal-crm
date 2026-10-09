from decimal import Decimal
import json

from django.contrib.auth import get_user_model
from django.test import TestCase
from django.urls import reverse

from apps.accounts.models import (
    BusinessMembership,
    UserBusinessContext,
)
from apps.customers.models import Customer
from apps.inventory.models import Product
from apps.orders.models import Order, OrderItem, OrderNumberSequence
from apps.tenants.models import Business


User = get_user_model()


class OrderAPISecurityTests(TestCase):
    """
    HTTP/API tests for the Orders module.

    These tests verify:
    - authentication
    - request validation
    - successful order creation
    - tenant isolation
    - order listing
    - order detail access
    """

    def setUp(self):
        self.user_a = User.objects.create_user(
            username="api_business_a_user",
            password="StrongPassword123!",
        )

        self.user_b = User.objects.create_user(
            username="api_business_b_user",
            password="StrongPassword123!",
        )

        self.business_a = Business.objects.create(
            name="API Business A",
            owner_name="Owner A",
        )

        self.business_b = Business.objects.create(
            name="API Business B",
            owner_name="Owner B",
        )

        BusinessMembership.objects.create(
            user=self.user_a,
            business=self.business_a,
            role=BusinessMembership.Role.OWNER,
            is_active=True,
        )

        UserBusinessContext.objects.create(
            user=self.user_a,
            current_business=self.business_a,
        )

        BusinessMembership.objects.create(
            user=self.user_b,
            business=self.business_b,
            role=BusinessMembership.Role.OWNER,
            is_active=True,
        )

        UserBusinessContext.objects.create(
            user=self.user_b,
            current_business=self.business_b,
        )

        self.customer_a = Customer.objects.create(
            business=self.business_a,
            store_name="Customer A",
            owner_name="Customer Owner A",
            phone_number="9100000001",
            state_region="UP",
        )

        self.customer_b = Customer.objects.create(
            business=self.business_b,
            store_name="Customer B",
            owner_name="Customer Owner B",
            phone_number="9100000002",
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

        self.create_url = reverse("create_order")
        self.list_url = reverse("order_list")

    def _login_as_a(self):
        self.client.force_login(self.user_a)

    def _login_as_b(self):
        self.client.force_login(self.user_b)

    def _create_payload(
        self,
        customer_id=None,
        product_id=None,
    ):
        return {
            "customer_id": (
                customer_id
                if customer_id is not None
                else self.customer_a.id
            ),
            "items": [
                {
                    "product_id": (
                        product_id
                        if product_id is not None
                        else self.product_a.id
                    ),
                    "quantity": 10,
                    "unit_price": "700.00",
                }
            ],
        }

    # ------------------------------------------------------------------
    # AUTHENTICATION
    # ------------------------------------------------------------------

    def test_create_requires_authentication(self):
        response = self.client.post(
            self.create_url,
            data=json.dumps(self._create_payload()),
            content_type="application/json",
        )

        self.assertEqual(response.status_code, 401)

        body = response.json()

        self.assertEqual(
            body["code"],
            "AUTHENTICATION_REQUIRED",
        )

        self.assertEqual(Order.objects.count(), 0)

    def test_list_requires_authentication(self):
        response = self.client.get(self.list_url)

        self.assertEqual(response.status_code, 401)

    def test_detail_requires_authentication(self):
        response = self.client.get(
            "/orders/999999/"
        )

        self.assertEqual(response.status_code, 401)

    # ------------------------------------------------------------------
    # CREATE ORDER
    # ------------------------------------------------------------------

    def test_authenticated_user_can_create_order(self):
        self._login_as_a()

        response = self.client.post(
            self.create_url,
            data=json.dumps(self._create_payload()),
            content_type="application/json",
        )

        self.assertEqual(response.status_code, 201)

        body = response.json()

        self.assertEqual(
            body["status"],
            "success",
        )

        self.assertIn(
            "order",
            body,
        )

        order = Order.objects.get()

        self.assertEqual(
            order.business,
            self.business_a,
        )

        self.assertEqual(
            order.customer,
            self.customer_a,
        )

        self.assertEqual(
            order.created_by,
            self.user_a,
        )

        self.assertEqual(
            order.total,
            Decimal("7000.00"),
        )

        self.assertEqual(
            OrderItem.objects.count(),
            1,
        )

    def test_invalid_json_is_rejected(self):
        self._login_as_a()

        response = self.client.post(
            self.create_url,
            data="{invalid json",
            content_type="application/json",
        )

        self.assertEqual(
            response.status_code,
            400,
        )

        self.assertEqual(
            response.json()["code"],
            "INVALID_JSON",
        )

        self.assertEqual(
            Order.objects.count(),
            0,
        )

    def test_non_object_json_is_rejected(self):
        self._login_as_a()

        response = self.client.post(
            self.create_url,
            data=json.dumps([]),
            content_type="application/json",
        )

        self.assertEqual(
            response.status_code,
            400,
        )

        self.assertEqual(
            response.json()["code"],
            "INVALID_REQUEST",
        )

    def test_missing_customer_is_rejected(self):
        self._login_as_a()

        payload = {
            "items": [
                {
                    "product_id": self.product_a.id,
                    "quantity": 10,
                    "unit_price": "700.00",
                }
            ]
        }

        response = self.client.post(
            self.create_url,
            data=json.dumps(payload),
            content_type="application/json",
        )

        self.assertEqual(
            response.status_code,
            400,
        )

        self.assertEqual(
            response.json()["code"],
            "MISSING_CUSTOMER",
        )

    def test_missing_items_is_rejected(self):
        self._login_as_a()

        payload = {
            "customer_id": self.customer_a.id,
        }

        response = self.client.post(
            self.create_url,
            data=json.dumps(payload),
            content_type="application/json",
        )

        self.assertEqual(
            response.status_code,
            400,
        )

        self.assertEqual(
            response.json()["code"],
            "MISSING_ITEMS",
        )

    def test_create_orders_use_business_scoped_sequence(self):
        self._login_as_a()

        response_one = self.client.post(
            self.create_url,
            data=json.dumps(self._create_payload()),
            content_type="application/json",
        )

        self.assertEqual(response_one.status_code, 201)

        response_two = self.client.post(
            self.create_url,
            data=json.dumps(self._create_payload()),
            content_type="application/json",
        )

        self.assertEqual(response_two.status_code, 201)

        orders = Order.objects.filter(
            business=self.business_a,
        ).order_by("id")

        self.assertEqual(orders.count(), 2)

        self.assertEqual(
            orders[0].order_number,
            "ORD-000001",
        )

        self.assertEqual(
            orders[1].order_number,
            "ORD-000002",
        )

        sequence = OrderNumberSequence.objects.get(
            business=self.business_a,
        )

        self.assertEqual(
            sequence.last_number,
            2,
        )

    def test_create_order_number_sequence_is_business_scoped(self):
        self._login_as_a()

        response_a = self.client.post(
            self.create_url,
            data=json.dumps(self._create_payload()),
            content_type="application/json",
        )

        self.assertEqual(
            response_a.status_code,
            201,
        )

        self._login_as_b()

        response_b = self.client.post(
            self.create_url,
            data=json.dumps(
                self._create_payload(
                    customer_id=self.customer_b.id,
                    product_id=self.product_b.id,
                )
            ),
            content_type="application/json",
        )

        self.assertEqual(
            response_b.status_code,
            201,
        )

        order_a = Order.objects.get(
            business=self.business_a,
        )

        order_b = Order.objects.get(
            business=self.business_b,
        )

        self.assertEqual(
            order_a.order_number,
            "ORD-000001",
        )

        self.assertEqual(
            order_b.order_number,
            "ORD-000001",
        )

        sequence_a = OrderNumberSequence.objects.get(
            business=self.business_a,
        )

        sequence_b = OrderNumberSequence.objects.get(
            business=self.business_b,
        )

        self.assertEqual(
            sequence_a.last_number,
            1,
        )

        self.assertEqual(
            sequence_b.last_number,
            1,
        )

    # ------------------------------------------------------------------
    # TENANT ISOLATION
    # ------------------------------------------------------------------

    def test_user_cannot_create_order_for_other_business_customer(self):
        self._login_as_a()

        payload = self._create_payload(
            customer_id=self.customer_b.id,
            product_id=self.product_a.id,
        )

        response = self.client.post(
            self.create_url,
            data=json.dumps(payload),
            content_type="application/json",
        )

        self.assertEqual(
            response.status_code,
            404,
        )

        self.assertEqual(
            response.json()["code"],
            "CUSTOMER_NOT_FOUND",
        )

        self.assertEqual(
            Order.objects.count(),
            0,
        )

    def test_user_cannot_create_order_with_other_business_product(self):
        self._login_as_a()

        payload = self._create_payload(
            customer_id=self.customer_a.id,
            product_id=self.product_b.id,
        )

        response = self.client.post(
            self.create_url,
            data=json.dumps(payload),
            content_type="application/json",
        )

        self.assertEqual(
            response.status_code,
            404,
        )

        self.assertEqual(
            response.json()["code"],
            "PRODUCT_NOT_FOUND",
        )

        self.assertEqual(
            Order.objects.count(),
            0,
        )

    # ------------------------------------------------------------------
    # LIST
    # ------------------------------------------------------------------

    def test_list_returns_only_current_business_orders(self):
        self._login_as_a()

        Order.objects.create(
            business=self.business_a,
            customer=self.customer_a,
            order_number="ORD-000001",
            status=Order.Status.DRAFT,
            payment_status=Order.PaymentStatus.UNPAID,
            subtotal="100.00",
            discount="0.00",
            tax="0.00",
            total="100.00",
            created_by=self.user_a,
        )

        Order.objects.create(
            business=self.business_b,
            customer=self.customer_b,
            order_number="ORD-000001",
            status=Order.Status.DRAFT,
            payment_status=Order.PaymentStatus.UNPAID,
            subtotal="200.00",
            discount="0.00",
            tax="0.00",
            total="200.00",
            created_by=self.user_b,
        )

        response = self.client.get(self.list_url)

        self.assertEqual(
            response.status_code,
            200,
        )

        body = response.json()

        self.assertEqual(
            body["status"],
            "success",
        )

        self.assertEqual(
            len(body["orders"]),
            1,
        )

        self.assertEqual(
            body["orders"][0]["order_number"],
            "ORD-000001",
        )

        self.assertEqual(
            body["orders"][0]["customer"]["store_name"],
            "Customer A",
        )

    # ------------------------------------------------------------------
    # DETAIL
    # ------------------------------------------------------------------

    def test_user_can_view_own_business_order(self):
        self._login_as_a()

        order = Order.objects.create(
            business=self.business_a,
            customer=self.customer_a,
            order_number="ORD-000001",
            status=Order.Status.DRAFT,
            payment_status=Order.PaymentStatus.UNPAID,
            subtotal="100.00",
            discount="0.00",
            tax="0.00",
            total="100.00",
            created_by=self.user_a,
        )

        response = self.client.get(
            reverse(
                "order_detail",
                kwargs={"order_id": order.id},
            )
        )

        self.assertEqual(
            response.status_code,
            200,
        )

        body = response.json()

        self.assertEqual(
            body["status"],
            "success",
        )

        self.assertEqual(
            body["order"]["id"],
            order.id,
        )

    def test_user_cannot_view_other_business_order(self):
        self._login_as_b()

        order = Order.objects.create(
            business=self.business_a,
            customer=self.customer_a,
            order_number="ORD-000001",
            status=Order.Status.DRAFT,
            payment_status=Order.PaymentStatus.UNPAID,
            subtotal="100.00",
            discount="0.00",
            tax="0.00",
            total="100.00",
            created_by=self.user_a,
        )

        response = self.client.get(
            reverse(
                "order_detail",
                kwargs={"order_id": order.id},
            )
        )

        self.assertEqual(
            response.status_code,
            404,
        )

        self.assertEqual(
            response.json()["code"],
            "ORDER_NOT_FOUND",
        )

    def test_nonexistent_order_returns_404(self):
        self._login_as_a()

        response = self.client.get(
            reverse(
                "order_detail",
                kwargs={"order_id": 999999},
            )
        )

        self.assertEqual(
            response.status_code,
            404,
        )

        self.assertEqual(
            response.json()["code"],
            "ORDER_NOT_FOUND",
        )