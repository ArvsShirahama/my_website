import io
import json
import uuid
from django.test import TestCase, Client, override_settings
from django.contrib.auth.models import User
from django.urls import reverse
from django.core.files.uploadedfile import SimpleUploadedFile
from django.utils import timezone

from chat.models import (
    UserProfile, Conversation, Message, Attachment, AdminLog, ConversationTheme,
)
from chat.views_chat import can_bypass_view_once, is_photo_swap_locked_for


class UserProfileModelTests(TestCase):
    """Tests for UserProfile model and helpers."""

    def setUp(self):
        self.user = User.objects.create_user(username='alice', password='testpass123')
        self.profile = UserProfile.objects.get(user=self.user)

    def test_profile_str(self):
        self.assertEqual(str(self.profile), "alice's Profile")

    def test_is_staff_user_default(self):
        self.assertFalse(self.profile.is_staff_user())

    def test_is_admin_user_default(self):
        self.assertFalse(self.profile.is_admin_user())

    def test_role_staff(self):
        self.profile.role = 'staff'
        self.profile.save()
        self.assertTrue(self.profile.is_staff_user())
        self.assertFalse(self.profile.is_admin_user())

    def test_role_admin(self):
        self.profile.role = 'admin'
        self.profile.save()
        self.assertTrue(self.profile.is_staff_user())
        self.assertTrue(self.profile.is_admin_user())


class ConversationModelTests(TestCase):
    """Tests for Conversation model."""

    def setUp(self):
        self.user1 = User.objects.create_user(username='alice', password='testpass123')
        self.user2 = User.objects.create_user(username='bob', password='testpass123')

    def test_create_conversation(self):
        conv = Conversation.objects.create(participant1=self.user1, participant2=self.user2)
        self.assertEqual(conv.participant1, self.user1)
        self.assertEqual(conv.participant2, self.user2)

    def test_get_other_participant(self):
        conv = Conversation.objects.create(participant1=self.user1, participant2=self.user2)
        self.assertEqual(conv.get_other_participant(self.user1), self.user2)
        self.assertEqual(conv.get_other_participant(self.user2), self.user1)

    def test_unique_participants(self):
        Conversation.objects.create(participant1=self.user1, participant2=self.user2)
        with self.assertRaises(Exception):
            Conversation.objects.create(participant1=self.user1, participant2=self.user2)


class AttachmentModelTests(TestCase):
    """Tests for Attachment model."""

    def test_attachment_str(self):
        file = SimpleUploadedFile('test.png', b'fakeimage', content_type='image/png')
        att = Attachment.objects.create(
            file=file, attachment_type='image', filename='test.png',
            file_size=9, mime_type='image/png'
        )
        self.assertIn('image', str(att))
        self.assertIn('test.png', str(att))


class MessageModelTests(TestCase):
    """Tests for Message model."""

    def setUp(self):
        self.user1 = User.objects.create_user(username='alice', password='testpass123')
        self.user2 = User.objects.create_user(username='bob', password='testpass123')
        self.conv = Conversation.objects.create(participant1=self.user1, participant2=self.user2)

    def test_message_str(self):
        msg = Message.objects.create(conversation=self.conv, sender=self.user1, text='Hello')
        self.assertEqual(str(msg), 'alice: Hello')

    def test_view_once_consumed_by(self):
        msg = Message.objects.create(conversation=self.conv, sender=self.user1, text='Secret', is_view_once=True)
        self.assertEqual(msg.view_once_consumed_by.count(), 0)
        msg.view_once_consumed_by.add(self.user2)
        self.assertTrue(msg.view_once_consumed_by.filter(id=self.user2.id).exists())


