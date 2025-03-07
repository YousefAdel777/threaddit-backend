from rest_framework.pagination import PageNumberPagination

class CustomPagination(PageNumberPagination):
    page_size_query_param = 'per_page'