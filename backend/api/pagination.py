from rest_framework.pagination import PageNumberPagination


class PageLimitPagination(PageNumberPagination):
    """Стандартный пагинатор с выводом запрошенного количества страниц."""
    page_size_query_param = 'limit'
    page_size = 2
