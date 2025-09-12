from rest_framework.views import APIView
from django.core.mail import send_mail
from django.conf import settings
from rest_framework.permissions import AllowAny
from rest_framework.response import Response
from rest_framework import status
from .serializers import SignupSerializer, RequestOTPSerializer, PasswordLoginSerializer, LoginSerializer
import random
from django.contrib.auth import get_user_model
from .models import OTP, User

from django.contrib.auth import authenticate, login, logout
from django.shortcuts import redirect
from rest_framework_simplejwt.tokens import RefreshToken

class LogoutView(APIView):
    def post(self, request):
        logout(request)
        return redirect('/')

User = get_user_model()

class SignupAPIView(APIView):
    permission_classes = [AllowAny]

    def post(self, request):
        serializer = SignupSerializer(data=request.data)
        if serializer.is_valid():
            serializer.save()
            return Response({"detail": "User created successfully"}, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class RequestOTPAPIView(APIView):
    permission_classes = [AllowAny]

    def post(self, request):
        serializer = RequestOTPSerializer(data=request.data)
        if serializer.is_valid():
            email = serializer.validated_data['email']

            # check if user exists
            try:
                user = User.objects.get(email=email)
            except User.DoesNotExist:
                return Response({"detail": "User not found"}, status=status.HTTP_404_NOT_FOUND)

            # generate OTP
            otp_code = f"{random.randint(100000, 999999)}"
            OTP.objects.create(email=email, code=otp_code)

            # send OTP (console backend)
            send_mail(
                "Your Login OTP",
                f"Your OTP is {otp_code}. It will expire in 5 minutes.",
                getattr(settings, "DEFAULT_FROM_EMAIL", "webmaster@localhost"),
                [email],
                fail_silently=False,
            )

            print("🔥 OTP SENT:", otp_code, "to", email)

            return Response({"detail": "OTP generated successfully", "otp": otp_code}, status=status.HTTP_200_OK)

        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    def get(self, request):
        # Handle GET requests gracefully with 405 Method Not Allowed
        return Response({"detail": "Method GET not allowed"}, status=status.HTTP_405_METHOD_NOT_ALLOWED)


def get_tokens_for_user(user):
    refresh = RefreshToken.for_user(user)
    return {
        'refresh': str(refresh),
        'access': str(refresh.access_token),
    }


class LoginAPIView(APIView):
    permission_classes = [AllowAny]

    def post(self, request):
        email = request.data.get("email")
        password = request.data.get("password")
        otp_code = request.data.get("otp")

        user = None

        # --- Password Login ---
        if password:
            user = authenticate(request, email=email, password=password)
            if user:
                login(request, user)
                if user.is_superuser:
                    # Redirect admin user to admin page
                    return redirect('/admin/')
                elif hasattr(user, 'profile'):
                    if user.profile.role == 'vendor':
                        # Redirect vendor to vendor page
                        return redirect('/vendors/')
                    else:
                        # Redirect customer to main UI page
                        return redirect('/')
                else:
                    # Default redirect to main UI page
                    return redirect('/')

        # --- OTP Login ---
        if not user and otp_code:
            otp = OTP.objects.filter(email=email, code=otp_code, is_used=False).order_by('-created_at').first()
            if otp and not otp.is_expired(expiry_minutes=5):
                otp.is_used = True
                otp.save()
                try:
                    user = User.objects.get(email=email)
                    if not user.is_active:
                        return Response({"detail": "User inactive"}, status=status.HTTP_400_BAD_REQUEST)
                except User.DoesNotExist:
                    return Response({"detail": "User not found"}, status=status.HTTP_404_NOT_FOUND)

        # --- Final Response ---
        if user:
            tokens = get_tokens_for_user(user)
            role = "admin" if user.is_superuser else user.profile.role
            return Response({
                "detail": "Login successful",
                "role": role,
                "tokens": tokens
            }, status=status.HTTP_200_OK)

        return Response({"detail": "Invalid credentials"}, status=status.HTTP_400_BAD_REQUEST)
