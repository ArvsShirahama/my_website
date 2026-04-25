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

from .models import UserProfile, Conversation, Message, Attachment


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
    messages = conversation.messages.filter(is_deleted=False).select_related('sender', 'attachment').order_by('created_at')
    
    return render(request, 'chat/conversation.html', {
        'conversation': conversation, 'other_user': other, 'messages': messages
    })


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
    
    message = Message.objects.create(conversation=conversation, sender=request.user, text=text, attachment=attachment)
    conversation.last_message = message
    conversation.save()
    
    return JsonResponse({'id': str(message.id), 'text': message.text, 'sender': message.sender.username,
                         'created_at': message.created_at.isoformat(),
                         'attachment': {'type': attachment.attachment_type, 'url': attachment.file.url} if attachment else None})


@login_required
def get_messages(request, conversation_id):
    """Get messages API"""
    conversation = get_object_or_404(Conversation, id=conversation_id)
    if request.user not in [conversation.participant1, conversation.participant2]:
        return JsonResponse({'error': 'Not a participant'}, status=403)
    
    last_id = request.GET.get('last_id')
    messages = conversation.messages.filter(is_deleted=False)
    if last_id:
        messages = messages.filter(id__gt=last_id)
    
    messages = messages.select_related('sender', 'attachment').order_by('created_at')
    data = []
    for msg in messages:
        data.append({'id': str(msg.id), 'text': msg.text, 'sender': msg.sender.username,
                     'is_me': msg.sender == request.user, 'created_at': msg.created_at.isoformat(),
                     'is_read': msg.is_read,
                     'attachment': {'type': msg.attachment.attachment_type if msg.attachment else None,
                                    'url': msg.attachment.file.url if msg.attachment else None} if msg.attachment else None})
    
    return JsonResponse({'messages': data})
