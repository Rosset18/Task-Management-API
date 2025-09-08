from rest_framework.permissions import BasePermission, SAFE_METHODS

class IsOwner(BasePermission):
    """
    Allow object access only to its owner.
    """

    def has_object_permission(self, request, view, obj):
        if hasattr(obj, "user"):
            return obj.user == request.user
        # For notifications: they belong to a user too
        if hasattr(obj, "owner"):
            return obj.owner == request.user
        return False

    def has_permission(self, request, view):
        # Auth is enforced globally; here we can allow all authenticated
        return bool(request.user and request.user.is_authenticated)

