from django.shortcuts import redirect


def home(request):
    """Redirect old home page to chat app"""
    return redirect('/chat/' if request.user.is_authenticated else '/chat/login/')


def login_view(request):
    """Redirect old login page to new chat login"""
    return redirect('/chat/login/')


def social_login(request):
    """Redirect old social login page to new chat login"""
    return redirect('/chat/login/')
