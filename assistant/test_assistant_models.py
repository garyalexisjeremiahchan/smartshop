"""
Unit Tests for Virtual Shopping Assistant Models

This module contains comprehensive unit tests for the assistant application models:
- Conversation model
- Message model
- ConversationContext model

Test Categories:
1. Model Creation Tests
2. Model Validation Tests
3. Model Relationship Tests
4. Model Method Tests
5. Model Query Tests

Running Tests:
    python manage.py test assistant.test_assistant_models -v 2
"""

from django.test import TestCase
from django.contrib.auth.models import User
from django.utils import timezone
from datetime import timedelta
from assistant.models import Conversation, Message, ConversationContext
import uuid


class ConversationModelTests(TestCase):
    """
    Test Case: Conversation Model
    
    Tests the Conversation model including creation, validation,
    relationships, and custom methods.
    """
    
    def setUp(self):
        """Set up test data before each test"""
        self.user = User.objects.create_user(
            username='testuser',
            email='test@example.com',
            password='testpass123'
        )
    
    def test_conversation_creation_with_user(self):
        """Test creating a conversation for authenticated user"""
        conversation = Conversation.objects.create(
            conversation_id=str(uuid.uuid4()),
            user=self.user
        )
        
        self.assertIsNotNone(conversation)
        self.assertEqual(conversation.user, self.user)
        self.assertEqual(conversation.total_messages, 0)
        self.assertIsNotNone(conversation.created_at)
    
    def test_conversation_creation_with_session(self):
        """Test creating a conversation for anonymous user with session"""
        session_key = 'test_session_12345'
        conversation = Conversation.objects.create(
            conversation_id=str(uuid.uuid4()),
            session_key=session_key
        )
        
        self.assertIsNotNone(conversation)
        self.assertIsNone(conversation.user)
        self.assertEqual(conversation.session_key, session_key)
    
    def test_conversation_unique_conversation_id(self):
        """Test that conversation_id must be unique"""
        conv_id = str(uuid.uuid4())
        Conversation.objects.create(
            conversation_id=conv_id,
            user=self.user
        )
        
        # Try to create another with same ID
        with self.assertRaises(Exception):
            Conversation.objects.create(
                conversation_id=conv_id,
                user=self.user
            )
    
    def test_conversation_str_method_with_user(self):
        """Test string representation of conversation with user"""
        conversation = Conversation.objects.create(
            conversation_id='test-conv-123',
            user=self.user
        )
        
        str_repr = str(conversation)
        self.assertIn('test-conv-123', str_repr)
        self.assertIn('testuser', str_repr)
    
    def test_conversation_str_method_with_session(self):
        """Test string representation of conversation with session only"""
        conversation = Conversation.objects.create(
            conversation_id='test-conv-456',
            session_key='session123456789'
        )
        
        str_repr = str(conversation)
        self.assertIn('test-conv-456', str_repr)
        self.assertIn('Session:', str_repr)
    
    def test_conversation_default_values(self):
        """Test that conversation has correct default values"""
        conversation = Conversation.objects.create(
            conversation_id=str(uuid.uuid4())
        )
        
        self.assertEqual(conversation.total_messages, 0)
        self.assertIsNotNone(conversation.last_activity)
        self.assertIsNone(conversation.user)
        self.assertEqual(conversation.session_key, '')
    
    def test_conversation_ordering(self):
        """Test that conversations are ordered by updated_at descending"""
        # Create multiple conversations with different timestamps
        conv1 = Conversation.objects.create(
            conversation_id='conv-1',
            user=self.user
        )
        conv2 = Conversation.objects.create(
            conversation_id='conv-2',
            user=self.user
        )
        
        # Update conv1 to be more recent
        conv1.total_messages = 5
        conv1.save()
        
        conversations = list(Conversation.objects.all())
        self.assertEqual(conversations[0], conv1)
        self.assertEqual(conversations[1], conv2)
    
    def test_conversation_user_deletion_sets_null(self):
        """Test that deleting user sets conversation.user to NULL"""
        conversation = Conversation.objects.create(
            conversation_id=str(uuid.uuid4()),
            user=self.user
        )
        
        user_id = self.user.id
        self.user.delete()
        
        conversation.refresh_from_db()
        self.assertIsNone(conversation.user)


