from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    initial = True

    dependencies = [
        ("inventory", "0002_customer_remaining_balance"),
        ("tenants", "0001_initial"),
    ]

    operations = [
        migrations.SeparateDatabaseAndState(
            database_operations=[],
            state_operations=[
                migrations.CreateModel(
                    name="Customer",
                    fields=[
                        (
                            "id",
                            models.BigAutoField(
                                auto_created=True,
                                primary_key=True,
                                serialize=False,
                                verbose_name="ID",
                            ),
                        ),
                        (
                            "store_name",
                            models.CharField(
                                max_length=150,
                            ),
                        ),
                        (
                            "owner_name",
                            models.CharField(
                                max_length=100,
                            ),
                        ),
                        (
                            "phone_number",
                            models.CharField(
                                max_length=15,
                            ),
                        ),
                        (
                            "state_region",
                            models.CharField(
                                max_length=50,
                            ),
                        ),
                        (
                            "gstin",
                            models.CharField(
                                blank=True,
                                max_length=15,
                                null=True,
                            ),
                        ),
                        (
                            "remaining_balance",
                            models.DecimalField(
                                decimal_places=2,
                                default=0.0,
                                help_text=(
                                    "Tracks outstanding unpaid balance "
                                    "for wholesale records."
                                ),
                                max_digits=12,
                            ),
                        ),
                        (
                            "created_at",
                            models.DateTimeField(
                                auto_now_add=True,
                            ),
                        ),
                        (
                            "updated_at",
                            models.DateTimeField(
                                auto_now=True,
                            ),
                        ),
                        (
                            "business",
                            models.ForeignKey(
                                on_delete=django.db.models.deletion.CASCADE,
                                related_name="customer_records",
                                to="tenants.business",
                            ),
                        ),
                    ],
                    options={
                        "db_table": "inventory_customer",
                    },
                ),
            ],
        ),
    ]
