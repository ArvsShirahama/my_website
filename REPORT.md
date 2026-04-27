# Django Chat App — Complete Setup & Render Deployment Guide

> **Project**: Django Chat with Google OAuth, Themes, View-Once Media, PhotoSwap  
> **Stack**: Django 6 + Vanilla JS + SQLite (local) / PostgreSQL (Render) + Whitenoise  
> **Deployment**: Render (Free Tier)

---

## 1. Local Project Setup (From Scratch)

### 1.1 Create Virtual Environment

```bash
python -m venv venv

# Windows
venv\Scripts\activate

# macOS/Linux
source venv/bin/activate
```

### 1.2 Install Dependencies

```bash
pip install -r requirements.txt
```

**Key packages in `requirements.txt`:**
- `Django==6.0.*`
- `dj-database-url` — database URL parsing
- `psycopg2-binary` — PostgreSQL adapter (needed for Render)
- `whitenoise` — static file serving in production
- `django-allauth` — Google OAuth
- `gunicorn` — WSGI server for Render
- `Pillow` — image handling

### 1.3 Initial Django Setup

```bash
django-admin startproject myproject .
python manage.py startapp chat
python manage.py startapp accounts
```

Register apps in `myproject/settings.py`:

```python
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
    'chat',
]

SITE_ID = 1
```

### 1.4 Local Database (SQLite)

`myproject/settings.py` already uses `dj_database_url` with a SQLite fallback:

```python
import dj_database_url

DATABASES = {
    'default': dj_database_url.config(
        default='sqlite:///' + os.path.join(BASE_DIR, 'db.sqlite3')
    )
}
```

**Local env has no `DATABASE_URL`**, so it automatically falls back to SQLite.

### 1.5 Run Local Migrations

```bash
python manage.py makemigrations
python manage.py migrate
```

### 1.6 Create Local Superuser

```bash
python manage.py createsuperuser
```

### 1.7 Run Local Server

```bash
python manage.py runserver
```

Visit: `http://127.0.0.1:8000`

---

## 2. Project Structure Overview

```
myproject/
├── manage.py
├── db.sqlite3              ← Local dev DB (gitignored but check status!)
├── media/                  ← User uploads
├── requirements.txt
├── render.yaml             ← Render deployment config
│
├── myproject/              ← Django project config
│   ├── settings.py         ← Database, static, OAuth, session config
│   ├── urls.py
│   ├── wsgi.py
│   └── asgi.py
│
├── accounts/               ← Basic user/auth app
│   ├── models.py
│   ├── views.py
│   └── urls.py
│
├── chat/                   ← Main application
│   ├── models.py           ← UserProfile, Conversation, Message,
│   │                         Attachment, ConversationTheme
│   ├── views_chat.py       ← Chat list, conversation, send/get messages,
│   │                         themes, view-once, PhotoSwap
│   ├── views_admin.py      ← Admin dashboard
│   ├── views_auth.py       ← Login/register
│   ├── urls.py             ← Route definitions
│   ├── templates/chat/
│   │   ├── base.html
│   │   ├── chat_list.html
│   │   ├── conversation.html   ← Main chat UI (~84KB, themes + PhotoSwap)
│   │   ├── profile.html
│   │   ├── login.html
│   │   ├── register.html
│   │   └── admin/
│   └── migrations/
│       ├── 0001_initial.py
│       ├── 0002_message_deleted_for.py
│       ├── 0003_userprofile_role.py
│       ├── 0004_message_is_view_once.py
│       ├── 0005_conversationtheme.py
│       └── 0006_message_is_photo_swap.py
│
└── templates/
    └── socialaccount/
        └── login.html      ← allauth override
```

---

## 3. Key Features Implemented

### 3.1 Google OAuth (allauth)

**Settings** (`myproject/settings.py`):

```python
AUTHENTICATION_BACKENDS = (
    'django.contrib.auth.backends.ModelBackend',
    'allauth.account.auth_backends.AuthenticationBackend',
)

SOCIALACCOUNT_PROVIDERS = {
    'google': {
        'SCOPE': ['profile', 'email'],
        'AUTH_PARAMS': {'access_type': 'online'},
    }
}

# Optional: inline OAuth credentials (avoids DB SocialApp rows on Render)
GOOGLE_OAUTH_CLIENT_ID = os.environ.get('GOOGLE_OAUTH_CLIENT_ID', '').strip()
GOOGLE_OAUTH_CLIENT_SECRET = os.environ.get('GOOGLE_OAUTH_CLIENT_SECRET', '').strip()
if GOOGLE_OAUTH_CLIENT_ID and GOOGLE_OAUTH_CLIENT_SECRET:
    SOCIALACCOUNT_PROVIDERS['google']['APP'] = {
        'client_id': GOOGLE_OAUTH_CLIENT_ID,
        'secret': GOOGLE_OAUTH_CLIENT_SECRET,
        'key': '',
    }
```

