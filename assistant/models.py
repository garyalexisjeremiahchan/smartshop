from django.db import models
from django.contrib.auth.models import User
from django.utils import timezone


class Conversation(models.Model):
    """Track assistant conversations for continuity and logging"""
    conversation_id = models.CharField(max_length=100, unique=True, db_index=True)
    user = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True, related_name='assistant_conversations')
    session_key = models.CharField(max_length=40, blank=True, help_text='Session ID for anonymous users')
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    # Metadata
    total_messages = models.PositiveIntegerField(default=0)
    last_activity = models.DateTimeField(default=timezone.now)
    
    class Meta:
        ordering = ['-updated_at']
        indexes = [
            models.Index(fields=['conversation_id']),
            models.Index(fields=['user', '-updated_at']),
            models.Index(fields=['session_key', '-updated_at']),
        ]
    
    def __str__(self):
        user_id = self.user.username if self.user else f"Session: {self.session_key[:8]}"
        return f"Conversation {self.conversation_id} - {user_id}"


class Message(models.Model):
    """Store individual messages in a conversation"""
    ROLE_CHOICES = [
        ('user', 'User'),
        ('assistant', 'Assistant'),
        ('system', 'System'),
        ('tool', 'Tool'),
    ]
    
    conversation = models.ForeignKey(Conversation, on_delete=models.CASCADE, related_name='messages')
    role = models.CharField(max_length=20, choices=ROLE_CHOICES)
    content = models.TextField()
    
    # For tool calls/results
    tool_call_id = models.CharField(max_length=100, blank=True)
    tool_name = models.CharField(max_length=100, blank=True)
    
    # Metadata
    created_at = models.DateTimeField(auto_now_add=True)
    tokens_used = models.PositiveIntegerField(default=0, help_text='Tokens consumed by this message')
    
    class Meta:
        ordering = ['created_at']
        indexes = [
            models.Index(fields=['conversation', 'created_at']),
        ]
    
    def __str__(self):
        return f"{self.role}: {self.content[:50]}..."


class ConversationContext(models.Model):
    """Store page context for conversations"""
    conversation = models.ForeignKey(Conversation, on_delete=models.CASCADE, related_name='contexts')
    
    # Page context
    page_url = models.CharField(max_length=500, blank=True)
    page_type = models.CharField(max_length=50, blank=True, help_text='e.g., product_detail, category, cart, search')
    product_id = models.PositiveIntegerField(null=True, blank=True)
    category_slug = models.CharField(max_length=200, blank=True)
    search_query = models.CharField(max_length=255, blank=True)
    
    # Cart summary
    cart_item_count = models.PositiveIntegerField(default=0)
    cart_total = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True)
    
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        ordering = ['-created_at']
    
    def __str__(self):
        return f"Context for {self.conversation.conversation_id} - {self.page_type}"
