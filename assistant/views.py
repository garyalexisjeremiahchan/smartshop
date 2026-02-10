"""
Views for the shopping assistant application.
Handles chat requests and context retrieval.
"""

import json
import logging
import uuid
from django.http import JsonResponse
from django.views.decorators.http import require_http_methods
from django.views.decorators.csrf import csrf_exempt
from django.contrib.auth.decorators import login_required
from django.utils import timezone
from django.core.cache import cache
from .services import AssistantService
from .models import Conversation, Message, ConversationContext

logger = logging.getLogger(__name__)


# Simple rate limiting decorator
def rate_limit(max_requests=10, window_seconds=60):
    """Simple rate limiting based on IP or session"""
    def decorator(view_func):
        def wrapped_view(request, *args, **kwargs):
            # Get identifier (IP + session key)
            ip = request.META.get('REMOTE_ADDR', 'unknown')
            session_key = request.session.session_key or 'anonymous'
            identifier = f"{ip}:{session_key}"
            
            cache_key = f"rate_limit_assistant_{identifier}"
            request_count = cache.get(cache_key, 0)
            
            if request_count >= max_requests:
                return JsonResponse({
                    'error': 'Rate limit exceeded. Please wait a moment.',
                    'reply': 'Too many requests. Please wait a moment before asking again.'
                }, status=429)
            
            # Increment counter
            cache.set(cache_key, request_count + 1, window_seconds)
            
            return view_func(request, *args, **kwargs)
        return wrapped_view
    return decorator


@require_http_methods(["POST"])
@rate_limit(max_requests=20, window_seconds=60)
def chat(request):
    """
    Main chat endpoint for the shopping assistant.
    
    Expects JSON payload:
    {
        "message": "User message text",
        "conversation_id": "optional-conversation-id",
        "page_context": {
            "page_type": "product_detail",
            "product_id": 123,
            "category": "electronics",
            "search_query": "laptop",
            "cart_item_count": 2,
            "cart_total": 199.99
        }
    }
    
    Returns JSON:
    {
        "reply": "Assistant response",
        "cards": [...],
        "suggestions": [...],
        "conversation_id": "..."
    }
    """
    try:
        # Parse request
        data = json.loads(request.body)
        user_message = data.get('message', '').strip()
        
        if not user_message:
            return JsonResponse({
                'error': 'Message is required',
                'reply': 'Please enter a message.'
            }, status=400)
        
        # Get or create conversation
        conversation_id = data.get('conversation_id')
        page_context = data.get('page_context', {})
        
        logger.info(f"Chat request: message='{user_message}', page_context={page_context}")
        
        conversation = _get_or_create_conversation(request, conversation_id)
        
        # Store page context
        if page_context:
            ConversationContext.objects.create(
                conversation=conversation,
                page_url=page_context.get('page_url', ''),
                page_type=page_context.get('page_type', ''),
                product_id=page_context.get('product_id'),
                category_slug=page_context.get('category', ''),
                search_query=page_context.get('search_query', ''),
                cart_item_count=page_context.get('cart_item_count', 0),
                cart_total=page_context.get('cart_total')
            )
        
        # Get conversation history (last 12 messages)
        messages = _get_conversation_history(conversation, limit=12)
        
        # Add user message to history
        messages.append({
            "role": "user",
            "content": user_message
        })
        
        # Store user message
        Message.objects.create(
            conversation=conversation,
            role='user',
            content=user_message
        )
        
        # Call assistant service
        assistant_service = AssistantService(request=request)
        response = assistant_service.chat(messages, page_context)
        
        # Store assistant response
        Message.objects.create(
            conversation=conversation,
            role='assistant',
            content=response.get('reply', '')
        )
        
        # Update conversation metadata
        conversation.total_messages += 2  # user + assistant
        conversation.last_activity = timezone.now()
        conversation.save()
        
        # Return response with conversation_id
        response['conversation_id'] = conversation.conversation_id
        
        return JsonResponse(response)
    
    except json.JSONDecodeError:
        return JsonResponse({
            'error': 'Invalid JSON',
            'reply': 'Invalid request format.'
        }, status=400)
    
    except Exception as e:
        logger.error(f"Error in chat endpoint: {str(e)}", exc_info=True)
        return JsonResponse({
            'error': 'Internal server error',
            'reply': 'I apologize, but I encountered an error. Please try again.'
        }, status=500)


@require_http_methods(["GET"])
def get_context(request):
    """
    Get current page context for the assistant.
    Useful for initializing the assistant with context.
    
    Returns:
    {
        "page_type": "...",
        "product_id": ...,
        "category": "...",
        ...
    }
    """
    # This would typically be populated by JavaScript on the frontend
    # For now, return a simple response
    return JsonResponse({
        "page_type": request.GET.get('page_type', ''),
        "product_id": request.GET.get('product_id'),
        "category": request.GET.get('category', ''),
        "search_query": request.GET.get('search_query', ''),
    })


def _get_or_create_conversation(request, conversation_id=None):
    """
    Get existing conversation or create a new one.
    Associates with user if logged in, otherwise uses session.
    """
    user = request.user if request.user.is_authenticated else None
    session_key = request.session.session_key
    
    # Ensure session exists
    if not session_key:
        request.session.create()
        session_key = request.session.session_key
    
    if conversation_id:
        # Try to get existing conversation
        try:
            conversation = Conversation.objects.get(conversation_id=conversation_id)
            
            # Associate with user if they just logged in
            if user and not conversation.user:
                conversation.user = user
                conversation.save()
            
            return conversation
        except Conversation.DoesNotExist:
            pass
    
    # Create new conversation
    new_conversation_id = str(uuid.uuid4())
    conversation = Conversation.objects.create(
        conversation_id=new_conversation_id,
        user=user,
        session_key=session_key
    )
    
    return conversation


def _get_conversation_history(conversation, limit=12):
    """
    Get conversation message history in OpenAI format.
    
    Args:
        conversation: Conversation object
        limit: Maximum number of messages to retrieve
    
    Returns:
        List of message dicts in OpenAI format
    """
    messages_qs = conversation.messages.filter(
        role__in=['user', 'assistant']
    ).order_by('-created_at')[:limit]
    
    # Reverse to get chronological order
    messages = list(reversed(messages_qs))
    
    return [
        {
            "role": msg.role,
            "content": msg.content
        }
        for msg in messages
    ]
