from rest_framework import permissions
from products.models import User

class IsAdminUser(permissions.BasePermission):
    """
    Permite acceso solo a usuarios admin (role='admin' o superusers)
    """
    def has_permission(self, request, view):
        return request.user.is_authenticated and (
            getattr(request.user, 'role', None) == 'admin' or 
            request.user.is_superuser
        )