from django.core import paginator
from rest_framework.pagination import PageNumberPagination


class CustomPagination(PageNumberPagination):
    """Пользовательский класс пагинации."""
    django_paginator_class = paginator.Paginator
    page_size = 2
    page_query_param = 'page'
    page_size_query_param = 'limit'
