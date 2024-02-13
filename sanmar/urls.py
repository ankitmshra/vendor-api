from django.urls import path
from .views import ProductsListView, CategoryListView, VerboseProductsView, UpdateDataView

app_name = 'sanmar'

urlpatterns = [
    path('products/', ProductsListView.as_view(), name='products-list'),
    path('update-data/', UpdateDataView.as_view(), name='update-data'),
    path('categories/', CategoryListView.as_view(), name='categories-list'),
    path('<str:product_number>/', VerboseProductsView.as_view(), name='product-variations'),
]