**Required env vars:**
- `GOOGLE_OAUTH_CLIENT_ID`
- `GOOGLE_OAUTH_CLIENT_SECRET`

### 3.2 Chat & Conversations

- **Conversation list** — all conversations for the logged-in user
- **Real-time messaging** — polling-based message fetching
- **Message delete** — soft delete per user (`deleted_for`)
- **Attachments** — images/videos with `Attachment` model

### 3.3 View-Once Media

- `Message.is_view_once` flag
- `Message.view_once_consumed_by` ManyToMany tracking
- **Sender cannot consume their own view-once media**
- **Admins/superusers can bypass** and re-open
- Both sender and recipient see a "tap to view" card

### 3.4 PhotoSwap (Mutual Unlock)

- `Message.is_photo_swap` flag
- **Locked** for recipient until they send matching media type (image-for-image, video-for-video) **after** the message was created
- **Sender always sees their own media unlocked**
- Unlock happens in real-time when the matching media is sent
- JS renders locked cards with unlock animation on state change

### 3.5 Conversation Themes

- `ConversationTheme` model (preset, custom colors, background image)
- Per-conversation theme customization
- Live preview in modal
- CSS variables + scoped theme overrides

---

## 4. Database Configuration (Local vs Render)

### 4.1 The Switching Logic

`myproject/settings.py`:

```python
import os
IS_RENDER = os.environ.get('RENDER', '').lower() == 'true'

import dj_database_url
DATABASES = {
    'default': dj_database_url.config(
        default='sqlite:///' + os.path.join(BASE_DIR, 'db.sqlite3')
    )
}
```

| Environment | `DATABASE_URL` present? | Result DB |
|-------------|------------------------|-----------|
| Local dev   | No                     | SQLite    |
| Render      | Yes (you set it)       | PostgreSQL|

### 4.2 Session Engine

Render free tier has no shell access. To avoid hard failures when DB session tables are temporarily missing:

```python
SESSION_ENGINE = os.environ.get(
    'SESSION_ENGINE',
    'django.contrib.sessions.backends.signed_cookies' if IS_RENDER else 'django.contrib.sessions.backends.db',
)
```

On Render: defaults to **signed cookies** (no DB table needed).  
On local: uses **database-backed sessions**.

---

## 5. Preparing for Render Deployment

### 5.1 Static Files

Whitenoise is already configured:

```python
MIDDLEWARE = [
    'django.middleware.security.SecurityMiddleware',
    'whitenoise.middleware.WhiteNoiseMiddleware',
    # ...
]

STATIC_URL = '/static/'
STATIC_ROOT = BASE_DIR / 'staticfiles'
STATICFILES_STORAGE = 'whitenoise.storage.CompressedManifestStaticFilesStorage'
```

### 5.2 Render Configuration File (`render.yaml`)

```yaml
services:
  - type: web
    name: django-google-oauth
    env: python
    plan: free
    buildCommand: "pip install -r requirements.txt && python manage.py collectstatic --noinput"
    startCommand: "python manage.py migrate --noinput && (python manage.py createsuperuser --noinput || true) && gunicorn myproject.wsgi:application"
    envVars:
      - key: DEBUG
        value: false
      - key: SECRET_KEY
        generateValue: true
      - key: GOOGLE_OAUTH_CLIENT_ID
        sync: false
      - key: GOOGLE_OAUTH_CLIENT_SECRET
        sync: false
      - key: DJANGO_SUPERUSER_USERNAME
        sync: false
      - key: DJANGO_SUPERUSER_EMAIL
        sync: false
      - key: DJANGO_SUPERUSER_PASSWORD
        sync: false
      - key: ALLOWED_HOSTS
        value: my-website-4jgk.onrender.com
```

**Notes:**
- `sync: false` means the value is set manually in the dashboard and won't be overwritten
- `migrate` runs on every restart (needed because free tier has no shell)
- `createsuperuser` runs with `|| true` so it doesn't crash if the user already exists

### 5.3 Git Hygiene — IMPORTANT

Your `db.sqlite3` must **NOT** be committed to git. If it is, Render will copy it on deploy, and your data will reset on every restart (ephemeral filesystem).

