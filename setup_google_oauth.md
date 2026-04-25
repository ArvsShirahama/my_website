# Google OAuth Setup Instructions

## 1. Create Google Cloud Project
1. Go to [Google Cloud Console](https://console.cloud.google.com/)
2. Create a new project or select an existing one
3. Enable the **Google+ API** (or **People API** for newer versions)

## 2. Create OAuth 2.0 Credentials
1. In the Google Cloud Console, go to **APIs & Services** > **Credentials**
2. Click **Create Credentials** > **OAuth 2.0 Client ID**
3. Select **Web application** as the application type
4. Add authorized redirect URI: `http://127.0.0.1:8000/accounts/google/login/callback/`
5. Click **Create**
6. Copy the **Client ID** and **Client Secret**

## 3. Configure in Django Admin
1. Run the Django development server: `python manage.py runserver`
2. Go to admin panel: http://127.0.0.1:8000/admin/
3. Login with your superuser credentials
4. Go to **SOCIAL ACCOUNTS** > **Social applications**
5. Click **Add social application**
6. Fill in the details:
   - **Provider**: Google
   - **Name**: Google OAuth (or any name you prefer)
   - **Client ID**: Your Google OAuth Client ID
   - **Secret Key**: Your Google OAuth Client Secret
7. In **Sites** section, select your site (should be example.com or localhost)
8. Click **Save**

## 4. Test Google Login
1. Go to http://127.0.0.1:8000/accounts/social/
2. Click "Continue with Google"
3. You should be redirected to Google for authentication
4. After successful authentication, you'll be redirected back to your site logged in

## Notes
- Make sure your Google Cloud project has the Google+ API enabled
- The redirect URI must exactly match what's configured in Google Cloud Console
- For production, use HTTPS and update the redirect URI accordingly
