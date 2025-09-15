# users/views.py
from rest_framework.views import APIView
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework.response import Response
from rest_framework import status
from django.core.mail import send_mail
from django.conf import settings
from django.contrib.auth import get_user_model, authenticate, login as django_login, logout
from rest_framework_simplejwt.tokens import RefreshToken
import random

from .models import OTP, User, Profile
from .serializers import SignupSerializer, RequestOTPSerializer

from django.shortcuts import render, redirect
from django.contrib.auth.decorators import login_required
from core.permissions import _user_role
from core.models import Vendor, Product, Category, Tags, CartOrderItems
from rest_framework_simplejwt.authentication import JWTAuthentication

from django.views.decorators.csrf import csrf_exempt
from django.utils.decorators import method_decorator

# Utility to create JWT tokens
def get_tokens_for_user(user):
    refresh = RefreshToken.for_user(user)
    return {
        "refresh": str(refresh),
        "access": str(refresh.access_token),
    }


# ------------------------
# Signup
# ------------------------
class SignupAPIView(APIView):
    permission_classes = [AllowAny]
    authentication_classes = []

    def post(self, request):
        serializer = SignupSerializer(data=request.data)
        if serializer.is_valid():
            serializer.save()
            return Response(
                {"detail": "User created successfully"},
                status=status.HTTP_201_CREATED,
            )
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


# ------------------------
# Request OTP
# ------------------------
class RequestOTPAPIView(APIView):
    permission_classes = [AllowAny]
    authentication_classes = []

    def post(self, request):
        serializer = RequestOTPSerializer(data=request.data)
        if serializer.is_valid():
            email = serializer.validated_data["email"]

            try:
                user = User.objects.get(email=email)
            except User.DoesNotExist:
                return Response({"detail": "User not found"}, status=status.HTTP_404_NOT_FOUND)

            # Generate OTP
            otp_code = f"{random.randint(100000, 999999)}"
            OTP.objects.create(email=email, code=otp_code)

            # Send OTP (console/email)
            send_mail(
                "Your Login OTP",
                f"Your OTP is {otp_code}. It will expire in 5 minutes.",
                getattr(settings, "DEFAULT_FROM_EMAIL", "webmaster@localhost"),
                [email],
                fail_silently=False,
            )

            print("🔥 OTP SENT:", otp_code, "to", email)

            return Response({"detail": "OTP sent successfully", "otp": otp_code}, status=status.HTTP_200_OK)

        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


