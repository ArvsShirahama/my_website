from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib.auth.models import User
from django.http import JsonResponse
from django.db.models import Q
from django.utils import timezone
from django.core.files.storage import default_storage
from django.core.files.base import ContentFile
import os
import uuid

from .models import UserProfile, Conversation, Message, Attachment, ConversationTheme


def can_bypass_view_once(user):
    """Admins/superusers can re-open view-once media."""
    profile = getattr(user, 'profile', None)
    if getattr(user, 'is_superuser', False):
        return True
    if profile and hasattr(profile, 'is_admin_user'):
        return profile.is_admin_user()
    return False


@login_required
def chat_list(request):
    """Chat list with recent conversations"""
    user = request.user
    conversations = Conversation.objects.filter(
        Q(participant1=user) | Q(participant2=user)
    ).select_related('participant1', 'participant2').prefetch_related('messages')
    
    chat_data = []
    for conv in conversations:
        other = conv.get_other_participant(user)
        last_msg = conv.messages.filter(is_deleted=False).order_by('-created_at').first()
        unread = conv.messages.filter(sender=other, is_read=False, is_deleted=False).count()
        chat_data.append({
            'conversation': conv,
            'other_user': other,
            'last_message': last_msg,
            'unread_count': unread,
        })
    
    chat_data.sort(key=lambda x: x['last_message'].created_at if x['last_message'] else conv.created_at, reverse=True)
    all_users = User.objects.exclude(id=user.id).select_related('profile')
    
    return render(request, 'chat/chat_list.html', {'conversations': chat_data, 'users': all_users})


@login_required
def chat_conversation(request, conversation_id):
    """Chat conversation view"""
    user = request.user
    conversation = get_object_or_404(Conversation, id=conversation_id)
    
    if user not in [conversation.participant1, conversation.participant2]:
        from django.http import HttpResponseForbidden
        return HttpResponseForbidden("You are not a participant")
    
    other = conversation.get_other_participant(user)
    conversation.messages.filter(sender=other, is_read=False).update(is_read=True, read_at=timezone.now())
    messages = conversation.messages.filter(is_deleted=False).exclude(deleted_for=user).select_related(
        'sender', 'attachment'
    ).prefetch_related('view_once_consumed_by').order_by('created_at')
    bypass = can_bypass_view_once(user)
    for msg in messages:
        msg.is_consumed_for_user = msg.is_view_once and not bypass and msg.view_once_consumed_by.filter(id=user.id).exists()
    
    theme = ConversationTheme.objects.filter(user=user, conversation=conversation).first()
    theme_data = serialize_theme(theme)

    return render(request, 'chat/conversation.html', {
        'conversation': conversation,
        'other_user': other,
        'messages': messages,
        'can_bypass_view_once': bypass,
        'theme_data': theme_data,
    })


def serialize_theme(theme):
    """Convert a ConversationTheme into a small dict the template/JS can consume."""
    if not theme:
        return {
            'preset': 'default',
            'bg_color': '',
            'bg_image': '',
            'bubble_me_color': '',
            'bubble_other_color': '',
            'text_color': '',
        }
    return {
        'preset': theme.preset,
        'bg_color': theme.bg_color or '',
        'bg_image': theme.bg_image.url if theme.bg_image else '',
        'bubble_me_color': theme.bubble_me_color or '',
        'bubble_other_color': theme.bubble_other_color or '',
        'text_color': theme.text_color or '',
    }


@login_required
def start_conversation(request, user_id):
    """Start a new conversation"""
    target_user = get_object_or_404(User, id=user_id)
    if target_user == request.user:
        return redirect('chat_list')
    
    existing = Conversation.objects.filter(
        (Q(participant1=request.user) & Q(participant2=target_user)) |
        (Q(participant1=target_user) & Q(participant2=request.user))
    ).first()
    
    if existing:
        return redirect('chat_conversation', conversation_id=existing.id)
    
    conversation = Conversation.objects.create(participant1=request.user, participant2=target_user)
    return redirect('chat_conversation', conversation_id=conversation.id)


