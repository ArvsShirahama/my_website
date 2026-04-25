# GitHub Upload Guide - Django Google OAuth Project

This guide covers uploading your Django Google OAuth authentication system to GitHub.

## Prerequisites

- Git installed on your system
- GitHub account
- Your Django project is ready for upload

## Step 1: Prepare Your Project

### 1.1 Check Your .gitignore File
Ensure your `.gitignore` file includes:

```
__pycache__/
*.pyc
db.sqlite3
.env
venv/
.env.*
*.log
media/
static/
.DS_Store
```

### 1.2 Remove Sensitive Data
Before uploading, ensure no sensitive information is in your code:

```python
# In settings.py, replace hardcoded values:
SECRET_KEY = 'django-insecure-j9s26*1b23!vg$ty$q#*s-gh!6-3*uxevg06et16rq1d@xitn2'
# Should be:
SECRET_KEY = os.environ.get('SECRET_KEY', 'your-default-key')

# Google OAuth credentials should be in environment variables
# Not hardcoded in the code
```

### 1.3 Create Environment Variables Template
Create `.env.example`:

```
SECRET_KEY=your-secret-key-here
GOOGLE_OAUTH_CLIENT_ID=your-google-client-id
GOOGLE_OAUTH_CLIENT_SECRET=your-google-client-secret
DEBUG=True
```

## Step 2: Initialize Git Repository

```bash
# Navigate to your project directory
cd c:\Users\Arvin\Desktop\myproject

# Initialize Git repository
git init

# Add all files
git add .

# Make initial commit
git commit -m "Initial commit: Django Google OAuth authentication system"
```

## Step 3: Create GitHub Repository

### 3.1 Using GitHub Website
1. Go to [GitHub](https://github.com)
2. Click "+" → "New repository"
3. Repository name: `django-google-oauth-auth`
4. Description: `Django authentication system with Google OAuth integration`
5. Choose Public or Private
6. Don't initialize with README (you already have one)
7. Click "Create repository"

### 3.2 Using GitHub CLI (Alternative)
```bash
# If you have GitHub CLI installed
gh repo create django-google-oauth-auth --public --description "Django authentication system with Google OAuth integration"
```

## Step 4: Connect Local Repository to GitHub

### 4.1 Using HTTPS (Recommended for beginners)
```bash
# Copy the HTTPS URL from your GitHub repository
# Example: https://github.com/username/django-google-oauth-auth.git

git remote add origin https://github.com/YOUR_USERNAME/django-google-oauth-auth.git
git branch -M main
git push -u origin main
```

### 4.2 Using SSH (If you have SSH keys set up)
```bash
# Copy the SSH URL from your GitHub repository
# Example: git@github.com:username/django-google-oauth-auth.git

git remote add origin git@github.com:YOUR_USERNAME/django-google-oauth-auth.git
git branch -M main
git push -u origin main
```

## Step 5: Verify Upload

1. Go to your GitHub repository page
2. Check that all files are uploaded
3. Verify the code looks correct
4. Check that sensitive files are excluded (should be in .gitignore)

## Step 6: Create README.md

Update your README.md with project information:

```markdown
# Django Google OAuth Authentication

A Django web application with traditional and Google OAuth authentication.

## Features

- Traditional username/password authentication
- Google OAuth authentication
- User registration and login
- Admin panel access
- Responsive design

## Quick Start

### Prerequisites

- Python 3.14+
- Django 6.0.4
- Google Cloud Account

### Installation

1. Clone the repository:
```bash
git clone https://github.com/YOUR_USERNAME/django-google-oauth-auth.git
cd django-google-oauth-auth
```

2. Create virtual environment:
```bash
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
```

3. Install dependencies:
```bash
pip install -r requirements.txt
```

4. Set up environment variables:
```bash
cp .env.example .env
# Edit .env with your configuration
```

5. Run migrations:
```bash
python manage.py migrate
```

6. Create superuser:
```bash
python manage.py createsuperuser
```

7. Start development server:
```bash
python manage.py runserver
```

### Google OAuth Setup

See [BUILD_GUIDE.md](BUILD_GUIDE.md) for detailed Google OAuth setup instructions.

## Project Structure

```
django-google-oauth-auth/
├── manage.py
├── requirements.txt
├── .gitignore
├── .env.example
├── README.md
├── BUILD_GUIDE.md
├── GITHUB_UPLOAD_GUIDE.md
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

## Usage

- Home page: http://127.0.0.1:8000/
- Login: http://127.0.0.1:8000/accounts/login/
- Google Login: http://127.0.0.1:8000/accounts/social/
- Admin: http://127.0.0.1:8000/admin/

## Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Commit your changes
5. Push to the branch
6. Create a Pull Request

## License

This project is open source and available under the [MIT License](LICENSE).
```

## Step 7: Add and Push README

```bash
git add README.md
git commit -m "Add comprehensive README documentation"
git push origin main
```

## Step 8: Optional - Add License

### 8.1 Create LICENSE file
```bash
# Create MIT License
echo "MIT License

Copyright (c) 2026 [Your Name]

Permission is hereby granted, free of charge, to any person obtaining a copy
of this software and associated documentation files (the "Software"), to deal
in the Software without restriction, including without limitation the rights
to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
copies of the Software, and to permit persons to whom the Software is
furnished to do so, subject to the following conditions:

The above copyright notice and this permission notice shall be included in all
copies or substantial portions of the Software.

THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
SOFTWARE." > LICENSE
```

### 8.2 Add license to repository
```bash
git add LICENSE
git commit -m "Add MIT License"
git push origin main
```

## Step 9: Final Repository Check

Your GitHub repository should now contain:
- ✅ Source code files
- ✅ Requirements.txt
- ✅ .gitignore
- ✅ README.md
- ✅ BUILD_GUIDE.md
- ✅ GITHUB_UPLOAD_GUIDE.md
- ✅ LICENSE (optional)
- ❌ No sensitive data
- ❌ No database files
- ❌ No cache files

## Common Issues and Solutions

### Issue: "Permission denied (publickey)"
**Solution**: Use HTTPS instead of SSH, or set up SSH keys properly.

### Issue: "Remote origin already exists"
**Solution**: 
```bash
git remote remove origin
git remote add origin https://github.com/YOUR_USERNAME/django-google-oauth-auth.git
```

### Issue: Large files not uploading
**Solution**: Check if large files are in .gitignore or use Git LFS for large files.

### Issue: Sensitive data uploaded
**Solution**: 
```bash
# Remove sensitive file from history
git filter-branch --force --index-filter 'git rm --cached --ignore-unmatch filename.py' --prune-empty --tag-name-filter cat -- --all
git push origin main --force
```

## Next Steps After Upload

1. **Share your repository**: Send the GitHub URL to collaborators
2. **Set up GitHub Pages** (optional): For project documentation
3. **Enable Issues**: For bug tracking and feature requests
4. **Add collaborators**: If working with a team
5. **Set up CI/CD**: For automated testing and deployment

## Security Best Practices

- ✅ Never commit secrets or API keys
- ✅ Use environment variables for sensitive data
- ✅ Keep your repository private if it contains sensitive business logic
- ✅ Regularly update dependencies
- ✅ Use branch protection for main branch
- ✅ Enable security alerts in GitHub

Your Django Google OAuth authentication system is now successfully uploaded to GitHub!
