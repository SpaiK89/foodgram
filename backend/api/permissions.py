from rest_framework import permissions


class AuthorOrAdminOrReadOnly(permissions.BasePermission):
    """Разрешения для автора и администратора, либо только для чтения"""
    def has_permission(self, request, view):
        return (request.method in permissions.SAFE_METHODS
                or request.user.is_authenticated)

    def has_object_permission(self, request, view, obj):
        return (request.method in permissions.SAFE_METHODS
                or obj.author == request.user
                or request.user.is_admin
                or request.user.is_staff)


class AdminOrReadOnly(permissions.BasePermission):
    """Разрешения для администратора, либо только для чтения"""
    def has_object_permission(self, request, view, obj):
        return (request.method in permissions.SAFE_METHODS
                or request.user.is_admin)
