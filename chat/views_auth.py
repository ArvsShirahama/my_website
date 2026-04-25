from django.shortcuts import render, redirect
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.models import User
from django.contrib.auth.decorators import login_required
from django.utils import timezone
from .models import UserProfile


def register_view(request):
    """User registration"""
    if request.method == 'POST':
        username = request.POST.get('username', '').strip()
        email = request.POST.get('email', '').strip()
        password = request.POST.get('password', '')
        confirm = request.POST.get('confirm_password', '')
        
        errors = []
        if not username: errors.append('Username is required')
        elif User.objects.filter(username=username).exists(): errors.append('Username already exists')
        if not email: errors.append('Email is required')
        elif User.objects.filter(email=email).exists(): errors.append('Email already registered')
        if len(password) < 6: errors.append('Password must be at least 6 characters')
        elif password != confirm: errors.append('Passwords do not match')
        
        if errors:
            return render(request, 'chat/register.html', {'errors': errors, 'data': request.POST})
        
        user = User.objects.create_user(username=username, email=email, password=password)
        UserProfile.objects.create(user=user)
        login(request, user)
        return redirect('chat_list')
    
    return render(request, 'chat/register.html')


def login_view(request):
    """User login"""
    if request.user.is_authenticated:
        return redirect('chat_list')
    
    if request.method == 'POST':
        username = request.POST.get('username', '').strip()
        password = request.POST.get('password', '')
        
        user = authenticate(request, username=username, password=password)
        if user is not None:
            login(request, user)
            profile, _ = UserProfile.objects.get_or_create(user=user)
            profile.is_online, profile.last_seen = True, timezone.now()
            profile.save()
            return redirect('chat_list')
        return render(request, 'chat/login.html', {'error': 'Invalid credentials'})
    
    return render(request, 'chat/login.html')


def logout_view(request):
    """User logout"""
    if request.user.is_authenticated:
        profile = getattr(request.user, 'profile', None)
        if profile:
            profile.is_online, profile.last_seen = False, timezone.now()
            profile.save()
    logout(request)
    return redirect('login')


@login_required
def profile_view(request):
    """User profile"""
    profile, _ = UserProfile.objects.get_or_create(user=request.user)
    
    if request.method == 'POST':
        request.user.first_name = request.POST.get('first_name', '')
        request.user.last_name = request.POST.get('last_name', '')
        request.user.save()
        
        profile.bio = request.POST.get('bio', '')
        if 'avatar' in request.FILES:
            profile.avatar = request.FILES['avatar']
        theme = request.POST.get('theme', 'system')
        if theme in ['light', 'dark', 'system']:
            profile.theme_preference = theme
        profile.save()
        return redirect('profile')
    
    return render(request, 'chat/profile.html', {'user': request.user, 'profile': profile})
