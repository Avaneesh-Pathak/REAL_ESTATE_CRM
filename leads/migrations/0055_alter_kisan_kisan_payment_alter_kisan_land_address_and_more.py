# Generated by Django 5.1.1 on 2024-10-22 15:34

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("leads", "0054_event"),
    ]

    operations = [
        migrations.AlterField(
            model_name="kisan",
            name="kisan_payment",
            field=models.DecimalField(
                blank=True, decimal_places=3, max_digits=10, null=True
            ),
        ),
        migrations.AlterField(
            model_name="kisan",
            name="land_address",
            field=models.TextField(blank=True, max_length=50, null=True),
        ),
        migrations.DeleteModel(
            name="Event",
        ),
    ]