class MessageModelTests(TestCase):
    """
    Test Case: Message Model
    
    Tests the Message model including creation, validation,
    and relationships with conversations.
    """
    
    def setUp(self):
        """Set up test data before each test"""
        self.conversation = Conversation.objects.create(
            conversation_id=str(uuid.uuid4())
        )
    
    def test_message_creation_user_role(self):
        """Test creating a user message"""
        message = Message.objects.create(
            conversation=self.conversation,
            role='user',
            content='Hello, I need help finding a laptop'
        )
        
        self.assertIsNotNone(message)
        self.assertEqual(message.role, 'user')
        self.assertEqual(message.content, 'Hello, I need help finding a laptop')
        self.assertIsNotNone(message.created_at)
    
    def test_message_creation_assistant_role(self):
        """Test creating an assistant message"""
        message = Message.objects.create(
            conversation=self.conversation,
            role='assistant',
            content="I'd be happy to help you find a laptop!"
        )
        
        self.assertEqual(message.role, 'assistant')
        self.assertIsNotNone(message.content)
    
    def test_message_creation_tool_role(self):
        """Test creating a tool message with tool metadata"""
        message = Message.objects.create(
            conversation=self.conversation,
            role='tool',
            content='{"products": []}',
            tool_call_id='call_abc123',
            tool_name='search_products'
        )
        
        self.assertEqual(message.role, 'tool')
        self.assertEqual(message.tool_call_id, 'call_abc123')
        self.assertEqual(message.tool_name, 'search_products')
    
    def test_message_conversation_relationship(self):
        """Test that messages are correctly linked to conversation"""
        Message.objects.create(
            conversation=self.conversation,
            role='user',
            content='Message 1'
        )
        Message.objects.create(
            conversation=self.conversation,
            role='assistant',
            content='Message 2'
        )
        
        messages = self.conversation.messages.all()
        self.assertEqual(messages.count(), 2)
    
    def test_message_cascade_delete(self):
        """Test that deleting conversation deletes associated messages"""
        Message.objects.create(
            conversation=self.conversation,
            role='user',
            content='Test message'
        )
        
        conversation_id = self.conversation.id
        self.conversation.delete()
        
        messages = Message.objects.filter(conversation_id=conversation_id)
        self.assertEqual(messages.count(), 0)
    
    def test_message_ordering_by_created_at(self):
        """Test that messages are ordered by creation time"""
        msg1 = Message.objects.create(
            conversation=self.conversation,
            role='user',
            content='First message'
        )
        msg2 = Message.objects.create(
            conversation=self.conversation,
            role='assistant',
            content='Second message'
        )
        
        messages = list(self.conversation.messages.all())
        self.assertEqual(messages[0], msg1)
        self.assertEqual(messages[1], msg2)
    
    def test_message_role_choices_validation(self):
        """Test that message role is validated against choices"""
        message = Message.objects.create(
            conversation=self.conversation,
            role='user',  # Valid choice
            content='Test'
        )
        self.assertEqual(message.role, 'user')


