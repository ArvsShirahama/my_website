from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required, user_passes_test
from django.contrib.auth.models import User
from django.http import JsonResponse
from django.utils import timezone
from django.db.models import Count, Q
from datetime import timedelta
from django.core.paginator import Paginator
import json
from django.urls import reverse

from .models import UserProfile, Conversation, Message, AdminLog


# ========== RBAC Helpers ==========

def is_staff_or_admin(user):
    """Allow staff and full admins into the dashboard."""
    if user.is_superuser:
        return True
    profile = getattr(user, 'profile', None)
    if profile and profile.role in ('staff', 'admin'):
        return True
    return user.is_staff


def is_admin_only(user):
    """Allow only full admins."""
    if user.is_superuser:
        return True
    profile = getattr(user, 'profile', None)
    if profile and profile.role == 'admin':
        return True
    return False


# ========== Dashboard ==========

@login_required
@user_passes_test(is_staff_or_admin, login_url='chat_list')
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
        'is_admin': is_admin_only(request.user),
    })


# ========== Users Management ==========

@login_required
@user_passes_test(is_admin_only, login_url='chat_list')
def admin_users(request):
    """Admin users management with role filter and search."""
    users_qs = User.objects.select_related('profile').annotate(
        message_count=Count('sent_messages')
    ).order_by('-date_joined')

    # Filter by role
    role_filter = request.GET.get('role', '')
    if role_filter in ('user', 'staff', 'admin'):
        users_qs = users_qs.filter(profile__role=role_filter)

    # Search by username or email
    search = request.GET.get('search', '').strip()
    if search:
        users_qs = users_qs.filter(
            Q(username__icontains=search) | Q(email__icontains=search)
        )

    paginator = Paginator(users_qs, 25)
    page_number = request.GET.get('page', 1)
    page_obj = paginator.get_page(page_number)

    return render(request, 'chat/admin/users.html', {
        'users': page_obj,
        'role_filter': role_filter,
        'search': search,
        'is_admin': is_admin_only(request.user),
    })


@login_required
@user_passes_test(is_admin_only, login_url='chat_list')
def admin_edit_user(request, user_id):
    """Edit user (username, password, role). Admin only."""
    target = get_object_or_404(User, id=user_id)
    if target == request.user:
        return JsonResponse({'error': 'Cannot edit yourself here. Use profile settings.'}, status=400)

    if request.method != 'POST':
        return JsonResponse({'error': 'Method not allowed'}, status=405)

    username = request.POST.get('username', '').strip()
    password = request.POST.get('password', '').strip()
    role = request.POST.get('role', '').strip()

    if username:
        if User.objects.filter(username=username).exclude(id=target.id).exists():
            return JsonResponse({'error': 'Username already taken'}, status=400)
        target.username = username

    if password:
        target.set_password(password)

    if role in ('user', 'staff', 'admin'):
        profile = getattr(target, 'profile', None)
        if not profile:
            profile = UserProfile.objects.create(user=target, role=role)
        else:
            profile.role = role
            profile.save()
        # Sync Django built-in flags
        target.is_staff = (role in ('staff', 'admin'))
        if role == 'admin':
            target.is_superuser = True
        else:
            target.is_superuser = False

    target.save()

    AdminLog.objects.create(
        admin_user=request.user, action_type='delete_user', target_user=target,
        details=f"Edited user {target.username} (role={role})"
    )
    return JsonResponse({'success': True, 'message': 'User updated'})


@login_required
@user_passes_test(is_admin_only, login_url='chat_list')
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


# ========== Messages Monitoring ==========

@login_required
@user_passes_test(is_staff_or_admin, login_url='chat_list')
def admin_messages(request):
    """Admin messages monitoring with filtering, search, pagination."""
    messages_qs = Message.objects.filter(is_deleted=False).select_related(
        'sender', 'conversation', 'attachment'
    ).order_by('-created_at')

    # Filter by user
    user_filter = request.GET.get('user', '')
    if user_filter:
        try:
            uid = int(user_filter)
            messages_qs = messages_qs.filter(
                Q(sender_id=uid) |
                Q(conversation__participant1_id=uid) |
                Q(conversation__participant2_id=uid)
            )
        except ValueError:
            pass

    # Filter by date range
    date_from = request.GET.get('date_from', '')
    date_to = request.GET.get('date_to', '')
    if date_from:
        messages_qs = messages_qs.filter(created_at__date__gte=date_from)
    if date_to:
        messages_qs = messages_qs.filter(created_at__date__lte=date_to)

    # Filter by message type
    msg_type = request.GET.get('type', '')
    if msg_type == 'text':
        messages_qs = messages_qs.filter(attachment__isnull=True)
    elif msg_type == 'image':
        messages_qs = messages_qs.filter(attachment__attachment_type='image')
    elif msg_type == 'video':
        messages_qs = messages_qs.filter(attachment__attachment_type='video')

    # Search keyword in text
    keyword = request.GET.get('keyword', '').strip()
    if keyword:
        messages_qs = messages_qs.filter(text__icontains=keyword)

    paginator = Paginator(messages_qs, 50)
    page_number = request.GET.get('page', 1)
    page_obj = paginator.get_page(page_number)

    users = User.objects.order_by('username')

    return render(request, 'chat/admin/messages.html', {
        'messages': page_obj,
        'users': users,
        'user_filter': user_filter,
        'date_from': date_from,
        'date_to': date_to,
        'msg_type': msg_type,
        'keyword': keyword,
        'is_admin': is_admin_only(request.user),
    })


