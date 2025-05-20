from django.contrib import admin
from django.urls import path, include
from rest_framework.routers import DefaultRouter
from products.views import ProductViewSet, AdminUserViewSet
from rest_framework_simplejwt.views import TokenObtainPairView
from products.views import AdminRegistrationView
from rest_framework import permissions
from drf_yasg.views import get_schema_view
from drf_yasg import openapi

schema_view = get_schema_view(
    openapi.Info(
        title="Product Management API",
        default_version='v1',
        description="API para gestión de productos con sistema de notificaciones",
        terms_of_service="https://www.tudominio.com/terms/",
        contact=openapi.Contact(email="soporte@tudominio.com"),
        license=openapi.License(name="BSD License"),
    ),
    public=True,
    permission_classes=(permissions.AllowAny,),
)

router = DefaultRouter()
router.register(r'products', ProductViewSet)
router.register(r'admin-users', AdminUserViewSet)

urlpatterns = [
    path('swagger/', schema_view.with_ui('swagger', cache_timeout=0), name='schema-swagger-ui'),
    path('redoc/', schema_view.with_ui('redoc', cache_timeout=0), name='schema-redoc'),
    path('admin/', admin.site.urls),
    path('api/', include(router.urls)),
    path('api-auth/', include('rest_framework.urls', namespace='rest_framework')),
    path('api/token/', TokenObtainPairView.as_view(), name='token_obtain_pair'),
    path('register-admin/', AdminRegistrationView.as_view(), name='register-admin'),
]