# core/permissions.py
from rest_framework.permissions import BasePermission


# core/permissions.py
def _user_role(user):
    """
    Helper to fetch the role for a user.
    - Superusers or staff are treated as 'admin'
    - Otherwise fall back to Profile.role (customer/vendor)
    """
    if not user.is_authenticated:
        return None
    
    # Staff or superuser → admin
    if user.is_staff or user.is_superuser:
        return "admin"

    # Normal users → check profile
    return getattr(user.profile, "role", None)






class IsCustomer(BasePermission):
    """Allow access only to users with role == 'customer'."""
    def has_permission(self, request, view):
        return request.user and request.user.is_authenticated and _user_role(request.user) == "customer"


class IsVendor(BasePermission):
    """Allow access only to users with role == 'vendor'."""
    def has_permission(self, request, view):
        return request.user and request.user.is_authenticated and _user_role(request.user) == "vendor"


class IsAdminUserCustom(BasePermission):
    """Allow access only to staff/superuser (admin)."""
    def has_permission(self, request, view):
        return request.user and request.user.is_authenticated and (request.user.is_staff or request.user.is_superuser)


class IsVendorOrAdmin(BasePermission):
    """Vendor or admin allowed (useful for create product)."""
    def has_permission(self, request, view):
        if not (request.user and request.user.is_authenticated):
            return False
        if request.user.is_staff or request.user.is_superuser:
            return True
        return _user_role(request.user) == "vendor"


# core/permissions.py

class IsProductOwnerOrAdmin(BasePermission):
    def has_object_permission(self, request, view, obj):
        if not (request.user and request.user.is_authenticated):
            return False
        if request.user.is_staff or request.user.is_superuser:
            return True
        # ✅ Product has vendor → vendor.user
        return obj.vendor and obj.vendor.user == request.user




class IsOrderViewer(BasePermission):
    def has_object_permission(self, request, view, obj):
        if not (request.user and request.user.is_authenticated):
            return False
        if request.user.is_staff or request.user.is_superuser:
            return True

        role = _user_role(request.user)
        if role == "customer":
            return getattr(obj, "user", None) == request.user

        if role == "vendor":
            # check if any order item belongs to this vendor
            for item in getattr(obj, "items").all():
                prod = getattr(item, "product", None)
                if prod and prod.vendor and prod.vendor.user == request.user:
                    return True
            return False

        return False


class IsOrderOwnerOrAdmin(BasePermission):
    def has_object_permission(self, request, view, obj):
        if not (request.user and request.user.is_authenticated):
            return False
        if request.user.is_staff or request.user.is_superuser:
            return True
        return obj.user == request.user


class IsNotCustomer(BasePermission):
    """Deny access to users with role == 'customer'."""
    def has_permission(self, request, view):
        return request.user and request.user.is_authenticated and _user_role(request.user) != "customer"
