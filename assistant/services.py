"""
OpenAI service integration and tool orchestration for the shopping assistant.
Handles tool-calling loop and conversation management.
"""

import json
import logging
from typing import List, Dict, Any
from openai import OpenAI
from django.conf import settings
from .prompts import SYSTEM_PROMPT, TOOL_DEFINITIONS
from . import tools

logger = logging.getLogger(__name__)


class AssistantService:
    """Manages OpenAI interactions and tool orchestration"""
    
    def __init__(self, request=None):
        """Initialize OpenAI client"""
        api_key = getattr(settings, 'OPENAI_API_KEY', None)
        if not api_key:
            raise ValueError("OPENAI_API_KEY not found in settings")
        self.client = OpenAI(api_key=api_key)
        self.model = getattr(settings, 'OPENAI_MODEL', 'gpt-4o-mini')
        self.max_iterations = 5  # Prevent infinite loops
        self.request = request  # Store request for cart operations
    
    def chat(self, messages: List[Dict[str, Any]], page_context: Dict[str, Any] = None) -> Dict[str, Any]:
        """
        Main chat function with tool-calling loop.
        
        Args:
            messages: Conversation history (list of message dicts)
            page_context: Current page context (product_id, category, etc.)
        
        Returns:
            Dict with assistant reply, product cards, and suggestions
        """
        try:
            # Prepare messages with system prompt
            full_messages = [{"role": "system", "content": self._build_system_prompt(page_context)}]
            full_messages.extend(messages)
            
            iteration = 0
            while iteration < self.max_iterations:
                iteration += 1
                
                # Call OpenAI with tools
                response = self.client.chat.completions.create(
                    model=self.model,
                    messages=full_messages,
                    tools=TOOL_DEFINITIONS,
                    tool_choice="auto",
                    temperature=0.7,
                    max_tokens=1000
                )
                
                assistant_message = response.choices[0].message
                
                # Check if assistant wants to use tools
                if assistant_message.tool_calls:
                    # Add assistant message with tool calls to history
                    full_messages.append({
                        "role": "assistant",
                        "content": assistant_message.content,
                        "tool_calls": [
                            {
                                "id": tc.id,
                                "type": "function",
                                "function": {
                                    "name": tc.function.name,
                                    "arguments": tc.function.arguments
                                }
                            }
                            for tc in assistant_message.tool_calls
                        ]
                    })
                    
                    # Execute each tool call
                    for tool_call in assistant_message.tool_calls:
                        function_name = tool_call.function.name
                        
                        try:
                            # Parse arguments
                            function_args = json.loads(tool_call.function.arguments)
                            
                            # Validate and execute tool
                            tool_result = self._execute_tool(function_name, function_args)
                            
                            # Add tool result to messages
                            full_messages.append({
                                "role": "tool",
                                "tool_call_id": tool_call.id,
                                "name": function_name,
                                "content": json.dumps(tool_result)
                            })
                            
                            logger.info(f"Executed tool: {function_name} with args: {function_args}")
                        
                        except json.JSONDecodeError as e:
                            logger.error(f"Failed to parse tool arguments: {e}")
                            full_messages.append({
                                "role": "tool",
                                "tool_call_id": tool_call.id,
                                "name": function_name,
                                "content": json.dumps({"success": False, "error": "Invalid arguments"})
                            })
                        except Exception as e:
                            logger.error(f"Tool execution error: {e}")
                            full_messages.append({
                                "role": "tool",
                                "tool_call_id": tool_call.id,
                                "name": function_name,
                                "content": json.dumps({"success": False, "error": str(e)})
                            })
                    
                    # Continue loop to get final response
                    continue
                
                else:
                    # No tool calls - return final response
                    return self._format_response(assistant_message.content, full_messages)
            
            # Max iterations reached
            logger.warning("Max iterations reached in chat loop")
            return {
                "reply": "I apologize, but I'm having trouble processing your request. Could you please try rephrasing?",
                "cards": [],
                "suggestions": []
            }
        
        except Exception as e:
            logger.error(f"Error in chat: {str(e)}")
            return {
                "reply": "I'm sorry, I encountered an error. Please try again.",
                "cards": [],
                "suggestions": [],
                "error": str(e)
            }
    
    def _build_system_prompt(self, page_context: Dict[str, Any] = None) -> str:
        """Build system prompt with optional page context"""
        prompt = SYSTEM_PROMPT
        
        if page_context:
            context_info = "\n\nCURRENT PAGE CONTEXT:\n"
            
            if page_context.get('page_type'):
                context_info += f"- Page type: {page_context['page_type']}\n"
            
            if page_context.get('product_id'):
                context_info += f"- User is viewing product ID: {page_context['product_id']}\n"
            
            if page_context.get('category'):
                context_info += f"- Current category: {page_context['category']}\n"
            
            if page_context.get('search_query'):
                context_info += f"- User searched for: {page_context['search_query']}\n"
            
            if page_context.get('cart_item_count'):
                context_info += f"- Cart has {page_context['cart_item_count']} items\n"
            
            prompt += context_info
        
        return prompt
    
    def _execute_tool(self, function_name: str, function_args: Dict[str, Any]) -> Dict[str, Any]:
        """
        Execute a tool function with validation and error handling.
        
        Args:
            function_name: Name of the tool function
            function_args: Arguments to pass to the function
        
        Returns:
            Tool execution result
        """
        # Map function names to actual functions
        tool_map = {
            'search_products': tools.search_products,
            'get_product_details': tools.get_product_details,
            'get_product_specs': tools.get_product_specs,
            'get_availability': tools.get_availability,
            'get_reviews_summary': tools.get_reviews_summary,
            'get_similar_products': tools.get_similar_products,
            'get_categories': tools.get_categories,
            'get_top_selling_products': tools.get_top_selling_products,
            'add_to_cart': tools.add_to_cart,
        }
        
        if function_name not in tool_map:
            return {"success": False, "error": f"Unknown tool: {function_name}"}
        
        # Validate and sanitize arguments
        sanitized_args = self._sanitize_args(function_name, function_args)
        
        # Add request object for cart operations
        if function_name == 'add_to_cart':
            sanitized_args['request'] = self.request
        
        # Execute the tool
        tool_func = tool_map[function_name]
        result = tool_func(**sanitized_args)
        
        return result
    
    def _sanitize_args(self, function_name: str, args: Dict[str, Any]) -> Dict[str, Any]:
        """Validate and sanitize tool arguments"""
        sanitized = {}
        
        # Common validations
        if 'product_id' in args:
            try:
                sanitized['product_id'] = int(args['product_id'])
                if sanitized['product_id'] <= 0:
                    raise ValueError("Product ID must be positive")
            except (ValueError, TypeError):
                raise ValueError("Invalid product_id")
        
        if 'limit' in args:
            try:
                limit = int(args['limit'])
                sanitized['limit'] = max(1, min(limit, 10))  # Clamp between 1-10
            except (ValueError, TypeError):
                sanitized['limit'] = 5
        
        if 'query' in args and args['query']:
            sanitized['query'] = str(args['query'])[:200]  # Limit query length
        
        if 'category' in args and args['category']:
            sanitized['category'] = str(args['category'])[:100]
        
        if 'min_price' in args and args['min_price'] is not None:
            try:
                sanitized['min_price'] = max(0, float(args['min_price']))
            except (ValueError, TypeError):
                pass
        
        if 'max_price' in args and args['max_price'] is not None:
            try:
                sanitized['max_price'] = max(0, float(args['max_price']))
            except (ValueError, TypeError):
                pass
        
        if 'min_rating' in args and args['min_rating'] is not None:
            try:
                sanitized['min_rating'] = max(1, min(5, float(args['min_rating'])))
            except (ValueError, TypeError):
                pass
        
        if 'in_stock_only' in args:
            sanitized['in_stock_only'] = bool(args['in_stock_only'])
        
        if 'sort' in args and args['sort']:
            allowed_sorts = ['popular', 'latest', 'price_low_high', 'price_high_low', 'rating']
            if args['sort'] in allowed_sorts:
                sanitized['sort'] = args['sort']
        
        if 'quantity' in args:
            try:
                quantity = int(args['quantity'])
                sanitized['quantity'] = max(1, min(quantity, 100))  # Clamp between 1-100
            except (ValueError, TypeError):
                sanitized['quantity'] = 1
        
        return sanitized
    
    def _format_response(self, assistant_text: str, messages: List[Dict]) -> Dict[str, Any]:
        """
        Format the assistant response with product cards extracted from tool results.
        
        Args:
            assistant_text: The assistant's text response
            messages: Full conversation history including tool calls
        
        Returns:
            Formatted response dict
        """
        cards = []
        suggestions = []
        
        # Extract product cards from recent tool results
        for msg in reversed(messages[-10:]):  # Check last 10 messages
            if msg.get('role') == 'tool':
                try:
                    tool_content = json.loads(msg['content'])
                    
                    # Extract products from search results
                    if 'products' in tool_content and tool_content.get('success'):
                        for product in tool_content['products'][:5]:  # Max 5 cards
                            if product not in cards:
                                cards.append(product)
                    
                    # Extract from similar products
                    if 'similar_products' in tool_content and tool_content.get('success'):
                        for product in tool_content['similar_products'][:5]:
                            if product not in cards:
                                cards.append(product)
                
                except (json.JSONDecodeError, KeyError):
                    continue
        
        # Generate contextual suggestions
        if cards:
            suggestions = [
                "Tell me more about any of these products",
                "Check availability",
                "Compare these options"
            ]
        else:
            suggestions = [
                "Search for products",
                "Show me categories",
                "What's popular?"
            ]
        
        return {
            "reply": assistant_text or "How can I help you?",
            "cards": cards[:5],  # Limit to 5 cards
            "suggestions": suggestions[:3]  # Limit to 3 suggestions
        }
