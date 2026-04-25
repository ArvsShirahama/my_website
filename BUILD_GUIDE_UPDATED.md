# Django Google OAuth Authentication System - Complete Build Guide

This guide documents the complete process of building a Django authentication system with Google OAuth integration using django-allauth, including development setup and Render deployment.

## Overview

A Django web application with:
- Traditional username/password authentication
- Google OAuth authentication
- User registration and login
- Admin panel access
- Production-ready deployment on Render

## Prerequisites

- Python 3.14+
- Django 6.0.4
- Google Cloud Account
- Basic Django knowledge
- Render account (for deployment)

## Step-by-Step Build Process

### 1. Project Setup

```bash
# Create Django project
django-admin startproject myproject
cd myproject

# Create accounts app
python manage.py startapp accounts

# Create templates directory
mkdir -p templates/accounts
```

### 2. Dependencies Installation

**requirements.txt:**
```txt
Django==6.0.4
django-allauth==0.57.0
dj-database-url==2.1.0
whitenoise==6.6.0
gunicorn==21.2.0
psycopg2-binary==2.9.9
```

Install dependencies:
```bash
pip install -r requirements.txt
```

### 3. Basic Configuration

**myproject/settings.py:**
```python
import os
from pathlib import Path

# Build paths inside the project like this: BASE_DIR / 'subdir'.
BASE_DIR = Path(__file__).resolve().parent.parent

# SECURITY WARNING: keep the secret key used in production secret!
SECRET_KEY = os.environ.get('SECRET_KEY', 'django-insecure-j9s26*1b23!vg$ty$q#*s-gh!6-3*uxevg06et16rq1d@xitn2')

# SECURITY WARNING: don't run with debug turned on in production!
DEBUG = os.environ.get('DEBUG', 'True') == 'True'

ALLOWED_HOSTS = os.environ.get('ALLOWED_HOSTS', 'localhost,127.0.0.1').split(',')

# Templates configuration
TEMPLATES = [
    {
        'BACKEND': 'django.template.backends.django.DjangoTemplates',
        'DIRS': [BASE_DIR / 'templates'],
        'APP_DIRS': True,
        'OPTIONS': {
            'context_processors': [
                'django.template.context_processors.request',
                'django.contrib.auth.context_processors.auth',
                'django.contrib.messages.context_processors.messages',
            ],
        },
    },
]

# Database configuration (for production)
import dj_database_url
DATABASES = {
    'default': dj_database_url.config(
        default='sqlite:///' + os.path.join(BASE_DIR, 'db.sqlite3')
    )
}

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
    'whitenoise.middleware.WhiteNoiseMiddleware',  # For static files in production
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

# Static files configuration
STATIC_URL = '/static/'
STATIC_ROOT = BASE_DIR / 'staticfiles'

# Media files configuration
MEDIA_URL = '/media/'
MEDIA_ROOT = BASE_DIR / 'media'

# Security settings for production
SECURE_BROWSER_XSS_FILTER = True
SECURE_CONTENT_TYPE_NOSNIFF = True
X_FRAME_OPTIONS = 'DENY'
```

### 4. URL Configuration

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

### 5. Views Implementation

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

### 6. Template Creation

