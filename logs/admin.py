# logs/admin.py
from django.contrib import admin
from .models import Log

@admin.register(Log)
class LogAdmin(admin.ModelAdmin):
    list_display = (
        "id",
        "created_at",
        "user",
        "action",
        "message_short",
        "related_model",
        "related_id",
        "ip_address",
    )
    list_filter = ("action", "related_model", "created_at")
    search_fields = ("message", "related_id", "user__email", "user__username")
    ordering = ("-created_at",)

    def message_short(self, obj):
        return (obj.message[:50] + "...") if len(obj.message) > 50 else obj.message
    message_short.short_description = "Message"
