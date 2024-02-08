from django import forms
from django.contrib import admin
from .models import Category, Products, Variations

class VariationsForm(forms.ModelForm):
    class Meta:
        model = Variations
        fields = '__all__'
        widgets = {
            'item_number' : forms.TextInput(attrs={'style': 'width: 80px;'}),
            'color_name': forms.TextInput(attrs={'style': 'width: 60px;'}),
            'hex_code': forms.TextInput(attrs={'style': 'width: 60px;'}),
            'size': forms.TextInput(attrs={'style': 'width: 40px;'}),
            'case_qty': forms.TextInput(attrs={'style': 'width: 40px;'}),
            'weight' : forms.TextInput(attrs={'style': 'width: 30px;'}),
            'front_image': forms.TextInput(attrs={'style': 'width: 40px;'}),
            'back_image': forms.TextInput(attrs={'style': 'width: 40px;'}),
            'side_image': forms.TextInput(attrs={'style': 'width: 40px;'}),
            'quantity': forms.TextInput(attrs={'style': 'width: 50px;'}),
            'price_per_piece': forms.TextInput(attrs={'style': 'width: 70px;'}),
            'price_per_dozen': forms.TextInput(attrs={'style': 'width: 70px;'}),
            'price_per_case': forms.TextInput(attrs={'style': 'width: 70px;'}),
            'retail_price': forms.TextInput(attrs={'style': 'width: 70px;'}),
        }

class VariationsInline(admin.TabularInline):
    model = Variations
    form = VariationsForm
    extra = 1  # Set the initial number of empty forms to display

    def get_readonly_fields(self, request, obj=None):
        if obj and obj.seller.username == 'alpb':
            return [f.name for f in self.model._meta.get_fields()]
        return super().get_readonly_fields(request, obj=obj)

class ProductsAdmin(admin.ModelAdmin):
    inlines = [VariationsInline]

    def get_readonly_fields(self, request, obj=None):
        if obj and obj.seller.username == 'alpb':
            read_only_fields = ['seller', 'product_number', 'brand_name', 'short_description', 'category', 'full_feature_description']
            return read_only_fields
        return super().get_readonly_fields(request, obj=obj)
# Register the models
admin.site.register(Category)
admin.site.register(Products, ProductsAdmin)