**accounts/templates/accounts/home.html:**
```html
{% load socialaccount %}
<!DOCTYPE html>
<html>
<head>
    <title>Home - Django OAuth</title>
    <style>
        body { font-family: Arial, sans-serif; margin: 40px; text-align: center; }
        .container { max-width: 800px; margin: 0 auto; }
        .welcome { font-size: 2em; margin-bottom: 20px; }
        .nav-links { margin: 20px 0; }
        .nav-links a { margin: 0 10px; text-decoration: none; color: #007cba; }
        .nav-links a:hover { text-decoration: underline; }
        .user-info { background: #f8f9fa; padding: 20px; border-radius: 8px; margin: 20px 0; }
    </style>
</head>
<body>
    <div class="container">
        <h1 class="welcome">Welcome to Django OAuth System</h1>
        
        {% if user.is_authenticated %}
            <div class="user-info">
                <h2>Hello, {{ user.username }}!</h2>
                <p>You are successfully logged in.</p>
                {% if user.socialaccount_set.all %}
                    <p>Logged in via: {{ user.socialaccount_set.first.0.provider }}</p>
                {% endif %}
            </div>
            <div class="nav-links">
                <a href="/logout/">Logout</a>
                <a href="/admin/">Admin Panel</a>
            </div>
        {% else %}
            <p>Welcome! Please choose a login method to continue.</p>
            <div class="nav-links">
                <a href="{% url 'accounts:login' %}">Traditional Login</a>
                <a href="{% url 'accounts:social_login' %}">Google Login</a>
                <a href="/admin/">Admin Panel</a>
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
    <title>Login - Django OAuth</title>
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
        .social-login { margin-top: 30px; text-align: center; }
        .google-btn {
            display: inline-flex;
            align-items: center;
            background-color: #4285f4;
            color: white;
            padding: 10px 15px;
            text-decoration: none;
            border-radius: 4px;
            margin: 10px;
        }
        .google-btn:hover { background-color: #357ae8; }
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
        
        <div class="social-login">
            <p>Or login with:</p>
            <a href="{% provider_login_url 'google' process='login' %}" class="google-btn">
                <svg width="16" height="16" viewBox="0 0 24 24" style="margin-right: 8px;">
                    <path fill="#ffffff" d="M22.56 12.25c0-.78-.07-1.53-.2-2.25H12v4.26h5.92c-.26 1.37-1.04 2.53-2.21 3.31v2.77h3.57c2.08-1.92 3.28-4.74 3.28-8.09z"/>
                    <path fill="#ffffff" d="M12 23c2.97 0 5.46-.98 7.28-2.66l-3.57-2.77c-.98.66-2.23 1.06-3.71 1.06-2.86 0-5.29-1.93-6.16-4.53H2.18v2.84C3.99 20.53 7.7 23 12 23z"/>
                    <path fill="#ffffff" d="M5.84 14.09c-.22-.66-.35-1.36-.35-2.09s.13-1.43.35-2.09V7.07H2.18C1.43 8.55 1 10.22 1 12s.43 3.45 1.18 4.93l2.85-2.22.81-.62z"/>
                    <path fill="#ffffff" d="M12 5.38c1.62 0 3.06.56 4.21 1.64l3.15-3.15C17.45 2.09 14.97 1 12 1 7.7 1 3.99 3.47 2.18 7.07l3.66 2.84c.87-2.6 3.3-4.53 6.16-4.53z"/>
                </svg>
                Google
            </a>
        </div>
        
        <div style="margin-top: 20px; text-align: center;">
            <a href="{% url 'accounts:social_login' %}" style="color: #007cba; text-decoration: none;">
                View Google Login Options
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
    <title>Google Login - Django OAuth</title>
    <style>
        body { font-family: Arial, sans-serif; margin: 40px; text-align: center; }
        .container { max-width: 500px; margin: 0 auto; }
        .google-btn {
            display: inline-flex;
            align-items: center;
            background-color: #4285f4;
            color: white;
            padding: 15px 25px;
            border: none;
            border-radius: 4px;
            cursor: pointer;
            text-decoration: none;
            font-size: 18px;
            font-weight: 500;
            margin: 10px;
        }
        .google-btn:hover {
            background-color: #357ae8;
        }
        .google-icon {
            width: 20px;
            height: 20px;
            margin-right: 10px;
        }
        .back-link { margin-top: 30px; }
        .back-link a { color: #007cba; text-decoration: none; }
        .back-link a:hover { text-decoration: underline; }
        .success { color: #28a745; margin-bottom: 20px; }
        .info { background: #e3f2fd; padding: 15px; border-radius: 5px; margin: 20px 0; }
    </style>
</head>
<body>
    <div class="container">
        <h2>Login with Google</h2>
        
        <div class="info">
            <h3>Google OAuth Setup Instructions</h3>
            <p><strong>Step 1:</strong> Go to <a href="https://console.cloud.google.com/" target="_blank">Google Cloud Console</a></p>
            <p><strong>Step 2:</strong> Create a new project or select existing one</p>
            <p><strong>Step 3:</strong> Enable "Google+ API" or "People API"</p>
            <p><strong>Step 4:</strong> Configure OAuth consent screen (External)</p>
            <p><strong>Step 5:</strong> Create OAuth 2.0 Client ID (Web application)</p>
            <p><strong>Step 6:</strong> Add redirect URI: <code>http://127.0.0.1:8000/accounts/google/login/callback/</code></p>
            <p><strong>Step 7:</strong> Copy Client ID and Client Secret</p>
            <p><strong>Step 8:</strong> Go to <a href="/admin/">Django Admin</a> → Social applications → Add new</p>
            <p><strong>Step 9:</strong> Enter Provider: Google, Client ID, Secret key, and select your site</p>
        </div>
        
        {% if user.is_authenticated %}
            <div class="success">
                ✅ You are already logged in as {{ user.username }}!
            </div>
        {% else %}
            <a href="{% provider_login_url 'google' process='login' %}" class="google-btn">
                <svg class="google-icon" viewBox="0 0 24 24">
                    <path fill="#ffffff" d="M22.56 12.25c0-.78-.07-1.53-.2-2.25H12v4.26h5.92c-.26 1.37-1.04 2.53-2.21 3.31v2.77h3.57c2.08-1.92 3.28-4.74 3.28-8.09z"/>
                    <path fill="#ffffff" d="M12 23c2.97 0 5.46-.98 7.28-2.66l-3.57-2.77c-.98.66-2.23 1.06-3.71 1.06-2.86 0-5.29-1.93-6.16-4.53H2.18v2.84C3.99 20.53 7.7 23 12 23z"/>
                    <path fill="#ffffff" d="M5.84 14.09c-.22-.66-.35-1.36-.35-2.09s.13-1.43.35-2.09V7.07H2.18C1.43 8.55 1 10.22 1 12s.43 3.45 1.18 4.93l2.85-2.22.81-.62z"/>
                    <path fill="#ffffff" d="M12 5.38c1.62 0 3.06.56 4.21 1.64l3.15-3.15C17.45 2.09 14.97 1 12 1 7.7 1 3.99 3.47 2.18 7.07l3.66 2.84c.87-2.6 3.3-4.53 6.16-4.53z"/>
                </svg>
                Continue with Google
            </a>
        {% endif %}
        
        <div class="back-link">
            <a href="{% url 'accounts:login' %}">← Back to regular login</a>
        </div>
    </div>
</body>
</html>
```

