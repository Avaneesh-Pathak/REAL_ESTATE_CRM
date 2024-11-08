# Generated by Django 5.1.1 on 2024-10-15 10:31

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("leads", "0017_remove_plotbooking_project_name_plotbooking_project_and_more"),
    ]

    operations = [
        migrations.AddField(
            model_name="plotbooking",
            name="emi_amount",
            field=models.DecimalField(
                blank=True, decimal_places=2, max_digits=10, null=True
            ),
        ),
        migrations.AddField(
            model_name="plotbooking",
            name="emi_tenure",
            field=models.IntegerField(blank=True, null=True),
        ),
        migrations.AddField(
            model_name="plotbooking",
            name="interest_rate",
            field=models.DecimalField(
                blank=True, decimal_places=2, max_digits=5, null=True
            ),
        ),
    ]
