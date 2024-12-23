# Generated by Django 5.1.1 on 2024-10-25 15:12

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("leads", "0056_followup_status"),
    ]

    operations = [
        migrations.AlterField(
            model_name="followup",
            name="status",
            field=models.CharField(
                choices=[
                    ("pending", "Pending"),
                    ("completed", "Completed"),
                    ("postponed", "Postponed"),
                    ("in-Progress", "In-Progress"),
                ],
                default="pending",
                max_length=20,
            ),
        ),
    ]
