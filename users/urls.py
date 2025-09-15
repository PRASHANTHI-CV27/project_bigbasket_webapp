# users/urls.py
from django.urls import path, include
from . import views
from .views import SignupAPIView, RequestOTPAPIView, LoginAPIView, LogoutView

urlpatterns = [
    path('signup/', SignupAPIView.as_view(), name='user-signup'),
    path('login/', LoginAPIView.as_view(), name='user-login'),
    path('request-otp/', RequestOTPAPIView.as_view(), name='user-request-otp'),
    path('logout/', LogoutView.as_view(), name='logout'),
    
    
    path("vendor/", include("users.vendor_urls")),

]