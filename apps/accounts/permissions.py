from rest_framework import permissions


class IsFacilitator(permissions.BasePermission):
    message = "Facilitator role required."

    def has_permission(self, request, view):
        if not request.user or not request.user.is_authenticated:
            return False
        return hasattr(request.user, "profile") and request.user.profile.role == "facilitator"


class IsSeeker(permissions.BasePermission):
    message = "Seeker role required."

    def has_permission(self, request, view):
        if not request.user or not request.user.is_authenticated:
            return False
        return hasattr(request.user, "profile") and request.user.profile.role == "seeker"


class IsOwnerOrReadOnly(permissions.BasePermission):
    def has_object_permission(self, request, view, obj):
        if request.method in permissions.SAFE_METHODS:
            return True
        owner = getattr(obj, "created_by", None)
        return owner == request.user
