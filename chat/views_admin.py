from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required, user_passes_test
from django.contrib.auth.models import User
from django.http import JsonResponse
from django.utils import timezone
from django.db.models import Count
from datetime import timedelta

from .models import UserProfile, Conversation, Message, AdminLog


def is_admin(user):
    return user.is_superuser or user.is_staff


@login_required
@user_passes_test(is_admin, login_url='chat_list')
def admin_dashboard(request):
    """Custom admin dashboard"""
    stats = {
        'total_users': User.objects.count(),
        'total_messages': Message.objects.filter(is_deleted=False).count(),
        'total_conversations': Conversation.objects.count(),
        'online_users': UserProfile.objects.filter(is_online=True).count(),
    }
    
    last_7 = timezone.now() - timedelta(days=7)
    stats['messages_last_7'] = Message.objects.filter(created_at__gte=last_7, is_deleted=False).count()
    stats['new_users_7'] = User.objects.filter(date_joined__gte=last_7).count()
    
    recent_users = User.objects.order_by('-date_joined')[:10]
    recent_messages = Message.objects.filter(is_deleted=False).order_by('-created_at')[:20]
    recent_logs = AdminLog.objects.order_by('-created_at')[:10]
    
    return render(request, 'chat/admin/dashboard.html', {
        'stats': stats,
        'recent_users': recent_users,
        'recent_messages': recent_messages,
        'recent_logs': recent_logs,
    })


@login_required
@user_passes_test(is_admin, login_url='chat_list')
def admin_users(request):
    """Admin users management"""
    users = User.objects.select_related('profile').annotate(
        message_count=Count('sent_messages')
    ).order_by('-date_joined')
    return render(request, 'chat/admin/users.html', {'users': users})


@login_required
@user_passes_test(is_admin, login_url='chat_list')
def admin_delete_user(request, user_id):
    """Delete user action"""
    if request.method != 'POST':
        return JsonResponse({'error': 'Method not allowed'}, status=405)
    
    target = get_object_or_404(User, id=user_id)
    if target == request.user:
        return JsonResponse({'error': 'Cannot delete yourself'}, status=400)
    
    AdminLog.objects.create(
        admin_user=request.user, action_type='delete_user', target_user=target,
        details=f"Deleted user {target.username}"
    )
    target.delete()
    return JsonResponse({'success': True, 'message': 'User deleted'})


@login_required
@user_passes_test(is_admin, login_url='chat_list')
def admin_messages(request):
    """Admin messages monitoring"""
    messages = Message.objects.filter(is_deleted=False).select_related(
        'sender', 'conversation'
    ).order_by('-created_at')[:100]
    return render(request, 'chat/admin/messages.html', {'messages': messages})


@login_required
@user_passes_test(is_admin, login_url='chat_list')
def admin_delete_message(request, message_id):
    """Delete message action"""
    if request.method != 'POST':
        return JsonResponse({'error': 'Method not allowed'}, status=405)
    
    message = get_object_or_404(Message, id=message_id)
    AdminLog.objects.create(
        admin_user=request.user, action_type='delete_message', target_user=message.sender,
        details=f"Deleted message from {message.sender.username}"
    )
    message.is_deleted = True
    message.save()
    return JsonResponse({'success': True, 'message': 'Message deleted'})


@login_required
@user_passes_test(is_admin, login_url='chat_list')
def admin_conversations(request):
    """Admin conversations monitoring"""
    conversations = Conversation.objects.select_related(
        'participant1', 'participant2'
    ).annotate(message_count=Count('messages')).order_by('-updated_at')
    return render(request, 'chat/admin/conversations.html', {'conversations': conversations})


@login_required
@user_passes_test(is_admin, login_url='chat_list')
def admin_logs(request):
    """Admin action logs"""
    logs = AdminLog.objects.select_related('admin_user', 'target_user').order_by('-created_at')[:100]
    return render(request, 'chat/admin/logs.html', {'logs': logs})
