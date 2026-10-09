from django.test import TestCase

from apps.inventory.models import InventoryItem, Product
from apps.inventory.ai.tool_router import AIToolRouter
from apps.tenants.models import Business


class AIToolRouterTests(TestCase):
    """Test AI tool routing into InventoryService."""

    def setUp(self):
        self.business = Business.objects.create(
            name="Test Business",
            owner_name="Test Owner",
        )

        self.product = Product.objects.create(
            business=self.business,
            name="Mono Fishing Net",
            twine_number="No. 2",
            mesh_size="40mm",
            color="Blue",
        )

        self.warehouse = InventoryItem.objects.create(
            business=self.business,
            product=self.product,
            location="WAREHOUSE",
            quantity=100,
        )

        self.shop = InventoryItem.objects.create(
            business=self.business,
            product=self.product,
            location="SHOP",
            quantity=20,
        )

        self.router = AIToolRouter(self.business)

    # ------------------------------------------------------------------
    # check_inventory
    # ------------------------------------------------------------------

    def test_check_inventory(self):
        """AI should be able to check current inventory."""

        result = self.router.execute(
            "check_inventory",
            {
                "product_name": "Mono Fishing Net",
                "location": "WAREHOUSE",
            },
        )

        self.assertIn('"status": "success"', result)
        self.assertIn('"operation": "inventory_checked"', result)
        self.assertIn('"total_quantity": 100', result)

    def test_check_inventory_total_stock(self):
        """AI should be able to check total stock across locations."""

        result = self.router.execute(
            "check_inventory",
            {
                "product_name": "Mono Fishing Net",
            },
        )

        self.assertIn('"status": "success"', result)
        self.assertIn('"total_quantity": 120', result)

    # ------------------------------------------------------------------
    # transfer_inventory
    # ------------------------------------------------------------------

    def test_transfer_inventory(self):
        """AI should be able to transfer stock between locations."""

        result = self.router.execute(
            "transfer_inventory",
            {
                "product_name": "Mono Fishing Net",
                "quantity": 30,
                "source_location": "WAREHOUSE",
                "destination_location": "SHOP",
            },
        )

        self.assertIn('"status": "success"', result)
        self.assertIn(
            '"operation": "inventory_transferred"',
            result,
        )

        self.warehouse.refresh_from_db()
        self.shop.refresh_from_db()

        self.assertEqual(self.warehouse.quantity, 70)
        self.assertEqual(self.shop.quantity, 50)

    # ------------------------------------------------------------------
    # dispatch_inventory
    # ------------------------------------------------------------------

    def test_dispatch_inventory(self):
        """AI should be able to dispatch stock externally."""

        result = self.router.execute(
            "dispatch_inventory",
            {
                "product_name": "Mono Fishing Net",
                "quantity": 10,
                "source_location": "WAREHOUSE",
                "customer_name": "ABC Traders",
            },
        )

        self.assertIn('"status": "success"', result)
        self.assertIn(
            '"operation": "inventory_dispatched"',
            result,
        )
        self.assertIn('"customer_name": "ABC Traders"', result)

        self.warehouse.refresh_from_db()

        self.assertEqual(self.warehouse.quantity, 90)

    # ------------------------------------------------------------------
    # receive_inventory
    # ------------------------------------------------------------------

    def test_receive_inventory(self):
        """AI should be able to record newly received stock."""

        result = self.router.execute(
            "receive_inventory",
            {
                "product_name": "Mono Fishing Net",
                "quantity": 50,
                "destination_location": "WAREHOUSE",
            },
        )

        self.assertIn('"status": "success"', result)
        self.assertIn(
            '"operation": "inventory_received"',
            result,
        )

        self.warehouse.refresh_from_db()

        self.assertEqual(self.warehouse.quantity, 150)

    # ------------------------------------------------------------------
    # Unknown tool
    # ------------------------------------------------------------------

    def test_unknown_tool_returns_error(self):
        """Unknown AI tools must never reach the inventory service."""

        result = self.router.execute(
            "delete_everything",
            {},
        )

        self.assertIn('"status": "error"', result)
        self.assertIn('"error_code": "UNKNOWN_TOOL"', result)

    # ------------------------------------------------------------------
    # Invalid arguments
    # ------------------------------------------------------------------

    def test_missing_product_name_returns_error(self):
        """Missing required product name should be rejected."""

        result = self.router.execute(
            "check_inventory",
            {
                "location": "WAREHOUSE",
            },
        )

        self.assertIn('"status": "error"', result)
        self.assertIn('"error_code": "INVALID_ARGUMENTS"', result)

    def test_invalid_quantity_returns_error(self):
        """Zero or negative quantities must be rejected."""

        result = self.router.execute(
            "transfer_inventory",
            {
                "product_name": "Mono Fishing Net",
                "quantity": 0,
                "source_location": "WAREHOUSE",
                "destination_location": "SHOP",
            },
        )

        self.assertIn('"status": "error"', result)
        self.assertIn('"error_code": "INVALID_ARGUMENTS"', result)

    # ------------------------------------------------------------------
    # Business rules
    # ------------------------------------------------------------------

    def test_insufficient_stock_returns_error(self):
        """AI cannot transfer more stock than is available."""

        result = self.router.execute(
            "transfer_inventory",
            {
                "product_name": "Mono Fishing Net",
                "quantity": 500,
                "source_location": "WAREHOUSE",
                "destination_location": "SHOP",
            },
        )

        self.assertIn('"status": "error"', result)
        self.assertIn(
            '"error_code": "INVENTORY_OPERATION_REJECTED"',
            result,
        )

    def test_same_location_transfer_returns_error(self):
        """AI cannot transfer stock to the same location."""

        result = self.router.execute(
            "transfer_inventory",
            {
                "product_name": "Mono Fishing Net",
                "quantity": 10,
                "source_location": "WAREHOUSE",
                "destination_location": "WAREHOUSE",
            },
        )

        self.assertIn('"status": "error"', result)
        self.assertIn(
            '"error_code": "INVENTORY_OPERATION_REJECTED"',
            result,
        )

    # ------------------------------------------------------------------
    # Product resolution
    # ------------------------------------------------------------------

    def test_unknown_product_returns_error(self):
        """AI should receive a safe error for an unknown product."""

        result = self.router.execute(
            "check_inventory",
            {
                "product_name": "Unknown Product",
            },
        )

        self.assertIn('"status": "error"', result)
        self.assertIn(
            '"error_code": "INVENTORY_OPERATION_REJECTED"',
            result,
        )