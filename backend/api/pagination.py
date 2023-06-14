from rest_framework.pagination import PageNumberPagination

from .params import PAGE_SIZE


class PageLimitPagination(PageNumberPagination):
    """Стандартный пагинатор с выводом запрошенного количества страниц."""
    page_size_query_param = 'limit'
    page_size = PAGE_SIZE