class ViewOnceHelperTests(TestCase):
    """Tests for can_bypass_view_once and is_photo_swap_locked_for helpers."""

    def setUp(self):
        self.user = User.objects.create_user(username='alice', password='testpass123')
        self.superuser = User.objects.create_superuser(username='admin', password='testpass123', email='admin@test.com')
        self.other = User.objects.create_user(username='bob', password='testpass123')
        self.conv = Conversation.objects.create(participant1=self.user, participant2=self.other)

    def test_can_bypass_view_once_superuser(self):
        self.assertTrue(can_bypass_view_once(self.superuser))

    def test_can_bypass_view_once_regular(self):
        self.assertFalse(can_bypass_view_once(self.user))

    def test_can_bypass_view_once_admin_role(self):
        profile = self.user.profile
        profile.role = 'admin'
        profile.save()
        self.assertTrue(can_bypass_view_once(self.user))

    def test_is_photo_swap_locked_for_not_swap(self):
        msg = Message.objects.create(conversation=self.conv, sender=self.user, text='Hello')
        self.assertFalse(is_photo_swap_locked_for(msg, self.user))

    def test_is_photo_swap_locked_for_approved(self):
        att = Attachment.objects.create(
            file=SimpleUploadedFile('a.png', b'x', content_type='image/png'),
            attachment_type='image', filename='a.png', file_size=1, mime_type='image/png'
        )
        msg = Message.objects.create(
            conversation=self.conv, sender=self.user, attachment=att,
            is_photo_swap=True, photo_swap_status='approved'
        )
        self.assertFalse(is_photo_swap_locked_for(msg, self.user))

    def test_is_photo_swap_locked_for_active(self):
        att = Attachment.objects.create(
            file=SimpleUploadedFile('a.png', b'x', content_type='image/png'),
            attachment_type='image', filename='a.png', file_size=1, mime_type='image/png'
        )
        msg = Message.objects.create(
            conversation=self.conv, sender=self.user, attachment=att,
            is_photo_swap=True, photo_swap_status='active'
        )
        self.assertTrue(is_photo_swap_locked_for(msg, self.user))
        self.assertTrue(is_photo_swap_locked_for(msg, self.other))

    def test_is_photo_swap_locked_for_pending(self):
        att = Attachment.objects.create(
            file=SimpleUploadedFile('a.png', b'x', content_type='image/png'),
            attachment_type='image', filename='a.png', file_size=1, mime_type='image/png'
        )
        msg = Message.objects.create(
            conversation=self.conv, sender=self.user, attachment=att,
            is_photo_swap=True, photo_swap_status='pending'
        )
        self.assertTrue(is_photo_swap_locked_for(msg, self.user))

    def test_is_photo_swap_locked_for_rejected(self):
        att = Attachment.objects.create(
            file=SimpleUploadedFile('a.png', b'x', content_type='image/png'),
            attachment_type='image', filename='a.png', file_size=1, mime_type='image/png'
        )
        msg = Message.objects.create(
            conversation=self.conv, sender=self.user, attachment=att,
            is_photo_swap=True, photo_swap_status='rejected'
        )
        self.assertTrue(is_photo_swap_locked_for(msg, self.user))


class AuthViewsTests(TestCase):
    """Tests for authentication views."""

    def setUp(self):
        self.client = Client()
        self.register_url = reverse('register')
        self.login_url = reverse('login')
        self.logout_url = reverse('logout')

    def test_register_success(self):
        resp = self.client.post(self.register_url, {
            'username': 'newuser',
            'email': 'new@example.com',
            'password': 'securepass123',
            'confirm_password': 'securepass123',
        })
        self.assertEqual(resp.status_code, 302)
        self.assertTrue(User.objects.filter(username='newuser').exists())

    def test_register_password_mismatch(self):
        resp = self.client.post(self.register_url, {
            'username': 'newuser',
            'email': 'new@example.com',
            'password': 'securepass123',
            'confirm_password': 'different',
        })
        self.assertEqual(resp.status_code, 200)
        self.assertIn('Passwords do not match', resp.content.decode())

    def test_register_duplicate_username(self):
        User.objects.create_user(username='newuser', password='testpass123')
        resp = self.client.post(self.register_url, {
            'username': 'newuser',
            'email': 'other@example.com',
            'password': 'securepass123',
            'confirm_password': 'securepass123',
        })
        self.assertEqual(resp.status_code, 200)
        self.assertIn('Username already exists', resp.content.decode())

    def test_login_success(self):
        User.objects.create_user(username='alice', password='testpass123')
        resp = self.client.post(self.login_url, {
            'username': 'alice',
            'password': 'testpass123',
        })
        self.assertEqual(resp.status_code, 302)

    def test_login_invalid(self):
        resp = self.client.post(self.login_url, {
            'username': 'nobody',
            'password': 'wrongpass',
        })
        self.assertEqual(resp.status_code, 200)
        self.assertIn('Invalid credentials', resp.content.decode())

    def test_logout_redirects(self):
        user = User.objects.create_user(username='alice', password='testpass123')
        self.client.force_login(user)
        resp = self.client.get(self.logout_url)
        self.assertEqual(resp.status_code, 302)


