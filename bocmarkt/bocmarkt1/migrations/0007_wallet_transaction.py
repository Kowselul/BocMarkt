# Generated by Django 5.1.6 on 2025-04-03 21:36

import django.db.models.deletion
from django.conf import settings
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('bocmarkt1', '0006_product_sold_date'),
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
    ]

    operations = [
        migrations.CreateModel(
            name='Wallet',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('balance', models.DecimalField(decimal_places=2, default=0.0, max_digits=10)),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('updated_at', models.DateTimeField(auto_now=True)),
                ('user', models.OneToOneField(on_delete=django.db.models.deletion.CASCADE, related_name='wallet', to=settings.AUTH_USER_MODEL)),
            ],
            options={
                'db_table': 'user_wallet',
            },
        ),
        migrations.CreateModel(
            name='Transaction',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('amount', models.DecimalField(decimal_places=2, max_digits=10)),
                ('type', models.CharField(choices=[('SALE', 'Sale'), ('PURCHASE', 'Purchase')], max_length=10)),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('description', models.CharField(blank=True, max_length=255)),
                ('product', models.ForeignKey(null=True, on_delete=django.db.models.deletion.SET_NULL, to='bocmarkt1.product')),
                ('wallet', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='transactions', to='bocmarkt1.wallet')),
            ],
            options={
                'ordering': ['-created_at'],
            },
        ),
    ]