class ConversationContextModelTests(TestCase):
    """
    Test Case: ConversationContext Model
    
    Tests the ConversationContext model which stores page context
    for each message in a conversation.
    """
    
    def setUp(self):
        """Set up test data before each test"""
        self.conversation = Conversation.objects.create(
            conversation_id=str(uuid.uuid4())
        )
    
    def test_context_creation_with_product_page(self):
        """Test creating context for product detail page"""
        context = ConversationContext.objects.create(
            conversation=self.conversation,
            page_url='/product/laptop-123/',
            page_type='product_detail',
            product_id=123,
            category_slug='electronics'
        )
        
        self.assertIsNotNone(context)
        self.assertEqual(context.page_type, 'product_detail')
        self.assertEqual(context.product_id, 123)
        self.assertEqual(context.category_slug, 'electronics')
    
    def test_context_creation_with_category_page(self):
        """Test creating context for category page"""
        context = ConversationContext.objects.create(
            conversation=self.conversation,
            page_url='/category/electronics/',
            page_type='category',
            category_slug='electronics'
        )
        
        self.assertEqual(context.page_type, 'category')
        self.assertEqual(context.category_slug, 'electronics')
        self.assertIsNone(context.product_id)
    
    def test_context_creation_with_search_page(self):
        """Test creating context for search results page"""
        context = ConversationContext.objects.create(
            conversation=self.conversation,
            page_url='/search/?q=laptop',
            page_type='search',
            search_query='laptop'
        )
        
        self.assertEqual(context.page_type, 'search')
        self.assertEqual(context.search_query, 'laptop')
    
    def test_context_with_cart_information(self):
        """Test creating context with cart information"""
        context = ConversationContext.objects.create(
            conversation=self.conversation,
            page_url='/cart/',
            page_type='cart',
            cart_item_count=3,
            cart_total=199.99
        )
        
        self.assertEqual(context.cart_item_count, 3)
        self.assertEqual(context.cart_total, 199.99)
    
    def test_context_cascade_delete(self):
        """Test that deleting conversation deletes associated contexts"""
        ConversationContext.objects.create(
            conversation=self.conversation,
            page_url='/test/',
            page_type='home'
        )
        
        conversation_id = self.conversation.id
        self.conversation.delete()
        
        contexts = ConversationContext.objects.filter(conversation_id=conversation_id)
        self.assertEqual(contexts.count(), 0)
    
    def test_context_default_values(self):
        """Test that context has correct default values"""
        context = ConversationContext.objects.create(
            conversation=self.conversation,
            page_url='/test/'
        )
        
        self.assertEqual(context.page_type, '')
        self.assertIsNone(context.product_id)
        self.assertEqual(context.category_slug, '')
        self.assertEqual(context.search_query, '')
        self.assertEqual(context.cart_item_count, 0)
        self.assertIsNone(context.cart_total)


class ConversationQueryTests(TestCase):
    """
    Test Case: Conversation Queries
    
    Tests complex queries and filtering on the Conversation model.
    """
    
    def setUp(self):
        """Set up test data before each test"""
        self.user1 = User.objects.create_user(
            username='user1',
            password='pass123'
        )
        self.user2 = User.objects.create_user(
            username='user2',
            password='pass123'
        )
    
    def test_query_conversations_by_user(self):
        """Test querying conversations for specific user"""
        conv1 = Conversation.objects.create(
            conversation_id='conv-user1-1',
            user=self.user1
        )
        conv2 = Conversation.objects.create(
            conversation_id='conv-user1-2',
            user=self.user1
        )
        Conversation.objects.create(
            conversation_id='conv-user2-1',
            user=self.user2
        )
        
        user1_convs = Conversation.objects.filter(user=self.user1)
        self.assertEqual(user1_convs.count(), 2)
        self.assertIn(conv1, user1_convs)
        self.assertIn(conv2, user1_convs)
    
    def test_query_conversations_by_session(self):
        """Test querying conversations for anonymous session"""
        session_key = 'test_session_123'
        conv = Conversation.objects.create(
            conversation_id='conv-session-1',
            session_key=session_key
        )
        
        session_convs = Conversation.objects.filter(session_key=session_key)
        self.assertEqual(session_convs.count(), 1)
        self.assertEqual(session_convs.first(), conv)
    
    def test_query_recent_conversations(self):
        """Test querying conversations by last activity"""
        old_conv = Conversation.objects.create(
            conversation_id='old-conv',
            user=self.user1
        )
        # Update last_activity to be old
        Conversation.objects.filter(id=old_conv.id).update(
            last_activity=timezone.now() - timedelta(days=30)
        )
        
        new_conv = Conversation.objects.create(
            conversation_id='new-conv',
            user=self.user1
        )
        
        # Get conversations from last 7 days
        week_ago = timezone.now() - timedelta(days=7)
        recent_convs = Conversation.objects.filter(
            user=self.user1,
            last_activity__gte=week_ago
        )
        
        self.assertEqual(recent_convs.count(), 1)
        self.assertEqual(recent_convs.first(), new_conv)
    
    def test_query_conversations_with_message_count(self):
        """Test filtering conversations by message count"""
        active_conv = Conversation.objects.create(
            conversation_id='active-conv',
            user=self.user1,
            total_messages=10
        )
        empty_conv = Conversation.objects.create(
            conversation_id='empty-conv',
            user=self.user1,
            total_messages=0
        )
        
        active_convs = Conversation.objects.filter(
            user=self.user1,
            total_messages__gt=0
        )
        
        self.assertEqual(active_convs.count(), 1)
        self.assertEqual(active_convs.first(), active_conv)
