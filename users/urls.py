from django.urls import path
from . import views

urlpatterns = [
    path("", views.home, name="home"),
    path('register/', views.register, name ='register'),
    path('login/', views.login_page, name ='login_page'),
    path('logout/', views.logout_page, name ='logout_page'),
    path('profile/', views.profile_page, name ='profile_page')

]