### 7. Database Setup

```bash
# Create and apply migrations
python manage.py makemigrations
python manage.py migrate

# Create superuser for admin access
python manage.py createsuperuser
```

### 8. Development Server Testing

```bash
# Start development server
python manage.py runserver
```

Test URLs:
- Home: http://127.0.0.1:8000/
- Traditional Login: http://127.0.0.1:8000/accounts/login/
- Google Login: http://127.0.0.1:8000/accounts/social/
- Admin: http://127.0.0.1:8000/admin/

### 9. Google OAuth Configuration

#### 9.1 Google Cloud Console Setup

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

#### 9.2 Django Admin Configuration

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

## Production Deployment on Render

### 10. Render Configuration Files

**render.yaml:**
```yaml
services:
  # Web Service
  - type: web
    name: django-google-oauth
    env: python
    plan: free
    buildCommand: pip install -r requirements.txt
    startCommand: gunicorn myproject.wsgi:application
    envVars:
      - key: DEBUG
        value: false
      - key: SECRET_KEY
        generateValue: true
      - key: DATABASE_URL
        fromDatabase:
          name: django-db
          property: connectionString
      - key: GOOGLE_OAUTH_CLIENT_ID
        sync: false
      - key: GOOGLE_OAUTH_CLIENT_SECRET
        sync: false
      - key: ALLOWED_HOSTS
        value: my-website-4jgk.onrender.com

  # PostgreSQL Database
  - type: pserv
    name: django-db
    plan: free
    env: docker
    databaseName: django_oauth_db
    user: django_user
```

**.gitignore:**
```
__pycache__/
*.pyc
db.sqlite3
.env
venv/
staticfiles/
media/
.DS_Store
```

### 11. Production Deployment Steps

#### 11.1 GitHub Setup

```bash
# Initialize git repository
git init
git add .
git commit -m "Initial Django OAuth project"

# Create GitHub repository
# Go to github.com and create new repository
git remote add origin https://github.com/yourusername/django-google-oauth.git
git push -u origin main
```

#### 11.2 Render Deployment

