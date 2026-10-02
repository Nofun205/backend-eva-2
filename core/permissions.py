from rest_framework import permissions

class IsStudent(permissions.BasePermission):
    """
    Permite acceso solo a usuarios con el rol de Estudiante.
    """
    def has_permission(self, request, view):
        return bool(request.user and request.user.is_authenticated and request.user.rol == 'ESTUDIANTE')

class IsCoordinator(permissions.BasePermission):
    """
    Permite acceso solo a usuarios con el rol de Coordinador Académico.
    """
    def has_permission(self, request, view):
        return bool(request.user and request.user.is_authenticated and request.user.rol == 'COORDINADOR')
