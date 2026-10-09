from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ("inventory", "0002_customer_remaining_balance"),
        ("orders", "0004_alter_order_customer"),
    ]

    operations = [
        migrations.SeparateDatabaseAndState(
            database_operations=[],
            state_operations=[
                migrations.DeleteModel(
                    name="Customer",
                ),
            ],
        ),
    ]