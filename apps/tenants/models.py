from django.db import models


class Business(models.Model):
    """
    Represents a business using the SaaS platform.

    Every business owns its own customers, products,
    inventory, orders, and other business data.
    """

    name = models.CharField(max_length=150)

    owner_name = models.CharField(max_length=100)

    phone_number = models.CharField(
        max_length=15,
        blank=True,
    )

    email = models.EmailField(
        blank=True,
    )

    state_region = models.CharField(
        max_length=100,
        blank=True,
    )

    gstin = models.CharField(
        max_length=15,
        blank=True,
        null=True,
    )

    is_active = models.BooleanField(
        default=True,
    )

    created_at = models.DateTimeField(
        auto_now_add=True,
    )

    updated_at = models.DateTimeField(
        auto_now=True,
    )

    class Meta:
        ordering = ["name"]

    def __str__(self):
        return self.name