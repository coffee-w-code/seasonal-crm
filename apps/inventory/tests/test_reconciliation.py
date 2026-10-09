from django.test import TestCase

from apps.inventory.models import InventoryItem, Product
from apps.inventory.services.reconciliation import (
    calculate_stock_discrepancy,
)
from apps.tenants.models import Business


class ReconciliationTenantIsolationTests(TestCase):
    """Verify that inventory operations remain isolated per business."""

    def setUp(self):
        self.business_a = Business.objects.create(
            name="Business A",
            owner_name="Owner A",
        )

        self.business_b = Business.objects.create(
            name="Business B",
            owner_name="Owner B",
        )

        self.product_a = Product.objects.create(
            business=self.business_a,
            name="Mono Fishing Net",
            twine_number="No. 2",
            mesh_size="40mm",
            color="Blue",
        )

        self.inventory_a = InventoryItem.objects.create(
            business=self.business_a,
            product=self.product_a,
            location="WAREHOUSE",
            quantity=100,
        )

    def test_business_can_access_its_own_inventory(self):
        """Business A should be able to reconcile its own inventory."""

        result = calculate_stock_discrepancy(
            business=self.business_a,
            product_id=self.product_a.id,
            location="WAREHOUSE",
            actual_count=95,
        )

        self.assertEqual(
            result["status"],
            "WARNING_SHORTAGE",
        )

        self.assertEqual(
            result["expected"],
            100,
        )

        self.assertEqual(
            result["actual"],
            95,
        )

        self.assertEqual(
            result["difference"],
            -5,
        )

    def test_business_cannot_access_another_business_product(self):
        """
        Business B must not be able to access
        Business A's product.
        """

        result = calculate_stock_discrepancy(
            business=self.business_b,
            product_id=self.product_a.id,
            location="WAREHOUSE",
            actual_count=95,
        )

        self.assertEqual(
            result["status"],
            "error",
        )

        self.assertEqual(
            result["code"],
            "PRODUCT_NOT_FOUND",
        )