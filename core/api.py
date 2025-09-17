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

from .models import Product, Category, Cart, CartItem, CartOrder, CartOrderItems, Vendor, Address, Payment
from .serializers import (
    ProductSerializer, CategorySerializer,
    CartSerializer, CartItemSerializer, CartOrderSerializer, VendorSerializer, CartOrderItemUpdateSerializer, AddressSerializer, PaymentSerializer

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


import razorpay
from django.conf import settings
import logging







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
    permission_classes = [IsCustomer]

    def post(self, request):
        try:
            cart = self._get_cart_for_request(request)
            items = list(cart.items.select_related('product').all())

            if not items:
                return Response({"detail": "Cart is empty"}, status=status.HTTP_400_BAD_REQUEST)

            with transaction.atomic():
                total_amount = Decimal("0.00")

                # calculate total
                for ci in items:
                    if not getattr(ci, "product", None):
                        return Response({"detail": f"CartItem {ci.id} missing product"}, status=status.HTTP_400_BAD_REQUEST)
                    product_price = Decimal(ci.product.price or ci.price_snapshot or 0)
                    qty = Decimal(ci.quantity or 0)
                    total_amount += product_price * qty

                # create order (not paid yet)
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

                # ❌ DO NOT clear the cart here

                serializer = CartOrderSerializer(order, context={'request': request})
                return Response(serializer.data, status=status.HTTP_201_CREATED)

        except Exception as e:
            traceback.print_exc()
            return Response({"detail": "Internal server error", "error": str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

    def _get_cart_for_request(self, request):
        if request.user.is_authenticated:
            cart, _ = Cart.objects.get_or_create(user=request.user)
        else:
            sid = request.session.session_key or request.session.create() or request.session.session_key
            cart, _ = Cart.objects.get_or_create(session_id=sid)
        return cart

# -------------------------------
# Order ViewSet
# -------------------------------


class OrderViewSet(viewsets.ModelViewSet):
    serializer_class = CartOrderSerializer
    queryset = CartOrder.objects.all().order_by('-order_date')

    def get_permissions(self):
        if self.action in ['update', 'partial_update', 'destroy']:
            return [permissions.IsAuthenticated(), IsOrderOwnerOrAdmin()]
        return [permissions.IsAuthenticated(), IsOrderViewer()]

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
    
    
logger = logging.getLogger(__name__)   
    

class CreateRazorpayOrderView(APIView):
    permission_classes = [permissions.IsAuthenticated]

    def post(self, request, *args, **kwargs):
        try:
            order_id = request.data.get("order_id")
            order = CartOrder.objects.get(id=order_id, user=request.user)

            amount_in_paise = int(order.price * 100)

            # ✅ Always create fresh client
            client = razorpay.Client(
                auth=(settings.RAZORPAY_KEY_ID, settings.RAZORPAY_KEY_SECRET)
            )

            # ✅ Create Razorpay order
            razorpay_order = client.order.create({
                "amount": 5000,
                "currency": "INR",
                "payment_capture": "1"
            })

            # ✅ Save Payment record
            payment = Payment.objects.create(
                order=order,
                user=request.user,
                method="razorpay",
                amount=order.price,
                status="pending",
                razorpay_order_id=razorpay_order["id"]
            )

            return Response({
                "razorpay_key_id": settings.RAZORPAY_KEY_ID,
                "razorpay_order_id": razorpay_order["id"],
                "razorpay_amount": razorpay_order["amount"],
                "razorpay_currency": razorpay_order["currency"],
                "payment_id": payment.id
            }, status=status.HTTP_201_CREATED)

        except CartOrder.DoesNotExist:
            return Response({"detail": "Order not found"}, status=status.HTTP_404_NOT_FOUND)
        except Exception as e:
            return Response({"detail": str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


class VerifyRazorpayPaymentView(APIView):
    permission_classes = [permissions.IsAuthenticated]

    def post(self, request, *args, **kwargs):
        payment_id = request.data.get("payment_id")
        razorpay_payment_id = request.data.get("razorpay_payment_id")
        razorpay_order_id = request.data.get("razorpay_order_id")
        razorpay_signature = request.data.get("razorpay_signature")

        try:
            payment = Payment.objects.get(id=payment_id, user=request.user)
        except Payment.DoesNotExist:
            return Response({"detail": "Payment not found"}, status=status.HTTP_404_NOT_FOUND)

        params_dict = {
            "razorpay_order_id": razorpay_order_id,
            "razorpay_payment_id": razorpay_payment_id,
            "razorpay_signature": razorpay_signature,
        }

        try:
             # ✅ Create client fresh each time
            client = razorpay.Client(
                auth=(settings.RAZORPAY_KEY_ID, settings.RAZORPAY_KEY_SECRET)
            )
            
            client.utility.verify_payment_signature(params_dict)

            # Update payment and order status
            payment.status = "success"
            payment.razorpay_payment_id = razorpay_payment_id
            payment.razorpay_signature = razorpay_signature
            payment.save()

            payment.order.paid_status = True
            payment.order.save()

            # ✅ clear cart logic here
            Cart.objects.filter(user=request.user).delete()

            # Serialize the updated payment object for a clean response
            serializer = PaymentSerializer(payment)
            return Response(serializer.data, status=status.HTTP_200_OK)

        except razorpay.errors.SignatureVerificationError:
            payment.status = "failed"
            payment.save()

            # Serialize the failed payment object
            serializer = PaymentSerializer(payment)
            return Response({"detail": "Payment verification failed", "payment": serializer.data}, 
                            status=status.HTTP_400_BAD_REQUEST
                            )
        except Exception as e:
            return Response({"detail": str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
    
    
    
    
    
    
    

    
    
