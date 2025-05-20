# products/schemas.py
from drf_yasg import openapi

product_schema = openapi.Schema(
    type=openapi.TYPE_OBJECT,
    properties={
        'id': openapi.Schema(type=openapi.TYPE_INTEGER),
        'sku': openapi.Schema(type=openapi.TYPE_STRING),
        'name': openapi.Schema(type=openapi.TYPE_STRING),
        'price': openapi.Schema(type=openapi.TYPE_NUMBER),
        'brand': openapi.Schema(type=openapi.TYPE_STRING),
        'view_count': openapi.Schema(type=openapi.TYPE_INTEGER),
        'list_view_count': openapi.Schema(type=openapi.TYPE_INTEGER),
        'created_at': openapi.Schema(type=openapi.TYPE_STRING),
        'updated_at': openapi.Schema(type=openapi.TYPE_STRING),
        'last_viewed': openapi.Schema(type=openapi.TYPE_STRING)
    }
)

error_schema = openapi.Schema(
    type=openapi.TYPE_OBJECT,
    properties={
        'detail': openapi.Schema(type=openapi.TYPE_STRING),
        'code': openapi.Schema(type=openapi.TYPE_STRING),
        'messages': openapi.Schema(
            type=openapi.TYPE_ARRAY,
            items=openapi.Items(type=openapi.TYPE_STRING)
        )
    }
)