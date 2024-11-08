# Generated by Django 4.2.5 on 2024-11-07 07:05

from django.conf import settings
from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ("leads", "0092_alter_plotbooking_plot_price_and_more"),
    ]

    operations = [
        migrations.AlterField(
            model_name="agent",
            name="organisation",
            field=models.ForeignKey(
                on_delete=django.db.models.deletion.CASCADE, to="leads.userprofile"
            ),
        ),
        migrations.AlterField(
            model_name="agent",
            name="user",
            field=models.OneToOneField(
                on_delete=django.db.models.deletion.CASCADE, to=settings.AUTH_USER_MODEL
            ),
        ),
    ]
