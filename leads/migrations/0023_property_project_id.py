# Generated by Django 5.1.2 on 2024-10-16 10:35

import django.db.models.deletion
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('leads', '0022_alter_project_title'),
    ]

    operations = [
        migrations.AddField(
            model_name='property',
            name='project_id',
            field=models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, to='leads.project'),
        ),
    ]
