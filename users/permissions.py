# users/permissions.py
from rest_framework.permissions import BasePermission

class IsAdminOrSuperUser(BasePermission):
    def has_permission(self, request, view):
        return request.user and (request.user.is_superuser or request.user.is_staff)
