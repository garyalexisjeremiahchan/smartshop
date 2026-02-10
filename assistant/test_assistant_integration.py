"""
Integration Tests for Virtual Shopping Assistant

This module contains integration tests that verify the complete workflow
of the Virtual Shopping Assistant, including view integration, chat conversations,
and end-to-end scenarios.

Test Categories:
1. Chat Endpoint Integration Tests
2. Tool Execution Integration Tests
3. Conversation Flow Tests
4. End-to-End Workflow Tests
5. Rate Limiting Tests
6. Session Management Tests

Running Tests:
    python manage.py test assistant.test_assistant_integration -v 2
"""

from django.test import TestCase, Client
from django.urls import reverse
from django.contrib.auth.models import User
from django.core.cache import cache
from unittest.mock import patch, MagicMock
from assistant.models import Conversation, Message, ConversationContext
from assistant.services import AssistantService
from store.models import Product, Category
from decimal import Decimal
import json


class ChatEndpointIntegrationTests(TestCase):
    """
    Test Case: Chat Endpoint Integration
    
    Tests the /assistant/chat/ endpoint with various scenarios
    """
    
    def setUp(self):
        """Set up test data"""
        self.client = Client()
        self.user = User.objects.create_user(
            username='testuser',
            email='test@example.com',
            password='testpass123'
        )
        
        # Create test product
        self.category = Category.objects.create(
            name='Electronics',
            slug='electronics',
            is_active=True
        )
        self.product = Product.objects.create(
            category=self.category,
            name='Test Laptop',
            slug='test-laptop',
            description='High-performance laptop',
            price=Decimal('999.99'),
            stock=10,
            is_active=True
        )
    
    def test_chat_endpoint_requires_post(self):
        """Test that chat endpoint only accepts POST requests"""
        response = self.client.get('/assistant/chat/')
        self.assertEqual(response.status_code, 405)  # Method not allowed
    
    def test_chat_endpoint_requires_message(self):
        """Test that chat endpoint requires a message"""
        response = self.client.post(
            '/assistant/chat/',
            data=json.dumps({'message': ''}),
            content_type='application/json'
        )
        
        self.assertEqual(response.status_code, 400)
        data = response.json()
        self.assertIn('error', data)
    
    @patch.object(AssistantService, 'chat')
    def test_chat_endpoint_creates_conversation(self, mock_chat):
        """Test that chat endpoint creates conversation"""
        mock_chat.return_value = {
            'reply': 'Hello! How can I help you?',
            'cards': [],
            'suggestions': []
        }
        
        response = self.client.post(
            '/assistant/chat/',
            data=json.dumps({
                'message': 'Hello',
                'page_context': {}
            }),
            content_type='application/json'
        )
        
        self.assertEqual(response.status_code, 200)
        data = response.json()
        
        # Check conversation was created
        self.assertIn('conversation_id', data)
        self.assertTrue(Conversation.objects.filter(
            conversation_id=data['conversation_id']
        ).exists())
    
    @patch.object(AssistantService, 'chat')
    def test_chat_endpoint_stores_messages(self, mock_chat):
        """Test that messages are stored in database"""
        mock_chat.return_value = {
            'reply': 'Test response',
            'cards': [],
            'suggestions': []
        }
        
        response = self.client.post(
            '/assistant/chat/',
            data=json.dumps({
                'message': 'Test message',
                'page_context': {}
            }),
            content_type='application/json'
        )
        
        data = response.json()
        conversation = Conversation.objects.get(
            conversation_id=data['conversation_id']
        )
        
        # Should have user message and assistant message
        self.assertEqual(conversation.messages.count(), 2)
        self.assertEqual(conversation.total_messages, 2)
    
    @patch.object(AssistantService, 'chat')
    def test_chat_endpoint_with_page_context(self, mock_chat):
        """Test that page context is stored"""
        mock_chat.return_value = {
            'reply': 'Response',
            'cards': [],
            'suggestions': []
        }
        
        page_context = {
            'page_url': '/product/test-laptop/',
            'page_type': 'product_detail',
            'product_id': self.product.id,
            'category': 'electronics'
        }
        
        response = self.client.post(
            '/assistant/chat/',
            data=json.dumps({
                'message': 'Tell me about this product',
                'page_context': page_context
            }),
            content_type='application/json'
        )
        
        data = response.json()
        conversation = Conversation.objects.get(
            conversation_id=data['conversation_id']
        )
        
        # Check context was stored
        context = ConversationContext.objects.filter(
            conversation=conversation
        ).first()
        self.assertIsNotNone(context)
        self.assertEqual(context.page_type, 'product_detail')
        self.assertEqual(context.product_id, self.product.id)
    
    @patch.object(AssistantService, 'chat')
    def test_chat_endpoint_continues_conversation(self, mock_chat):
        """Test continuing an existing conversation"""
        mock_chat.return_value = {
            'reply': 'Response',
            'cards': [],
            'suggestions': []
        }
        
        # First message
        response1 = self.client.post(
            '/assistant/chat/',
            data=json.dumps({
                'message': 'First message',
                'page_context': {}
            }),
            content_type='application/json'
        )
        data1 = response1.json()
        conv_id = data1['conversation_id']
        
        # Second message with same conversation
        response2 = self.client.post(
            '/assistant/chat/',
            data=json.dumps({
                'message': 'Second message',
                'conversation_id': conv_id,
                'page_context': {}
            }),
            content_type='application/json'
        )
        
        conversation = Conversation.objects.get(conversation_id=conv_id)
        
        # Should have 4 messages (2 user + 2 assistant)
        self.assertEqual(conversation.messages.count(), 4)
        self.assertEqual(conversation.total_messages, 4)
    
    def test_chat_endpoint_handles_invalid_json(self):
        """Test handling of invalid JSON"""
        response = self.client.post(
            '/assistant/chat/',
            data='invalid json',
            content_type='application/json'
        )
        
        self.assertEqual(response.status_code, 400)


