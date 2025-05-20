from rest_framework import viewsets, status
from rest_framework.response import Response
from rest_framework.decorators import action
from .models import Product, User
from .serializers import ProductSerializer, UserSerializer, AdminRegistrationSerializer
from core.permissions import IsAdminUser
from django.core.mail import send_mail
from django.conf import settings
from threading import Thread
from rest_framework.permissions import AllowAny
from rest_framework.views import APIView
from django.db.models import F, Sum, Count
from datetime import datetime, timedelta
import logging
from .tasks import send_product_update_notification
from django.db import transaction
from django.db.models import Avg

logger = logging.getLogger(__name__)

# products/views.py
from drf_yasg.utils import swagger_auto_schema
from drf_yasg import openapi

class ProductViewSet(viewsets.ModelViewSet):
    queryset = Product.objects.all()
    serializer_class = ProductSerializer
    
    def get_permissions(self):
        if self.action in ['list', 'retrieve', 'stats', 'view_analytics']:
            return []  # AllowAny
        return [IsAdminUser()]

    def retrieve(self, request, *args, **kwargs):
        if not request.user.is_authenticated:
            self._increment_view_count(kwargs['pk'])
        return super().retrieve(request, *args, **kwargs)

    def list(self, request, *args, **kwargs):
        if not request.user.is_authenticated:
            self._increment_list_view_count()
        return super().list(request, *args, **kwargs)

    @transaction.atomic
    def _increment_view_count(self, product_id):
        """Incrementa el contador de vistas de forma atómica"""
        try:
            Product.objects.filter(pk=product_id).select_for_update().update(
                view_count=F('view_count') + 1,
                last_viewed=datetime.now()
            )
        except Exception as e:
            logger.error(f"Error incrementing view count: {str(e)}", 
                        exc_info=True, extra={'product_id': product_id})

    @transaction.atomic
    def _increment_list_view_count(self):
        """Incrementa el contador de vistas del listado"""
        try:
            Product.objects.all().select_for_update().update(
                list_view_count=F('list_view_count') + 1
            )
        except Exception as e:
            logger.error(f"Error incrementing list view count: {str(e)}", 
                        exc_info=True)

    def perform_create(self, serializer):
        """Crea un producto y asigna el creador"""
        serializer.save(created_by=self.request.user)

    def perform_update(self, serializer):
        """Actualiza un producto y notifica cambios"""
        old_instance = self.get_object()
        instance = serializer.save(last_updated_by=self.request.user)
        
        if self.request.user.is_admin:
            changes = self._detect_changes(old_instance, instance)
            if changes:
                self._send_notifications(instance, changes)

    def _detect_changes(self, old_instance, new_instance):
        """Detecta cambios significativos en el producto"""
        changes = {}
        significant_fields = ['price', 'name', 'brand', 'sku']
        
        for field in significant_fields:
            old_value = getattr(old_instance, field)
            new_value = getattr(new_instance, field)
            if old_value != new_value:
                changes[field] = {'old': old_value, 'new': new_value}
                
        return changes

    def _send_notifications(self, product, changes):
        """Envía notificaciones a través de Celery"""
        product_data = {
            'id': product.id,
            'name': product.name,
            'sku': product.sku,
            'brand': product.brand,
            'updated_at': product.updated_at.strftime("%Y-%m-%d %H:%M:%S")
        }
        
        send_product_update_notification.delay(
            product_data=product_data,
            changes=changes,
            updated_by_id=self.request.user.id
        )

    @action(detail=False, methods=['GET'])
    def stats(self, request):
        """Estadísticas básicas de productos"""
        stats = {
            'total_products': Product.objects.count(),
            'total_views': Product.objects.aggregate(total=Sum('view_count'))['total'] or 0,
            'total_list_views': Product.objects.aggregate(total=Sum('list_view_count'))['total'] or 0,
            'most_viewed': ProductSerializer(
                Product.objects.order_by('-view_count')[:5],
                many=True
            ).data,
            'recently_updated': ProductSerializer(
                Product.objects.order_by('-updated_at')[:5],
                many=True
            ).data
        }
        return Response(stats)

    @action(detail=False, methods=['GET'])
    def view_analytics(self, request):
        """Analíticas avanzadas de visualizaciones"""
        time_range = request.query_params.get('range', '7d')
        
        try:
            if time_range == '24h':
                delta = timedelta(hours=24)
            elif time_range == '7d':
                delta = timedelta(days=7)
            elif time_range == '30d':
                delta = timedelta(days=30)
            else:
                delta = timedelta(days=7)
        except ValueError:
            delta = timedelta(days=7)
            
        cutoff_date = datetime.now() - delta

        analytics = {
            'period': str(delta),
            'start_date': cutoff_date,
            'end_date': datetime.now(),
            'metrics': {
                'total_views': Product.objects.filter(
                    last_viewed__gte=cutoff_date
                ).aggregate(total=Sum('view_count'))['total'] or 0,
                'unique_products_viewed': Product.objects.filter(
                    last_viewed__gte=cutoff_date
                ).count(),
                'views_per_product': Product.objects.filter(
                    last_viewed__gte=cutoff_date
                ).aggregate(avg=Avg('view_count'))['avg'] or 0
            },
            'product_views': Product.objects.filter(
                last_viewed__gte=cutoff_date
            ).values('id', 'sku', 'name').annotate(
                views=Sum('view_count'),
                last_viewed=F('last_viewed')
            ).order_by('-views'),
            'trending_products': Product.objects.filter(
                last_viewed__gte=cutoff_date
            ).annotate(
                view_increase=Sum('view_count') / delta.days
            ).order_by('-view_increase')[:5]
        }

        return Response(analytics)


class AdminUserViewSet(viewsets.ModelViewSet):
    queryset = User.objects.filter(role=User.ADMIN)
    serializer_class = UserSerializer
    permission_classes = [IsAdminUser]

    def create(self, request, *args, **kwargs):
        required_fields = ['username', 'password', 'email']
        if not all(field in request.data for field in required_fields):
            return Response(
                {'detail': f'Faltan campos requeridos: {", ".join(required_fields)}'},
                status=status.HTTP_400_BAD_REQUEST
            )

        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        
        # Fuerza el rol admin al crear
        self.perform_create(serializer)
        headers = self.get_success_headers(serializer.data)
        return Response(serializer.data, status=status.HTTP_201_CREATED, headers=headers)

    def perform_create(self, serializer):
        serializer.save(role=User.ADMIN, is_staff=True)
    
    def update(self, request, *args, **kwargs):
        instance = self.get_object()
        data = request.data.copy()
        
        # Si es PUT (no PATCH), completa con los valores actuales
        if not kwargs.get('partial', False):
            for field in ['username', 'email']:
                if field not in data:
                    data[field] = getattr(instance, field)
        
        serializer = self.get_serializer(instance, data=data, partial=kwargs.get('partial', False))
        serializer.is_valid(raise_exception=True)
        self.perform_update(serializer)
        
        return Response(serializer.data)
    

class AdminRegistrationView(APIView):
    permission_classes = [AllowAny]
    serializer_class = AdminRegistrationSerializer
    
    def post(self, request):
        serializer = self.serializer_class(data=request.data)
        if serializer.is_valid():
            user = serializer.save()
            return Response({
                'message': 'Administrador registrado exitosamente',
                'username': user.username,
                'email': user.email,
                'role': user.role
            }, status=status.HTTP_201_CREATED)
        
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)