from __future__ import annotations

import json

from django.contrib.auth import get_user_model
from django.test import Client, TestCase

from apps.accounts.context import set_current_business
from apps.accounts.models import BusinessMembership
from apps.inventory.models import InventoryItem, Product, StockMovement
from apps.tenants.models import Business


class InventoryApiTestCase(TestCase):
    """
    HTTP-level tests for the inventory stock-movement API.

    These tests verify that the HTTP boundary:
    - resolves the user's explicitly selected business;
    - passes the business into the inventory service;
    - supports receive, transfer, and dispatch;
    - preserves tenant isolation;
    - returns appropriate validation errors.
    """

    @classmethod
    def setUpTestData(cls):
        User = get_user_model()

        cls.business = Business.objects.create(
            name="API Test Business",
            owner_name="API Owner",
            phone_number="9999999999",
            email="api@test.com",
            state_region="Uttar Pradesh",
            is_active=True,
        )

        cls.other_business = Business.objects.create(
            name="Other API Business",
            owner_name="Other Owner",
            phone_number="8888888888",
            email="other@test.com",
            state_region="Uttar Pradesh",
            is_active=True,
        )

        cls.user = User.objects.create_user(
            username="inventory_api_user",
            password="test-password-123",
        )

        cls.other_user = User.objects.create_user(
            username="other_inventory_api_user",
            password="test-password-123",
        )

        BusinessMembership.objects.create(
            user=cls.user,
            business=cls.business,
            role=BusinessMembership.Role.OWNER,
            is_active=True,
        )

        BusinessMembership.objects.create(
            user=cls.other_user,
            business=cls.other_business,
            role=BusinessMembership.Role.OWNER,
            is_active=True,
        )

        cls.product = Product.objects.create(
            business=cls.business,
            name="API Fishing Net",
        )

        cls.other_product = Product.objects.create(
            business=cls.other_business,
            name="API Fishing Net",
        )

        InventoryItem.objects.create(
            business=cls.business,
            product=cls.product,
            location="WAREHOUSE",
            quantity=100,
        )

        InventoryItem.objects.create(
            business=cls.business,
            product=cls.product,
            location="SHOP",
            quantity=20,
        )

    def setUp(self):
        self.client = Client()

        # Explicitly select the business through the central
        # current-business context mechanism.
        set_current_business(
            self.user,
            self.business,
        )

    def login(self):
        self.client.force_login(self.user)

    def post_stock_move(
        self,
        *,
        product_id,
        quantity,
        source,
        destination,
        notes=None,
    ):
        return self.client.post(
            "/inventory/move/",
            data=json.dumps(
                {
                    "product_id": product_id,
                    "quantity": quantity,
                    "source": source,
                    "destination": destination,
                    "notes": notes,
                }
            ),
            content_type="application/json",
        )

    # ------------------------------------------------------------------
    # RECEIVE
    # ------------------------------------------------------------------

    def test_stock_move_receive(self):
        self.login()

        response = self.post_stock_move(
            product_id=self.product.id,
            quantity=10,
            source="EXTERNAL",
            destination="WAREHOUSE",
            notes="Supplier delivery",
        )

        self.assertEqual(response.status_code, 200)

        warehouse = InventoryItem.objects.get(
            business=self.business,
            product=self.product,
            location="WAREHOUSE",
        )

        self.assertEqual(warehouse.quantity, 110)

        movement = StockMovement.objects.get(
            business=self.business,
            product=self.product,
            quantity=10,
            movement_type="INCOMING",
        )

        self.assertEqual(
            movement.source_location,
            "EXTERNAL",
        )

        self.assertEqual(
            movement.destination_location,
            "WAREHOUSE",
        )

    # ------------------------------------------------------------------
    # TRANSFER
    # ------------------------------------------------------------------

    def test_stock_move_transfer(self):
        self.login()

        response = self.post_stock_move(
            product_id=self.product.id,
            quantity=25,
            source="WAREHOUSE",
            destination="SHOP",
            notes="Move stock to shop",
        )

        self.assertEqual(response.status_code, 200)

        warehouse = InventoryItem.objects.get(
            business=self.business,
            product=self.product,
            location="WAREHOUSE",
        )

        shop = InventoryItem.objects.get(
            business=self.business,
            product=self.product,
            location="SHOP",
        )

        self.assertEqual(warehouse.quantity, 75)
        self.assertEqual(shop.quantity, 45)

        movement = StockMovement.objects.get(
            business=self.business,
            product=self.product,
            quantity=25,
            movement_type="TRANSFER",
        )

        self.assertEqual(
            movement.source_location,
            "WAREHOUSE",
        )

        self.assertEqual(
            movement.destination_location,
            "SHOP",
        )

    # ------------------------------------------------------------------
    # DISPATCH
    # ------------------------------------------------------------------

    def test_stock_move_dispatch(self):
        self.login()

        response = self.post_stock_move(
            product_id=self.product.id,
            quantity=15,
            source="SHOP",
            destination="EXTERNAL",
            notes="Customer dispatch",
        )

        self.assertEqual(response.status_code, 200)

        shop = InventoryItem.objects.get(
            business=self.business,
            product=self.product,
            location="SHOP",
        )

        self.assertEqual(shop.quantity, 5)

        movement = StockMovement.objects.get(
            business=self.business,
            product=self.product,
            quantity=15,
            movement_type="OUTGOING",
        )

        self.assertEqual(
            movement.source_location,
            "SHOP",
        )

        self.assertEqual(
            movement.destination_location,
            "EXTERNAL",
        )

    # ------------------------------------------------------------------
    # TENANT ISOLATION
    # ------------------------------------------------------------------

    def test_stock_move_cannot_access_product_from_another_business(self):
        self.login()

        response = self.post_stock_move(
            product_id=self.other_product.id,
            quantity=10,
            source="EXTERNAL",
            destination="WAREHOUSE",
        )

        self.assertEqual(response.status_code, 400)

        self.assertFalse(
            InventoryItem.objects.filter(
                business=self.business,
                product=self.other_product,
            ).exists()
        )

    # ------------------------------------------------------------------
    # VALIDATION
    # ------------------------------------------------------------------

    def test_stock_move_rejects_zero_quantity(self):
        self.login()

        response = self.post_stock_move(
            product_id=self.product.id,
            quantity=0,
            source="WAREHOUSE",
            destination="SHOP",
        )

        self.assertEqual(response.status_code, 400)

    def test_stock_move_rejects_insufficient_stock(self):
        self.login()

        response = self.post_stock_move(
            product_id=self.product.id,
            quantity=999,
            source="WAREHOUSE",
            destination="SHOP",
        )

        self.assertEqual(response.status_code, 400)

        warehouse = InventoryItem.objects.get(
            business=self.business,
            product=self.product,
            location="WAREHOUSE",
        )

        shop = InventoryItem.objects.get(
            business=self.business,
            product=self.product,
            location="SHOP",
        )

        self.assertEqual(warehouse.quantity, 100)
        self.assertEqual(shop.quantity, 20)

    def test_stock_move_requires_authenticated_user(self):
        response = self.post_stock_move(
            product_id=self.product.id,
            quantity=10,
            source="EXTERNAL",
            destination="WAREHOUSE",
        )

        self.assertEqual(response.status_code, 403)

    def test_stock_move_requires_selected_business(self):
        self.client.force_login(self.user)

        from apps.accounts.models import UserBusinessContext

        UserBusinessContext.objects.filter(
            user=self.user,
        ).delete()

        response = self.post_stock_move(
            product_id=self.product.id,
            quantity=10,
            source="EXTERNAL",
            destination="WAREHOUSE",
        )

        self.assertEqual(response.status_code, 403)
