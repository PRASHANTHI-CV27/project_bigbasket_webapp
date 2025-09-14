# users/views.py
from rest_framework.views import APIView
from rest_framework.permissions import AllowAny
from rest_framework.response import Response
from rest_framework import status
from django.core.mail import send_mail
from django.conf import settings
from django.contrib.auth import get_user_model, authenticate, login as django_login, logout
from rest_framework_simplejwt.tokens import RefreshToken
import random

from .models import OTP, User, Profile
from .serializers import SignupSerializer, RequestOTPSerializer

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
                redirect_url = "/vendors/"
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
from rest_framework_simplejwt.authentication import JWTAuthentication

class LogoutView(APIView):
    authentication_classes = [JWTAuthentication]

    def post(self, request):
        logout(request)
        return Response({"detail": "Logged out successfully"}, status=status.HTTP_200_OK)