class ChatListViewTests(TestCase):
    """Tests for chat_list view."""

    def setUp(self):
        self.client = Client()
        self.user = User.objects.create_user(username='alice', password='testpass123')
        self.other = User.objects.create_user(username='bob', password='testpass123')
        self.url = reverse('chat_list')

    def test_redirects_when_not_logged_in(self):
        resp = self.client.get(self.url)
        self.assertEqual(resp.status_code, 302)

    def test_shows_conversations(self):
        self.client.force_login(self.user)
        conv = Conversation.objects.create(participant1=self.user, participant2=self.other)
        Message.objects.create(conversation=conv, sender=self.other, text='Hi')
        resp = self.client.get(self.url)
        self.assertEqual(resp.status_code, 200)
        self.assertContains(resp, 'bob')


class ChatConversationViewTests(TestCase):
    """Tests for chat_conversation view."""

    def setUp(self):
        self.client = Client()
        self.user = User.objects.create_user(username='alice', password='testpass123')
        self.other = User.objects.create_user(username='bob', password='testpass123')
        self.conv = Conversation.objects.create(participant1=self.user, participant2=self.other)
        self.url = reverse('chat_conversation', args=[self.conv.id])

    def test_non_participant_forbidden(self):
        outsider = User.objects.create_user(username='eve', password='testpass123')
        self.client.force_login(outsider)
        resp = self.client.get(self.url)
        self.assertEqual(resp.status_code, 403)

    def test_participant_can_view(self):
        self.client.force_login(self.user)
        resp = self.client.get(self.url)
        self.assertEqual(resp.status_code, 200)

    def test_unconsumed_view_once_hides_url(self):
        """Sender should NOT see attachment_url for their own unconsumed view-once message."""
        att = Attachment.objects.create(
            file=SimpleUploadedFile('a.png', b'x', content_type='image/png'),
            attachment_type='image', filename='a.png', file_size=1, mime_type='image/png'
        )
        msg = Message.objects.create(
            conversation=self.conv, sender=self.user, attachment=att,
            is_view_once=True
        )
        self.client.force_login(self.user)
        resp = self.client.get(self.url)
        self.assertEqual(resp.status_code, 200)
        # The template should not render a raw media tag; instead it shows the view-once card
        content = resp.content.decode()
        self.assertNotIn('data-media-url="/chat/api/attachment/', content)

    def test_consumed_view_once_shows_url(self):
        att = Attachment.objects.create(
            file=SimpleUploadedFile('a.png', b'x', content_type='image/png'),
            attachment_type='image', filename='a.png', file_size=1, mime_type='image/png'
        )
        msg = Message.objects.create(
            conversation=self.conv, sender=self.user, attachment=att,
            is_view_once=True
        )
        msg.view_once_consumed_by.add(self.user)
        self.client.force_login(self.user)
        resp = self.client.get(self.url)
        self.assertEqual(resp.status_code, 200)
        content = resp.content.decode()
        self.assertIn('data-media-url', content)

    def test_mark_messages_read(self):
        Message.objects.create(conversation=self.conv, sender=self.other, text='Unread', is_read=False)
        self.client.force_login(self.user)
        self.client.get(self.url)
        self.assertTrue(Message.objects.filter(sender=self.other, is_read=True).exists())


class StartConversationViewTests(TestCase):
    """Tests for start_conversation view."""

    def setUp(self):
        self.client = Client()
        self.user = User.objects.create_user(username='alice', password='testpass123')
        self.other = User.objects.create_user(username='bob', password='testpass123')
        self.url = reverse('start_conversation', args=[self.other.id])

    def test_creates_conversation(self):
        self.client.force_login(self.user)
        resp = self.client.get(self.url)
        self.assertEqual(resp.status_code, 302)
        self.assertTrue(Conversation.objects.filter(
            participant1=self.user, participant2=self.other
        ).exists())

    def test_redirects_to_existing(self):
        self.client.force_login(self.user)
        existing = Conversation.objects.create(participant1=self.user, participant2=self.other)
        resp = self.client.get(self.url)
        self.assertRedirects(resp, reverse('chat_conversation', args=[existing.id]), fetch_redirect_response=False)

    def test_cannot_start_with_self(self):
        self.client.force_login(self.user)
        url = reverse('start_conversation', args=[self.user.id])
        resp = self.client.get(url)
        self.assertEqual(resp.status_code, 302)
        self.assertFalse(Conversation.objects.filter(participant1=self.user, participant2=self.user).exists())


