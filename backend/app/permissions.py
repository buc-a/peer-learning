"""
Общие DRF-разрешения (permission classes) для всего проекта.
"""

from rest_framework.permissions import BasePermission, SAFE_METHODS


class IsOwnerOrReadOnly(BasePermission):
    """
    Разрешает безопасные методы (GET, HEAD, OPTIONS) всем аутентифицированным
    (или анонимным, если view допускает).
    Небезопасные методы (PUT, PATCH, DELETE) — только владельцу объекта.

    View должна определять атрибут `owner_field` (по умолчанию 'author'),
    указывающий на поле модели, которое содержит ссылку на владельца.
    """

    owner_field: str = 'author'

    def has_permission(self, request, view):
        # Безопасные методы не требуют дополнительных проверок здесь —
        # конкретный объект ещё не известен.
        return True

    def has_object_permission(self, request, view, obj):
        # Чтение разрешено всем.
        if request.method in SAFE_METHODS:
            return True
        # Запись — только владельцу.
        owner_field = getattr(view, 'owner_field', self.owner_field)
        owner = getattr(obj, owner_field, None)
        return owner == request.user
