# Generated by Django 5.1.1 on 2024-10-18 06:38

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        (
            "leads",
            "0029_rename_total_commission_shared_agent_commission_percentage_and_more",
        ),
    ]

    operations = [
        migrations.CreateModel(
            name="Area",
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
                ("length", models.IntegerField()),
                ("breadth", models.IntegerField()),
                ("area", models.IntegerField()),
            ],
            options={
                "constraints": [
                    models.UniqueConstraint(
                        fields=("length", "breadth"), name="unique_length_breadth"
                    )
                ],
            },
        ),
    ]