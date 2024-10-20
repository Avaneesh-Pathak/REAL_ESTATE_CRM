# Generated by Django 5.1.1 on 2024-10-18 12:04

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("leads", "0036_property_area"),
    ]

    operations = [
        migrations.AlterField(
            model_name="daybook",
            name="amount",
            field=models.DecimalField(
                blank=True, decimal_places=2, max_digits=10, null=True
            ),
        ),
    ]