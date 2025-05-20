from django.contrib.auth.models import AbstractUser
from django.db import models

class User(AbstractUser):
    ADMIN = 'admin'
    
    ROLE_CHOICES = [
        (ADMIN, 'Admin'),
    ]
    
    role = models.CharField(
        max_length=20,
        choices=ROLE_CHOICES,
        blank=True,  # Cambiado de default=ANONYMOUS a blank=True
    )
    
    @property
    def is_admin(self):
        return self.role == self.ADMIN or self.is_superuser
    
    groups = models.ManyToManyField(
        'auth.Group',
        related_name='custom_user_set',
        blank=True,
        help_text='The groups this user belongs to...',
        verbose_name='groups',
    )
    
    user_permissions = models.ManyToManyField(
        'auth.Permission',
        related_name='custom_user_set',
        blank=True,
        help_text='Specific permissions for this user...',
        verbose_name='user permissions',
    )
    
    class Meta:
        db_table = 'custom_user'
        
    def __str__(self):
        return self.username

class Product(models.Model):
    sku = models.CharField(max_length=50, unique=True)
    name = models.CharField(max_length=255)
    price = models.DecimalField(max_digits=10, decimal_places=2)
    brand = models.CharField(max_length=255)
    view_count = models.PositiveIntegerField(default=0)
    created_by = models.ForeignKey(User, related_name='products_created', on_delete=models.CASCADE, blank=True, null=True)
    last_updated_by = models.ForeignKey(User, null=True, on_delete=models.SET_NULL)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    list_view_count = models.PositiveIntegerField(default=0)
    last_viewed = models.DateTimeField(null=True, blank=True)

    def __str__(self):
        return f"{self.sku} - {self.name}"
    
class Notification(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    title = models.CharField(max_length=200)
    message = models.TextField()
    metadata = models.JSONField(default=dict)
    created_at = models.DateTimeField(auto_now_add=True)
    read = models.BooleanField(default=False)