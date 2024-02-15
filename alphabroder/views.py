from rest_framework.generics import ListAPIView, RetrieveAPIView
from rest_framework import filters
from django.http import Http404
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from rest_framework.pagination import PageNumberPagination
from django.db.models import Min, Max, F, Value
from django.db.models.functions import Coalesce
from .sync import UpdateALPDB
from .models import Products, Category
from .serializers import (
    ProductCategoryReadSerializer,
    ProductReadSerializer,
    VerboseProductReadSerializer
)

#####################################################
#                   Helper Classes                  #
#####################################################
# pagination
class StandardResultsSetPagination(PageNumberPagination):
    page_size = 100
    page_size_query_param = 'page_size'
    max_page_size = 1000


#####################################################
#                 Updatedata Class                  #
#####################################################
class UpdateDataView(APIView):
    def get(self, request, *args, **kwargs):
        try:
            alp_sync = UpdateALPDB()
            result = alp_sync.start()
            return Response({"message": "Data updated successfully."},
                            status=status.HTTP_200_OK)

        except Exception as e:
            return Response({"error": str(e)}, 
                            status=status.HTTP_500_INTERNAL_SERVER_ERROR)
        

#####################################################
#                   API Controllers                 #
#####################################################
class ProductsListView(ListAPIView):
    serializer_class = ProductReadSerializer
    pagination_class = StandardResultsSetPagination
    filter_backends = [filters.SearchFilter]
    search_fields = ['product_number', 'short_description']  # Add fields to search

    def get_queryset(self):
        category_param = self.request.query_params.get('category', None)

        if category_param:
            if not Category.objects.filter(category__iexact=category_param).exists():
                raise Http404("Category does not exist")

            # Filter styles by category
            products = Products.objects.filter(category__category__iexact=category_param)
        else:
            products = Products.objects.all()

        return products

    def list(self, request, *args, **kwargs):
        queryset = self.filter_queryset(self.get_queryset())  # Apply search filter
        queryset = queryset.annotate(
            min_price=Coalesce(Min('variations__retail_price'), Value(None)),
            max_price=Coalesce(Max('variations__retail_price'), Value(None))
        )

        # Exclude products with null price ranges
        queryset = queryset.exclude(min_price=None, max_price=None)

        # Paginate the queryset
        page = self.paginate_queryset(queryset)
        if page is not None:
            serializer = self.get_serializer(page, many=True)
            return self.get_paginated_response(serializer.data)

        serializer = self.get_serializer(queryset, many=True)
        return Response(serializer.data, status=status.HTTP_404_NOT_FOUND if not queryset.exists() else status.HTTP_200_OK)


class CategoryListView(ListAPIView):
    queryset = Category.objects.all()
    serializer_class = ProductCategoryReadSerializer
    pagination_class = StandardResultsSetPagination


class VerboseProductsView(RetrieveAPIView):
    queryset = Products.objects.all()
    serializer_class = VerboseProductReadSerializer
    lookup_field = 'product_number'

    def get_serializer_context(self):
        context = super().get_serializer_context()
        context['product_number'] = self.kwargs['product_number']
        return context

    def get_object(self):
        product_number = self.kwargs['product_number']
        return Products.objects.get(product_number=product_number)