class SendMessageViewTests(TestCase):
    """Tests for send_message API."""

    def setUp(self):
        self.client = Client()
        self.user = User.objects.create_user(username='alice', password='testpass123')
        self.other = User.objects.create_user(username='bob', password='testpass123')
        self.conv = Conversation.objects.create(participant1=self.user, participant2=self.other)
        self.url = reverse('send_message', args=[self.conv.id])

    def test_send_text(self):
        self.client.force_login(self.user)
        resp = self.client.post(self.url, {'text': 'Hello world'})
        self.assertEqual(resp.status_code, 200)
        data = resp.json()
        self.assertEqual(data['text'], 'Hello world')
        self.assertEqual(data['sender'], 'alice')

    def test_send_empty_rejected(self):
        self.client.force_login(self.user)
        resp = self.client.post(self.url, {})
        self.assertEqual(resp.status_code, 400)
        self.assertIn('error', resp.json())

    def test_non_participant_rejected(self):
        outsider = User.objects.create_user(username='eve', password='testpass123')
        self.client.force_login(outsider)
        resp = self.client.post(self.url, {'text': 'Hello'})
        self.assertEqual(resp.status_code, 403)

    def test_send_view_once(self):
        self.client.force_login(self.user)
        resp = self.client.post(self.url, {
            'text': 'Secret',
            'view_once': '1',
            'file': SimpleUploadedFile('a.png', b'x', content_type='image/png'),
        })
        self.assertEqual(resp.status_code, 200)
        data = resp.json()
        self.assertTrue(data['is_view_once'])

    def test_send_photo_swap(self):
        self.client.force_login(self.user)
        resp = self.client.post(self.url, {
            'text': 'Swap',
            'photo_swap': '1',
            'file': SimpleUploadedFile('a.png', b'x', content_type='image/png'),
        })
        self.assertEqual(resp.status_code, 200)
        data = resp.json()
        self.assertTrue(data['is_photo_swap'])
        self.assertEqual(data['photo_swap_status'], 'active')

    def test_photo_swap_response(self):
        att = Attachment.objects.create(
            file=SimpleUploadedFile('orig.png', b'x', content_type='image/png'),
            attachment_type='image', filename='orig.png', file_size=1, mime_type='image/png'
        )
        original = Message.objects.create(
            conversation=self.conv, sender=self.user, attachment=att,
            is_photo_swap=True, photo_swap_status='active'
        )
        self.client.force_login(self.other)
        resp = self.client.post(self.url, {
            'text': 'Response',
            'photo_swap_response': '1',
            'photo_swap_original_id': str(original.id),
            'file': SimpleUploadedFile('resp.png', b'x', content_type='image/png'),
        })
        self.assertEqual(resp.status_code, 200)
        original.refresh_from_db()
        self.assertEqual(original.photo_swap_status, 'pending')

    def test_photo_swap_response_type_mismatch(self):
        att = Attachment.objects.create(
            file=SimpleUploadedFile('orig.png', b'x', content_type='image/png'),
            attachment_type='image', filename='orig.png', file_size=1, mime_type='image/png'
        )
        original = Message.objects.create(
            conversation=self.conv, sender=self.user, attachment=att,
            is_photo_swap=True, photo_swap_status='active'
        )
        self.client.force_login(self.other)
        resp = self.client.post(self.url, {
            'text': 'Response',
            'photo_swap_response': '1',
            'photo_swap_original_id': str(original.id),
            'file': SimpleUploadedFile('resp.mp4', b'x', content_type='video/mp4'),
        })
        self.assertEqual(resp.status_code, 400)


class GetMessagesViewTests(TestCase):
    """Tests for get_messages API."""

    def setUp(self):
        self.client = Client()
        self.user = User.objects.create_user(username='alice', password='testpass123')
        self.other = User.objects.create_user(username='bob', password='testpass123')
        self.conv = Conversation.objects.create(participant1=self.user, participant2=self.other)
        self.url = reverse('get_messages', args=[self.conv.id])

    def test_get_messages(self):
        Message.objects.create(conversation=self.conv, sender=self.user, text='Hi')
        self.client.force_login(self.user)
        resp = self.client.get(self.url)
        self.assertEqual(resp.status_code, 200)
        data = resp.json()
        self.assertEqual(len(data['messages']), 1)
        self.assertEqual(data['messages'][0]['text'], 'Hi')

    def test_get_messages_excludes_deleted(self):
        msg = Message.objects.create(conversation=self.conv, sender=self.user, text='Hi')
        msg.deleted_for.add(self.user)
        self.client.force_login(self.user)
        resp = self.client.get(self.url)
        self.assertEqual(resp.status_code, 200)
        data = resp.json()
        self.assertEqual(len(data['messages']), 0)

    def test_get_messages_with_last_id(self):
        msg1 = Message.objects.create(conversation=self.conv, sender=self.user, text='First')
        Message.objects.create(conversation=self.conv, sender=self.user, text='Second')
        self.client.force_login(self.user)
        resp = self.client.get(self.url, {'last_id': str(msg1.id)})
        self.assertEqual(resp.status_code, 200)
        data = resp.json()
        self.assertEqual(len(data['messages']), 1)
        self.assertEqual(data['messages'][0]['text'], 'Second')

    def test_view_once_url_hidden_until_consumed(self):
        att = Attachment.objects.create(
            file=SimpleUploadedFile('a.png', b'x', content_type='image/png'),
            attachment_type='image', filename='a.png', file_size=1, mime_type='image/png'
        )
        msg = Message.objects.create(
            conversation=self.conv, sender=self.user, attachment=att, is_view_once=True
        )
        self.client.force_login(self.other)
        resp = self.client.get(self.url)
        data = resp.json()
        self.assertIsNone(data['messages'][0]['attachment']['url'])

    def test_view_once_url_shown_when_consumed(self):
        att = Attachment.objects.create(
            file=SimpleUploadedFile('a.png', b'x', content_type='image/png'),
            attachment_type='image', filename='a.png', file_size=1, mime_type='image/png'
        )
        msg = Message.objects.create(
            conversation=self.conv, sender=self.user, attachment=att, is_view_once=True
        )
        msg.view_once_consumed_by.add(self.other)
        self.client.force_login(self.other)
        resp = self.client.get(self.url)
        data = resp.json()
        self.assertIsNotNone(data['messages'][0]['attachment']['url'])


