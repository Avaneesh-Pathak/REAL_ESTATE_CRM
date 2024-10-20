# Generated by Django 5.1.1 on 2024-10-16 09:14

import django.db.models.deletion
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("leads", "0019_rename_basic_price_plotbooking_plot_price"),
    ]

    operations = [
        migrations.CreateModel(
            name="EMIPayment",
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
                ("due_date", models.DateField()),
                ("emi_amount", models.DecimalField(decimal_places=2, max_digits=10)),
                (
                    "amount_paid",
                    models.DecimalField(decimal_places=2, default=0, max_digits=10),
                ),
                (
                    "status",
                    models.CharField(
                        choices=[("Pending", "Pending"), ("Paid", "Paid")],
                        default="Pending",
                        max_length=20,
                    ),
                ),
                (
                    "plot_booking",
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.CASCADE,
                        related_name="emi_payments",
                        to="leads.plotbooking",
                    ),
                ),
            ],
        ),
    ]