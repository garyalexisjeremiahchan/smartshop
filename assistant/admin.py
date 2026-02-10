from django.contrib import admin
from .models import Conversation, Message, ConversationContext


@admin.register(Conversation)
class ConversationAdmin(admin.ModelAdmin):
    list_display = ['conversation_id', 'user', 'session_key', 'total_messages', 'last_activity', 'created_at']
    list_filter = ['created_at', 'last_activity']
    search_fields = ['conversation_id', 'user__username', 'session_key']
    readonly_fields = ['conversation_id', 'created_at', 'updated_at']


@admin.register(Message)
class MessageAdmin(admin.ModelAdmin):
    list_display = ['id', 'conversation', 'role', 'content_preview', 'created_at']
    list_filter = ['role', 'created_at']
    search_fields = ['content', 'conversation__conversation_id']
    readonly_fields = ['created_at']
    
    def content_preview(self, obj):
        return obj.content[:100] + '...' if len(obj.content) > 100 else obj.content
    content_preview.short_description = 'Content'


@admin.register(ConversationContext)
class ConversationContextAdmin(admin.ModelAdmin):
    list_display = ['conversation', 'page_type', 'product_id', 'category_slug', 'created_at']
    list_filter = ['page_type', 'created_at']
    search_fields = ['conversation__conversation_id', 'category_slug', 'search_query']
    readonly_fields = ['created_at']