class ConsumeViewOnceTests(TestCase):
    """Tests for consume_view_once_media API."""

    def setUp(self):
        self.client = Client()
        self.user = User.objects.create_user(username='alice', password='testpass123')
        self.other = User.objects.create_user(username='bob', password='testpass123')
        self.conv = Conversation.objects.create(participant1=self.user, participant2=self.other)
        att = Attachment.objects.create(
            file=SimpleUploadedFile('a.png', b'x', content_type='image/png'),
            attachment_type='image', filename='a.png', file_size=1, mime_type='image/png'
        )
        self.msg = Message.objects.create(
            conversation=self.conv, sender=self.user, attachment=att,
            is_view_once=True
        )
        self.url = reverse('consume_view_once_media', args=[self.msg.id])

    def test_non_participant_rejected(self):
        outsider = User.objects.create_user(username='eve', password='testpass123')
        self.client.force_login(outsider)
        resp = self.client.post(self.url)
        self.assertEqual(resp.status_code, 403)

    def test_not_view_once_rejected(self):
        plain = Message.objects.create(conversation=self.conv, sender=self.user, text='Plain')
        url = reverse('consume_view_once_media', args=[plain.id])
        self.client.force_login(self.other)
        resp = self.client.post(url)
        self.assertEqual(resp.status_code, 400)

    def test_get_method_rejected(self):
        self.client.force_login(self.other)
        resp = self.client.get(self.url)
        self.assertEqual(resp.status_code, 405)

    def test_receiver_can_consume(self):
        self.client.force_login(self.other)
        resp = self.client.post(self.url)
        self.assertEqual(resp.status_code, 200)
        data = resp.json()
        self.assertTrue(data['success'])
        self.assertTrue(data['consumed'])
        self.assertIsNotNone(data['url'])
        self.assertTrue(self.msg.view_once_consumed_by.filter(id=self.other.id).exists())

    def test_sender_can_consume(self):
        """Sender must also consume their own view-once message to view it."""
        self.client.force_login(self.user)
        resp = self.client.post(self.url)
        self.assertEqual(resp.status_code, 200)
        data = resp.json()
        self.assertTrue(data['success'])
        self.assertTrue(data['consumed'])
        self.assertIsNotNone(data['url'])
        self.assertTrue(self.msg.view_once_consumed_by.filter(id=self.user.id).exists())

    def test_double_consume_rejected(self):
        self.msg.view_once_consumed_by.add(self.other)
        self.client.force_login(self.other)
        resp = self.client.post(self.url)
        self.assertEqual(resp.status_code, 403)
        self.assertEqual(resp.json()['error'], 'Already viewed')

    def test_admin_bypass(self):
        admin = User.objects.create_superuser(username='admin', password='testpass123', email='a@test.com')
        self.conv.participant1 = admin
        self.conv.save()
        self.client.force_login(admin)
        resp = self.client.post(self.url)
        self.assertEqual(resp.status_code, 200)
        data = resp.json()
        self.assertTrue(data['bypassed'])
        self.assertFalse(data['consumed'])
        self.assertIsNotNone(data['url'])


