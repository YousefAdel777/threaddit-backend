from celery import shared_task
from django.utils import timezone
from .models import Ban

@shared_task
def delete_expired_bans():
    Ban.objects.filter(expires_at__lt=timezone.now()).delete()