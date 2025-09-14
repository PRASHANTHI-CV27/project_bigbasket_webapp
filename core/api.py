# core/api.py
from rest_framework import viewsets, status, permissions
from rest_framework.response import Response
from django.shortcuts import get_object_or_404
from rest_framework.views import APIView
from django.db import transaction
from decimal import Decimal
import uuid
import traceback
from rest_framework.decorators import action

from .models import Product, Category, Cart, CartItem, CartOrder, CartOrderItems, Vendor, Address
from .serializers import (
    ProductSerializer, CategorySerializer,
    CartSerializer, CartItemSerializer, CartOrderSerializer, VendorSerializer, CartOrderItemUpdateSerializer, AddressSerializer

)
from users.serializers import UserSerializer
from users.models import User

# ✅ Import custom permissions
from core.permissions import (
    IsCustomer, IsVendorOrAdmin, IsProductOwnerOrAdmin, IsOrderViewer,IsVendor,IsAdminUserCustom, IsNotCustomer, IsOrderOwnerOrAdmin
)
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework import status
from rest_framework_simplejwt.authentication import JWTAuthentication

# -------------------------------
# Product ViewSet
# -------------------------------

class ProductViewSet(viewsets.ModelViewSet):
    authentication_classes = [JWTAuthentication]
    serializer_class = ProductSerializer

    def get_queryset(self):
        qs = Product.objects.all().order_by('-date').prefetch_related('productimages_set')

        # filter by category id or cid
        cat = self.request.query_params.get('category')
        if cat:
            if cat.isdigit():
                qs = qs.filter(category_id=int(cat))
            else:
                qs = qs.filter(category__cid=cat)

        # filter by search term
        q = self.request.query_params.get('q')
        if q:
            qs = qs.filter(title__icontains=q)

        return qs

    def get_permissions(self):
        if self.action == "create":
            return [IsVendorOrAdmin()]             # ✅ vendor or admin can create
        if self.action in ["update", "partial_update", "destroy"]:
            return [IsProductOwnerOrAdmin()]       # ✅ only owner vendor or admin
        return [permissions.AllowAny()]            # ✅ public can read


# -------------------------------
# Category ViewSet
# -------------------------------
class CategoryViewSet(viewsets.ReadOnlyModelViewSet):
    queryset = Category.objects.all().order_by('title')
    serializer_class = CategorySerializer
    permission_classes = [permissions.AllowAny]  # ✅ categories visible to all


# -------------------------------
# Cart ViewSet
# -------------------------------
from rest_framework.permissions import IsAuthenticated, AllowAny
from rest_framework.authentication import SessionAuthentication

class CartViewSet(viewsets.ViewSet):
    authentication_classes = [JWTAuthentication, SessionAuthentication]
    permission_classes = [AllowAny]

    def _get_cart(self, request):
        if request.user.is_authenticated:
            cart, _ = Cart.objects.get_or_create(user=request.user)
        else:
            sid = request.session.session_key or request.session.create() or request.session.session_key
            cart, _ = Cart.objects.get_or_create(session_id=sid)
        return cart

    def list(self, request):
        cart = self._get_cart(request)
        serializer = CartSerializer(cart, context={'request': request})
        return Response(serializer.data)

    def create(self, request):
        cart = self._get_cart(request)
        product_id = request.data.get('product')
        qty = int(request.data.get('quantity', 1))

        product = get_object_or_404(Product, pk=product_id)
        item, created = CartItem.objects.get_or_create(cart=cart, product=product)
        if not created:
            item.quantity += qty
        else:
            item.price_snapshot = product.price
            item.quantity = qty
        item.save()

        return Response(CartSerializer(cart, context={'request': request}).data)

    # 🔹 Update item quantity
    def partial_update(self, request, pk=None):
        cart = self._get_cart(request)
        try:
            item = cart.items.get(pk=pk)
        except CartItem.DoesNotExist:
            return Response({"detail": "Item not found"}, status=status.HTTP_404_NOT_FOUND)

        delta = int(request.data.get("delta", 0))
        item.quantity += delta
        if item.quantity <= 0:
            item.delete()
        else:
            item.save()

        return Response(CartSerializer(cart, context={'request': request}).data)

    # 🔹 Remove item
    def destroy(self, request, pk=None):
        cart = self._get_cart(request)
        try:
            item = cart.items.get(pk=pk)
            item.delete()
        except CartItem.DoesNotExist:
            return Response({"detail": "Item not found"}, status=status.HTTP_404_NOT_FOUND)

        return Response(CartSerializer(cart, context={'request': request}).data)