class DeleteMessageViewTests(TestCase):
    """Tests for delete_message API."""

    def setUp(self):
        self.client = Client()
        self.user = User.objects.create_user(username='alice', password='testpass123')
        self.other = User.objects.create_user(username='bob', password='testpass123')
        self.conv = Conversation.objects.create(participant1=self.user, participant2=self.other)
        self.msg = Message.objects.create(conversation=self.conv, sender=self.user, text='Hello')
        self.url = reverse('delete_message', args=[self.msg.id])

    def test_delete_for_me(self):
        self.client.force_login(self.other)
        resp = self.client.post(self.url, {'mode': 'me'})
        self.assertEqual(resp.status_code, 200)
        self.assertTrue(self.msg.deleted_for.filter(id=self.other.id).exists())
        self.assertFalse(self.msg.is_deleted)

    def test_delete_for_everyone_as_sender(self):
        self.client.force_login(self.user)
        resp = self.client.post(self.url, {'mode': 'everyone'})
        self.assertEqual(resp.status_code, 200)
        self.msg.refresh_from_db()
        self.assertTrue(self.msg.is_deleted)

    def test_delete_for_everyone_as_non_sender_rejected(self):
        self.client.force_login(self.other)
        resp = self.client.post(self.url, {'mode': 'everyone'})
        self.assertEqual(resp.status_code, 403)

    def test_non_participant_rejected(self):
        outsider = User.objects.create_user(username='eve', password='testpass123')
        self.client.force_login(outsider)
        resp = self.client.post(self.url)
        self.assertEqual(resp.status_code, 403)


class ServeAttachmentTests(TestCase):
    """Tests for serve_attachment API."""

    def setUp(self):
        self.client = Client()
        self.user = User.objects.create_user(username='alice', password='testpass123')
        self.other = User.objects.create_user(username='bob', password='testpass123')
        self.conv = Conversation.objects.create(participant1=self.user, participant2=self.other)
        self.att = Attachment.objects.create(
            file=SimpleUploadedFile('a.png', b'x', content_type='image/png'),
            attachment_type='image', filename='a.png', file_size=1, mime_type='image/png'
        )
        Message.objects.create(conversation=self.conv, sender=self.user, attachment=self.att)
        self.url = reverse('serve_attachment', args=[self.att.id])

    def test_participant_can_access(self):
        self.client.force_login(self.user)
        resp = self.client.get(self.url)
        self.assertEqual(resp.status_code, 200)

    def test_non_participant_forbidden(self):
        outsider = User.objects.create_user(username='eve', password='testpass123')
        self.client.force_login(outsider)
        resp = self.client.get(self.url)
        self.assertEqual(resp.status_code, 403)


class AdminDashboardTests(TestCase):
    """Tests for admin dashboard views."""

    def setUp(self):
        self.client = Client()
        self.admin = User.objects.create_superuser(username='admin', password='testpass123', email='a@test.com')
        self.staff = User.objects.create_user(username='staff', password='testpass123')
        profile = self.staff.profile
        profile.role = 'staff'
        profile.save()
        self.user = User.objects.create_user(username='alice', password='testpass123')
        self.other = User.objects.create_user(username='bob', password='testpass123')
        self.conv = Conversation.objects.create(participant1=self.user, participant2=self.other)
        self.msg = Message.objects.create(conversation=self.conv, sender=self.user, text='Hello')

    def test_admin_dashboard_access(self):
        self.client.force_login(self.admin)
        resp = self.client.get(reverse('admin_dashboard'))
        self.assertEqual(resp.status_code, 200)

    def test_staff_dashboard_access(self):
        self.client.force_login(self.staff)
        resp = self.client.get(reverse('admin_dashboard'))
        self.assertEqual(resp.status_code, 200)

    def test_regular_user_redirected(self):
        self.client.force_login(self.user)
        resp = self.client.get(reverse('admin_dashboard'))
        self.assertEqual(resp.status_code, 302)

    def test_admin_users_list(self):
        self.client.force_login(self.admin)
        resp = self.client.get(reverse('admin_users'))
        self.assertEqual(resp.status_code, 200)
        self.assertContains(resp, 'alice')

    def test_admin_messages_list(self):
        self.client.force_login(self.admin)
        resp = self.client.get(reverse('admin_messages'))
        self.assertEqual(resp.status_code, 200)
        self.assertContains(resp, 'Hello')

    def test_admin_conversations_list(self):
        self.client.force_login(self.admin)
        resp = self.client.get(reverse('admin_conversations'))
        self.assertEqual(resp.status_code, 200)

    def test_admin_logs_list(self):
        AdminLog.objects.create(admin_user=self.admin, action_type='delete_message', details='test')
        self.client.force_login(self.admin)
        resp = self.client.get(reverse('admin_logs'))
        self.assertEqual(resp.status_code, 200)
        self.assertContains(resp, 'test')