class RateLimitingIntegrationTests(TestCase):
    """
    Test Case: Rate Limiting Integration
    
    Tests the rate limiting functionality
    """
    
    def setUp(self):
        """Set up test data"""
        self.client = Client()
        cache.clear()
    
    @patch.object(AssistantService, 'chat')
    def test_rate_limiting_allows_requests_within_limit(self, mock_chat):
        """Test that requests within limit are allowed"""
        mock_chat.return_value = {
            'reply': 'Response',
            'cards': [],
            'suggestions': []
        }
        
        # Make 5 requests (well within 20 limit)
        for i in range(5):
            response = self.client.post(
                '/assistant/chat/',
                data=json.dumps({
                    'message': f'Message {i}',
                    'page_context': {}
                }),
                content_type='application/json'
            )
            self.assertEqual(response.status_code, 200)
    
    @patch.object(AssistantService, 'chat')
    def test_rate_limiting_blocks_excessive_requests(self, mock_chat):
        """Test that excessive requests are blocked after threshold"""
        mock_chat.return_value = {
            'reply': 'Response',
            'cards': [],
            'suggestions': []
        }
        
        # Make requests up to and beyond the limit
        client_ip = '192.168.1.100'
        
        # Initialize session by making a request first
        session = self.client.session
        session.save()
        
        for i in range(22):
            response = self.client.post(
                '/assistant/chat/',
                data=json.dumps({
                    'message': f'Message {i}',
                    'page_context': {}
                }),
                content_type='application/json',
                REMOTE_ADDR=client_ip
            )
            
            # Check status
            if i < 20:
                # First 20 should succeed
                self.assertEqual(response.status_code, 200, 
                    f"Request {i} should succeed, got {response.status_code}")
            else:
                # 21st and 22nd should be rate limited
                self.assertEqual(response.status_code, 429,
                    f"Request {i} should be rate limited, got {response.status_code}")
                if response.status_code == 429:
                    data = response.json()
                    self.assertIn('Rate limit', data['error'])


