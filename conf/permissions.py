from rest_framework import permissions

class IsOwnerByGUIDOrAdminForUserApp(permissions.BasePermission):
    """
    Permite acceso si el usuario autenticado es dueño del recurso 
    (por GUID), o si es staff/superuser.
    """

    def has_object_permission(self, request, view, obj):
        """Verifica permisos de usuario para realizar acciones"""
        authenticated_user_guid = getattr(request.user, 'guid', None)
        object_guid = getattr(obj, 'guid', None)

        # 1. Si el usuario es staff o superuser, siempre tiene permiso.
        if request.user and (
            request.user.is_staff or request.user.is_superuser):
            print("Permission granted: User is staff or superuser.")
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
            print(f"Method is SAFE. Is owner: {is_owner}")
            return is_owner

        # 4. Para métodos no seguros (POST, PUT, PATCH, DELETE):
        # Solo el dueño o un admin pueden modificar/eliminar el objeto.
        print(f"Method is UNSAFE. Is owner: {is_owner}")
        return is_owner
