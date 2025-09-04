import uuid
from django.contrib.auth.models import AbstractUser, BaseUserManager
from django.db import models
from django.utils.text import slugify
from django.utils.translation import gettext_lazy as _
from django.utils import timezone

class UserManager(BaseUserManager):
    use_in_migrations = True

    def create_user(
            self, email, store_name, 
            phone_number, password=None, **extra_fields):
        if not email:
            raise ValueError(_('El correo electrónico es obligatorio.'))
        if not phone_number:
            raise ValueError('El número de teléfono es obligatorio.')
        if not store_name:
            raise ValueError('El nombre de la tienda es obligatorio.')

        email = self.normalize_email(email)
        user = self.model(
            email=email,
            phone_number=phone_number,
            store_name=store_name,
            **extra_fields
        )
        user.set_password(password)
        user.save(using=self._db)
        return user

    def create_superuser(
            self, 
            email, 
            phone_number, 
            store_name, 
            password=None, 
            **extra_fields):
        
        extra_fields.setdefault('is_staff', True)
        extra_fields.setdefault('is_superuser', True)
        extra_fields.setdefault('is_2fa_enabled', True)
        return self.create_user(
            email, phone_number, store_name, password, **extra_fields)


class CustomUser(AbstractUser):
    """Usuario personalizado para el proyecto"""
    guid = models.UUIDField(
        default=uuid.uuid4, unique=True, editable=False)

    username = None  # No usamos username
    store_name = models.CharField(blank=False, null=False, unique=True)
    slug = models.SlugField(default="", null=False)
    email = models.EmailField(_('email address'), unique=True)
    phone_number = models.CharField(max_length=15, unique=True)
    #profile picture
    store_logo_url = models.URLField(
        max_length=500, null=True, blank=True)

    # 2FA vía SMS para entregar el token
    is_2fa_enabled = models.BooleanField(default=True)
    current_otp = models.CharField(max_length=6, blank=True, null=True)
    code_expires_at = models.DateTimeField(blank=True, null=True)
    last_2fa_verified_at = models.DateTimeField(blank=True, null=True)

    #codigo para el login para que junto a otp validen y den el token
    login_session_code = models.CharField(
        max_length=6, blank=True, null=True)
    login_session_expires_at = models.DateTimeField(blank=True, null=True)

    USERNAME_FIELD = 'email'
    REQUIRED_FIELDS = ['phone_number', 'store_name']

    objects = UserManager()

    def save(self, *args, **kwargs):
        """Guarda usuario y genera slug"""
        # Solo genera/actualiza el slug si el store_name cambia
        # o si el slug está vacío (nueva instancia)
        if not self.slug or (
                self.pk 
                and CustomUser.objects.get(pk=self.pk).store_name 
                != self.store_name):
            
            base_slug = slugify(self.store_name)
            self.slug = base_slug
            counter = 1
            # Se asegura que el slug sea unico
            while CustomUser.objects.filter(
                slug=self.slug).exclude(pk=self.pk).exists():

                self.slug = f"{base_slug}-{counter}"
                counter += 1
        super().save(*args, **kwargs)

    def __str__(self):
        return self.store_name

    def has_valid_otp(self, code):
        """Valida el codigo del sms para generar el token"""
        return (
            self.current_otp == code and
            self.code_expires_at and
            timezone.now() < self.code_expires_at
        )
    
    def has_valid_session_token(self, code):
        """Valida el codigo de sesión para mandar el sms"""
        return (
            self.login_session_code == code and
            self.login_session_expires_at and
            timezone.now() < self.login_session_expires_at
        )