1. **Create Render Account**: Sign up at [render.com](https://render.com)
2. **Create Web Service**:
   - Connect to your GitHub repository
   - Select "Web Service"
   - Runtime: Python 3
   - Build Command: `pip install -r requirements.txt`
   - Start Command: `gunicorn myproject.wsgi:application`
3. **Create PostgreSQL Database**:
   - Add PostgreSQL service
   - Plan: Free tier
   - Database name: `django_oauth_db`
4. **Configure Environment Variables**:
   - `DEBUG`: `false`
   - `ALLOWED_HOSTS`: `your-app-name.onrender.com`
   - `GOOGLE_OAUTH_CLIENT_ID`: Your Google Client ID
   - `GOOGLE_OAUTH_CLIENT_SECRET`: Your Google Client Secret
5. **Update Google OAuth Redirect URI**:
   - Go to Google Cloud Console
   - Add production redirect URI: `https://your-app-name.onrender.com/accounts/google/login/callback/`

#### 11.3 Production Migration

After deployment, run migrations via Render shell:
```bash
# Access Render shell for your service
python manage.py migrate
python manage.py collectstatic --noinput
python manage.py createsuperuser
```

### 12. Production Configuration

#### 12.1 Google OAuth Production Setup

1. Update Google Cloud Console:
   - Add production redirect URI: `https://your-app-name.onrender.com/accounts/google/login/callback/`
   - Update authorized domains if needed

2. Configure Django Admin in Production:
   - Access: `https://your-app-name.onrender.com/admin/`
   - Create SocialApp with Google provider
   - Enter production Client ID and Secret

#### 12.2 Security Settings

The production settings include:
- `DEBUG = False`
- Environment variable configuration
- Whitenoise for static files
- PostgreSQL database
- Secure headers

## Key Features Implemented

1. **Traditional Authentication**: Username/password login using Django's built-in authentication
2. **Google OAuth**: Social login using Google accounts
3. **User Management**: Automatic user creation for OAuth users
4. **Responsive Design**: Clean, mobile-friendly templates
5. **Admin Integration**: Full admin panel access
6. **Production Ready**: Configured for Render deployment
7. **Security**: CSRF protection, secure redirects, environment variables

## Dependencies

```txt
Django==6.0.4
django-allauth==0.57.0
dj-database-url==2.1.0
whitenoise==6.6.0
gunicorn==21.2.0
psycopg2-binary==2.9.9
```

## File Structure

```
myproject/
├── manage.py
├── requirements.txt
├── render.yaml
├── .gitignore
├── myproject/
│   ├── __init__.py
│   ├── settings.py
│   ├── urls.py
│   ├── wsgi.py
│   └── asgi.py
├── accounts/
│   ├── __init__.py
│   ├── admin.py
│   ├── apps.py
│   ├── models.py
│   ├── views.py
│   ├── urls.py
│   ├── tests.py
│   └── templates/
│       └── accounts/
│           ├── home.html
│           ├── login.html
│           └── social_login.html
└── templates/
    └── admin/  # Removed - reverted to default Django admin
```

## Troubleshooting

### Common Issues

1. **TemplateDoesNotExist**: Ensure `accounts` is in `INSTALLED_APPS` and templates directory is configured
2. **NoReverseMatch**: Check URL patterns include proper namespaces
3. **SocialApp.DoesNotExist**: Configure Google OAuth in Django admin
4. **OAuth errors**: Verify redirect URI matches Google Cloud Console
5. **Render deployment errors**: Check start command and environment variables
6. **ModuleNotFoundError**: Ensure correct WSGI path in render.yaml

### Debug Commands

```bash
# Check migrations
python manage.py showmigrations

# Create superuser
python manage.py createsuperuser

# Check configuration
python manage.py check

# Collect static files
python manage.py collectstatic
```

## Security Considerations

- Store Google OAuth credentials as environment variables
- Use HTTPS in production (Render provides this automatically)
- Set `DEBUG = False` in production
- Configure `ALLOWED_HOSTS` for production domain
- Regularly update dependencies
- Use PostgreSQL instead of SQLite in production
- Enable secure headers

## Performance Optimization

- Use PostgreSQL for production database
- Configure static files serving with Whitenoise
- Enable caching in production
- Use CDN for static assets
- Optimize database queries

## Monitoring and Maintenance

- Monitor Render logs for errors
- Regularly update dependencies
- Backup database regularly
- Monitor OAuth token usage
- Check for security updates

This complete authentication system provides both traditional and social login options with a clean, user-friendly interface, fully configured for production deployment on Render.