class AdminBulkDeleteTests(TestCase):
    """Tests for admin_bulk_delete_messages."""

    def setUp(self):
        self.client = Client()
        self.admin = User.objects.create_superuser(username='admin', password='testpass123', email='a@test.com')
        self.user = User.objects.create_user(username='alice', password='testpass123')
        self.other = User.objects.create_user(username='bob', password='testpass123')
        self.conv = Conversation.objects.create(participant1=self.user, participant2=self.other)
        self.msg1 = Message.objects.create(conversation=self.conv, sender=self.user, text='M1')
        self.msg2 = Message.objects.create(conversation=self.conv, sender=self.user, text='M2')
        self.url = reverse('admin_bulk_delete_messages')

    def test_bulk_delete_success(self):
        self.client.force_login(self.admin)
        resp = self.client.post(
            self.url,
            {'message_ids': [str(self.msg1.id), str(self.msg2.id)]}
        )
        self.assertEqual(resp.status_code, 200)
        data = resp.json()
        self.assertTrue(data['success'])
        self.assertEqual(data['deleted'], 2)
        self.msg1.refresh_from_db()
        self.msg2.refresh_from_db()
        self.assertTrue(self.msg1.is_deleted)
        self.assertTrue(self.msg2.is_deleted)

    def test_bulk_delete_success_json(self):
        self.client.force_login(self.admin)
        resp = self.client.post(
            self.url,
            data=json.dumps({'message_ids': [str(self.msg1.id), str(self.msg2.id)]}),
            content_type='application/json'
        )
        self.assertEqual(resp.status_code, 200)
        data = resp.json()
        self.assertTrue(data['success'])
        self.assertEqual(data['deleted'], 2)

    def test_bulk_delete_no_ids(self):
        self.client.force_login(self.admin)
        resp = self.client.post(self.url)
        self.assertEqual(resp.status_code, 400)

    def test_non_admin_rejected(self):
        self.client.force_login(self.user)
        resp = self.client.post(self.url)
        self.assertEqual(resp.status_code, 302)


class AdminPhotoSwapTests(TestCase):
    """Tests for PhotoSwap admin approve/reject."""

    def setUp(self):
        self.client = Client()
        self.admin = User.objects.create_superuser(username='admin', password='testpass123', email='a@test.com')
        self.user = User.objects.create_user(username='alice', password='testpass123')
        self.other = User.objects.create_user(username='bob', password='testpass123')
        self.conv = Conversation.objects.create(participant1=self.user, participant2=self.other)
        att = Attachment.objects.create(
            file=SimpleUploadedFile('a.png', b'x', content_type='image/png'),
            attachment_type='image', filename='a.png', file_size=1, mime_type='image/png'
        )
        self.msg = Message.objects.create(
            conversation=self.conv, sender=self.user, attachment=att,
            is_photo_swap=True, photo_swap_status='pending'
        )
        self.approve_url = reverse('admin_photo_swap_approve', args=[self.msg.id])
        self.reject_url = reverse('admin_photo_swap_reject', args=[self.msg.id])

    def test_approve_changes_status(self):
        self.client.force_login(self.admin)
        resp = self.client.post(self.approve_url)
        self.assertEqual(resp.status_code, 200)
        self.msg.refresh_from_db()
        self.assertEqual(self.msg.photo_swap_status, 'approved')

    def test_reject_changes_status(self):
        self.client.force_login(self.admin)
        resp = self.client.post(self.reject_url)
        self.assertEqual(resp.status_code, 200)
        self.msg.refresh_from_db()
        self.assertEqual(self.msg.photo_swap_status, 'rejected')

    def test_approve_non_post_rejected(self):
        self.client.force_login(self.admin)
        resp = self.client.get(self.approve_url)
        self.assertEqual(resp.status_code, 405)

    def test_reject_non_post_rejected(self):
        self.client.force_login(self.admin)
        resp = self.client.get(self.reject_url)
        self.assertEqual(resp.status_code, 405)

    def test_approve_creates_log(self):
        self.client.force_login(self.admin)
        self.client.post(self.approve_url)
        self.assertTrue(AdminLog.objects.filter(action_type='delete_message').exists())

    def test_non_admin_redirected(self):
        self.client.force_login(self.user)
        resp = self.client.post(self.approve_url)
        self.assertEqual(resp.status_code, 302)


