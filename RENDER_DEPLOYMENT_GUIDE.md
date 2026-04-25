# Render Deployment Guide - Django Google OAuth Project

This guide covers deploying your Django Google OAuth authentication system to Render.com.

## Prerequisites

- GitHub account with your project uploaded
- Render.com account (free tier available)
- Google Cloud Console access (for OAuth configuration)
- Basic understanding of environment variables

## Step 1: Prepare Your Project for Production

### 1.1 Update Settings for Production

**myproject/settings.py:**
```python
import os
from pathlib import Path
import dj_database_url

# Build paths inside the project like this: BASE_DIR / 'subdir'.
BASE_DIR = Path(__file__).resolve().parent.parent

# SECURITY WARNING: keep the secret key used in production secret!
SECRET_KEY = os.environ.get('SECRET_KEY', 'django-insecure-default-key-for-dev')

# SECURITY WARNING: don't run with debug turned on in production!
DEBUG = os.environ.get('DEBUG', 'False') == 'True'

ALLOWED_HOSTS = ['*']  # In production, set specific domains

# Application definition
INSTALLED_APPS = [
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',
    'accounts',
    'django.contrib.sites',
    'allauth',
    'allauth.account',
    'allauth.socialaccount',
    'allauth.socialaccount.providers.google',
]

MIDDLEWARE = [
    'django.middleware.security.SecurityMiddleware',
    'whitenoise.middleware.WhiteNoiseMiddleware',  # Add for static files
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.middleware.common.CommonMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'allauth.account.middleware.AccountMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',
]

ROOT_URLCONF = 'myproject.urls'

TEMPLATES = [
    {
        'BACKEND': 'django.template.backends.django.DjangoTemplates',
        'DIRS': [],
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

WSGI_APPLICATION = 'myproject.wsgi.application'

# Database - Use PostgreSQL on Render
DATABASES = {
    'default': dj_database_url.parse(os.environ.get('DATABASE_URL'))
}

# Password validation
AUTH_PASSWORD_VALIDATORS = [
    {
        'NAME': 'django.contrib.auth.password_validation.UserAttributeSimilarityValidator',
    },
    {
        'NAME': 'django.contrib.auth.password_validation.MinimumLengthValidator',
    },
    {
        'NAME': 'django.contrib.auth.password_validation.CommonPasswordValidator',
    },
    {
        'NAME': 'django.contrib.auth.password_validation.NumericPasswordValidator',
    },
]

# Internationalization
LANGUAGE_CODE = 'en-us'
TIME_ZONE = 'UTC'
USE_I18N = True
USE_TZ = True

# Static files (CSS, JavaScript, Images)
STATIC_URL = '/static/'
STATIC_ROOT = BASE_DIR / 'staticfiles'

# Whitenoise configuration
STATICFILES_STORAGE = 'whitenoise.storage.CompressedManifestStaticFilesStorage'

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

# Security settings for production
SECURE_BROWSER_XSS_FILTER = True
SECURE_CONTENT_TYPE_NOSNIFF = True
X_FRAME_OPTIONS = 'DENY'
```

### 1.2 Update Requirements.txt

Add production dependencies:

```txt
Django==6.0.4
django-allauth==65.15.1
dj-database-url==3.1.2
whitenoise==6.8.2
gunicorn==23.0.0
psycopg2-binary==2.9.10
```

### 1.3 Create render.yaml

Create `render.yaml` in your project root:

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

  # PostgreSQL Database
  - type: pserv
    name: django-db
    plan: free
    env: docker
    databaseName: django_oauth_db
    user: django_user
```

### 1.4 Update .gitignore

```gitignore
__pycache__/
*.pyc
db.sqlite3
.env
venv/
.env.*
*.log
media/
.DS_Store
staticfiles/
```

## Step 2: Update Google OAuth Configuration

### 2.1 Update Google Cloud Console

1. Go to [Google Cloud Console](https://console.cloud.google.com/)
2. Select your project
3. Go to APIs & Services > Credentials
4. Find your OAuth 2.0 Client ID
5. Click "Edit"
6. Add your Render domain to Authorized redirect URIs:
   - `https://your-app-name.onrender.com/accounts/google/login/callback/`
7. Save changes

### 2.2 Note Your Credentials
Keep your Google OAuth Client ID and Secret handy for Render configuration.

## Step 3: Deploy to Render

### 3.1 Sign Up for Render

