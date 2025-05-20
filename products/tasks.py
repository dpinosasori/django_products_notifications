from django.core.mail import send_mail
from django.template.loader import render_to_string
from django.utils.html import strip_tags
from django.conf import settings
from celery import shared_task
import logging
from .models import User
from datetime import datetime
logger = logging.getLogger(__name__)

@shared_task(bind=True, max_retries=3, default_retry_delay=60)
def send_product_update_notification(self, product_data, changes, updated_by_id):
    try:
        
        # Obtener todos los admins excepto quien hizo el cambio
        admins = User.objects.filter(role=User.ADMIN).exclude(id=updated_by_id)
        
        if not admins.exists():
            logger.info("No hay administradores para notificar")
            return

        context = {
            'product': product_data,
            'changes': changes,
            'updated_by': User.objects.get(id=updated_by_id),
            'date': product_data.get('updated_at', '')
        }

        subject = f"🔄 Actualización de Producto: {product_data['name']}"
        html_message = render_to_string('products/emails/product_updated.html', context)
        text_message = strip_tags(html_message)

        # Opción 1: Enviar un correo por cada admin (recomendado para tracking individual)
        for admin in admins:
            send_mail(
                subject,
                text_message,
                settings.DEFAULT_FROM_EMAIL,
                [admin.email],  # Lista de destinatarios como parámetro posicional
                html_message=html_message,
                fail_silently=False
            )
        
        logger.info(f"Notificación enviada a {len(admins)} administradores")

    except Exception as e:
        logger.error(f"Error en tarea de notificación: {str(e)}")
        raise self.retry(exc=e, countdown=60)
    
@shared_task(bind=True, max_retries=3, default_retry_delay=60)
def send_product_creation_notification(self, product_data, created_by_id):
    """Notificación cuando se crea un nuevo producto"""
    try:
        admins = User.objects.filter(role=User.ADMIN).exclude(id=created_by_id)
        if not admins.exists():
            return

        context = {
            'product': product_data,
            'action': 'created',
            'user': User.objects.get(id=created_by_id),
            'date': datetime.now().strftime("%d/%m/%Y %H:%M")
        }

        html_message = render_to_string('products/emails/product_action.html', context)
        text_message = strip_tags(html_message)
        subject = f"➕ Nuevo Producto: {product_data['name']}"

        for admin in admins:
            send_mail(
                subject,
                text_message,
                settings.DEFAULT_FROM_EMAIL,
                [admin.email],
                html_message=html_message,
                fail_silently=False
            )

    except Exception as e:
        logger.error(f"Error notificando creación: {str(e)}")
        raise self.retry(exc=e)

@shared_task(bind=True, max_retries=3, default_retry_delay=60)
def send_product_deletion_notification(self, product_data, deleted_by_id):
    """Notificación cuando se elimina un producto"""
    try:
        admins = User.objects.filter(role=User.ADMIN).exclude(id=deleted_by_id)
        if not admins.exists():
            return

        context = {
            'product': product_data,
            'action': 'deleted',
            'user': User.objects.get(id=deleted_by_id),
            'date': datetime.now().strftime("%d/%m/%Y %H:%M")
        }

        html_message = render_to_string('products/emails/product_action.html', context)
        text_message = strip_tags(html_message)
        subject = f"❌ Producto Eliminado: {product_data['name']}"

        for admin in admins:
            send_mail(
                subject,
                text_message,
                settings.DEFAULT_FROM_EMAIL,
                [admin.email],
                html_message=html_message,
                fail_silently=False
            )

    except Exception as e:
        logger.error(f"Error notificando eliminación: {str(e)}")
        raise self.retry(exc=e)