class ConversationFlowIntegrationTests(TestCase):
    """
    Test Case: Conversation Flow Integration
    
    Tests the complete conversation workflow including message history
    """
    
    def setUp(self):
        """Set up test data"""
        self.client = Client()
        
        # Create test products
        self.category = Category.objects.create(
            name='Electronics',
            slug='electronics',
            is_active=True
        )
        Product.objects.create(
            category=self.category,
            name='Laptop A',
            slug='laptop-a',
            description='Great laptop',
            price=Decimal('899.99'),
            stock=10,
            is_active=True
        )
    
    @patch.object(AssistantService, 'chat')
    def test_conversation_maintains_context(self, mock_chat):
        """Test that conversation context is maintained across messages"""
        mock_chat.return_value = {
            'reply': 'Response',
            'cards': [],
            'suggestions': []
        }
        
        # Start conversation
        response1 = self.client.post(
            '/assistant/chat/',
            data=json.dumps({
                'message': 'Show me laptops',
                'page_context': {}
            }),
            content_type='application/json'
        )
        conv_id = response1.json()['conversation_id']
        
        # Continue conversation
        response2 = self.client.post(
            '/assistant/chat/',
            data=json.dumps({
                'message': 'Add it to cart',
                'conversation_id': conv_id,
                'page_context': {}
            }),
            content_type='application/json'
        )
        
        # Check that assistant service was called with message history
        self.assertEqual(mock_chat.call_count, 2)
        
        # Second call should include previous messages
        second_call_args = mock_chat.call_args_list[1][0]
        messages = second_call_args[0]
        
        # Should have at least user's first message in history
        self.assertGreater(len(messages), 1)
    
    @patch.object(AssistantService, 'chat')
    def test_conversation_updates_last_activity(self, mock_chat):
        """Test that last_activity is updated with each message"""
        mock_chat.return_value = {
            'reply': 'Response',
            'cards': [],
            'suggestions': []
        }
        
        # Send first message
        response = self.client.post(
            '/assistant/chat/',
            data=json.dumps({
                'message': 'Hello',
                'page_context': {}
            }),
            content_type='application/json'
        )
        
        conv_id = response.json()['conversation_id']
        conversation = Conversation.objects.get(conversation_id=conv_id)
        first_activity = conversation.last_activity
        
        # Send second message
        self.client.post(
            '/assistant/chat/',
            data=json.dumps({
                'message': 'Another message',
                'conversation_id': conv_id,
                'page_context': {}
            }),
            content_type='application/json'
        )
        
        conversation.refresh_from_db()
        second_activity = conversation.last_activity
        
        # Last activity should be updated
        self.assertGreater(second_activity, first_activity)


class EndToEndWorkflowTests(TestCase):
    """
    Test Case: End-to-End Workflow
    
    Tests complete user scenarios from start to finish
    """
    
    def setUp(self):
        """Set up test data"""
        self.client = Client()
        
        # Create comprehensive test data
        self.category = Category.objects.create(
            name='Electronics',
            slug='electronics',
            is_active=True
        )
        
        self.laptop = Product.objects.create(
            category=self.category,
            name='Gaming Laptop',
            slug='gaming-laptop',
            description='High-performance gaming laptop',
            specifications='16GB RAM, RTX 3060',
            price=Decimal('1299.99'),
            stock=5,
            units_sold=50,
            is_active=True
        )
    
    @patch('assistant.services.OpenAI')
    def test_complete_product_search_workflow(self, mock_openai_class):
        """Test complete workflow: search -> details -> add to cart"""
        # Mock OpenAI responses
        mock_client = MagicMock()
        mock_openai_class.return_value = mock_client
        
        # Mock search response
        search_response = MagicMock()
        search_response.choices = [MagicMock()]
        search_response.choices[0].message.content = "I found a gaming laptop for you!"
        search_response.choices[0].message.tool_calls = [
            MagicMock(
                id='call_1',
                function=MagicMock(
                    name='search_products',
                    arguments='{"query": "laptop"}'
                )
            )
        ]
        
        # Final response after tool call
        final_response = MagicMock()
        final_response.choices = [MagicMock()]
        final_response.choices[0].message.content = "I found this laptop for you!"
        final_response.choices[0].message.tool_calls = None
        
        mock_client.chat.completions.create.side_effect = [
            search_response,
            final_response
        ]
        
        # User searches for laptop
        response = self.client.post(
            '/assistant/chat/',
            data=json.dumps({
                'message': 'I need a gaming laptop',
                'page_context': {
                    'page_url': '/',
                    'page_type': 'home'
                }
            }),
            content_type='application/json'
        )
        
        self.assertEqual(response.status_code, 200)
        data = response.json()
        
        # Should get a response
        self.assertIn('reply', data)
        self.assertIn('conversation_id', data)
        
        # Verify conversation and messages were created
        conversation = Conversation.objects.get(
            conversation_id=data['conversation_id']
        )
        self.assertGreater(conversation.messages.count(), 0)
    
    @patch.object(AssistantService, 'chat')
    def test_authenticated_user_session_management(self, mock_chat):
        """Test session management for authenticated users"""
        mock_chat.return_value = {
            'reply': 'Response',
            'cards': [],
            'suggestions': []
        }
        
        # Login user
        user = User.objects.create_user(
            username='testuser',
            password='pass123'
        )
        self.client.login(username='testuser', password='pass123')
        
        # Send message
        response = self.client.post(
            '/assistant/chat/',
            data=json.dumps({
                'message': 'Hello',
                'page_context': {}
            }),
            content_type='application/json'
        )
        
        conv_id = response.json()['conversation_id']
        conversation = Conversation.objects.get(conversation_id=conv_id)
        
        # Conversation should be linked to user
        self.assertEqual(conversation.user, user)
    
    @patch.object(AssistantService, 'chat')
    def test_anonymous_user_session_management(self, mock_chat):
        """Test session management for anonymous users"""
        mock_chat.return_value = {
            'reply': 'Response',
            'cards': [],
            'suggestions': []
        }
        
        # Don't login - use anonymous session
        response = self.client.post(
            '/assistant/chat/',
            data=json.dumps({
                'message': 'Hello',
                'page_context': {}
            }),
            content_type='application/json'
        )
        
        conv_id = response.json()['conversation_id']
        conversation = Conversation.objects.get(conversation_id=conv_id)
        
        # Conversation should not have a user
        self.assertIsNone(conversation.user)
        # But should have session_key if session exists
        # (Note: session_key might be empty in test environment)


