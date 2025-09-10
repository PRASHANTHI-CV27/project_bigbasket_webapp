
from django.shortcuts import render, redirect
from django.contrib.auth import get_user_model, login,logout, authenticate
from django.http import HttpResponse
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from .models import Profile




User = get_user_model()

def home(request):
    print("DEBUG HOME request.user:", request.user, request.user.is_authenticated)
    return render(request, "index.html")

def register(request):
    if request.method == 'POST':
        email = request.POST.get('email', '').strip()
        name = request.POST.get('name', '').strip()
        password = request.POST.get('password', '')

        if not email or not password:
            messages.error(request, "Email and password are required.")
            return redirect("register")

        if User.objects.filter(email=email).exists():
            messages.error(request, "Email already registered")
            return redirect("register")

        # ✅ use keyword args
        user = User.objects.create_user(username=name or email, email=email, password=password)
        user.first_name = name
        user.save()
        
        user = authenticate(request, username=email, password=password)
        if user is not None:
            login(request, user)
            messages.success(request, f"Welcome {user.first_name or user.email}")
            return redirect("home")
        else:
            # fallback: set backend and login (rare)
            user.backend = "django.contrib.auth.backends.ModelBackend"
            

        login(request, user)   # auto login after signup
        return redirect("home")

    return render(request, 'register.html')


# users/views.py
from django.contrib.auth import authenticate, login
from django.contrib import messages
from django.shortcuts import redirect, render

def login_page(request):
    if request.method == "POST":
        email = request.POST.get("email", "").strip()
        password = request.POST.get("password", "")
        user = authenticate(request, username=email, password=password)
        print("DEBUG authenticate ->", user)        # temp debug
        if user is not None:
            login(request, user)
            print("DEBUG after login request.user:", request.user, request.user.is_authenticated)
            messages.success(request, "Logged in")
            return redirect("home")   # must redirect (not render)
        messages.error(request, "Invalid credentials")
        return redirect("login_page")
    return render(request, "login.html")


def logout_page(request):
    logout(request)
    return redirect('home')


@login_required(login_url='login_page')
def profile_page(request):
    profile, created = Profile.objects.get_or_create(user=request.user)
    if request.method == 'POST':
        first_name = request.POST.get('first_name', '')
        last_name = request.POST.get('last_name', '')
        address = request.POST.get('address', '')
        phone_number = request.POST.get('phone_number', '')

        request.user.first_name = first_name
        request.user.last_name = last_name
        request.user.save()
        
        

        profile.address = request.POST.get('address', profile.address)
        profile.phone = request.POST.get('phone_number', profile.phone)
        profile.save()

        messages.success(request, "Profile updated successfully")

    return render(request, "profile.html", {"user_profile": profile})