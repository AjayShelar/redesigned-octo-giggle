from typing import Optional

from django.contrib.auth import get_user_model
from rest_framework.permissions import BasePermission, SAFE_METHODS

from .models import UserProfile


def get_role(user: Optional[get_user_model()]):
    if not user or not user.is_authenticated:
        return None
    try:
        profile = UserProfile.objects.get(user=user)
        return profile.role
    except UserProfile.DoesNotExist:
        return UserProfile.Role.VIEWER


class RolePermission(BasePermission):
    """Role-based permission using a view's role_permissions map.

    role_permissions example:
      {"list": ["admin", "operator", "viewer"], "create": ["admin"]}
    """

    def has_permission(self, request, view):
        role = get_role(request.user)
        if role is None:
            return False
        if role == UserProfile.Role.ADMIN:
            return True

        role_permissions = getattr(view, "role_permissions", {})
        action = getattr(view, "action", None)
        allowed = role_permissions.get(action) or role_permissions.get("*")
        if allowed is not None:
            return role in allowed

        if request.method in SAFE_METHODS:
            return role in [UserProfile.Role.ADMIN, UserProfile.Role.OPERATOR, UserProfile.Role.VIEWER]

        return False
