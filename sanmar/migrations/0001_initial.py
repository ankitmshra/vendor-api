# Generated by Django 5.0.1 on 2024-02-13 21:14

import django.db.models.deletion
from django.db import migrations, models


class Migration(migrations.Migration):

    initial = True

    dependencies = [
    ]

    operations = [
        migrations.CreateModel(
            name='Category',
            fields=[
                ('category', models.CharField(max_length=255, primary_key=True, serialize=False, unique=True)),
                ('category_image', models.CharField(max_length=255)),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('updated_at', models.DateTimeField(auto_now=True)),
            ],
            options={
                'verbose_name': 'Category',
                'verbose_name_plural': 'Categories',
                'ordering': ('-created_at',),
            },
        ),
        migrations.CreateModel(
            name='Products',
            fields=[
                ('product_id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='Product ID')),
                ('product_number', models.CharField(max_length=255, unique=True)),
                ('brand_name', models.CharField(max_length=255)),
                ('short_description', models.CharField(max_length=255)),
                ('full_feature_description', models.TextField()),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('updated_at', models.DateTimeField(auto_now=True)),
                ('category', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='products', to='sanmar.category')),
            ],
            options={
                'verbose_name': 'Product',
                'verbose_name_plural': 'Products',
                'ordering': ('-created_at',),
            },
        ),
        migrations.CreateModel(
            name='Variations',
            fields=[
                ('item_number', models.CharField(max_length=255, primary_key=True, serialize=False, unique=True)),
                ('color_name', models.CharField(max_length=255)),
                ('hex_code', models.CharField(max_length=255)),
                ('size', models.CharField(max_length=255)),
                ('case_qty', models.IntegerField()),
                ('weight', models.CharField(max_length=255)),
                ('front_image', models.CharField(max_length=255)),
                ('back_image', models.CharField(max_length=255)),
                ('gtin', models.CharField(max_length=255)),
                ('quantity', models.IntegerField(null=True)),
                ('price_per_piece', models.DecimalField(decimal_places=2, max_digits=10, null=True)),
                ('price_per_dozen', models.DecimalField(decimal_places=2, max_digits=10, null=True)),
                ('price_per_case', models.DecimalField(decimal_places=2, max_digits=10, null=True)),
                ('retail_price', models.DecimalField(decimal_places=2, max_digits=10, null=True)),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('updated_at', models.DateTimeField(auto_now=True)),
                ('product_number', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='variations', to='sanmar.products')),
            ],
            options={
                'verbose_name': 'Variation',
                'verbose_name_plural': 'Variations',
                'ordering': ('-created_at',),
            },
        ),
    ]