class ToolExecutionIntegrationTests(TestCase):
    """
    Test Case: Tool Execution Integration
    
    Tests integration between services and tools
    """
    
    def setUp(self):
        """Set up test data"""
        self.category = Category.objects.create(
            name='Electronics',
            slug='electronics',
            is_active=True
        )
        
        Product.objects.create(
            category=self.category,
            name='Test Product',
            slug='test-product',
            description='Test description',
            price=Decimal('99.99'),
            stock=10,
            is_active=True
        )
    
    @patch('assistant.services.OpenAI')
    def test_service_executes_search_tool(self, mock_openai_class):
        """Test that service correctly executes search_products tool"""
        from django.test import RequestFactory
        
        # Mock OpenAI
        mock_client = MagicMock()
        mock_openai_class.return_value = mock_client
        
        # Mock tool call response
        tool_response = MagicMock()
        tool_response.choices = [MagicMock()]
        tool_response.choices[0].message.content = None
        tool_response.choices[0].message.tool_calls = [
            MagicMock(
                id='call_1',
                function=MagicMock(
                    name='search_products',
                    arguments='{"query": "test"}'
                )
            )
        ]
        
        # Final response
        final_response = MagicMock()
        final_response.choices = [MagicMock()]
        final_response.choices[0].message.content = "Found products!"
        final_response.choices[0].message.tool_calls = None
        
        mock_client.chat.completions.create.side_effect = [
            tool_response,
            final_response
        ]
        
        # Create request
        factory = RequestFactory()
        request = factory.get('/')
        
        # Execute service
        service = AssistantService(request=request)
        result = service.chat(
            [{'role': 'user', 'content': 'Search for test products'}],
            {}
        )
        
        # Should get a response
        self.assertIn('reply', result)
        self.assertEqual(result['reply'], "Found products!")


