from rest_framework import permissions

class IsOwnerByGUIDOrAdminForUserApp(permissions.BasePermission):
    """
    Permite acceso si el usuario autenticado es dueño del recurso 
    (por GUID), o si es staff/superuser. para app user
    """

    def has_object_permission(self, request, view, obj):
        """
        Verifica permisos de usuario para realizar 
        acciones en la app users
        """
        authenticated_user_guid = getattr(request.user, 'guid', None)
        object_guid = getattr(obj, 'guid', None)

        # 1. Si el usuario es staff o superuser, siempre tiene permiso.
        if request.user and (
            request.user.is_staff or request.user.is_superuser):
            return True

        # 2. Comprobar si el usuario autenticado es el dueño del objeto.
        # Asegúrate de que ambos, 
        # el usuario autenticado y el objeto, tengan un GUID.
        is_owner = (authenticated_user_guid is not None and
                    object_guid is not None and
                    str(authenticated_user_guid) == str(object_guid))

        # 3. Para métodos seguros (GET, HEAD, OPTIONS):
        # Con la política de tu ViewSet, solo el dueño o un admin pueden
        # ver los detalles del objeto.
        if request.method in permissions.SAFE_METHODS:
            return is_owner

        # 4. Para métodos no seguros (POST, PUT, PATCH, DELETE):
        # Solo el dueño o un admin pueden modificar/eliminar el objeto.
        return is_owner


class IsOwnerByGUIDOrAdminForRestApp(permissions.BasePermission):
    """
    Permite acceso si el usuario autenticado es dueño del recurso 
    (por GUID), o si es staff/superuser.
    se utiliza en cualquier app que no sea usuario
    """

    def has_object_permission(self, request, view, obj):
        user = request.user

        # 1. Si no está autenticado → DRF debe devolver 401 automáticamente
        if not user or not user.is_authenticated:
            return False

        # 2. Si el usuario es staff o superuser, siempre tiene permiso.
        if user.is_staff or user.is_superuser:
            return True

        # 3. Verificar si es dueño del objeto.
        is_owner = str(user.guid) == str(obj.store_name.guid)

        # 4. Métodos de solo lectura → permitir si es dueño
        if request.method in permissions.SAFE_METHODS:
            return is_owner

        # 5. Métodos de modificación → permitir solo si es dueño
        return is_owner
