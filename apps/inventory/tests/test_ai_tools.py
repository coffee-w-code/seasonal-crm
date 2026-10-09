from __future__ import annotations

import json

from django.test import TestCase

from apps.inventory.ai.tool_router import AIToolRouter
from apps.inventory.models import (
    InventoryItem,
    Product,
    StockMovement,
)
from apps.tenants.models import Business


class AIInventoryToolsTestCase(TestCase):
    """Integration tests for the AI inventory tool layer."""

    def setUp(self):
        self.business = Business.objects.create(
            name="Test Fishing Nets",
            owner_name="Test Owner",
            phone_number="9876543210",
            email="test@example.com",
            state_region="Uttar Pradesh",
            is_active=True,
        )

        self.other_business = Business.objects.create(
            name="Other Business",
            owner_name="Other Owner",
            phone_number="9876543211",
            email="other@example.com",
            state_region="Uttar Pradesh",
            is_active=True,
        )

        self.product = Product.objects.create(
            business=self.business,
            name="Nylon Net",
            twine_number="210D",
            mesh_size="2 inch",
            color="Green",
            selvedge_details="Standard",
        )

        self.other_product = Product.objects.create(
            business=self.other_business,
            name="Nylon Net",
            twine_number="210D",
            mesh_size="2 inch",
            color="Green",
            selvedge_details="Standard",
        )

        InventoryItem.objects.create(
            business=self.business,
            product=self.product,
            location="HOME",
            quantity=10,
        )

        InventoryItem.objects.create(
            business=self.business,
            product=self.product,
            location="SHOP",
            quantity=20,
        )

        InventoryItem.objects.create(
            business=self.business,
            product=self.product,
            location="WAREHOUSE",
            quantity=100,
        )

        self.router = AIToolRouter(
            business=self.business,
        )

    # ------------------------------------------------------------------
    # check_inventory
    # ------------------------------------------------------------------

    def test_check_inventory_returns_location_stock(self):
        result = self.router.execute(
            "check_inventory",
            {
                "product_name": "Nylon Net",
                "location": "WAREHOUSE",
            },
        )

        data = json.loads(result)

        self.assertEqual(
            data["status"],
            "success",
        )

        self.assertEqual(
            data["data"]["total_quantity"],
            100,
        )

        self.assertEqual(
            data["data"]["locations"]["WAREHOUSE"],
            100,
        )

    def test_check_inventory_returns_total_stock(self):
        result = self.router.execute(
            "check_inventory",
            {
                "product_name": "Nylon Net",
            },
        )

        data = json.loads(result)

        self.assertEqual(
            data["status"],
            "success",
        )

        self.assertEqual(
            data["data"]["total_quantity"],
            130,
        )

    # ------------------------------------------------------------------
    # transfer_inventory
    # ------------------------------------------------------------------

    def test_transfer_inventory_moves_stock_between_locations(self):
        result = self.router.execute(
            "transfer_inventory",
            {
                "product_name": "Nylon Net",
                "quantity": 25,
                "source_location": "WAREHOUSE",
                "destination_location": "SHOP",
            },
        )

        data = json.loads(result)

        self.assertEqual(
            data["status"],
            "success",
        )

        self.assertEqual(
            data["data"]["quantity"],
            25,
        )

        self.assertEqual(
            data["data"]["source_quantity_after"],
            75,
        )

        self.assertEqual(
            data["data"]["destination_quantity_after"],
            45,
        )

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

        self.assertEqual(
            warehouse.quantity,
            75,
        )

        self.assertEqual(
            shop.quantity,
            45,
        )

        self.assertEqual(
            StockMovement.objects.filter(
                business=self.business,
                product=self.product,
                movement_type="TRANSFER",
            ).count(),
            1,
        )

    def test_transfer_inventory_rejects_insufficient_stock(self):
        result = self.router.execute(
            "transfer_inventory",
            {
                "product_name": "Nylon Net",
                "quantity": 500,
                "source_location": "WAREHOUSE",
                "destination_location": "SHOP",
            },
        )

        data = json.loads(result)

        self.assertEqual(
            data["status"],
            "error",
        )

        self.assertEqual(
            data["error_code"],
            "INVENTORY_OPERATION_REJECTED",
        )

        warehouse = InventoryItem.objects.get(
            business=self.business,
            product=self.product,
            location="WAREHOUSE",
        )

        self.assertEqual(
            warehouse.quantity,
            100,
        )

    def test_transfer_inventory_rejects_same_location(self):
        result = self.router.execute(
            "transfer_inventory",
            {
                "product_name": "Nylon Net",
                "quantity": 10,
                "source_location": "SHOP",
                "destination_location": "SHOP",
            },
        )

        data = json.loads(result)

        self.assertEqual(
            data["status"],
            "error",
        )

        self.assertEqual(
            data["error_code"],
            "INVENTORY_OPERATION_REJECTED",
        )

    # ------------------------------------------------------------------
    # dispatch_inventory
    # ------------------------------------------------------------------

    def test_dispatch_inventory_reduces_stock(self):
        result = self.router.execute(
            "dispatch_inventory",
            {
                "product_name": "Nylon Net",
                "quantity": 30,
                "source_location": "WAREHOUSE",
                "customer_name": "Ramesh Store",
            },
        )

        data = json.loads(result)

        self.assertEqual(
            data["status"],
            "success",
        )

        self.assertEqual(
            data["data"]["quantity"],
            30,
        )

        self.assertEqual(
            data["data"]["remaining_source_quantity"],
            70,
        )

        warehouse = InventoryItem.objects.get(
            business=self.business,
            product=self.product,
            location="WAREHOUSE",
        )

        self.assertEqual(
            warehouse.quantity,
            70,
        )

        movement = StockMovement.objects.get(
            business=self.business,
            product=self.product,
            movement_type="OUTGOING",
        )

        self.assertEqual(
            movement.quantity,
            30,
        )

        self.assertIn(
            "Customer: Ramesh Store",
            movement.notes,
        )

    def test_dispatch_inventory_rejects_insufficient_stock(self):
        result = self.router.execute(
            "dispatch_inventory",
            {
                "product_name": "Nylon Net",
                "quantity": 500,
                "source_location": "WAREHOUSE",
            },
        )

        data = json.loads(result)

        self.assertEqual(
            data["status"],
            "error",
        )

        self.assertEqual(
            data["error_code"],
            "INVENTORY_OPERATION_REJECTED",
        )

    # ------------------------------------------------------------------
    # receive_inventory
    # ------------------------------------------------------------------

    def test_receive_inventory_increases_stock(self):
        result = self.router.execute(
            "receive_inventory",
            {
                "product_name": "Nylon Net",
                "quantity": 50,
                "destination_location": "WAREHOUSE",
                "notes": "Factory delivery",
            },
        )

        data = json.loads(result)

        self.assertEqual(
            data["status"],
            "success",
        )

        self.assertEqual(
            data["data"]["quantity"],
            50,
        )

        self.assertEqual(
            data["data"]["destination_quantity_after"],
            150,
        )

        warehouse = InventoryItem.objects.get(
            business=self.business,
            product=self.product,
            location="WAREHOUSE",
        )

        self.assertEqual(
            warehouse.quantity,
            150,
        )

        movement = StockMovement.objects.get(
            business=self.business,
            product=self.product,
            movement_type="INCOMING",
        )

        self.assertEqual(
            movement.quantity,
            50,
        )

        self.assertEqual(
            movement.destination_location,
            "WAREHOUSE",
        )

    # ------------------------------------------------------------------
    # Validation / tenant isolation
    # ------------------------------------------------------------------

    def test_unknown_tool_is_rejected(self):
        result = self.router.execute(
            "delete_everything",
            {},
        )

        data = json.loads(result)

        self.assertEqual(
            data["status"],
            "error",
        )

        self.assertEqual(
            data["error_code"],
            "UNKNOWN_TOOL",
        )

    def test_missing_required_argument_is_rejected(self):
        result = self.router.execute(
            "check_inventory",
            {},
        )

        data = json.loads(result)

        self.assertEqual(
            data["status"],
            "error",
        )

        self.assertEqual(
            data["error_code"],
            "INVALID_ARGUMENTS",
        )

    def test_invalid_quantity_is_rejected(self):
        result = self.router.execute(
            "transfer_inventory",
            {
                "product_name": "Nylon Net",
                "quantity": 0,
                "source_location": "WAREHOUSE",
                "destination_location": "SHOP",
            },
        )

        data = json.loads(result)

        self.assertEqual(
            data["status"],
            "error",
        )

        self.assertEqual(
            data["error_code"],
            "INVALID_ARGUMENTS",
        )

    def test_business_cannot_access_another_business_product(self):
        result = self.router.execute(
            "check_inventory",
            {
                "product_name": "Nylon Net",
                "location": "WAREHOUSE",
            },
        )

        data = json.loads(result)

        self.assertEqual(
            data["status"],
            "success",
        )

        self.assertEqual(
            data["data"]["product_id"],
            self.product.id,
        )

        self.assertNotEqual(
            data["data"]["product_id"],
            self.other_product.id,
        )