@login_required
def send_message(request, conversation_id):
    """Send message API"""
    if request.method != 'POST':
        return JsonResponse({'error': 'Method not allowed'}, status=405)
    
    conversation = get_object_or_404(Conversation, id=conversation_id)
    if request.user not in [conversation.participant1, conversation.participant2]:
        return JsonResponse({'error': 'Not a participant'}, status=403)
    
    text = request.POST.get('text', '').strip()
    if not text and 'file' not in request.FILES:
        return JsonResponse({'error': 'Message cannot be empty'}, status=400)

    view_once = request.POST.get('view_once', '0').lower() in ('1', 'true', 'on', 'yes')
    attachment = None
    if 'file' in request.FILES:
        uploaded_file = request.FILES['file']
        file_type = 'image' if uploaded_file.content_type.startswith('image/') else 'video'
        ext = os.path.splitext(uploaded_file.name)[1]
        filename = f"{uuid.uuid4()}{ext}"
        path = default_storage.save(f'attachments/{filename}', ContentFile(uploaded_file.read()))
        
        attachment = Attachment.objects.create(
            file=path, attachment_type=file_type, filename=uploaded_file.name,
            file_size=uploaded_file.size, mime_type=uploaded_file.content_type
        )
    else:
        view_once = False
    
    message = Message.objects.create(
        conversation=conversation,
        sender=request.user,
        text=text,
        attachment=attachment,
        is_view_once=view_once,
    )
    conversation.last_message = message
    conversation.save()
    
    return JsonResponse({'id': str(message.id), 'text': message.text, 'sender': message.sender.username,
                         'created_at': message.created_at.isoformat(),
                         'is_view_once': message.is_view_once,
                         'view_once_consumed': False,
                         'attachment': {'type': attachment.attachment_type, 'url': attachment.file.url} if attachment else None})


@login_required
def get_messages(request, conversation_id):
    """Get messages API"""
    conversation = get_object_or_404(Conversation, id=conversation_id)
    if request.user not in [conversation.participant1, conversation.participant2]:
        return JsonResponse({'error': 'Not a participant'}, status=403)

    last_id = request.GET.get('last_id')
    bypass = can_bypass_view_once(request.user)
    messages = conversation.messages.filter(is_deleted=False).exclude(deleted_for=request.user)
    if last_id:
        messages = messages.filter(id__gt=last_id)

    messages = messages.select_related('sender', 'attachment').prefetch_related('view_once_consumed_by').order_by('created_at')
    data = []
    for msg in messages:
        consumed = msg.is_view_once and not bypass and msg.view_once_consumed_by.filter(id=request.user.id).exists()
        attachment_data = None
        if msg.attachment:
            attachment_data = {
                'type': msg.attachment.attachment_type,
                'url': None if consumed else msg.attachment.file.url,
            }
        data.append({'id': str(msg.id), 'text': msg.text, 'sender': msg.sender.username,
                     'is_me': msg.sender == request.user, 'created_at': msg.created_at.isoformat(),
                     'is_read': msg.is_read,
                     'is_view_once': msg.is_view_once,
                     'view_once_consumed': consumed,
                     'attachment': attachment_data})

    return JsonResponse({'messages': data})


@login_required
def consume_view_once_media(request, message_id):
    """Mark a view-once message as consumed for the current user."""
    if request.method != 'POST':
        return JsonResponse({'error': 'Method not allowed'}, status=405)

    message = get_object_or_404(Message.objects.select_related('conversation', 'attachment'), id=message_id)
    user = request.user

    if user not in [message.conversation.participant1, message.conversation.participant2]:
        return JsonResponse({'error': 'Not a participant'}, status=403)

    if not message.is_view_once or not message.attachment:
        return JsonResponse({'success': False, 'error': 'Not a view-once media message'}, status=400)

    if can_bypass_view_once(user):
        return JsonResponse({'success': True, 'consumed': False, 'bypassed': True})

    message.view_once_consumed_by.add(user)
    return JsonResponse({'success': True, 'consumed': True, 'bypassed': False})


