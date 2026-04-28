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

    ROLE_CHOICES = [
        ('user', 'User'),
        ('staff', 'Staff'),
        ('admin', 'Admin'),
    ]

    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='profile')
    avatar = models.ImageField(upload_to='avatars/', blank=True, null=True)
    bio = models.TextField(max_length=500, blank=True)
    theme_preference = models.CharField(max_length=10, choices=THEME_CHOICES, default='system')
    role = models.CharField(max_length=10, choices=ROLE_CHOICES, default='user')
    last_seen = models.DateTimeField(default=timezone.now)
    is_online = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = 'chat_user_profile'

    def __str__(self):
        return f"{self.user.username}'s Profile"

    def is_staff_user(self):
        return self.role in ('staff', 'admin') or self.user.is_staff

    def is_admin_user(self):
        return self.role == 'admin' or self.user.is_superuser


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
    deleted_for = models.ManyToManyField(User, related_name='deleted_messages', blank=True)
    is_view_once = models.BooleanField(default=False)
    view_once_consumed_by = models.ManyToManyField(
        User,
        related_name='consumed_view_once_messages',
        blank=True,
    )
    is_photo_swap = models.BooleanField(default=False)
    PHOTO_SWAP_STATUS_CHOICES = [
        ('active', 'Active'),
        ('pending', 'Pending'),
        ('approved', 'Approved'),
        ('rejected', 'Rejected'),
    ]
    photo_swap_status = models.CharField(
        max_length=10,
        choices=PHOTO_SWAP_STATUS_CHOICES,
        default='approved',
        blank=True,
        help_text='PhotoSwap state: active=waiting for response, pending=admin review, approved=revealed, rejected=blocked'
    )
    photo_swap_response_to = models.ForeignKey(
        'self',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='photo_swap_responses',
        help_text='Links a response message to the original PhotoSwap message'
    )

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


class ConversationTheme(models.Model):
    """Per-user, per-conversation chat theme customization."""
    PRESET_CHOICES = [
        ('default', 'Default'),
        ('light', 'Light'),
        ('dark', 'Dark'),
        ('gradient_blue', 'Blue Gradient'),
        ('gradient_sunset', 'Sunset Gradient'),
        ('gradient_aurora', 'Aurora Gradient'),
        ('solid', 'Solid Color'),
        ('image', 'Custom Image'),
    ]

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='conversation_themes')
    conversation = models.ForeignKey(Conversation, on_delete=models.CASCADE, related_name='themes')
    preset = models.CharField(max_length=20, choices=PRESET_CHOICES, default='default')
    bg_color = models.CharField(max_length=32, blank=True)
    bg_image = models.ImageField(upload_to='chat_themes/', blank=True, null=True)
    bubble_me_color = models.CharField(max_length=32, blank=True)
    bubble_other_color = models.CharField(max_length=32, blank=True)
    text_color = models.CharField(max_length=32, blank=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = 'chat_conversation_theme'
        unique_together = ['user', 'conversation']
        indexes = [
            models.Index(fields=['user', 'conversation']),
        ]

    def __str__(self):
        return f"Theme[{self.user.username} / {self.conversation_id}] = {self.preset}"


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
        return f"{self.admin_user.username}: {self.action_type} at {self.created_at}"


class AdminDocument(models.Model):
    """Documents uploaded by admins for reference or distribution."""
    FILE_TYPES = [
        ('image', 'Image'),
        ('pdf', 'PDF'),
        ('document', 'Document'),
        ('spreadsheet', 'Spreadsheet'),
        ('presentation', 'Presentation'),
        ('text', 'Text'),
        ('other', 'Other'),
    ]

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    title = models.CharField(max_length=255)
    description = models.TextField(blank=True)
    file = models.FileField(upload_to='admin_documents/%Y/%m/%d/')
    file_type = models.CharField(max_length=15, choices=FILE_TYPES, default='other')
    mime_type = models.CharField(max_length=100, blank=True)
    file_size = models.PositiveIntegerField(default=0)
    filename = models.CharField(max_length=255, blank=True)
    uploaded_by = models.ForeignKey(User, on_delete=models.CASCADE, related_name='admin_documents')
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = 'chat_admin_document'
        ordering = ['-created_at']

    def __str__(self):
        return f"{self.title} ({self.filename})"
