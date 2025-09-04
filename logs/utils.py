# logs/utils.py
from .models import Log

def create_log(user, action, message, related_model=None, related_id=None, ip=None):
    Log.objects.create(
        user=user if user and user.is_authenticated else None,
        action=action,
        message=message,
        related_model=related_model,
        related_id=related_id,
        ip_address=ip
    )
