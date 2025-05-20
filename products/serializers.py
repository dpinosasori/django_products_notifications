from rest_framework import serializers
from products.models import Product, User
from django.contrib.auth.hashers import make_password
from pathlib import Path
import os
from dotenv import load_dotenv
from os.path import join

BASE_DIR = Path(__file__).resolve().parent.parent
dotenv_path = join(BASE_DIR, '.env')
load_dotenv(dotenv_path)

class ProductSerializer(serializers.ModelSerializer):
    class Meta:
        model = Product
        fields = '__all__'
        read_only_fields = ('created_by', 'created_at', 'updated_at')
        extra_kwargs = {
            'sku': {'required': False},
            'name': {'required': False},
            'price': {'required': False},
            'brand': {'required': False}
        }
    
    def create(self, validated_data):
        validated_data['created_by'] = self.context['request'].user
        return super().create(validated_data)
    
    def update(self, instance, validated_data):
        # Elimina campos no proporcionados para mantener los valores existentes
        for attr, value in validated_data.items():
            setattr(instance, attr, value)
        instance.save()
        return instance
    

class UserSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = ['id', 'username', 'password', 'email', 'role']
        extra_kwargs = {
            'username': {'required': False},  # Hacemos username opcional en updates
            'password': {
                'write_only': True,
                'required': False,
                'allow_blank': True
            },
            'role': {'read_only': True}
        }

    def validate(self, data):
        # Validación especial para creación
        if self.instance is None:  # Es creación (POST)
            if 'username' not in data:
                raise serializers.ValidationError({"username": "This field is required when creating a user."})
            if 'password' not in data or not data['password']:
                raise serializers.ValidationError({"password": "This field is required when creating a user."})
        
        return data

    def update(self, instance, validated_data):
        # Elimina password si está vacío o no fue proporcionado
        if 'password' in validated_data and not validated_data['password']:
            validated_data.pop('password')
            
        return super().update(instance, validated_data)
    

class AdminRegistrationSerializer(serializers.ModelSerializer):
    auth_key = serializers.CharField(write_only=True, required=True)
    password = serializers.CharField(write_only=True, required=True, min_length=8)
    
    class Meta:
        model = User
        fields = ['username', 'email', 'password', 'auth_key']
        extra_kwargs = {
            'username': {'required': True},
            'email': {'required': True}
        }
    
    def validate(self, data):
        if data['auth_key'] != os.getenv('ADMIN_AUTH_KEY'):
            raise serializers.ValidationError({"auth_key": "Llave de autenticación inválida"})
        return data
    
    def create(self, validated_data):
        validated_data.pop('auth_key')  # Eliminamos la llave que no es parte del modelo
        validated_data['password'] = make_password(validated_data['password'])
        validated_data['role'] = User.ADMIN
        validated_data['is_staff'] = True
        
        return User.objects.create(**validated_data)