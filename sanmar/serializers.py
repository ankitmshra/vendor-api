from rest_framework import serializers
from django.db.models import Min, Max

from .models import Category, Products, Variations

class ProductCategoryReadSerializer(serializers.ModelSerializer):
    """
    Serializer class for product categories
    """

    class Meta:
        model = Category
        fields = ['category', 'category_image']


class ProductReadSerializer(serializers.ModelSerializer):
    front_image = serializers.SerializerMethodField()
    price_range = serializers.SerializerMethodField()

    class Meta:
        model = Products
        fields = ['product_number', 'short_description', 
                  'category', 'full_feature_description', 'front_image', 'price_range']

    def get_front_image(self, obj):
        # Get the first product related to the product
        product = Variations.objects.filter(product_number=obj).first()
        if product:
            return product.front_image
        return None
    
    def get_price_range(self, obj):
        # Get the minimum and maximum retail prices from related variations
        min_price = obj.variations.aggregate(min_price=Min('retail_price'))['min_price']
        max_price = obj.variations.aggregate(max_price=Max('retail_price'))['max_price']

        return {'min_price': min_price, 'max_price': max_price}
    
class VariationsSerializer(serializers.ModelSerializer):
    class Meta:
        model = Variations
        fields = [
            'item_number', 'product_number', 'color_name', 'hex_code',
            'size', 'case_qty', 'weight', 'front_image', 'back_image',
            'gtin', 'created_at', 'updated_at', 'quantity', 'price_per_piece', 'price_per_dozen', 
            'price_per_case', 'retail_price',
        ]
    
class VerboseProductReadSerializer(serializers.ModelSerializer):
    variations = VariationsSerializer(many=True, read_only=True)

    class Meta:
        model = Products
        fields = ['product_number', 'short_description', 'brand_name', 'category',
                'full_feature_description', 'created_at', 'updated_at', 'variations']