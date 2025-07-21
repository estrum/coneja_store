import uuid
from django.contrib.auth.models import AbstractUser, BaseUserManager
from django.db import models
from django.utils.translation import gettext_lazy as _
from django.utils import timezone

class UsuarioManager(BaseUserManager):
    use_in_migrations = True

    def create_user(self, email, phone_number, password=None, **extra_fields):
        if not email:
            raise ValueError(_('El correo electrónico es obligatorio.'))
        if not phone_number:
            raise ValueError('El número de teléfono es obligatorio.')

        email = self.normalize_email(email)
        user = self.model(
            email=email,
            phone_number=phone_number,
            **extra_fields
        )
        user.set_password(password)
        user.save(using=self._db)
        return user

    def create_superuser(self, email, phone_number, password=None, **extra_fields):
        extra_fields.setdefault('is_staff', True)
        extra_fields.setdefault('is_superuser', True)
        extra_fields.setdefault('is_2fa_enabled', True)
        return self.create_user(email, phone_number, password, **extra_fields)


class Usuario(AbstractUser):
    guid = models.UUIDField(default=uuid.uuid4, unique=True, editable=False)

    username = None  # No usamos username
    email = models.EmailField(_('email address'), unique=True)
    phone_number = models.CharField(max_length=15, unique=True)

    # 2FA vía SMS para entregar el token
    is_2fa_enabled = models.BooleanField(default=True)
    current_otp = models.CharField(max_length=6, blank=True, null=True)
    code_expires_at = models.DateTimeField(blank=True, null=True)
    last_2fa_verified_at = models.DateTimeField(blank=True, null=True)

    #codigo para el login para que junto a otp validen y entreguen el token
    login_session_code = models.CharField(max_length=6, blank=True, null=True)
    login_session_expires_at = models.DateTimeField(blank=True, null=True)

    USERNAME_FIELD = 'email'
    REQUIRED_FIELDS = ['phone_number']

    objects = UsuarioManager()

    def __str__(self):
        return self.email

    def has_valid_otp(self, code):
        return (
            self.current_otp == code and
            self.code_expires_at and
            timezone.now() < self.code_expires_at
        )
    
    def has_valid_session_token(self, code):
        return (
            self.login_session_code == code and
            self.login_session_expires_at and
            timezone.now() < self.login_session_expires_at
        )
