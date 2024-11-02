# Generated by Django 4.2.5 on 2024-11-01 15:32

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("leads", "0075_property_development_cost_property_land_area_and_more"),
    ]

    operations = [
        migrations.AddField(
            model_name="project",
            name="total_development_cost",
            field=models.DecimalField(
                blank=True, decimal_places=2, max_digits=15, null=True
            ),
        ),
        migrations.AddField(
            model_name="project",
            name="total_land_cost",
            field=models.DecimalField(
                blank=True, decimal_places=2, max_digits=15, null=True
            ),
        ),
    ]