# -------------------------------
# Checkout View
# -------------------------------
class CheckoutView(APIView):
    permission_classes = [IsCustomer]  # ✅ only customers can checkout

    def post(self, request):
        try:
            cart = self._get_cart_for_request(request)
            items = list(cart.items.select_related('product').all())

            if not items:
                return Response({"detail": "Cart is empty"}, status=status.HTTP_400_BAD_REQUEST)

            with transaction.atomic():
                total_amount = Decimal("0.00")

                for ci in items:
                    if not getattr(ci, "product", None):
                        return Response({"detail": f"CartItem {ci.id} missing product"}, status=status.HTTP_400_BAD_REQUEST)

                    product_price = Decimal(ci.product.price or ci.price_snapshot or 0)
                    qty = Decimal(ci.quantity or 0)
                    total_amount += product_price * qty

                # create order
                invoice = uuid.uuid4().hex[:12].upper()
                order = CartOrder.objects.create(
                    user=request.user,
                    invoice_no=invoice,
                    price=total_amount,
                    paid_status=False,
                    order_status='processing'
                )

                # create order items
                for ci in items:
                    product = ci.product
                    CartOrderItems.objects.create(
                        order=order,
                        product=product,
                        item_status='pending',
                        item=product.title if product else str(ci),
                        image=(product.image if getattr(product, 'image', None) else None),
                        qty=ci.quantity,
                        price=product.price if product else (ci.price_snapshot or 0),
                        total=Decimal(ci.quantity) * Decimal(product.price if product else (ci.price_snapshot or 0))
                    )

                # clear cart
                cart.items.all().delete()

                serializer = CartOrderSerializer(order, context={'request': request})
                return Response(serializer.data, status=status.HTTP_201_CREATED)

        except Exception as e:
            traceback.print_exc()
            return Response(
                {"detail": "Internal server error during checkout",
                 "error": str(e),
                 "traceback": traceback.format_exc()},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )

    def _get_cart_for_request(self, request):
        if request.user.is_authenticated:
            cart, _ = Cart.objects.get_or_create(user=request.user)
        else:
            sid = request.session.session_key or request.session.create() or request.session.session_key
            cart, _ = Cart.objects.get_or_create(session_id=sid)

        if request.user.is_authenticated and cart.session_id and not cart.user:
            user_cart, _ = Cart.objects.get_or_create(user=request.user)
            for item in cart.items.all():
                existing = user_cart.items.filter(product=item.product).first()
                if existing:
                    existing.quantity += item.quantity
                    existing.save()
                else:
                    item.cart = user_cart
                    item.save()
            cart.delete()
            cart = user_cart

        return cart


# -------------------------------
# Order ViewSet
# -------------------------------


class OrderViewSet(viewsets.ModelViewSet):
    serializer_class = CartOrderSerializer

    def get_permissions(self):
        if self.action in ['update', 'partial_update', 'destroy']:
            return [permissions.IsAuthenticated, IsOrderOwnerOrAdmin()]
        return [permissions.IsAuthenticated, IsOrderViewer()]

    def get_queryset(self):
        qs = CartOrder.objects.all().order_by('-order_date')
        user = self.request.user
        if user.is_staff or user.is_superuser:
            return qs
        return qs.filter(user=user)

    # ✅ Vendor/Admin can update per item status
    @action(detail=True, methods=['patch'], permission_classes=[IsVendorOrAdmin])
    def update_item_status(self, request, pk=None):
        order = self.get_object()
        item_id = request.data.get("item_id")
        new_status = request.data.get("item_status")

        if not item_id or not new_status:
            return Response({"detail": "item_id and item_status required"}, status=400)

        try:
            item = order.items.get(id=item_id)
        except CartOrderItems.DoesNotExist:
            return Response({"detail": "Item not found in this order"}, status=404)

        # ✅ Admin can update any item
        if request.user.is_staff or request.user.is_superuser:
            item.item_status = new_status
            item.save()
            return Response({"detail": f"Admin updated item {item.id} to {new_status}"})

        # ✅ Vendor can only update their own items
        if item.product.vendor and item.product.vendor.user == request.user:
            item.item_status = new_status
            item.save()
            return Response({"detail": f"Vendor updated item {item.id} to {new_status}"})

        return Response({"detail": "Permission denied"}, status=403)

class VendorViewSet(viewsets.ModelViewSet):
    queryset = Vendor.objects.all().order_by("title")
    serializer_class = VendorSerializer

    def perform_create(self, serializer):
        # When a vendor user creates a vendor, link it automatically
        serializer.save(user=self.request.user)

    def get_permissions(self):
        if self.action in ["create", "update", "partial_update", "destroy"]:
            return [IsVendorOrAdmin()]
        return [IsNotCustomer()]  # ✅ customers cannot see vendors


# -------------------------------
# User ViewSet (Admin only)
# -------------------------------
class UserViewSet(viewsets.ModelViewSet):
    queryset = User.objects.all().order_by('-date_joined')
    serializer_class = UserSerializer
    permission_classes = [IsAdminUserCustom]  # ✅ only admin



class AddressViewSet(viewsets.ModelViewSet):
    serializer_class = AddressSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        # Only addresses for the logged-in user
        return Address.objects.filter(user=self.request.user).order_by("-status", "-id")

    def perform_create(self, serializer):
        # If user has no default, make this the default
        is_first = not Address.objects.filter(user=self.request.user, status=True).exists()
        addr = serializer.save(user=self.request.user, status=is_first or serializer.validated_data.get("status", False))
        # If this address is default, unset status for others
        if addr.status:
            Address.objects.filter(user=self.request.user).exclude(pk=addr.pk).update(status=False)

    def partial_update(self, request, *args, **kwargs):
        # Keep normal partial_update behaviour, but if status=True set it as default and unset others
        instance = self.get_object()
        status_val = request.data.get("status", None)
        serializer = self.get_serializer(instance, data=request.data, partial=True)
        serializer.is_valid(raise_exception=True)
        serializer.save()
        if status_val in [True, "true", "True", "1", 1]:
            Address.objects.filter(user=self.request.user).exclude(pk=instance.pk).update(status=False)
        return Response(serializer.data)

    @action(detail=True, methods=["post"])
    def set_default(self, request, pk=None):
        addr = self.get_object()
        Address.objects.filter(user=request.user).update(status=False)
        addr.status = True
        addr.save()
        return Response(self.get_serializer(addr).data, status=status.HTTP_200_OK)