class AdminUserEditTests(TestCase):
    """Tests for admin user editing and deletion."""

    def setUp(self):
        self.client = Client()
        self.admin = User.objects.create_superuser(username='admin', password='testpass123', email='a@test.com')
        self.target = User.objects.create_user(username='victim', password='testpass123')

    def test_edit_user(self):
        self.client.force_login(self.admin)
        url = reverse('admin_edit_user', args=[self.target.id])
        resp = self.client.post(url, {'username': 'renamed', 'role': 'staff'})
        self.assertEqual(resp.status_code, 200)
        self.target.refresh_from_db()
        self.assertEqual(self.target.username, 'renamed')
        self.assertTrue(self.target.is_staff)

    def test_delete_user(self):
        self.client.force_login(self.admin)
        url = reverse('admin_delete_user', args=[self.target.id])
        resp = self.client.post(url)
        self.assertEqual(resp.status_code, 200)
        self.assertFalse(User.objects.filter(id=self.target.id).exists())

    def test_cannot_delete_self(self):
        self.client.force_login(self.admin)
        url = reverse('admin_delete_user', args=[self.admin.id])
        resp = self.client.post(url)
        self.assertEqual(resp.status_code, 400)


class AdminMessageDeleteTests(TestCase):
    """Tests for admin single message delete."""

    def setUp(self):
        self.client = Client()
        self.admin = User.objects.create_superuser(username='admin', password='testpass123', email='a@test.com')
        self.user = User.objects.create_user(username='alice', password='testpass123')
        self.other = User.objects.create_user(username='bob', password='testpass123')
        self.conv = Conversation.objects.create(participant1=self.user, participant2=self.other)
        self.msg = Message.objects.create(conversation=self.conv, sender=self.user, text='Hello')
        self.url = reverse('admin_delete_message', args=[self.msg.id])

    def test_delete_message(self):
        self.client.force_login(self.admin)
        resp = self.client.post(self.url)
        self.assertEqual(resp.status_code, 200)
        self.msg.refresh_from_db()
        self.assertTrue(self.msg.is_deleted)

    def test_non_admin_redirected(self):
        self.client.force_login(self.user)
        resp = self.client.post(self.url)
        self.assertEqual(resp.status_code, 302)


class ProfileViewTests(TestCase):
    """Tests for profile view."""

    def setUp(self):
        self.client = Client()
        self.user = User.objects.create_user(username='alice', password='testpass123')
        self.url = reverse('profile')

    def test_get_profile(self):
        self.client.force_login(self.user)
        resp = self.client.get(self.url)
        self.assertEqual(resp.status_code, 200)

    def test_update_profile(self):
        self.client.force_login(self.user)
        resp = self.client.post(self.url, {
            'first_name': 'Alice',
            'last_name': 'Smith',
            'bio': 'Hello world',
            'theme': 'dark',
        })
        self.assertEqual(resp.status_code, 302)
        self.user.refresh_from_db()
        self.assertEqual(self.user.first_name, 'Alice')
        profile = self.user.profile
        self.assertEqual(profile.bio, 'Hello world')
        self.assertEqual(profile.theme_preference, 'dark')


class ConversationThemeTests(TestCase):
    """Tests for conversation theme API."""

    def setUp(self):
        self.client = Client()
        self.user = User.objects.create_user(username='alice', password='testpass123')
        self.other = User.objects.create_user(username='bob', password='testpass123')
        self.conv = Conversation.objects.create(participant1=self.user, participant2=self.other)

    def test_get_theme(self):
        self.client.force_login(self.user)
        url = reverse('get_conversation_theme', args=[self.conv.id])
        resp = self.client.get(url)
        self.assertEqual(resp.status_code, 200)
        data = resp.json()
        self.assertEqual(data['theme']['preset'], 'default')

    def test_set_theme(self):
        self.client.force_login(self.user)
        url = reverse('set_conversation_theme', args=[self.conv.id])
        resp = self.client.post(url, {
            'preset': 'dark',
            'bg_color': '#000',
        })
        self.assertEqual(resp.status_code, 200)
        theme = ConversationTheme.objects.get(user=self.user, conversation=self.conv)
        self.assertEqual(theme.preset, 'dark')

    def test_reset_theme(self):
        ConversationTheme.objects.create(user=self.user, conversation=self.conv, preset='dark')
        self.client.force_login(self.user)
        url = reverse('reset_conversation_theme', args=[self.conv.id])
        resp = self.client.post(url)
        self.assertEqual(resp.status_code, 200)
        self.assertFalse(ConversationTheme.objects.filter(user=self.user, conversation=self.conv).exists())
        data = resp.json()
        self.assertEqual(data['theme']['preset'], 'default')
