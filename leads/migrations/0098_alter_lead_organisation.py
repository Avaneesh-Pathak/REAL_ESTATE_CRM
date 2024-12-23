# Generated by Django 4.2.5 on 2024-11-09 05:35

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ("leads", "0097_alter_user_is_organisor"),
    ]

    operations = [
        migrations.AlterField(
            model_name="lead",
            name="organisation",
            field=models.ForeignKey(
                blank=True,
                null=True,
                on_delete=django.db.models.deletion.DO_NOTHING,
                to="leads.userprofile",
            ),
        ),
    ]