# ------------------------
# Login (OTP only)
# ------------------------
class LoginAPIView(APIView):
    permission_classes = [AllowAny]
    authentication_classes = []

    def post(self, request):
        import logging
        logger = logging.getLogger(__name__)

        email = request.data.get("email")
        otp_code = request.data.get("otp")

        if not otp_code:
            return Response({"detail": "OTP required"}, status=status.HTTP_400_BAD_REQUEST)

        # Validate OTP
        otp = OTP.objects.filter(email=email, code=otp_code, is_used=False).order_by("-created_at").first()
        if not otp or otp.is_expired(expiry_minutes=5):
            return Response({"detail": "Invalid or expired OTP"}, status=status.HTTP_400_BAD_REQUEST)

        otp.is_used = True
        otp.save()

        try:
            user = User.objects.get(email=email)
        except User.DoesNotExist:
            return Response({"detail": "User not found"}, status=status.HTTP_404_NOT_FOUND)

        try:
            # Create Django session for admin access
            # Specify backend to avoid ValueError when multiple backends are configured
            backend = None
            if hasattr(user, 'backend'):
                backend = user.backend
            else:
                from django.conf import settings
                backend = settings.AUTHENTICATION_BACKENDS[0]
            django_login(request, user, backend=backend)

            # Issue tokens
            tokens = get_tokens_for_user(user)
            role = "admin" if user.is_superuser or user.is_staff else getattr(user.profile, "role", "customer")

            # Decide dashboard redirect
            if role == "admin":
                redirect_url = "/admin/"
            elif role == "vendor":
                redirect_url = "/users/vendor/"
            else:
                redirect_url = "/"

            response_data = {
                "detail": "Login successful",
                "role": role,
                "tokens": tokens,
                "redirect_url": redirect_url,
            }
            logger.info(f"Login response data: {response_data}")
            return Response(response_data, status=status.HTTP_200_OK)
        except Exception as e:
            logger.error(f"Error during login: {e}", exc_info=True)
            return Response({"detail": "Internal server error during login"}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


# ------------------------
# Logout
# ------------------------


class LogoutView(APIView):
    authentication_classes = [JWTAuthentication]
    permission_classes = [IsAuthenticated]

    def post(self, request):
        logout(request)
        return Response({"detail": "Logged out successfully"}, status=status.HTTP_200_OK)












@login_required
def vendor_dashboard(request):
    if not hasattr(request.user, "profile") or request.user.profile.role != "vendor":
        return redirect("/")
    
    vendor = Vendor.objects.filter(user=request.user).first()
    return render(request, "vendor.html", {"vendor": vendor})


@login_required
def vendor_profile(request):
    if not hasattr(request.user, "profile") or request.user.profile.role != "vendor":
        return redirect("/")
    vendor = Vendor.objects.filter(user=request.user).first()
    return render(request, "vendor_profile.html",  {"vendor": vendor})





@login_required
def vendor_edit_profile(request):
    if not hasattr(request.user, "profile") or request.user.profile.role != "vendor":
        return redirect("/")
    
    vendor = Vendor.objects.filter(user=request.user).first()

    if request.method == "POST":
        vendor.title = request.POST.get("title")
        vendor.description = request.POST.get("description")
        vendor.address = request.POST.get("address")
        vendor.contact = request.POST.get("contact")

        if "image" in request.FILES:
            vendor.image = request.FILES["image"]

        vendor.save()
        return redirect("vendor-profile")  # 👈 make sure this matches urls.py

    return render(request, "vendor-edit-profile.html", {"vendor": vendor})



@login_required
def vendor_products(request):
    # only vendors allowed
    if not hasattr(request.user, "profile") or request.user.profile.role != "vendor":
        return redirect("/")

    vendor = Vendor.objects.filter(user=request.user).first()
    products = Product.objects.filter(vendor=vendor)   # ✅ fetch only this vendor's products

    return render(request, "vendor_products.html", {"products": products})




@login_required
def add_product(request):
    vendor = Vendor.objects.filter(user=request.user).first()
    categories = Category.objects.all()
    tags = Tags.objects.all()
    product_status_choices = Product._meta.get_field("product_status").choices

    if request.method == "POST":
        product = Product.objects.create(
            user=request.user,
            vendor=vendor,
            category_id=request.POST.get("category"),
            brand=request.POST.get("brand"),
            title=request.POST.get("title"),
            description=request.POST.get("description"),
            price=request.POST.get("price"),
            old_price=request.POST.get("old_price") or None,
            specifications=request.POST.get("specifications"),
            product_status=request.POST.get("product_status"),
            featured=True if request.POST.get("featured") else False,
            highlights=request.POST.get("highlights") or "[]",
            image=request.FILES.get("image"),
        )

        # ManyToMany (tags)
        selected_tags = request.POST.getlist("tags")
        if selected_tags:
            product.tags.set(selected_tags)

        return redirect("vendor-products")

    return render(request, "add_product.html", {
        "categories": categories,
        "tags": tags,
        "product_status_choices": product_status_choices,
    })
    
    
    
    
@login_required
def edit_product(request, pk):
    vendor = Vendor.objects.filter(user=request.user).first()
    product = get_object_or_404(Product, pk=pk, vendor=vendor)

    categories = Category.objects.all()
    tags = Tags.objects.all()
    product_status_choices = Product._meta.get_field("product_status").choices

    if request.method == "POST":
        product.category_id = request.POST.get("category")
        product.brand = request.POST.get("brand")
        product.title = request.POST.get("title")
        product.description = request.POST.get("description")
        product.price = request.POST.get("price")
        product.old_price = request.POST.get("old_price") or None
        product.specifications = request.POST.get("specifications")
        product.product_status = request.POST.get("product_status")
        product.featured = True if request.POST.get("featured") else False
        product.highlights = request.POST.get("highlights") or "[]"

        if "image" in request.FILES:
            product.image = request.FILES["image"]

        product.save()

        # ManyToMany tags
        selected_tags = request.POST.getlist("tags")
        product.tags.set(selected_tags)

        return redirect("vendor-products")

    return render(request, "edit_product.html", {
        "product": product,
        "categories": categories,
        "tags": tags,
        "product_status_choices": product_status_choices,
    })



@login_required
def delete_product(request, pk):
    """Delete vendor's own product"""
    product = get_object_or_404(Product, pk=pk, vendor__user=request.user)
    product.delete()
    return redirect("vendor-products")





@login_required
def vendor_orders(request):
    # Ensure only vendors
    if not hasattr(request.user, "profile") or request.user.profile.role != "vendor":
        return redirect("/")

    vendor = Vendor.objects.filter(user=request.user).first()
    # ✅ Filter only orders that contain this vendor's products
    orders = CartOrderItems.objects.filter(product__vendor=vendor).select_related("order", "product")

    return render(request, "vendor_orders.html", {"orders": orders})


@login_required
def update_order_status(request, pk):
    if not hasattr(request.user, "profile") or request.user.profile.role != "vendor":
        return redirect("/")

    vendor = Vendor.objects.filter(user=request.user).first()
    order_item = get_object_or_404(CartOrderItems, pk=pk, product__vendor=vendor)  # ✅ vendor restriction

    if request.method == "POST":
        new_status = request.POST.get("item_status")
        order_item.item_status = new_status
        order_item.save()
        return redirect("vendor-orders")

    return render(request, "update_order_status.html", {"order_item": order_item})
