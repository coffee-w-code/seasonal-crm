from django.db import models

from apps.tenants.models import Business


class Product(models.Model):
    """A product owned by a specific business."""

    business = models.ForeignKey(
        Business,
        on_delete=models.CASCADE,
        related_name="products",
    )

    name = models.CharField(max_length=100)

    twine_number = models.CharField(
        max_length=30,
    )

    mesh_size = models.CharField(
        max_length=50,
    )

    color = models.CharField(
        max_length=30,
    )

    selvedge_details = models.CharField(
        max_length=100,
        blank=True,
    )

    created_at = models.DateTimeField(
        auto_now_add=True,
    )

    updated_at = models.DateTimeField(
        auto_now=True,
    )

    class Meta:
        ordering = ["name"]

        indexes = [
            models.Index(
                fields=["business", "name"],
                name="product_business_name_idx",
            ),
        ]

    def __str__(self):
        return (
            f"{self.name} "
            f"({self.twine_number} - "
            f"{self.mesh_size} - "
            f"{self.color})"
        )


class InventoryItem(models.Model):
    """Current quantity of a product at a specific business location."""

    LOCATION_CHOICES = [
        ("HOME", "Home Base"),
        ("SHOP", "Main Shop"),
        ("WAREHOUSE", "Transport Warehouse"),
    ]

    business = models.ForeignKey(
        Business,
        on_delete=models.CASCADE,
        related_name="inventory_items",
    )

    product = models.ForeignKey(
        Product,
        on_delete=models.CASCADE,
        related_name="inventory_items",
    )

    location = models.CharField(
        max_length=10,
        choices=LOCATION_CHOICES,
    )

    quantity = models.PositiveIntegerField(
        default=0,
    )

    last_updated = models.DateTimeField(
        auto_now=True,
    )

    class Meta:
        constraints = [
            models.UniqueConstraint(
                fields=["business", "product", "location"],
                name="uniq_business_product_loc",
            ),
        ]

        indexes = [
            models.Index(
                fields=["business", "location"],
                name="inv_business_loc_idx",
            ),
        ]

    def __str__(self):
        return (
            f"{self.product.name}: "
            f"{self.quantity} units at "
            f"{self.get_location_display()}"
        )

class StockMovement(models.Model):
    """Immutable record of inventory movement."""

    MOVEMENT_TYPES = [
        ("INCOMING", "Fresh Arrival from Factory"),
        ("TRANSFER", "Internal Shift Between Locations"),
        ("OUTGOING", "Sold to Client / Dispatched"),
        ("ADJUSTMENT", "Inventory Reconciliation Adjustment"),
    ]

    LOCATION_CHOICES = [
        ("HOME", "Home Base"),
        ("SHOP", "Main Shop"),
        ("WAREHOUSE", "Transport Warehouse"),
        ("EXTERNAL", "External"),
    ]

    business = models.ForeignKey(
        Business,
        on_delete=models.CASCADE,
        related_name="stock_movements",
    )

    product = models.ForeignKey(
        Product,
        on_delete=models.CASCADE,
        related_name="stock_movements",
    )

    quantity = models.PositiveIntegerField()

    movement_type = models.CharField(
        max_length=15,
        choices=MOVEMENT_TYPES,
    )

    source_location = models.CharField(
        max_length=10,
        choices=LOCATION_CHOICES,
        default="EXTERNAL",
    )

    destination_location = models.CharField(
        max_length=10,
        choices=LOCATION_CHOICES,
        default="EXTERNAL",
    )

    timestamp = models.DateTimeField(
        auto_now_add=True,
    )

    notes = models.TextField(
        blank=True,
        null=True,
    )

    class Meta:
        ordering = ["-timestamp"]

        indexes = [
            models.Index(
                fields=["business", "product", "-timestamp"],
                name="movement_business_product_idx",
            ),
        ]

    def __str__(self):
        return (
            f"{self.movement_type}: "
            f"{self.quantity} units of "
            f"{self.product.name}"
        )


class StockAudit(models.Model):
    """Permanent record of inventory reconciliation."""

    INVESTIGATION_REASONS = [
        ("DAMAGE", "Damaged Stock"),
        ("MISSING_SALE", "Missing Sale Entry"),
        ("COUNT_ERROR", "Staff Counting Error"),
        ("SUPPLIER", "Supplier Discrepancy"),
        ("THEFT", "Theft Suspected"),
        ("OTHER", "Other / Unspecified"),
    ]

    business = models.ForeignKey(
        Business,
        on_delete=models.CASCADE,
        related_name="stock_audits",
    )

    product = models.ForeignKey(
        Product,
        on_delete=models.CASCADE,
        related_name="stock_audits",
    )

    location = models.CharField(
        max_length=10,
        choices=InventoryItem.LOCATION_CHOICES,
    )

    expected_quantity = models.PositiveIntegerField()

    actual_quantity = models.PositiveIntegerField()

    # actual - expected
    # Negative = shortage
    # Positive = surplus
    difference = models.IntegerField()

    reason = models.CharField(
        max_length=20,
        choices=INVESTIGATION_REASONS,
        default="OTHER",
    )

    owner_notes = models.TextField(
        blank=True,
        null=True,
    )

    timestamp = models.DateTimeField(
        auto_now_add=True,
    )

    class Meta:
        ordering = ["-timestamp"]

        indexes = [
            models.Index(
                fields=["business", "product", "-timestamp"],
                name="audit_business_product_idx",
            ),
        ]

    def __str__(self):
        return (
            f"Audit: {self.product.name} "
            f"({self.difference:+d} units at {self.location})"
        )