@login_required
def delete_message(request, message_id):
    """Delete message for me or for everyone"""
    if request.method != 'POST':
        return JsonResponse({'error': 'Method not allowed'}, status=405)

    message = get_object_or_404(Message, id=message_id)
    user = request.user

    if user not in [message.conversation.participant1, message.conversation.participant2]:
        return JsonResponse({'error': 'Not a participant'}, status=403)

    mode = request.POST.get('mode', 'me')

    if mode == 'everyone':
        if message.sender != user:
            return JsonResponse({'error': 'Only sender can delete for everyone'}, status=403)
        message.is_deleted = True
        message.save()
    else:
        message.deleted_for.add(user)

    return JsonResponse({'success': True, 'mode': mode})


# ===== Conversation theme APIs =====

VALID_PRESETS = {choice[0] for choice in ConversationTheme.PRESET_CHOICES}
COLOR_FIELDS = ('bg_color', 'bubble_me_color', 'bubble_other_color', 'text_color')
MAX_THEME_IMAGE_BYTES = 5 * 1024 * 1024  # 5 MB


def _is_valid_color(value):
    """Accept a small whitelist of CSS color formats to avoid injecting arbitrary CSS."""
    if not value:
        return True
    value = value.strip()
    if len(value) > 32:
        return False
    if value.startswith('#') and (len(value) in (4, 7, 9)):
        return all(c in '0123456789abcdefABCDEF' for c in value[1:])
    if value.startswith('rgb(') or value.startswith('rgba('):
        return value.endswith(')') and ';' not in value and '/*' not in value
    # named colors / simple words
    return value.replace('-', '').replace('_', '').isalnum()


@login_required
def get_conversation_theme(request, conversation_id):
    conversation = get_object_or_404(Conversation, id=conversation_id)
    if request.user not in [conversation.participant1, conversation.participant2]:
        return JsonResponse({'error': 'Not a participant'}, status=403)

    theme = ConversationTheme.objects.filter(user=request.user, conversation=conversation).first()
    return JsonResponse({'success': True, 'theme': serialize_theme(theme)})


@login_required
def set_conversation_theme(request, conversation_id):
    if request.method != 'POST':
        return JsonResponse({'error': 'Method not allowed'}, status=405)

    conversation = get_object_or_404(Conversation, id=conversation_id)
    if request.user not in [conversation.participant1, conversation.participant2]:
        return JsonResponse({'error': 'Not a participant'}, status=403)

    preset = request.POST.get('preset', 'default').strip()
    if preset not in VALID_PRESETS:
        return JsonResponse({'error': 'Invalid preset'}, status=400)

    colors = {}
    for field in COLOR_FIELDS:
        val = request.POST.get(field, '').strip()
        if not _is_valid_color(val):
            return JsonResponse({'error': f'Invalid {field}'}, status=400)
        colors[field] = val

    theme, _created = ConversationTheme.objects.get_or_create(
        user=request.user, conversation=conversation
    )
    theme.preset = preset
    for field, val in colors.items():
        setattr(theme, field, val)

    if 'bg_image' in request.FILES:
        uploaded = request.FILES['bg_image']
        if not uploaded.content_type.startswith('image/'):
            return JsonResponse({'error': 'bg_image must be an image'}, status=400)
        if uploaded.size > MAX_THEME_IMAGE_BYTES:
            return JsonResponse({'error': 'bg_image too large (max 5MB)'}, status=400)
        if theme.bg_image:
            try:
                theme.bg_image.delete(save=False)
            except Exception:
                pass
        theme.bg_image = uploaded
    elif request.POST.get('clear_bg_image') == '1' and theme.bg_image:
        try:
            theme.bg_image.delete(save=False)
        except Exception:
            pass
        theme.bg_image = None

    theme.save()
    return JsonResponse({'success': True, 'theme': serialize_theme(theme)})


@login_required
def reset_conversation_theme(request, conversation_id):
    if request.method != 'POST':
        return JsonResponse({'error': 'Method not allowed'}, status=405)

    conversation = get_object_or_404(Conversation, id=conversation_id)
    if request.user not in [conversation.participant1, conversation.participant2]:
        return JsonResponse({'error': 'Not a participant'}, status=403)

    theme = ConversationTheme.objects.filter(user=request.user, conversation=conversation).first()
    if theme:
        if theme.bg_image:
            try:
                theme.bg_image.delete(save=False)
            except Exception:
                pass
        theme.delete()

    return JsonResponse({'success': True, 'theme': serialize_theme(None)})
