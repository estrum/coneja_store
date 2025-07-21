from django.contrib import admin
from django.contrib.auth.admin import UserAdmin as BaseUserAdmin
from django.utils.translation import gettext_lazy as _
from .models import Usuario

@admin.register(Usuario)
class UsuarioAdmin(BaseUserAdmin):
    # Campos que se muestran en la lista de usuarios
    list_display = ('email', 'phone_number', 'is_staff', 'is_superuser', 'is_active')
    search_fields = ('email', 'phone_number')
    ordering = ('email',)

    # Campos editables en el formulario
    fieldsets = (
        (None, {'fields': ('email', 'phone_number', 'password')}),
        (_('Permisos'), {'fields': ('is_active', 'is_staff', 'is_superuser', 'groups', 'user_permissions')}),
        (_('Información adicional'), {'fields': ('is_2fa_enabled', 'last_2fa_verified_at')}),
        (_('Fechas importantes'), {'fields': ('last_login', 'date_joined')}),
    )

    # Campos cuando se crea un nuevo usuario desde el admin
    add_fieldsets = (
        (None, {
            'classes': ('wide',),
            'fields': ('email', 'phone_number', 'password1', 'password2'),
        }),
    )

    readonly_fields = ('last_2fa_verified_at', 'last_login', 'date_joined')
