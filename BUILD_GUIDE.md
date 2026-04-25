# Django Google OAuth Authentication System - Build Guide

This guide documents the complete process of building a Django authentication system with Google OAuth integration using django-allauth.

## Overview

A Django web application with:
- Traditional username/password authentication
- Google OAuth authentication
- User registration and login
- Admin panel access

## Prerequisites

- Python 3.14+
- Django 6.0.4
- Google Cloud Account
- Basic Django knowledge

## Step-by-Step Build Process

### 1. Project Setup

```bash
# Create Django project
django-admin startproject myproject
cd myproject

# Create accounts app
python manage.py startapp accounts
```

### 2. Basic Configuration

**myproject/settings.py:**
```python
# Add accounts app to INSTALLED_APPS
INSTALLED_APPS = [
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',
    'accounts',  # Added
    'django.contrib.sites',
    'allauth',
    'allauth.account',
    'allauth.socialaccount',
    'allauth.socialaccount.providers.google',
]

# Add required middleware
MIDDLEWARE = [
    'django.middleware.security.SecurityMiddleware',
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.middleware.common.CommonMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'allauth.account.middleware.AccountMiddleware',  # Added
    'django.middleware.clickjacking.XFrameOptionsMiddleware',
]

# Authentication backends
AUTHENTICATION_BACKENDS = (
    'django.contrib.auth.backends.ModelBackend',
    'allauth.account.auth_backends.AuthenticationBackend',
)

# Google OAuth settings
SOCIALACCOUNT_PROVIDERS = {
    'google': {
        'SCOPE': [
            'profile',
            'email',
        ],
        'AUTH_PARAMS': {
            'access_type': 'online',
        }
    }
}

# Login/Logout settings
LOGIN_REDIRECT_URL = '/'
LOGOUT_REDIRECT_URL = '/'
ACCOUNT_LOGOUT_ON_GET = True

# Site configuration
SITE_ID = 1
```

### 3. URL Configuration

**myproject/urls.py:**
```python
from django.contrib import admin
from django.urls import path, include
from accounts import views

urlpatterns = [
    path('', views.home, name='home'),  # Home page
    path('admin/', admin.site.urls),
    path('accounts/', include('accounts.urls')),  # Custom accounts
    path('accounts/', include('allauth.urls')),  # Django-allauth
]
```

**accounts/urls.py:**
```python
from django.urls import path
from . import views

app_name = 'accounts'

urlpatterns = [
    path('login/', views.login_view, name='login'),
    path('social/', views.social_login, name='social_login'),
]
```

### 4. Views Implementation

**accounts/views.py:**
```python
from django.shortcuts import render, redirect
from django.contrib.auth import authenticate, login
from django.contrib.auth.forms import AuthenticationForm

def home(request):
    """Home page view"""
    return render(request, 'accounts/home.html')

def login_view(request):
    """Traditional login view"""
    if request.method == 'POST':
        form = AuthenticationForm(request, data=request.POST)
        if form.is_valid():
            username = form.cleaned_data.get('username')
            password = form.cleaned_data.get('password')
            user = authenticate(username=username, password=password)
            if user is not None:
                login(request, user)
                return redirect('home')
    else:
        form = AuthenticationForm()
    
    return render(request, 'accounts/login.html', {'form': form})

def social_login(request):
    """Social login page view"""
    return render(request, 'accounts/social_login.html')
```

### 5. Template Creation

**accounts/templates/accounts/home.html:**
```html
<!DOCTYPE html>
<html>
<head>
    <title>Home</title>
    <style>
        body { font-family: Arial, sans-serif; margin: 40px; text-align: center; }
        .container { max-width: 800px; margin: 0 auto; }
        .welcome { font-size: 2em; margin-bottom: 20px; }
        .nav-links { margin: 20px 0; }
        .nav-links a { margin: 0 10px; text-decoration: none; color: #007cba; }
        .nav-links a:hover { text-decoration: underline; }
    </style>
</head>
<body>
    <div class="container">
        <h1 class="welcome">Welcome to My Django Project</h1>
        
        {% if user.is_authenticated %}
            <p>Hello, {{ user.username }}! You are logged in.</p>
            <div class="nav-links">
                <a href="{% url 'accounts:login' %}">Login</a>
                <a href="/admin/">Admin</a>
            </div>
        {% else %}
            <p>Welcome! Please log in to continue.</p>
            <div class="nav-links">
                <a href="{% url 'accounts:login' %}">Login</a>
                <a href="{% url 'accounts:social_login' %}">Google Login</a>
                <a href="/admin/">Admin</a>
            </div>
        {% endif %}
    </div>
</body>
</html>
```

