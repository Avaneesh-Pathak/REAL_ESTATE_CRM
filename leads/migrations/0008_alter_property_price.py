# Generated by Django 5.1.2 on 2024-10-14 15:30

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('leads', '0007_rename_description_property_block_and_more'),
    ]

    operations = [
        migrations.AlterField(
            model_name='property',
            name='price',
            field=models.DecimalField(blank=True, decimal_places=2, max_digits=15, null=True),
        ),
    ]