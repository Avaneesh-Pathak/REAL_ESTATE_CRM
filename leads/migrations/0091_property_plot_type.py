# Generated by Django 4.2.5 on 2024-11-06 08:11

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("leads", "0090_project_dev_cost"),
    ]

    operations = [
        migrations.AddField(
            model_name="property",
            name="plot_type",
            field=models.CharField(
                choices=[
                    ("normal", "Normal"),
                    ("corner", "Corner"),
                    ("special", "Special"),
                ],
                default="Normal",
                max_length=50,
            ),
        ),
    ]