**Check if it's tracked:**

```bash
git ls-files | grep sqlite3
```

**If you see output, untrack it:**

```bash
git rm --cached db.sqlite3
git commit -m "Stop tracking db.sqlite3"
```

**Verify `.gitignore` contains:**

```
*.sqlite3
db.sqlite3
```

---

## 6. Creating the Render PostgreSQL Database

### 6.1 In the Render Dashboard

1. Go to **Dashboard** → **New** → **PostgreSQL**
2. Choose **Free** plan
3. Give it a name (e.g., `myproject-db`)
4. Wait for it to provision (status = "Available")

### 6.2 Get the Internal Database URL

1. Click your PostgreSQL instance
2. Go to the **Connections** tab
3. Copy the **Internal Database URL** (NOT External)
   - Format: `postgres://username:password@dpg-xxx.internal:5432/dbname`

### 6.3 Add DATABASE_URL to Your Web Service

1. Go to your **Web Service** → **Environment** tab
2. Click **Add Environment Variable**
3. **Key**: `DATABASE_URL`
4. **Value**: Paste the Internal Database URL from step 6.2
5. Click **Save Changes**

**Do NOT hardcode DATABASE_URL in `render.yaml`.** The comment in the file is only a reminder.

---

## 7. First Deploy to Render

### 7.1 Push to GitHub

```bash
git add .
git commit -m "Ready for Render deploy"
git push origin main
```

### 7.2 Connect Render to GitHub

1. Render Dashboard → **New** → **Web Service**
2. Connect your GitHub repository
3. Render will auto-detect `render.yaml`
4. Click **Create Web Service**

### 7.3 Watch the Build & Start Logs

You should see:

```
==> Running build command...
pip install -r requirements.txt
python manage.py collectstatic --noinput

==> Running start command...
python manage.py migrate --noinput
Operations to perform:
  Apply all migrations: admin, auth, chat, contenttypes, sessions, sites, socialaccount
  Running migrations: ... OK
python manage.py createsuperuser --noinput
Superuser creation skipped: username already exists.   (or similar)
gunicorn myproject.wsgi:application
```

### 7.4 Verify Postgres is Connected

Visit your deployed site and try to:
1. Load the homepage
2. Register / log in
3. If no "relation django_session does not exist" error appears, Postgres is connected and migrated

---

## 8. Environment Variables Reference

| Variable | Required? | Where Set | Purpose |
|----------|-----------|-----------|---------|
| `DATABASE_URL` | **Yes (Render)** | Render Dashboard | PostgreSQL connection string |
| `SECRET_KEY` | Yes | `render.yaml` (auto-gen) | Django security |
| `DEBUG` | Yes | `render.yaml` | Set to `false` on Render |
| `ALLOWED_HOSTS` | Yes | `render.yaml` | Your Render domain |
| `RENDER` | Auto | Render (auto-set) | Detects Render environment |
| `GOOGLE_OAUTH_CLIENT_ID` | Optional | Render Dashboard | Google OAuth |
| `GOOGLE_OAUTH_CLIENT_SECRET` | Optional | Render Dashboard | Google OAuth |
| `DJANGO_SUPERUSER_USERNAME` | Optional | Render Dashboard | Auto-creates admin |
| `DJANGO_SUPERUSER_EMAIL` | Optional | Render Dashboard | Auto-creates admin |
| `DJANGO_SUPERUSER_PASSWORD` | Optional | Render Dashboard | Auto-creates admin |
| `SESSION_ENGINE` | Optional | Render Dashboard | Override session backend |

---

## 9. Troubleshooting Common Issues

### 9.1 "relation django_session does not exist"

**Cause**: Postgres is connected but migrations haven't run.

**Fix**: Migrations run in `startCommand`. If you still see this:
- Check deploy logs for migration errors
- Ensure `DATABASE_URL` is correct and pointing to the **internal** URL
- Temporarily set `SESSION_ENGINE=django.contrib.sessions.backends.signed_cookies` to bypass

### 9.2 Deleted Users / Data Reappears

**Cause**: `db.sqlite3` was committed to git. Render copies it on deploy, overwriting Postgres data, or uses the file directly.

**Fix**:
```bash
git rm --cached db.sqlite3
git commit -m "Remove sqlite from tracking"
git push
```

### 9.3 Can't Create Superuser (No Shell Access)

Render free tier has no shell. Use the auto-create in `startCommand`:

