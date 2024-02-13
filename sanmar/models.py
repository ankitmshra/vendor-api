from django.db import models
from django.utils.translation import gettext_lazy as _

class Category(models.Model):
    # Category
    category = models.CharField(max_length=255, unique=True, primary_key=True)
    category_image = models.CharField(max_length=255)

    # product create and update fields
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ("-created_at",)
        verbose_name = _("Category")
        verbose_name_plural = _("Categories")

    def __str__(self):
        return self.category


class Products(models.Model):
    product_id = models.BigAutoField(auto_created=True,
                                     primary_key=True,
                                     serialize=False,
                                     verbose_name='Product ID')
    product_number = models.CharField(max_length=255, unique=True)
    brand_name = models.CharField(max_length=255)
    short_description = models.CharField(max_length=255)
    category = models.ForeignKey(
        Category,
        on_delete=models.CASCADE,
        related_name='products',
    )
    full_feature_description = models.TextField()

    # product create and update fields
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ("-created_at",)
        verbose_name = _("Product")
        verbose_name_plural = _("Products")

    def __str__(self):
        return f"{self.product_number} - {self.short_description}"


class Variations(models.Model):
    item_number = models.CharField(max_length=255, unique=True, primary_key=True)
    product_number = models.ForeignKey(
        Products,
        on_delete=models.CASCADE,
        related_name='variations',
    )
    color_name = models.CharField(max_length=255)
    hex_code = models.CharField(max_length=255)
    size = models.CharField(max_length=255)
    case_qty = models.IntegerField()
    weight = models.CharField(max_length=255)
    front_image = models.CharField(max_length=255)
    back_image = models.CharField(max_length=255, null=True)
    gtin = models.CharField(max_length=255)

    # inventory Field
    quantity = models.IntegerField(null=True)

    # Price Field
    price_per_piece = models.DecimalField(max_digits=10, decimal_places=2, null=True)
    price_per_dozen = models.DecimalField(max_digits=10, decimal_places=2, null=True)
    price_per_case = models.DecimalField(max_digits=10, decimal_places=2, null=True)
    retail_price = models.DecimalField(max_digits=10, decimal_places=2, null=True)

    # product create and update fields
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ("-created_at",)
        verbose_name = _("Variation")
        verbose_name_plural = _("Variations")

    def __str__(self):
        return self.item_number