**accounts/templates/accounts/login.html:**
```html
{% load socialaccount %}
<!DOCTYPE html>
<html>
<head>
    <title>Login</title>
    <style>
        body { font-family: Arial, sans-serif; margin: 40px; }
        .form-container { max-width: 400px; margin: 0 auto; }
        .form-group { margin-bottom: 15px; }
        label { display: block; margin-bottom: 5px; }
        input[type="text"], input[type="password"] { 
            width: 100%; padding: 8px; border: 1px solid #ddd; 
        }
        button { background-color: #007cba; color: white; padding: 10px 15px; 
                border: none; cursor: pointer; }
        button:hover { background-color: #005a87; }
        .error { color: red; margin-bottom: 10px; }
    </style>
</head>
<body>
    <div class="form-container">
        <h2>Login</h2>
        
        {% if form.non_field_errors %}
            <div class="error">
                {% for error in form.non_field_errors %}
                    {{ error }}
                {% endfor %}
            </div>
        {% endif %}
        
        <form method="post">
            {% csrf_token %}
            
            <div class="form-group">
                <label for="{{ form.username.id_for_label }}">Username:</label>
                {{ form.username }}
                {% if form.username.errors %}
                    <div class="error">{{ form.username.errors }}</div>
                {% endif %}
            </div>
            
            <div class="form-group">
                <label for="{{ form.password.id_for_label }}">Password:</label>
                {{ form.password }}
                {% if form.password.errors %}
                    <div class="error">{{ form.password.errors }}</div>
                {% endif %}
            </div>
            
            <button type="submit">Login</button>
        </form>
        
        <div style="margin-top: 30px; text-align: center;">
            <p>Or login with:</p>
            <a href="{% url 'accounts:social_login' %}" style="display: inline-flex; align-items: center; background-color: #4285f4; color: white; padding: 10px 15px; text-decoration: none; border-radius: 4px;">
                <svg width="16" height="16" viewBox="0 0 24 24" style="margin-right: 8px;">
                    <path fill="#ffffff" d="M22.56 12.25c0-.78-.07-1.53-.2-2.25H12v4.26h5.92c-.26 1.37-1.04 2.53-2.21 3.31v2.77h3.57c2.08-1.92 3.28-4.74 3.28-8.09z"/>
                    <path fill="#ffffff" d="M12 23c2.97 0 5.46-.98 7.28-2.66l-3.57-2.77c-.98.66-2.23 1.06-3.71 1.06-2.86 0-5.29-1.93-6.16-4.53H2.18v2.84C3.99 20.53 7.7 23 12 23z"/>
                    <path fill="#ffffff" d="M5.84 14.09c-.22-.66-.35-1.36-.35-2.09s.13-1.43.35-2.09V7.07H2.18C1.43 8.55 1 10.22 1 12s.43 3.45 1.18 4.93l2.85-2.22.81-.62z"/>
                    <path fill="#ffffff" d="M12 5.38c1.62 0 3.06.56 4.21 1.64l3.15-3.15C17.45 2.09 14.97 1 12 1 7.7 1 3.99 3.47 2.18 7.07l3.66 2.84c.87-2.6 3.3-4.53 6.16-4.53z"/>
                </svg>
                Google
            </a>
        </div>
    </div>
</body>
</html>
```

**accounts/templates/accounts/social_login.html:**
```html
{% load socialaccount %}
<!DOCTYPE html>
<html>
<head>
    <title>Google Login</title>
    <style>
        body { font-family: Arial, sans-serif; margin: 40px; text-align: center; }
        .container { max-width: 400px; margin: 0 auto; }
        .google-btn {
            display: inline-flex;
            align-items: center;
            background-color: #4285f4;
            color: white;
            padding: 12px 20px;
            border: none;
            border-radius: 4px;
            cursor: pointer;
            text-decoration: none;
            font-size: 16px;
            font-weight: 500;
            margin: 10px;
        }
        .google-btn:hover {
            background-color: #357ae8;
        }
        .google-icon {
            width: 18px;
            height: 18px;
            margin-right: 8px;
        }
        .back-link { margin-top: 20px; }
        .back-link a { color: #007cba; text-decoration: none; }
        .back-link a:hover { text-decoration: underline; }
        .success { color: #28a745; margin-bottom: 20px; }
    </style>
</head>
<body>
    <div class="container">
        <h2>Login with Google</h2>
        
        <div class="success">
            ✅ Google OAuth is configured and ready to use!
        </div>
        
        <a href="{% provider_login_url 'google' process='login' %}" class="google-btn">
            <svg class="google-icon" viewBox="0 0 24 24">
                <path fill="#ffffff" d="M22.56 12.25c0-.78-.07-1.53-.2-2.25H12v4.26h5.92c-.26 1.37-1.04 2.53-2.21 3.31v2.77h3.57c2.08-1.92 3.28-4.74 3.28-8.09z"/>
                <path fill="#ffffff" d="M12 23c2.97 0 5.46-.98 7.28-2.66l-3.57-2.77c-.98.66-2.23 1.06-3.71 1.06-2.86 0-5.29-1.93-6.16-4.53H2.18v2.84C3.99 20.53 7.7 23 12 23z"/>
                <path fill="#ffffff" d="M5.84 14.09c-.22-.66-.35-1.36-.35-2.09s.13-1.43.35-2.09V7.07H2.18C1.43 8.55 1 10.22 1 12s.43 3.45 1.18 4.93l2.85-2.22.81-.62z"/>
                <path fill="#ffffff" d="M12 5.38c1.62 0 3.06.56 4.21 1.64l3.15-3.15C17.45 2.09 14.97 1 12 1 7.7 1 3.99 3.47 2.18 7.07l3.66 2.84c.87-2.6 3.3-4.53 6.16-4.53z"/>
            </svg>
            Continue with Google
        </a>
        
        <div class="back-link">
            <a href="{% url 'accounts:login' %}">← Back to regular login</a>
        </div>
    </div>
</body>
</html>
```