Set these in Render Dashboard Environment:
- `DJANGO_SUPERUSER_USERNAME=admin`
- `DJANGO_SUPERUSER_EMAIL=admin@example.com`
- `DJANGO_SUPERUSER_PASSWORD=yourpassword`

On next restart, the superuser will be created automatically.

### 9.4 Static Files Not Loading (404)

- Ensure `whitenoise` is in `requirements.txt`
- Ensure `WhiteNoiseMiddleware` is in `MIDDLEWARE`
- Ensure `STATIC_ROOT` and `STATICFILES_STORAGE` are set
- Check build logs for `collectstatic` output

### 9.5 Media Uploads Disappear on Restart

Render free tier has an ephemeral filesystem. Uploaded files in `media/` will be lost on every restart.

**Solutions:**
- Use an external storage service (AWS S3, Cloudinary)
- Upgrade to Render paid tier with persistent disk
- Accept the limitation for a free demo project

---

## 10. Development Workflow Summary

| Task | Local Command | Render |
|------|--------------|--------|
| Install deps | `pip install -r requirements.txt` | Auto (buildCommand) |
| Run migrations | `python manage.py migrate` | Auto (startCommand) |
| Create superuser | `python manage.py createsuperuser` | Auto via env vars |
| Collect static | `python manage.py collectstatic` | Auto (buildCommand) |
| Run server | `python manage.py runserver` | gunicorn (startCommand) |
| Database | SQLite (fallback) | PostgreSQL via `DATABASE_URL` |

---

## 11. Quick Checklist Before Every Deploy

- [ ] `db.sqlite3` is NOT committed to git
- [ ] All migrations are committed (`git status` shows clean)
- [ ] `DATABASE_URL` is set in Render Dashboard
- [ ] `ALLOWED_HOSTS` in `render.yaml` matches your actual Render URL
- [ ] `DEBUG` is `false` in `render.yaml`
- [ ] `DJANGO_SUPERUSER_*` env vars are set (if you need an admin)
- [ ] `GOOGLE_OAUTH_CLIENT_ID` and `SECRET` are set (if using OAuth)
- [ ] Build logs show `collectstatic` success
- [ ] Start logs show `migrate` success

---

## 12. Security Hardening (Applied)

### 12.1 Protected Media URLs (P0)

**Problem**: Attachment files were served via direct `/media/attachments/...` URLs, bypassing all authentication. Anyone with the link could access view-once and PhotoSwap content forever.

**Fix**: Added `serve_attachment` view at `/chat/api/attachment/<uuid>/` that:
- Requires login
- Verifies the requesting user is a participant in the conversation containing the attachment
- Returns `FileResponse` with the correct `Content-Type` header
- Returns 403 if unauthorized or file missing

**Files changed**:
- `chat/views_chat.py` — new `serve_attachment` view + `_attachment_url()` helper
- `chat/urls.py` — new route `api/attachment/<uuid:attachment_id>/`
- `chat/views_chat.py` — `send_message`, `get_messages`, `chat_conversation` now return protected URLs instead of direct media URLs
- `chat/templates/chat/conversation.html` — template uses `msg.attachment_url` instead of `msg.attachment.file.url`

### 12.2 Login Rate Limiting (P1)

**Problem**: `/login/` had no rate limiting, making brute-force password attacks trivial.

**Fix**: Applied `django-ratelimit` `@ratelimit(key='ip', rate='5/m', method='POST', block=True)` to `login_view`.

**Files changed**:
- `chat/views_auth.py` — added import and decorator

### 12.3 HTTPS Cookie Security (P2)

**Problem**: Cookies and sessions were not forced over HTTPS, allowing session hijacking on public networks.

**Fix**: Added security settings to `settings.py`:

```python
SECURE_SSL_REDIRECT = not DEBUG
SESSION_COOKIE_SECURE = not DEBUG
CSRF_COOKIE_SECURE = not DEBUG
SECURE_BROWSER_XSS_FILTER = True
SECURE_CONTENT_TYPE_NOSNIFF = True
```

**Files changed**:
- `myproject/settings.py`

### 12.4 Stronger Passwords (P3)

**Problem**: Minimum password length was 6 characters.

**Fix**: Raised minimum to 8 characters in registration validation.

**Files changed**:
- `chat/views_auth.py`

### 12.5 MIME Spoofing Protection (P4)

**Problem**: File upload type was determined by the browser's `content_type` header, allowing attackers to upload malicious files disguised as images/videos.

