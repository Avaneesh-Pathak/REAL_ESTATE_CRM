# Generated by Django 4.2.5 on 2024-11-12 05:03

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("leads", "0112_product_qty"),
    ]

    operations = [
        migrations.AddField(
            model_name="plotbooking",
            name="total_paid",
            field=models.DecimalField(
                blank=True, decimal_places=2, max_digits=10, null=True
            ),
        ),
    ]