@login_required
@user_passes_test(is_staff_or_admin, login_url='chat_list')
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
@user_passes_test(is_staff_or_admin, login_url='chat_list')
def admin_bulk_delete_messages(request):
    """Bulk delete messages (soft delete)."""
    if request.method != 'POST':
        return JsonResponse({'error': 'Method not allowed'}, status=405)
    if request.content_type == 'application/json':
        try:
            body = json.loads(request.body.decode('utf-8')) if request.body else {}
            ids = body.get('message_ids', [])
        except Exception:
            ids = []
    else:
        ids = request.POST.getlist('message_ids[]') or request.POST.getlist('message_ids')
    if not ids:
        return JsonResponse({'error': 'No messages selected'}, status=400)
    deleted = 0
    for msg_id in ids:
        try:
            msg = Message.objects.get(id=msg_id, is_deleted=False)
            msg.is_deleted = True
            msg.save()
            deleted += 1
            AdminLog.objects.create(
                admin_user=request.user, action_type='delete_message', target_user=msg.sender,
                details=f"Bulk deleted message from {msg.sender.username}"
            )
        except (Message.DoesNotExist, ValueError):
            continue
    return JsonResponse({'success': True, 'message': f'{deleted} message(s) deleted', 'deleted': deleted})


# ========== Conversations & Thread View ==========

@login_required
@user_passes_test(is_staff_or_admin, login_url='chat_list')
def admin_conversations(request):
    """Admin conversations monitoring with user filtering."""
    conv_qs = Conversation.objects.select_related(
        'participant1', 'participant2', 'last_message'
    ).annotate(message_count=Count('messages')).order_by('-updated_at')

    # Filter by participant user
    user_filter = request.GET.get('user', '')
    if user_filter:
        try:
            uid = int(user_filter)
            conv_qs = conv_qs.filter(
                Q(participant1_id=uid) | Q(participant2_id=uid)
            )
        except ValueError:
            pass

    # Search by username
    search = request.GET.get('search', '').strip()
    if search:
        conv_qs = conv_qs.filter(
            Q(participant1__username__icontains=search) |
            Q(participant2__username__icontains=search)
        )

    paginator = Paginator(conv_qs, 25)
    page_number = request.GET.get('page', 1)
    page_obj = paginator.get_page(page_number)

    users = User.objects.order_by('username')

    return render(request, 'chat/admin/conversations.html', {
        'conversations': page_obj,
        'users': users,
        'user_filter': user_filter,
        'search': search,
        'is_admin': is_admin_only(request.user),
    })


@login_required
@user_passes_test(is_staff_or_admin, login_url='chat_list')
def admin_conversation_detail(request, conversation_id):
    """View messages within a specific conversation (chat thread view)."""
    conversation = get_object_or_404(Conversation, id=conversation_id)

    messages_qs = conversation.messages.filter(is_deleted=False).select_related(
        'sender', 'attachment'
    ).order_by('created_at')

    # Filter by type
    msg_type = request.GET.get('type', '')
    if msg_type == 'text':
        messages_qs = messages_qs.filter(attachment__isnull=True)
    elif msg_type == 'image':
        messages_qs = messages_qs.filter(attachment__attachment_type='image')
    elif msg_type == 'video':
        messages_qs = messages_qs.filter(attachment__attachment_type='video')

    # Date range
    date_from = request.GET.get('date_from', '')
    date_to = request.GET.get('date_to', '')
    if date_from:
        messages_qs = messages_qs.filter(created_at__date__gte=date_from)
    if date_to:
        messages_qs = messages_qs.filter(created_at__date__lte=date_to)

    # Search keyword
    keyword = request.GET.get('keyword', '').strip()
    if keyword:
        messages_qs = messages_qs.filter(text__icontains=keyword)

    paginator = Paginator(messages_qs, 100)
    page_number = request.GET.get('page', 1)
    page_obj = paginator.get_page(page_number)

    p1 = conversation.participant1
    p2 = conversation.participant2

    return render(request, 'chat/admin/conversation_detail.html', {
        'conversation': conversation,
        'messages': page_obj,
        'participant1': p1,
        'participant2': p2,
        'msg_type': msg_type,
        'date_from': date_from,
        'date_to': date_to,
        'keyword': keyword,
        'is_admin': is_admin_only(request.user),
    })


# ========== PhotoSwap Verification ==========

