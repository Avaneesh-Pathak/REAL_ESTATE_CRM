# Generated by Django 5.1.1 on 2024-10-26 13:26

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("leads", "0057_alter_followup_status"),
    ]

    operations = [
        migrations.AddField(
            model_name="agent",
            name="total_commission",
            field=models.DecimalField(decimal_places=2, default=0.0, max_digits=10),
        ),
    ]