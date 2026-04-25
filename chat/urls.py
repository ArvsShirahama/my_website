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
    
    # Admin Dashboard
    path('admin/dashboard/', views_admin.admin_dashboard, name='admin_dashboard'),
    path('admin/users/', views_admin.admin_users, name='admin_users'),
    path('admin/messages/', views_admin.admin_messages, name='admin_messages'),
    path('admin/conversations/', views_admin.admin_conversations, name='admin_conversations'),
    path('admin/logs/', views_admin.admin_logs, name='admin_logs'),
    
    # Admin API
    path('admin/api/delete-user/<int:user_id>/', views_admin.admin_delete_user, name='admin_delete_user'),
    path('admin/api/delete-message/<uuid:message_id>/', views_admin.admin_delete_message, name='admin_delete_message'),
]