@login_required
@user_passes_test(is_staff_or_admin, login_url='chat_list')
def admin_photo_swap_queue(request):
    """Admin review queue for PhotoSwap pairs (original + response)."""
    status_filter = request.GET.get('status', 'pending')
    if status_filter not in ('pending', 'approved', 'rejected', 'all'):
        status_filter = 'pending'

    # Find original PhotoSwap messages (not responses) with their responses
    qs = Message.objects.filter(
        is_photo_swap=True,
        is_deleted=False,
        attachment__isnull=False,
        photo_swap_response_to__isnull=True,
    ).select_related('sender', 'conversation', 'attachment').prefetch_related(
        'photo_swap_responses__sender',
        'photo_swap_responses__attachment',
        'photo_swap_responses__conversation',
    ).order_by('-created_at')

    if status_filter != 'all':
        qs = qs.filter(photo_swap_status=status_filter)

    pairs = []
    for original in qs:
        original.attachment_url = reverse('serve_attachment', args=[original.attachment.id]) if original.attachment else None
        responses = list(original.photo_swap_responses.filter(
            is_deleted=False,
            attachment__isnull=False,
        ).order_by('created_at'))
        for resp in responses:
            resp.attachment_url = reverse('serve_attachment', args=[resp.attachment.id]) if resp.attachment else None
        pair = {
            'original': original,
            'responses': responses,
            'conversation': original.conversation,
        }
        pairs.append(pair)

    return render(request, 'chat/admin/photo_swap_queue.html', {
        'pairs': pairs,
        'status_filter': status_filter,
        'is_admin': is_admin_only(request.user),
    })


@login_required
@user_passes_test(is_staff_or_admin, login_url='chat_list')
def admin_photo_swap_detail(request, message_id):
    """Detail view of a PhotoSwap pair (original + response)."""
    # Try to find the message as original first, then as response
    msg = get_object_or_404(
        Message.objects.select_related('sender', 'conversation', 'attachment'),
        id=message_id, is_photo_swap=True, is_deleted=False, attachment__isnull=False
    )
    msg.attachment_url = reverse('serve_attachment', args=[msg.attachment.id]) if msg.attachment else None

    # Determine original and response
    if msg.photo_swap_response_to:
        original = msg.photo_swap_response_to
        response = msg
    else:
        original = msg
        response = msg.photo_swap_responses.filter(is_deleted=False, attachment__isnull=False).order_by('created_at').first()

    original.attachment_url = reverse('serve_attachment', args=[original.attachment.id]) if original.attachment else None
    if response:
        response.attachment_url = reverse('serve_attachment', args=[response.attachment.id]) if response.attachment else None

    return render(request, 'chat/admin/photo_swap_detail.html', {
        'original': original,
        'response': response,
        'is_admin': is_admin_only(request.user),
    })


def _get_photo_swap_pair(message_id):
    """Return (original, response) for a PhotoSwap message, regardless of which ID is given."""
    msg = get_object_or_404(Message, id=message_id, is_photo_swap=True, is_deleted=False)
    if msg.photo_swap_response_to:
        original = msg.photo_swap_response_to
        response = msg
    else:
        original = msg
        response = msg.photo_swap_responses.filter(is_deleted=False, attachment__isnull=False).order_by('created_at').first()
    return original, response


@login_required
@user_passes_test(is_staff_or_admin, login_url='chat_list')
def admin_photo_swap_approve(request, message_id):
    """Approve a PhotoSwap pair so both messages become visible."""
    if request.method != 'POST':
        return JsonResponse({'error': 'Method not allowed'}, status=405)

    original, response = _get_photo_swap_pair(message_id)
    original.photo_swap_status = 'approved'
    original.save(update_fields=['photo_swap_status'])
    if response:
        response.photo_swap_status = 'approved'
        response.save(update_fields=['photo_swap_status'])

    AdminLog.objects.create(
        admin_user=request.user,
        action_type='delete_message',
        target_user=original.sender,
        details=f"Approved PhotoSwap pair {original.id} / {response.id if response else 'N/A'} in conversation {original.conversation_id}"
    )
    return JsonResponse({'success': True, 'status': 'approved'})


@login_required
@user_passes_test(is_staff_or_admin, login_url='chat_list')
def admin_photo_swap_reject(request, message_id):
    """Reject a PhotoSwap pair (keeps both hidden from the other participants)."""
    if request.method != 'POST':
        return JsonResponse({'error': 'Method not allowed'}, status=405)

    original, response = _get_photo_swap_pair(message_id)
    original.photo_swap_status = 'rejected'
    original.save(update_fields=['photo_swap_status'])
    if response:
        response.photo_swap_status = 'rejected'
        response.save(update_fields=['photo_swap_status'])

    AdminLog.objects.create(
        admin_user=request.user,
        action_type='delete_message',
        target_user=original.sender,
        details=f"Rejected PhotoSwap pair {original.id} / {response.id if response else 'N/A'} in conversation {original.conversation_id}"
    )
    return JsonResponse({'success': True, 'status': 'rejected'})


# ========== Logs ==========

@login_required
@user_passes_test(is_staff_or_admin, login_url='chat_list')
def admin_logs(request):
    """Admin action logs"""
    logs = AdminLog.objects.select_related('admin_user', 'target_user').order_by('-created_at')[:100]
    return render(request, 'chat/admin/logs.html', {'logs': logs, 'is_admin': is_admin_only(request.user)})
