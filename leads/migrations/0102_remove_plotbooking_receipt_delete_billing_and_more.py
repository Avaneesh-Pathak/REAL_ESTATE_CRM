# Generated by Django 4.2.5 on 2024-11-10 14:31

from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ("leads", "0101_receipt_billing_plotbooking_receipt"),
    ]

    operations = [
        migrations.RemoveField(
            model_name="plotbooking",
            name="receipt",
        ),
        migrations.DeleteModel(
            name="Billing",
        ),
        migrations.DeleteModel(
            name="Receipt",
        ),
    ]