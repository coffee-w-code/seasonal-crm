from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ("customers", "0001_initial"),
        ("inventory", "0003_remove_customer"),
    ]

    operations = [
        migrations.SeparateDatabaseAndState(
            database_operations=[],
            state_operations=[
                migrations.AlterField(
                    model_name="customer",
                    name="business",
                    field=models.ForeignKey(
                        on_delete=django.db.models.deletion.CASCADE,
                        related_name="customers",
                        to="tenants.business",
                    ),
                ),
                migrations.AddIndex(
                    model_name="customer",
                    index=models.Index(
                        fields=["business", "phone_number"],
                        name="cust_business_phone_idx",
                    ),
                ),
            ],
        ),
    ]