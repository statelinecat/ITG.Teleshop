# Generated by Django 5.1.3 on 2025-01-12 17:39

import django.core.validators
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('flower_shop', '0007_alter_cart_options'),
    ]

    operations = [
        migrations.AlterField(
            model_name='product',
            name='price',
            field=models.DecimalField(decimal_places=2, max_digits=10, validators=[django.core.validators.MinValueValidator(0)], verbose_name='Цена'),
        ),
        migrations.AlterField(
            model_name='report',
            name='date',
            field=models.DateField(auto_now_add=True, db_index=True, verbose_name='Дата отчета'),
        ),
        migrations.AlterField(
            model_name='review',
            name='created_at',
            field=models.DateTimeField(auto_now_add=True, db_index=True, verbose_name='Дата создания'),
        ),
        migrations.AlterField(
            model_name='user',
            name='telegram_id',
            field=models.CharField(blank=True, db_index=True, max_length=100, null=True, verbose_name='Telegram ID'),
        ),
        migrations.AlterUniqueTogether(
            name='cartitem',
            unique_together={('cart', 'product')},
        ),
        migrations.AlterUniqueTogether(
            name='orderitem',
            unique_together={('order', 'product')},
        ),
    ]
