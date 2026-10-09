from django.db import models

from apps.tenants.models import Business


class Customer(models.Model):
    """
    A customer belonging to a specific business.

    The physical database table is intentionally kept as
    `inventory_customer` during the migration from the legacy
    inventory app to the dedicated customers app.
    """

    business = models.ForeignKey(
        Business,
        on_delete=models.CASCADE,
        related_name="customers",
    )

    store_name = models.CharField(max_length=150)
    owner_name = models.CharField(max_length=100)
    phone_number = models.CharField(max_length=15)
    state_region = models.CharField(max_length=50)
    gstin = models.CharField(
        max_length=15,
        blank=True,
        null=True,
    )

    remaining_balance = models.DecimalField(
        max_digits=12,
        decimal_places=2,
        default=0.00,
        help_text="Tracks outstanding unpaid balance for wholesale records.",
    )

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = "inventory_customer"
        indexes = [
            models.Index(
                fields=["business", "phone_number"],
                name="cust_business_phone_idx",
            ),
        ]
        constraints = [
            models.UniqueConstraint(
                fields=["business", "phone_number"],
                name="unique_customer_phone_per_business",
            ),
        ]

    def __str__(self):
        return (
            f"{self.store_name} "
            f"({self.owner_name} - "
            f"{self.state_region})"
        )