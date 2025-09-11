from rest_framework.views import APIView
from django.core.mail import send_mail
from django.conf import settings
from rest_framework.permissions import AllowAny
from rest_framework.response import Response
from rest_framework import status
from .serializers import SignupSerializer,RequestOTPSerializer, PasswordLoginSerializer,LoginSerializer
import random
from django.contrib.auth import get_user_model
from .models import OTP, User

from django.contrib.auth import authenticate, login

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

            return Response({"detail": "OTP generated successfully","otp": otp_code  }, status=status.HTTP_200_OK)


        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
    
    
    
    

# --- Login with password (for everyone, required for admin) ---
from rest_framework_simplejwt.tokens import RefreshToken
from django.contrib.auth import authenticate, login

def get_tokens_for_user(user):
    refresh = RefreshToken.for_user(user)
    return {
        "refresh": str(refresh),
        "access": str(refresh.access_token),
    }

# --- Login with password ---
class PasswordLoginAPIView(APIView):
    permission_classes = [AllowAny]

    def post(self, request):
        serializer = PasswordLoginSerializer(data=request.data)
        if serializer.is_valid():
            email = serializer.validated_data['email']
            password = serializer.validated_data['password']

            user = authenticate(request, email=email, password=password)
            if user is not None:
                tokens = get_tokens_for_user(user)
                role = "admin" if user.is_superuser else user.profile.role
                return Response({
                    "detail": "Login successful",
                    "role": role,
                    "tokens": tokens
                }, status=status.HTTP_200_OK)

            return Response({"detail": "Invalid credentials"}, status=status.HTTP_400_BAD_REQUEST)

        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


# --- Verify OTP (Login with OTP) ---
class VerifyOTPAPIView(APIView):
    permission_classes = [AllowAny]

    def post(self, request):
        serializer = LoginSerializer(data=request.data)
        if not serializer.is_valid():
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

        email = serializer.validated_data['email']
        otp_code = serializer.validated_data['otp']

        otp = OTP.objects.filter(email=email, code=otp_code, is_used=False).order_by('-created_at').first()
        if not otp:
            return Response({"detail": "Invalid OTP"}, status=status.HTTP_400_BAD_REQUEST)

        if otp.is_expired(expiry_minutes=5):
            return Response({"detail": "OTP expired"}, status=status.HTTP_400_BAD_REQUEST)

        otp.is_used = True
        otp.save()

        try:
            user = User.objects.get(email=email)
        except User.DoesNotExist:
            return Response({"detail": "User not found"}, status=status.HTTP_404_NOT_FOUND)

        if not user.is_active:
            return Response({"detail": "User inactive"}, status=status.HTTP_400_BAD_REQUEST)

        tokens = get_tokens_for_user(user)
        role = "admin" if user.is_superuser else user.profile.role

        return Response({
            "detail": "Login successful",
            "role": role,
            "tokens": tokens
        }, status=status.HTTP_200_OK)

