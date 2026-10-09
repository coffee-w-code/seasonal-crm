from __future__ import annotations

import json

from django.test import TestCase

from apps.tenants.models import Business

from apps.inventory.models import (
    InventoryItem,
    Product,
    StockMovement,
)
from apps.inventory.services.inventory_service import (
    InventoryService,
    InventoryServiceError,
    InsufficientStockError,
    InvalidLocationError,
    InvalidQuantityError,
    SameLocationTransferError,
)


class InventoryServiceTestCase(TestCase):
    """
    Tests the core inventory business logic.

    These tests do NOT involve:
    - OpenAI
    - WebSockets
    - React
    - AIToolRouter

    They test InventoryService directly.
    """

    @classmethod
    def setUpTestData(cls):
        cls.business = Business.objects.create(
            name="Test Fishing Business",
            owner_name="Test Owner",
            phone_number="9999999999",
            email="test@example.com",
            state_region="Uttar Pradesh",
            is_active=True,
        )

        cls.other_business = Business.objects.create(
            name="Other Fishing Business",
            owner_name="Other Owner",
            phone_number="8888888888",
            email="other@example.com",
            state_region="Uttar Pradesh",
            is_active=True,
        )

        cls.product = Product.objects.create(
            business=cls.business,
            name="Fishing Net",
        )

        cls.other_product = Product.objects.create(
            business=cls.other_business,
            name="Fishing Net",
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

        InventoryItem.objects.create(
            business=cls.business,
            product=cls.product,
            location="HOME",
            quantity=10,
        )

    # ------------------------------------------------------------------
    # Helpers
    # ------------------------------------------------------------------

    def get_stock_item(self, location: str) -> InventoryItem:
        return InventoryItem.objects.get(
            business=self.business,
            product=self.product,
            location=location,
        )

    # ------------------------------------------------------------------
    # CHECK INVENTORY
    # ------------------------------------------------------------------

    def test_get_stock_returns_total_inventory(self):
        result = InventoryService.get_stock(
            self.business,
            product_name="Fishing Net",
        )

        self.assertEqual(
            result["product_name"],
            "Fishing Net",
        )

        self.assertEqual(
            result["locations"]["WAREHOUSE"],
            100,
        )

        self.assertEqual(
            result["locations"]["SHOP"],
            20,
        )

        self.assertEqual(
            result["locations"]["HOME"],
            10,
        )

        self.assertEqual(
            result["total_quantity"],
            130,
        )

    def test_get_stock_for_specific_location(self):
        result = InventoryService.get_stock(
            self.business,
            product_name="Fishing Net",
            location="WAREHOUSE",
        )

        self.assertEqual(
            result["locations"],
            {
                "WAREHOUSE": 100,
            },
        )

        self.assertEqual(
            result["total_quantity"],
            100,
        )

    # ------------------------------------------------------------------
    # TRANSFER
    # ------------------------------------------------------------------

    def test_transfer_moves_stock_between_locations(self):
        result = InventoryService.transfer(
            self.business,
            product_name="Fishing Net",
            quantity=30,
            source_location="WAREHOUSE",
            destination_location="SHOP",
            notes="Test transfer",
        )

        warehouse = self.get_stock_item("WAREHOUSE")
        shop = self.get_stock_item("SHOP")

        self.assertEqual(
            warehouse.quantity,
            70,
        )

        self.assertEqual(
            shop.quantity,
            50,
        )

        self.assertEqual(
            result.quantity,
            30,
        )

        self.assertEqual(
            result.source_quantity_after,
            70,
        )

        self.assertEqual(
            result.destination_quantity_after,
            50,
        )

        self.assertEqual(
            result.movement_type,
            "TRANSFER",
        )

        movement = StockMovement.objects.get(
            id=result.movement_id,
        )

        self.assertEqual(
            movement.business,
            self.business,
        )

        self.assertEqual(
            movement.product,
            self.product,
        )

        self.assertEqual(
            movement.quantity,
            30,
        )

        self.assertEqual(
            movement.movement_type,
            "TRANSFER",
        )

        self.assertEqual(
            movement.source_location,
            "WAREHOUSE",
        )

        self.assertEqual(
            movement.destination_location,
            "SHOP",
        )

    def test_transfer_rejects_insufficient_stock(self):
        warehouse_before = self.get_stock_item(
            "WAREHOUSE"
        ).quantity

        shop_before = self.get_stock_item(
            "SHOP"
        ).quantity

        with self.assertRaises(InsufficientStockError):
            InventoryService.transfer(
                self.business,
                product_name="Fishing Net",
                quantity=500,
                source_location="WAREHOUSE",
                destination_location="SHOP",
            )

        warehouse_after = self.get_stock_item(
            "WAREHOUSE"
        ).quantity

        shop_after = self.get_stock_item(
            "SHOP"
        ).quantity

        self.assertEqual(
            warehouse_before,
            warehouse_after,
        )

        self.assertEqual(
            shop_before,
            shop_after,
        )

    def test_transfer_rejects_same_location(self):
        with self.assertRaises(
            SameLocationTransferError
        ):
            InventoryService.transfer(
                self.business,
                product_name="Fishing Net",
                quantity=10,
                source_location="SHOP",
                destination_location="SHOP",
            )

    def test_transfer_rejects_invalid_source_location(self):
        with self.assertRaises(
            InvalidLocationError
        ):
            InventoryService.transfer(
                self.business,
                product_name="Fishing Net",
                quantity=10,
                source_location="GARAGE",
                destination_location="SHOP",
            )

    def test_transfer_rejects_invalid_destination_location(self):
        with self.assertRaises(
            InvalidLocationError
        ):
            InventoryService.transfer(
                self.business,
                product_name="Fishing Net",
                quantity=10,
                source_location="SHOP",
                destination_location="GARAGE",
            )

    def test_transfer_rejects_zero_quantity(self):
        with self.assertRaises(
            InvalidQuantityError
        ):
            InventoryService.transfer(
                self.business,
                product_name="Fishing Net",
                quantity=0,
                source_location="WAREHOUSE",
                destination_location="SHOP",
            )

    def test_transfer_rejects_negative_quantity(self):
        with self.assertRaises(
            InvalidQuantityError
        ):
            InventoryService.transfer(
                self.business,
                product_name="Fishing Net",
                quantity=-10,
                source_location="WAREHOUSE",
                destination_location="SHOP",
            )

    # ------------------------------------------------------------------
    # DISPATCH
    # ------------------------------------------------------------------

    def test_dispatch_removes_stock(self):
        result = InventoryService.dispatch(
            self.business,
            product_name="Fishing Net",
            quantity=15,
            source_location="SHOP",
            notes="Customer dispatch",
        )

        shop = self.get_stock_item("SHOP")

        self.assertEqual(
            shop.quantity,
            5,
        )

        self.assertEqual(
            result.source_quantity_after,
            5,
        )

        self.assertEqual(
            result.destination_location,
            "EXTERNAL",
        )

        self.assertEqual(
            result.movement_type,
            "OUTGOING",
        )

        movement = StockMovement.objects.get(
            id=result.movement_id,
        )

        self.assertEqual(
            movement.movement_type,
            "OUTGOING",
        )

        self.assertEqual(
            movement.source_location,
            "SHOP",
        )

        self.assertEqual(
            movement.destination_location,
            "EXTERNAL",
        )

    def test_dispatch_rejects_insufficient_stock(self):
        shop_before = self.get_stock_item(
            "SHOP"
        ).quantity

        with self.assertRaises(
            InsufficientStockError
        ):
            InventoryService.dispatch(
                self.business,
                product_name="Fishing Net",
                quantity=999,
                source_location="SHOP",
            )

        shop_after = self.get_stock_item(
            "SHOP"
        ).quantity

        self.assertEqual(
            shop_before,
            shop_after,
        )

    # ------------------------------------------------------------------
    # RECEIVE
    # ------------------------------------------------------------------

    def test_receive_adds_stock(self):
        result = InventoryService.receive(
            self.business,
            product_name="Fishing Net",
            quantity=50,
            destination_location="WAREHOUSE",
            notes="Supplier delivery",
        )

        warehouse = self.get_stock_item(
            "WAREHOUSE"
        )

        self.assertEqual(
            warehouse.quantity,
            150,
        )

        self.assertEqual(
            result.destination_quantity_after,
            150,
        )

        self.assertEqual(
            result.source_location,
            "EXTERNAL",
        )

        self.assertEqual(
            result.destination_location,
            "WAREHOUSE",
        )

        self.assertEqual(
            result.movement_type,
            "INCOMING",
        )

        movement = StockMovement.objects.get(
            id=result.movement_id,
        )

        self.assertEqual(
            movement.movement_type,
            "INCOMING",
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
    # ADJUSTMENT
    # ------------------------------------------------------------------

    def test_adjust_changes_stock_to_physical_count(self):
        result = InventoryService.adjust(
            self.business,
            product_name="Fishing Net",
            location="WAREHOUSE",
            new_quantity=90,
            notes="Physical stock count",
        )

        warehouse = self.get_stock_item(
            "WAREHOUSE"
        )

        self.assertEqual(
            warehouse.quantity,
            90,
        )

        self.assertEqual(
            result.quantity,
            10,
        )

        self.assertEqual(
            result.movement_type,
            "ADJUSTMENT",
        )

        movement = StockMovement.objects.get(
            id=result.movement_id,
        )

        self.assertEqual(
            movement.quantity,
            10,
        )

        self.assertEqual(
            movement.movement_type,
            "ADJUSTMENT",
        )

    def test_adjust_rejects_negative_quantity(self):
        with self.assertRaises(
            InvalidQuantityError
        ):
            InventoryService.adjust(
                self.business,
                product_name="Fishing Net",
                location="WAREHOUSE",
                new_quantity=-1,
            )

    # ------------------------------------------------------------------
    # PRODUCT RESOLUTION
    # ------------------------------------------------------------------

    def test_product_can_be_found_case_insensitively(self):
        product = InventoryService.resolve_product(
            self.business,
            product_name="fIsHiNg NeT",
        )

        self.assertEqual(
            product.id,
            self.product.id,
        )

    def test_unknown_product_is_rejected(self):
        with self.assertRaises(
            InventoryServiceError
        ):
            InventoryService.resolve_product(
                self.business,
                product_name="Unknown Product",
            )

    # ------------------------------------------------------------------
    # TENANT ISOLATION
    # ------------------------------------------------------------------

    def test_business_cannot_access_another_business_product(self):
        with self.assertRaises(
            InventoryServiceError
        ):
            InventoryService.get_stock(
                self.business,
                product_id=self.other_product.id,
            )

    # ------------------------------------------------------------------
    # MOVEMENT HISTORY
    # ------------------------------------------------------------------

    def test_movement_history_is_scoped_to_business(self):
        InventoryService.receive(
            self.business,
            product_name="Fishing Net",
            quantity=5,
            destination_location="WAREHOUSE",
        )

        history = InventoryService.get_movement_history(
            self.business,
        )

        self.assertEqual(
            history.count(),
            1,
        )

        movement = history.first()

        self.assertEqual(
            movement.business,
            self.business,
        )

        self.assertEqual(
            movement.product,
            self.product,
        )