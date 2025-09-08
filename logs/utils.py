# logs/utils.py
from .models import Log

def create_log(
        user, action, 
        message, related_model=None, 
        ip=None):
    """
    CREATE A REGISTER AFTER AN ACTION
    """
    Log.objects.create(
        user=user if user and user.is_authenticated else None,
        action=action,
        message=message,
        related_model=related_model,
        ip_address=ip
    )
