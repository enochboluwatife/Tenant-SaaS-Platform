"""
Custom pagination classes for the Multi-Tenant SaaS Platform.
"""

from rest_framework.pagination import PageNumberPagination, LimitOffsetPagination
from rest_framework.response import Response


class StandardResultsSetPagination(PageNumberPagination):
    """
    Standard pagination with configurable page size.
    """
    page_size = 20
    page_size_query_param = 'page_size'
    max_page_size = 100
    
    def get_paginated_response(self, data):
        return Response({
            'count': self.page.paginator.count,
            'next': self.get_next_link(),
            'previous': self.get_previous_link(),
            'results': data,
            'page': self.page.number,
            'pages': self.page.paginator.num_pages,
        })


class LargeResultsSetPagination(PageNumberPagination):
    """
    Pagination for large result sets.
    """
    page_size = 50
    page_size_query_param = 'page_size'
    max_page_size = 200


class SmallResultsSetPagination(PageNumberPagination):
    """
    Pagination for small result sets.
    """
    page_size = 10
    page_size_query_param = 'page_size'
    max_page_size = 50


class TenantAwarePagination(PageNumberPagination):
    """
    Pagination that includes tenant information in the response.
    """
    page_size = 20
    page_size_query_param = 'page_size'
    max_page_size = 100
    
    def get_paginated_response(self, data):
        response_data = {
            'count': self.page.paginator.count,
            'next': self.get_next_link(),
            'previous': self.get_previous_link(),
            'results': data,
            'page': self.page.number,
            'pages': self.page.paginator.num_pages,
        }
        
        # Add tenant information if available
        if hasattr(self.request, 'tenant') and self.request.tenant:
            response_data['tenant'] = {
                'id': self.request.tenant.id,
                'name': self.request.tenant.name,
                'domain': self.request.tenant.domain,
            }
        
        return Response(response_data)


class CursorPagination(LimitOffsetPagination):
    """
    Cursor-based pagination for real-time data.
    """
    default_limit = 20
    limit_query_param = 'limit'
    offset_query_param = 'offset'
    max_limit = 100
    
    def get_paginated_response(self, data):
        return Response({
            'count': self.count,
            'next': self.get_next_link(),
            'previous': self.get_previous_link(),
            'results': data,
            'limit': self.limit,
            'offset': self.offset,
        })
