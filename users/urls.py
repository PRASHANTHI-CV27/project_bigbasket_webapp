# users/urls.py
from django.urls import path
from .views import SignupAPIView, RequestOTPAPIView, VerifyOTPAPIView, PasswordLoginAPIView

urlpatterns = [
    path('signup/', SignupAPIView.as_view(), name='user-signup'),
    path('request-otp/', RequestOTPAPIView.as_view(), name='user-request-otp'),
    path('verify-otp/', VerifyOTPAPIView.as_view(), name='user-verify-otp'),
    path('login/password/', PasswordLoginAPIView.as_view(), name='user-login-password'),
   
]