from django.urls import path
from . import views_chat, views_auth, views_admin

urlpatterns = [
    # Auth
    path('register/', views_auth.register_view, name='register'),
    path('login/', views_auth.login_view, name='login'),
    path('logout/', views_auth.logout_view, name='logout'),
    
    # Profile
    path('profile/', views_auth.profile_view, name='profile'),
    
    # Chat
    path('', views_chat.chat_list, name='chat_list'),
    path('conversation/<uuid:conversation_id>/', views_chat.chat_conversation, name='chat_conversation'),
    path('start/<int:user_id>/', views_chat.start_conversation, name='start_conversation'),
    
    # API
    path('api/send/<uuid:conversation_id>/', views_chat.send_message, name='send_message'),
    path('api/messages/<uuid:conversation_id>/', views_chat.get_messages, name='get_messages'),
    path('api/delete-message/<uuid:message_id>/', views_chat.delete_message, name='delete_message'),
    path('api/view-once/consume/<uuid:message_id>/', views_chat.consume_view_once_media, name='consume_view_once_media'),
    path('api/attachment/<uuid:attachment_id>/', views_chat.serve_attachment, name='serve_attachment'),
    path('api/theme/<uuid:conversation_id>/', views_chat.get_conversation_theme, name='get_conversation_theme'),
    path('api/theme/<uuid:conversation_id>/set/', views_chat.set_conversation_theme, name='set_conversation_theme'),
    path('api/theme/<uuid:conversation_id>/reset/', views_chat.reset_conversation_theme, name='reset_conversation_theme'),
    
    # Admin Dashboard
    path('admin/dashboard/', views_admin.admin_dashboard, name='admin_dashboard'),
    path('admin/users/', views_admin.admin_users, name='admin_users'),
    path('admin/users/edit/<int:user_id>/', views_admin.admin_edit_user, name='admin_edit_user'),
    path('admin/users/delete/<int:user_id>/', views_admin.admin_delete_user, name='admin_delete_user'),
    path('admin/messages/', views_admin.admin_messages, name='admin_messages'),
    path('admin/messages/delete/<uuid:message_id>/', views_admin.admin_delete_message, name='admin_delete_message'),
    path('admin/api/bulk-delete-messages/', views_admin.admin_bulk_delete_messages, name='admin_bulk_delete_messages'),
    path('admin/conversations/', views_admin.admin_conversations, name='admin_conversations'),
    path('admin/conversations/<uuid:conversation_id>/', views_admin.admin_conversation_detail, name='admin_conversation_detail'),
    path('admin/logs/', views_admin.admin_logs, name='admin_logs'),
    path('admin/documents/', views_admin.admin_documents, name='admin_documents'),
    path('admin/documents/<uuid:doc_id>/', views_admin.admin_serve_document, name='admin_serve_document'),
    path('admin/documents/delete/<uuid:doc_id>/', views_admin.admin_delete_document, name='admin_delete_document'),
    path('admin/photoswap/', views_admin.admin_photo_swap_queue, name='admin_photo_swap_queue'),
    path('admin/photoswap/detail/<uuid:message_id>/', views_admin.admin_photo_swap_detail, name='admin_photo_swap_detail'),
    path('admin/photoswap/approve/<uuid:message_id>/', views_admin.admin_photo_swap_approve, name='admin_photo_swap_approve'),
    path('admin/photoswap/reject/<uuid:message_id>/', views_admin.admin_photo_swap_reject, name='admin_photo_swap_reject'),
    
    # Admin API
    path('admin/api/delete-user/<int:user_id>/', views_admin.admin_delete_user, name='admin_delete_user'),
    path('admin/api/delete-message/<uuid:message_id>/', views_admin.admin_delete_message, name='admin_delete_message'),
]