**Fix**: Added `python-magic` (libmagic binding) to verify actual file content:
- Reads first 4KB of uploaded file
- Validates against whitelist: `image/jpeg`, `image/png`, `image/gif`, `image/webp`, `image/bmp`, `video/mp4`, `video/webm`, `video/ogg`, `video/quicktime`
- Rejects upload with 400 error if actual type doesn't match whitelist
- Stores verified MIME type in `Attachment.mime_type` instead of client-reported value

**Files changed**:
- `requirements.txt` — added `python-magic==0.4.27`
- `chat/views_chat.py` — added validation logic in `send_message`

---

## 13. Admin Dashboard Enhancements

### 13.1 Bulk Message Delete

**Problem**: Admin had to delete messages one by one in the message history.

**Fix**: Added bulk delete functionality with checkboxes, "Select All", and "Delete Selected" button.

**Files changed**:
- `chat/views_admin.py` — added `admin_bulk_delete_messages` view with soft delete (`is_deleted=True`)
- `chat/urls.py` — added route `admin/api/bulk-delete-messages/`
- `chat/templates/chat/admin/messages.html` — added checkboxes per message, select-all checkbox, delete button, and JavaScript AJAX handler with CSRF protection

### 13.2 PhotoSwap Queue Button Fix

**Problem**: Clicking Approve/Reject buttons in admin PhotoSwap queue displayed raw JSON output instead of processing the action.

**Fix**: Intercepted form submissions with JavaScript AJAX, then reload the page on success.

**Files changed**:
- `chat/templates/chat/admin/photo_swap_queue.html` — added AJAX form interception for `.ps-approve-form` and `.ps-reject-form`

---

## 14. PhotoSwap System Improvements

### 14.1 Pending State UI

**Problem**: After sending a PhotoSwap, the sender saw a confusing "Verifying media..." message with no visual feedback.

**Fix**: Added a CSS spinner animation and clearer text: "System review, please wait" / "Loading".

**Files changed**:
- `chat/templates/chat/conversation.html` — added `.swap-loader` CSS spinner, updated template and `renderPhotoSwapLockedHtml()` for `pending` status

### 14.2 Rejected State UI

**Problem**: Rejected PhotoSwap showed unclear or poorly worded status text.

**Fix**: Updated text to "Does not meet requirements" / "System review: media does not meet requirements".

**Files changed**:
- `chat/templates/chat/conversation.html` — updated template and `renderPhotoSwapLockedHtml()` for `rejected` status

### 14.3 Sender's Own PhotoSwap Blurring

**Problem**: The sender could see their own PhotoSwap media immediately after sending, defeating the mutual unlock concept.

**Fix**: Modified locking logic so everyone (sender and receiver) sees a locked/blurred card until admin approval.

- `pending` → locked with "System review, please wait"
- `rejected` → locked with "Does not meet requirements"
- `active` → locked for sender ("PhotoSwap sent / Waiting for response"), clickable for receiver ("PhotoSwap Active / Tap to respond")
- `approved` → unlocked for everyone

**Files changed**:
- `chat/views_chat.py` — `is_photo_swap_locked_for()` now returns `True` for sender too until `approved`
- `chat/templates/chat/conversation.html` — added `data-is-sender` attribute, differentiated text for sender vs receiver, restricted cursor/hover to receiver's active cards, prevented sender from clicking their own active card

---

## 15. View-Once Fix for Sender

**Problem**: The sender could still see their own view-once media after sending it, even though the receiver could only view it once. This leaked the media URL in page source and defeated the one-time access promise.

**Fix**: Enforced strict one-time access for **both** sender and receiver.

**Backend changes**:
- `chat/views_chat.py` — `chat_conversation` now sets `attachment_url = None` for unconsumed view-once messages
- `chat/views_chat.py` — `get_messages` API withholds attachment URL until consumed
- `chat/views_chat.py` — `consume_view_once_media` removed the sender exception; sender must now consume like anyone else. Returns the protected URL on success. Returns 403 if already consumed.

**Frontend changes**:
- `chat/templates/chat/conversation.html` — `renderViewOnceCardHtml()` no longer leaks the URL in `data-media-url`
- `chat/templates/chat/conversation.html` — click handler now calls consume API first, receives the URL, then opens the viewer. If already viewed, shows an error.
- `chat/templates/chat/conversation.html` — removed old consume-on-close behavior from media viewer

**Result**: Neither sender nor receiver can inspect the page source to find the media URL. Both get exactly one view. Admins/superusers can still bypass.

---

*Generated for project at `c:\Users\Arvin\Desktop\myproject`*