1. Go to [Render.com](https://render.com)
2. Sign up with GitHub (recommended)
3. Authorize Render to access your GitHub repositories

### 3.2 Create New Web Service

1. Click "New +" → "Web Service"
2. Select your GitHub repository
3. Configure the service:
   - **Name**: `django-google-oauth` (or your preferred name)
   - **Environment**: Python 3
   - **Branch**: main
   - **Build Command**: `pip install -r requirements.txt`
   - **Start Command**: `gunicorn myproject.wsgi:application`

### 3.3 Configure Environment Variables

Add these environment variables in Render dashboard:

1. **DEBUG**: `false`
2. **SECRET_KEY**: Generate a new secret key
3. **GOOGLE_OAUTH_CLIENT_ID**: Your Google OAuth Client ID
4. **GOOGLE_OAUTH_CLIENT_SECRET**: Your Google OAuth Client Secret

### 3.4 Add PostgreSQL Database

1. In your service dashboard, click "Database"
2. Click "Create New Database"
3. Select PostgreSQL
4. Choose Free plan
5. Give it a name (e.g., `django-db`)
6. Click "Create Database"

### 3.5 Run Migrations

After deployment, you'll need to run migrations:

1. Go to your service dashboard
2. Click "Shell" (or "Exec")
3. Run these commands:
```bash
python manage.py migrate
python manage.py createsuperuser
python manage.py collectstatic --noinput
```

## Step 4: Configure Django Admin

### 4.1 Access Admin Panel

1. Go to `https://your-app-name.onrender.com/admin/`
2. Login with your superuser credentials

### 4.2 Configure Google Social App

1. Go to "SOCIAL ACCOUNTS" > "Social applications"
2. Click "Add social application"
3. Fill in:
   - **Provider**: Google
   - **Name**: Google OAuth (Production)
   - **Client ID**: Your Google OAuth Client ID
   - **Secret key**: Your Google OAuth Client Secret
4. In "Sites" section, select your site
5. Click "Save"

## Step 5: Test Your Deployment

### 5.1 Verify URLs

- **Home**: `https://your-app-name.onrender.com/`
- **Login**: `https://your-app-name.onrender.com/accounts/login/`
- **Google Login**: `https://your-app-name.onrender.com/accounts/social/`
- **Admin**: `https://your-app-name.onrender.com/admin/`

### 5.2 Test Google OAuth

1. Click "Continue with Google"
2. You should be redirected to Google
3. Authenticate with your Google account
4. Redirect back to your Render app
5. You should be logged in

## Step 6: Monitor and Debug

### 6.1 View Logs

1. Go to your service dashboard on Render
2. Click "Logs" tab
3. Monitor for any errors

### 6.2 Common Issues and Solutions

**Issue: "502 Bad Gateway"**
- Check if the start command is correct
- Verify all dependencies are installed
- Check logs for specific error messages

**Issue: "Database connection error"**
- Verify DATABASE_URL environment variable
- Check if PostgreSQL database is running
- Run migrations manually via shell

**Issue: "Static files not loading"**
- Run `python manage.py collectstatic --noinput`
- Verify STATIC_URL and STATIC_ROOT settings
- Check if Whitenoise is properly configured

**Issue: "Google OAuth redirect error"**
- Verify redirect URI in Google Cloud Console
- Check if domain matches exactly
- Ensure HTTPS is used (Render provides HTTPS automatically)

## Step 7: Custom Domain (Optional)

### 7.1 Add Custom Domain

1. In Render dashboard, go to your service
2. Click "Custom Domains"
3. Add your domain (e.g., `yourapp.com`)
4. Update DNS records as instructed by Render

### 7.2 Update Google OAuth

1. Go back to Google Cloud Console
2. Add your custom domain to authorized redirect URIs:
   - `https://yourapp.com/accounts/google/login/callback/`

## Step 8: Backup and Maintenance

### 8.1 Database Backups

Render automatically creates daily backups for PostgreSQL databases. You can:

1. Go to your database dashboard
2. Click "Backups" tab
3. Download or restore backups as needed

### 8.2 Regular Maintenance

- Monitor logs regularly
- Update dependencies when needed
- Keep Google OAuth credentials secure
- Monitor usage on Render free tier

## Production Best Practices

### Security
- ✅ Use HTTPS (automatic on Render)
- ✅ Set DEBUG=False
- ✅ Use environment variables for secrets
- ✅ Keep dependencies updated
- ✅ Monitor security advisories

### Performance
- ✅ Use PostgreSQL instead of SQLite
- ✅ Configure static files properly
- ✅ Use Whitenoise for static file serving
- ✅ Monitor resource usage

### Reliability
- ✅ Set up proper error logging
- ✅ Monitor application health
- ✅ Have a backup strategy
- ✅ Test deployment process

## Cost Considerations

### Render Free Tier Limits
- **Web Service**: 750 hours/month
- **Database**: 256MB RAM, 10GB storage
- **Bandwidth**: 100GB/month

### When to Upgrade
- High traffic applications
- Need for more database storage
- Background workers required
- Custom domains on free tier

## Troubleshooting Checklist

Before contacting support, check:

- [ ] Environment variables are set correctly
- [ ] Database is accessible and migrations run
- [ ] Static files are collected
- [ ] Google OAuth redirect URIs match
- [ ] Logs show specific error messages
- [ ] Dependencies are compatible

Your Django Google OAuth application is now deployed on Render and accessible to users worldwide!
