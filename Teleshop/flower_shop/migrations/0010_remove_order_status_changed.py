# Generated by Django 5.1.3 on 2025-01-13 03:45

from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('flower_shop', '0009_order_status_changed'),
    ]

    operations = [
        migrations.RemoveField(
            model_name='order',
            name='status_changed',
        ),
    ]
