# Generated by Django 4.2.5 on 2024-11-03 10:05

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("leads", "0078_rename_kisan_data_property_land"),
    ]

    operations = [
        migrations.AddField(
            model_name="property",
            name="is_in_emi",
            field=models.BooleanField(default=False),
        ),
    ]
