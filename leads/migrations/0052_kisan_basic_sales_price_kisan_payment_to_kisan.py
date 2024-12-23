# Generated by Django 5.1.1 on 2024-10-21 05:38

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("leads", "0051_kisan_alter_plotbooking_project"),
    ]

    operations = [
        migrations.AddField(
            model_name="kisan",
            name="basic_sales_price",
            field=models.DecimalField(
                blank=True, decimal_places=2, max_digits=12, null=True
            ),
        ),
        migrations.AddField(
            model_name="kisan",
            name="payment_to_kisan",
            field=models.DecimalField(
                blank=True, decimal_places=2, max_digits=12, null=True
            ),
        ),
    ]