### 6. Database Setup

```bash
# Create and apply migrations
python manage.py makemigrations
python manage.py migrate

# Create superuser for admin access
python manage.py createsuperuser
```

### 7. Google OAuth Configuration

#### 7.1 Google Cloud Console Setup

1. Go to [Google Cloud Console](https://console.cloud.google.com/)
2. Create new project or select existing one
3. Enable Google+ API or People API
4. Configure OAuth consent screen:
   - Go to APIs & Services > OAuth consent screen
   - Select External
   - Fill in app name, user support email, developer contact
5. Create OAuth 2.0 credentials:
   - Go to APIs & Services > Credentials
   - Create OAuth 2.0 Client ID
   - Select Web application
   - Add redirect URI: `http://127.0.0.1:8000/accounts/google/login/callback/`
   - Copy Client ID and Client Secret

#### 7.2 Django Admin Configuration

1. Start development server: `python manage.py runserver`
2. Go to http://127.0.0.1:8000/admin/
3. Navigate to SOCIAL ACCOUNTS > Social applications
4. Add new social application:
   - Provider: Google
   - Name: Google OAuth
   - Client ID: [Your Google Client ID]
   - Secret key: [Your Google Client Secret]
   - Sites: Select your site
5. Save

### 8. Testing the System

```bash
# Start development server
python manage.py runserver
```

Test URLs:
- Home: http://127.0.0.1:8000/
- Traditional Login: http://127.0.0.1:8000/accounts/login/
- Google Login: http://127.0.0.1:8000/accounts/social/
- Admin: http://127.0.0.1:8000/admin/

## Key Features Implemented

1. **Traditional Authentication**: Username/password login using Django's built-in authentication
2. **Google OAuth**: Social login using Google accounts
3. **User Management**: Automatic user creation for OAuth users
4. **Responsive Design**: Clean, mobile-friendly templates
5. **Admin Integration**: Full admin panel access
6. **Security**: CSRF protection, secure redirects

## Dependencies

```txt
Django==6.0.4
django-allauth  # Social authentication
```

## File Structure

```
myproject/
├── manage.py
├── myproject/
│   ├── __init__.py
│   ├── settings.py
│   ├── urls.py
│   ├── wsgi.py
│   └── asgi.py
└── accounts/
    ├── __init__.py
    ├── admin.py
    ├── apps.py
    ├── models.py
    ├── views.py
    ├── urls.py
    ├── tests.py
    └── templates/
        └── accounts/
            ├── home.html
            ├── login.html
            └── social_login.html
```

## Troubleshooting

### Common Issues

1. **TemplateDoesNotExist**: Ensure `accounts` is in `INSTALLED_APPS`
2. **NoReverseMatch**: Check URL patterns include proper namespaces
3. **SocialApp.DoesNotExist**: Configure Google OAuth in Django admin
4. **OAuth errors**: Verify redirect URI matches Google Cloud Console

### Debug Commands

```bash
# Check migrations
python manage.py showmigrations

# Create superuser
python manage.py createsuperuser

# Check configuration
python manage.py check
```

## Security Considerations

- Store Google OAuth credentials securely
- Use HTTPS in production
- Set `DEBUG = False` in production
- Configure `ALLOWED_HOSTS` for production
- Regularly update dependencies

## Production Deployment

1. Set environment variables for OAuth credentials
2. Configure production database
3. Set up static files serving
4. Configure domain and SSL
5. Update redirect URIs to production domain

This complete authentication system provides both traditional and social login options with a clean, user-friendly interface.
