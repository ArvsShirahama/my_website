# Django Google OAuth Authentication System

A Django web application with Google OAuth authentication using django-allauth.

## Features

- Traditional username/password authentication
- Google OAuth social login
- Admin panel access
- One-to-one chat with real-time messaging
- Media sharing (images and videos) with lightbox viewer
- Message deletion (delete for me / delete for everyone)
- Production-ready for Render deployment

## Project Structure

```
myproject/
├── accounts/              # Custom accounts app
│   ├── migrations/        # Database migrations
│   ├── templates/         # Account templates
│   │   └── accounts/      # Home, login, social login
│   ├── admin.py           # Admin configuration
│   ├── apps.py            # App configuration
│   ├── models.py          # Database models
│   ├── urls.py            # URL patterns
│   ├── views.py           # View functions
│   └── tests.py           # Unit tests
├── myproject/             # Main Django project
│   ├── settings.py        # Django settings
│   ├── urls.py            # Root URL configuration
│   ├── wsgi.py            # WSGI application
│   └── asgi.py            # ASGI application
├── templates/             # Global templates (empty - for future use)
├── manage.py              # Django management script
├── requirements.txt       # Python dependencies
├── render.yaml            # Render deployment config
└── .gitignore             # Git ignore rules
```

## Quick Start

1. Install dependencies: `pip install -r requirements.txt`
2. Run migrations: `python manage.py migrate`
3. Create superuser: `python manage.py createsuperuser`
4. Start server: `python manage.py runserver`

## Deployment

See `BUILD_GUIDE_UPDATED.md` for complete deployment instructions.

## Documentation

- `BUILD_GUIDE_UPDATED.md` - Complete build and deployment guide
- `GITHUB_UPLOAD_GUIDE.md` - GitHub repository setup
- `RENDER_DEPLOYMENT_GUIDE.md` - Render deployment steps