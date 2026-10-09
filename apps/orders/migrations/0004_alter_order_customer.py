from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("customers", "0001_initial"),
        ("orders", "0003_ordernumbersequence"),
    ]

    operations = [
        migrations.SeparateDatabaseAndState(
            database_operations=[],
            state_operations=[
                migrations.AlterField(
                    model_name="order",
                    name="customer",
                    field=models.ForeignKey(
                        on_delete=models.PROTECT,
                        related_name="orders",
                        to="customers.customer",
                    ),
                ),
            ],
        ),
    ]