class ChatClearingTests(TestCase):
    """
    Test Case: Chat Clearing and Reset Functionality
    
    Tests the ability to clear chat and start new conversations
    """
    
    def setUp(self):
        """Set up test data"""
        self.client = Client()
        self.user = User.objects.create_user(
            username='testuser',
            email='test@example.com',
            password='testpass123'
        )
        
        # Create test category and product
        self.category = Category.objects.create(
            name='Electronics',
            slug='electronics',
            is_active=True
        )
        
        self.product = Product.objects.create(
            name='Test Laptop',
            slug='test-laptop',
            description='A test laptop',
            price=Decimal('999.99'),
            category=self.category,
            stock=10,
            is_active=True
        )
    
    @patch('assistant.services.OpenAI')
    def test_starting_new_conversation_without_id(self, mock_openai_class):
        """Test that a new conversation can be started without conversation_id"""
        # Mock OpenAI response
        mock_client = MagicMock()
        mock_openai_class.return_value = mock_client
        
        mock_response = MagicMock()
        mock_response.choices = [MagicMock()]
        mock_response.choices[0].message.content = "Hello! How can I help?"
        mock_response.choices[0].message.tool_calls = None
        mock_client.chat.completions.create.return_value = mock_response
        
        # Send message without conversation_id (simulates cleared chat)
        response = self.client.post(
            '/assistant/chat/',
            data=json.dumps({
                'message': 'Hello',
                'page_context': {}
            }),
            content_type='application/json'
        )
        
        self.assertEqual(response.status_code, 200)
        data = response.json()
        
        # Should receive a new conversation_id
        self.assertIn('conversation_id', data)
        self.assertIsNotNone(data['conversation_id'])
        
        # Should create a new conversation in database
        self.assertEqual(Conversation.objects.count(), 1)
        conversation = Conversation.objects.first()
        self.assertEqual(conversation.total_messages, 2)  # user + assistant
    
    @patch('assistant.services.OpenAI')
    def test_multiple_conversations_created_separately(self, mock_openai_class):
        """Test that clearing and restarting creates separate conversations"""
        # Mock OpenAI response
        mock_client = MagicMock()
        mock_openai_class.return_value = mock_client
        
        mock_response = MagicMock()
        mock_response.choices = [MagicMock()]
        mock_response.choices[0].message.content = "Response"
        mock_response.choices[0].message.tool_calls = None
        mock_client.chat.completions.create.return_value = mock_response
        
        # First conversation
        response1 = self.client.post(
            '/assistant/chat/',
            data=json.dumps({
                'message': 'First message',
                'page_context': {}
            }),
            content_type='application/json'
        )
        
        conversation_id_1 = response1.json()['conversation_id']
        
        # Second conversation (simulating cleared chat - no conversation_id)
        response2 = self.client.post(
            '/assistant/chat/',
            data=json.dumps({
                'message': 'New conversation message',
                'page_context': {}
            }),
            content_type='application/json'
        )
        
        conversation_id_2 = response2.json()['conversation_id']
        
        # Should have different conversation IDs
        self.assertNotEqual(conversation_id_1, conversation_id_2)
        
        # Should have 2 separate conversations in database
        self.assertEqual(Conversation.objects.count(), 2)
    
    @patch('assistant.services.OpenAI')
    def test_conversation_history_isolated_after_clear(self, mock_openai_class):
        """Test that conversation history is isolated after clearing chat"""
        # Mock OpenAI response
        mock_client = MagicMock()
        mock_openai_class.return_value = mock_client
        
        mock_response = MagicMock()
        mock_response.choices = [MagicMock()]
        mock_response.choices[0].message.content = "Response"
        mock_response.choices[0].message.tool_calls = None
        mock_client.chat.completions.create.return_value = mock_response
        
        # First conversation with multiple messages
        response1 = self.client.post(
            '/assistant/chat/',
            data=json.dumps({
                'message': 'First message',
                'page_context': {}
            }),
            content_type='application/json'
        )
        conversation_id_1 = response1.json()['conversation_id']
        
        # Continue first conversation
        self.client.post(
            '/assistant/chat/',
            data=json.dumps({
                'message': 'Second message',
                'conversation_id': conversation_id_1,
                'page_context': {}
            }),
            content_type='application/json'
        )
        
        # Start new conversation (cleared chat)
        response2 = self.client.post(
            '/assistant/chat/',
            data=json.dumps({
                'message': 'New conversation',
                'page_context': {}
            }),
            content_type='application/json'
        )
        conversation_id_2 = response2.json()['conversation_id']
        
        # Verify first conversation has 4 messages (2 user + 2 assistant)
        conversation1 = Conversation.objects.get(conversation_id=conversation_id_1)
        self.assertEqual(conversation1.messages.count(), 4)
        self.assertEqual(conversation1.total_messages, 4)
        
        # Verify second conversation has only 2 messages (1 user + 1 assistant)
        conversation2 = Conversation.objects.get(conversation_id=conversation_id_2)
        self.assertEqual(conversation2.messages.count(), 2)
        self.assertEqual(conversation2.total_messages, 2)
        
        # Verify messages are isolated
        conv1_messages = list(conversation1.messages.values_list('content', flat=True))
        conv2_messages = list(conversation2.messages.values_list('content', flat=True))
        
        self.assertIn('First message', conv1_messages)
        self.assertIn('Second message', conv1_messages)
        self.assertNotIn('New conversation', conv1_messages)
        
        self.assertIn('New conversation', conv2_messages)
        self.assertNotIn('First message', conv2_messages)
    
    def test_conversation_context_preserved_per_conversation(self):
        """Test that page context is preserved per conversation"""
        # Create first conversation with context
        conversation1 = Conversation.objects.create(
            conversation_id='conv-1',
            session_key='session-123'
        )
        
        ConversationContext.objects.create(
            conversation=conversation1,
            page_type='product_detail',
            product_id=self.product.id,
            category_slug='electronics'
        )
        
        # Create second conversation (new chat) with different context
        conversation2 = Conversation.objects.create(
            conversation_id='conv-2',
            session_key='session-123'
        )
        
        ConversationContext.objects.create(
            conversation=conversation2,
            page_type='home',
            product_id=None,
            category_slug=''
        )
        
        # Verify contexts are separate
        conv1_contexts = conversation1.contexts.all()
        conv2_contexts = conversation2.contexts.all()
        
        self.assertEqual(conv1_contexts.count(), 1)
        self.assertEqual(conv2_contexts.count(), 1)
        
        self.assertEqual(conv1_contexts.first().page_type, 'product_detail')
        self.assertEqual(conv1_contexts.first().product_id, self.product.id)
        
        self.assertEqual(conv2_contexts.first().page_type, 'home')
        self.assertIsNone(conv2_contexts.first().product_id)
