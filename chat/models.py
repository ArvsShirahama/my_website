from django.db import models
from django.contrib.auth.models import User
from django.utils import timezone
import uuid


class UserProfile(models.Model):
    """Extended user profile with avatar and theme preference"""
    THEME_CHOICES = [
        ('light', 'Light'),
        ('dark', 'Dark'),
        ('system', 'System'),
    ]
    
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='profile')
    avatar = models.ImageField(upload_to='avatars/', blank=True, null=True)
    bio = models.TextField(max_length=500, blank=True)
    theme_preference = models.CharField(max_length=10, choices=THEME_CHOICES, default='system')
    last_seen = models.DateTimeField(default=timezone.now)
    is_online = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = 'chat_user_profile'

    def __str__(self):
        return f"{self.user.username}'s Profile"


class Conversation(models.Model):
    """One-to-one conversation between two users"""
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    participant1 = models.ForeignKey(User, on_delete=models.CASCADE, related_name='conversations_as_p1')
    participant2 = models.ForeignKey(User, on_delete=models.CASCADE, related_name='conversations_as_p2')
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    last_message = models.ForeignKey('Message', on_delete=models.SET_NULL, null=True, blank=True, related_name='+')

    class Meta:
        db_table = 'chat_conversation'
        unique_together = ['participant1', 'participant2']
        indexes = [
            models.Index(fields=['participant1', 'participant2']),
            models.Index(fields=['updated_at']),
        ]

    def __str__(self):
        return f"Chat between {self.participant1.username} and {self.participant2.username}"

    def get_other_participant(self, user):
        """Get the other participant in the conversation"""
        return self.participant2 if user == self.participant1 else self.participant1


class Attachment(models.Model):
    """File attachments for messages (images, videos)"""
    ATTACHMENT_TYPES = [
        ('image', 'Image'),
        ('video', 'Video'),
    ]
    
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    file = models.FileField(upload_to='attachments/%Y/%m/%d/')
    attachment_type = models.CharField(max_length=10, choices=ATTACHMENT_TYPES)
    filename = models.CharField(max_length=255)
    file_size = models.PositiveIntegerField()
    mime_type = models.CharField(max_length=100)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = 'chat_attachment'

    def __str__(self):
        return f"{self.attachment_type}: {self.filename}"


class Message(models.Model):
    """Individual chat message"""
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    conversation = models.ForeignKey(Conversation, on_delete=models.CASCADE, related_name='messages')
    sender = models.ForeignKey(User, on_delete=models.CASCADE, related_name='sent_messages')
    text = models.TextField(blank=True)
    attachment = models.ForeignKey(Attachment, on_delete=models.CASCADE, null=True, blank=True)
    is_read = models.BooleanField(default=False)
    read_at = models.DateTimeField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    is_deleted = models.BooleanField(default=False)

    class Meta:
        db_table = 'chat_message'
        ordering = ['created_at']
        indexes = [
            models.Index(fields=['conversation', 'created_at']),
            models.Index(fields=['sender', 'created_at']),
        ]

    def __str__(self):
        preview = self.text[:50] if self.text else 'Attachment'
        return f"{self.sender.username}: {preview}"


class AdminLog(models.Model):
    """Log for admin actions"""
    ACTION_TYPES = [
        ('delete_user', 'Delete User'),
        ('delete_message', 'Delete Message'),
        ('delete_conversation', 'Delete Conversation'),
        ('ban_user', 'Ban User'),
        ('unban_user', 'Unban User'),
    ]
    
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    admin_user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='admin_actions')
    action_type = models.CharField(max_length=20, choices=ACTION_TYPES)
    target_user = models.ForeignKey(User, on_delete=models.CASCADE, null=True, blank=True, related_name='+')
    details = models.TextField(blank=True)
    ip_address = models.GenericIPAddressField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = 'chat_admin_log'
        ordering = ['-created_at']

    def __str__(self):
        return f"{self.admin_user.username} - {self.action_type} at {self.created_at}"
