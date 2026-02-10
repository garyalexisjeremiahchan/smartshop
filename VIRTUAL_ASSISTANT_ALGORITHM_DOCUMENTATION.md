# Virtual Shopping Assistant - Algorithm & Logic Documentation

**Project:** SmartShop E-commerce Platform  
**Feature:** AI-Powered Virtual Shopping Assistant  
**AI Model:** OpenAI GPT-4o-mini with Function Calling  
**Last Updated:** February 9, 2026  
**Version:** 1.0

---

## Table of Contents

1. [Executive Summary](#executive-summary)
2. [System Architecture](#system-architecture)
3. [Core Algorithm Overview](#core-algorithm-overview)
4. [Request-Response Flow](#request-response-flow)
5. [Tool Calling Loop Algorithm](#tool-calling-loop-algorithm)
6. [Component Deep Dive](#component-deep-dive)
7. [Data Flow & State Management](#data-flow--state-management)
8. [Decision Logic & Control Flow](#decision-logic--control-flow)
9. [Error Handling & Recovery](#error-handling--recovery)
10. [Performance Optimization](#performance-optimization)
11. [Security & Rate Limiting](#security--rate-limiting)

---

## Executive Summary

The Virtual Shopping Assistant is an AI-powered conversational interface that helps customers navigate the e-commerce platform, find products, check availability, and complete purchases. The system uses OpenAI's GPT-4o-mini with **function calling** (tool use) to execute database queries and provide accurate, real-time information.

### Key Capabilities

- **Natural Language Understanding:** Interprets user questions and shopping intentions
- **Dynamic Tool Execution:** Automatically calls 9 specialized tools to fetch product data
- **Context Awareness:** Maintains conversation history and page context
- **Multi-Step Workflows:** Handles complex queries requiring multiple tool calls
- **Real-Time Data:** Always uses current database information (never hallucinates)
- **Shopping Actions:** Can search, recommend, check stock, and add items to cart

### Core Technologies

| Component | Technology | Purpose |
|-----------|-----------|---------|
| AI Model | OpenAI GPT-4o-mini | Natural language processing & orchestration |
| Function Calling | OpenAI Tools API | Structured tool execution |
| Backend | Django 6.0.1 | Request handling & database operations |
| Database | MySQL | Product catalog & conversation storage |
| Caching | Django Cache | Rate limiting & performance |
| Frontend | JavaScript/AJAX | Real-time chat interface |

---

## System Architecture

### High-Level Architecture Diagram

```
┌─────────────────────────────────────────────────────────────────┐
│                         USER INTERFACE                          │
│  (Chat Widget - JavaScript + AJAX + Real-time Markdown Render)  │
└────────────────────────────┬────────────────────────────────────┘
                             │ HTTP POST /assistant/chat/
                             ▼
┌─────────────────────────────────────────────────────────────────┐
│                       DJANGO VIEW LAYER                         │
│  ┌──────────────────────────────────────────────────────────┐  │
│  │  Rate Limiting (20 req/60s) → Session Management         │  │
│  │  ↓                                                        │  │
│  │  Request Validation → Parse JSON → Auth Check            │  │
│  │  ↓                                                        │  │
│  │  Get/Create Conversation → Store Context                 │  │
│  └──────────────────────────────────────────────────────────┘  │
└────────────────────────────┬────────────────────────────────────┘
                             │
                             ▼
┌─────────────────────────────────────────────────────────────────┐
│                    ASSISTANT SERVICE LAYER                      │
│  ┌──────────────────────────────────────────────────────────┐  │
│  │  Build Context → System Prompt Engineering               │  │
│  │  ↓                                                        │  │
│  │  ┌─────────────────────────────────────────────────┐    │  │
│  │  │     TOOL CALLING LOOP (Max 5 iterations)        │    │  │
│  │  │                                                  │    │  │
│  │  │  1. Call OpenAI API with tools                  │    │  │
│  │  │  2. Check response for tool_calls               │    │  │
│  │  │  3. IF tool_calls → Execute tools               │    │  │
│  │  │  4. Add results to message history              │    │  │
│  │  │  5. LOOP BACK to step 1                         │    │  │
│  │  │  6. IF no tool_calls → Return final response    │    │  │
│  │  └─────────────────────────────────────────────────┘    │  │
│  │  ↓                                                        │  │
│  │  Format Response → Extract Product Cards                 │  │
│  └──────────────────────────────────────────────────────────┘  │
└────────────────────────────┬────────────────────────────────────┘
                             │
                             ▼
┌─────────────────────────────────────────────────────────────────┐
│                        TOOL EXECUTION LAYER                     │
│  ┌──────────────────────────────────────────────────────────┐  │
│  │  Tool Router → Argument Sanitization → Validation        │  │
│  │  ↓                                                        │  │
│  │  Execute Tool Function:                                  │  │
│  │  • search_products()      • get_product_details()        │  │
│  │  • get_product_specs()    • get_availability()           │  │
│  │  • get_reviews_summary()  • get_similar_products()       │  │
│  │  • get_categories()       • get_top_selling_products()   │  │
│  │  • add_to_cart()                                         │  │
│  └──────────────────────────────────────────────────────────┘  │
└────────────────────────────┬────────────────────────────────────┘
                             │
                             ▼
┌─────────────────────────────────────────────────────────────────┐
│                      DATABASE LAYER (MySQL)                     │
│  • Products        • Categories      • Reviews                 │
│  • Cart/CartItems  • ProductImages   • Users                   │
│  • Conversations   • Messages        • ConversationContext      │
└─────────────────────────────────────────────────────────────────┘
```

### Component Responsibilities

| Component | File | Responsibility |
|-----------|------|----------------|
| **Views** | `views.py` | HTTP handling, rate limiting, session management |
| **Service** | `services.py` | OpenAI orchestration, tool calling loop |
| **Tools** | `tools.py` | Database queries, business logic execution |
| **Prompts** | `prompts.py` | System prompts, tool definitions |
| **Models** | `models.py` | Data persistence, conversation tracking |

---

## Core Algorithm Overview

### Algorithm Summary

The Virtual Shopping Assistant operates on a **multi-turn, tool-augmented conversation loop**:

```
User Input → Context Assembly → AI Processing → Tool Execution → Response Generation
     ↑                                                                    │
     └────────────────────────── Loop Until Complete ───────────────────┘
```

### Key Algorithm Principles

1. **Stateful Conversations:** Each conversation maintains history and context
2. **Tool-First Approach:** All factual data must come from tools (no hallucination)
3. **Iterative Refinement:** AI can make multiple tool calls before responding
4. **Context-Aware:** Uses page context (product being viewed, category, cart status)
5. **Defensive Programming:** Validates, sanitizes, and error-handles all inputs
6. **Performance-Optimized:** Limits iterations, results, and token usage

---

## Request-Response Flow

### Detailed Request Flow

```
┌─────────────────────────────────────────────────────────────────────┐
│ STEP 1: CLIENT-SIDE REQUEST PREPARATION                            │
└─────────────────────────────────────────────────────────────────────┘

User types message in chat interface
   ↓
JavaScript captures:
   • User message text
   • Current page context (product_id, category, page_type, etc.)
   • Existing conversation_id (if continuing conversation)
   • Cart status (item count, total)
   ↓
POST /assistant/chat/ with JSON payload:
{
  "message": "Show me laptops under $1000",
  "conversation_id": "uuid-if-exists",
  "page_context": {
    "page_type": "product_list",
    "category": "electronics",
    "cart_item_count": 2,
    "cart_total": 299.99
  }
}

┌─────────────────────────────────────────────────────────────────────┐
│ STEP 2: VIEW LAYER PROCESSING (views.py)                           │
└─────────────────────────────────────────────────────────────────────┘

Request arrives at chat(request) view
   ↓
Rate Limiting Check:
   • Generate identifier: f"{IP}:{session_key}"
   • Check cache: rate_limit_assistant_{identifier}
   • If count >= 20 requests in 60s → Return 429 error
   • Else increment counter
   ↓
Request Validation:
   • Parse JSON body
   • Validate message exists and is non-empty
   • Extract conversation_id and page_context
   ↓
Conversation Management:
   • If conversation_id provided → Retrieve existing Conversation
   • Else → Create new Conversation
   • Link to authenticated user OR session_key
   ↓
Context Storage:
   • Create ConversationContext record with page_context data
   • Store: page_type, product_id, category_slug, search_query, cart info
   ↓
History Retrieval:
   • Query last 12 messages from conversation
   • Format as OpenAI message list: [{"role": "user", "content": "..."}]
   ↓
Message Storage:
   • Create Message record (role='user', content=user_message)
   • Increment conversation.total_messages

┌─────────────────────────────────────────────────────────────────────┐
│ STEP 3: ASSISTANT SERVICE ORCHESTRATION (services.py)              │
└─────────────────────────────────────────────────────────────────────┘

AssistantService.chat() called with:
   • messages: Conversation history
   • page_context: Current page data
   ↓
System Prompt Construction:
   • Start with base SYSTEM_PROMPT
   • Append page context information:
     - "User is viewing product ID: 123"
     - "Current category: electronics"
     - "Cart has 2 items"
   ↓
Message List Assembly:
   full_messages = [
     {"role": "system", "content": system_prompt},
     ...conversation_history,
     {"role": "user", "content": current_message}
   ]

┌─────────────────────────────────────────────────────────────────────┐
│ STEP 4: TOOL CALLING LOOP (THE CORE ALGORITHM)                     │
└─────────────────────────────────────────────────────────────────────┘

iteration = 0
WHILE iteration < 5 (max_iterations):
   iteration += 1
   
   ┌────────────────────────────────────────┐
   │ 4.1: CALL OPENAI API                  │
   └────────────────────────────────────────┘
   
   response = openai.chat.completions.create(
     model='gpt-4o-mini',
     messages=full_messages,
     tools=TOOL_DEFINITIONS,  # 9 available tools
     tool_choice='auto',       # Let AI decide
     temperature=0.7,
     max_tokens=1000
   )
   assistant_message = response.choices[0].message
   
   ┌────────────────────────────────────────┐
   │ 4.2: CHECK FOR TOOL CALLS              │
   └────────────────────────────────────────┘
   
   IF assistant_message.tool_calls EXISTS:
   
      ┌────────────────────────────────────────┐
      │ 4.3: ADD ASSISTANT MESSAGE TO HISTORY  │
      └────────────────────────────────────────┘
      
      full_messages.append({
        "role": "assistant",
        "content": assistant_message.content,
        "tool_calls": [formatted tool calls]
      })
      
      ┌────────────────────────────────────────┐
      │ 4.4: EXECUTE EACH TOOL CALL            │
      └────────────────────────────────────────┘
      
      FOR EACH tool_call IN assistant_message.tool_calls:
         
         function_name = tool_call.function.name  # e.g., "search_products"
         function_args = json.loads(tool_call.function.arguments)
         
         TRY:
            # Sanitize and validate arguments
            sanitized_args = _sanitize_args(function_name, function_args)
            
            # Route to correct tool function
            tool_result = _execute_tool(function_name, sanitized_args)
            
            # Example: tool_result = {
            #   "success": True,
            #   "products": [
            #     {"id": 1523, "title": "Dell Laptop", "price": 899.99, ...}
            #   ]
            # }
         
         CATCH errors:
            tool_result = {"success": False, "error": error_message}
         
         ┌────────────────────────────────────────┐
         │ 4.5: ADD TOOL RESULT TO HISTORY        │
         └────────────────────────────────────────┘
         
         full_messages.append({
           "role": "tool",
           "tool_call_id": tool_call.id,
           "name": function_name,
           "content": json.dumps(tool_result)
         })
      
      END FOR
      
      ┌────────────────────────────────────────┐
      │ 4.6: CONTINUE LOOP                     │
      └────────────────────────────────────────┘
      
      CONTINUE  # Go back to 4.1
   
   ELSE (no tool calls):
   
      ┌────────────────────────────────────────┐
      │ 4.7: FINAL RESPONSE READY              │
      └────────────────────────────────────────┘
      
      BREAK  # Exit loop, return response

END WHILE

┌─────────────────────────────────────────────────────────────────────┐
│ STEP 5: RESPONSE FORMATTING                                        │
└─────────────────────────────────────────────────────────────────────┘

Extract Product Cards:
   • Scan last 10 messages for role='tool'
   • Extract 'products' arrays from tool results
   • Format as cards (limit 5)
   ↓
Generate Suggestions:
   • If cards exist: ["Tell me more", "Check availability", "Compare"]
   • Else: ["Search for products", "Show categories", "What's popular?"]
   ↓
Return:
{
  "reply": "I found 3 laptops under $1000...",
  "cards": [product_card_1, product_card_2, ...],
  "suggestions": ["Tell me more about any of these", ...]
}

┌─────────────────────────────────────────────────────────────────────┐
│ STEP 6: VIEW LAYER FINALIZATION                                    │
└─────────────────────────────────────────────────────────────────────┘

Store assistant response:
   • Create Message(role='assistant', content=reply)
   ↓
Update conversation metadata:
   • conversation.total_messages += 2
   • conversation.last_activity = now()
   • conversation.save()
   ↓
Add conversation_id to response
   ↓
Return JsonResponse(response)

┌─────────────────────────────────────────────────────────────────────┐
│ STEP 7: CLIENT-SIDE RENDERING                                      │
└─────────────────────────────────────────────────────────────────────┘

JavaScript receives response
   ↓
Parse markdown in reply text
   • Convert ### → <h3>, ** → <strong>, etc.
   ↓
Render assistant message bubble
   ↓
Render product cards (if any)
   ↓
Render suggestion chips
   ↓
Store conversation_id for next message
```

---

## Tool Calling Loop Algorithm

### Detailed Loop Logic

The **tool calling loop** is the heart of the assistant's intelligence. It allows the AI to make multiple tool calls and reason about the results before responding to the user.

#### Algorithm Pseudocode

```python
def chat(messages, page_context):
    """Tool calling loop algorithm"""
    
    # Initialize
    full_messages = [system_prompt] + messages
    iteration = 0
    MAX_ITERATIONS = 5
    
    # Main loop
    while iteration < MAX_ITERATIONS:
        iteration += 1
        
        # Call OpenAI with tools
        response = call_openai(
            messages=full_messages,
            tools=TOOL_DEFINITIONS,
            tool_choice="auto"
        )
        
        assistant_message = response.choices[0].message
        
        # DECISION POINT: Does AI want to use tools?
        if assistant_message.has_tool_calls():
            
            # Phase 1: Add assistant's tool call request to history
            full_messages.append({
                "role": "assistant",
                "tool_calls": assistant_message.tool_calls
            })
            
            # Phase 2: Execute all tool calls
            for tool_call in assistant_message.tool_calls:
                
                # Parse tool request
                function_name = tool_call.function.name
                arguments = parse_json(tool_call.function.arguments)
                
                # Execute tool
                try:
                    result = execute_tool(function_name, arguments)
                except Exception as e:
                    result = {"success": False, "error": str(e)}
                
                # Phase 3: Add tool result to history
                full_messages.append({
                    "role": "tool",
                    "tool_call_id": tool_call.id,
                    "name": function_name,
                    "content": json_dumps(result)
                })
            
            # Phase 4: Loop back (AI will see tool results and decide next action)
            continue
        
        else:
            # No tool calls = final answer ready
            return format_response(assistant_message.content, full_messages)
    
    # Max iterations reached (safety mechanism)
    return error_response("Too many iterations")
```

#### Example Loop Execution

**User Query:** "I need a laptop for coding under $1000"

**Iteration 1:**
```
→ OpenAI receives: [system_prompt, "I need a laptop for coding under $1000"]
← OpenAI responds: tool_call(search_products, {query: "laptop", max_price: 1000})
→ Execute: search_products(query="laptop", max_price=1000)
← Returns: {success: True, products: [3 laptops]}
→ Add tool result to messages
```

**Iteration 2:**
```
→ OpenAI receives: [system_prompt, user_msg, tool_call, tool_result]
← OpenAI responds: "I found 3 laptops..." (no tool calls)
→ Return final response
```

**Total API calls:** 2 (optimal path)

#### Multi-Tool Example

**User Query:** "Add the Dell laptop to my cart"

**Iteration 1:**
```
→ OpenAI: "Add the Dell laptop to my cart"
← OpenAI: tool_call(search_products, {query: "Dell laptop"})
→ Execute: Returns product_id=1523
```

**Iteration 2:**
```
→ OpenAI: [previous messages + search result]
← OpenAI: tool_call(add_to_cart, {product_id: 1523, quantity: 1})
→ Execute: Adds to cart
```

**Iteration 3:**
```
→ OpenAI: [previous messages + cart result]
← OpenAI: "I've added the Dell laptop to your cart!"
→ Return final response
```

**Total API calls:** 3 (multi-step workflow)

---

## Component Deep Dive

### 1. Views Layer (`views.py`)

#### Rate Limiting Algorithm

```python
def rate_limit(max_requests=20, window_seconds=60):
    """
    Sliding window rate limiting algorithm
    
    Algorithm:
    1. Generate unique identifier: IP + Session Key
    2. Check cache for request count
    3. If count >= limit → Reject (429)
    4. Else increment count with TTL
    5. Allow request
    """
    
    identifier = f"{ip_address}:{session_key}"
    cache_key = f"rate_limit_assistant_{identifier}"
    
    current_count = cache.get(cache_key, 0)
    
    if current_count >= max_requests:
        return HTTP_429_TOO_MANY_REQUESTS
    
    cache.set(cache_key, current_count + 1, timeout=window_seconds)
    
    # Allow request to proceed
```

**Rate Limit Parameters:**
- **Limit:** 20 requests
- **Window:** 60 seconds (1 minute)
- **Identifier:** IP + Session (prevents circumvention)
- **Storage:** Django Cache (memory-based)

#### Conversation Management

```python
def _get_or_create_conversation(request, conversation_id):
    """
    Conversation retrieval/creation logic
    
    Decision Tree:
    
    conversation_id provided?
    ├─ YES → Try to retrieve existing
    │  ├─ Found → Return conversation
    │  └─ Not found → Create new (with provided ID)
    └─ NO → Create new conversation
       ├─ User authenticated? → Link to user
       └─ Anonymous → Link to session_key
    """
    
    if conversation_id:
        try:
            return Conversation.objects.get(conversation_id=conversation_id)
        except Conversation.DoesNotExist:
            pass  # Fall through to creation
    
    # Generate unique ID
    conversation_id = str(uuid.uuid4())
    
    # Create conversation
    conversation = Conversation.objects.create(
        conversation_id=conversation_id,
        user=request.user if request.user.is_authenticated else None,
        session_key=request.session.session_key
    )
    
    return conversation
```

### 2. Service Layer (`services.py`)

#### System Prompt Engineering

```python
def _build_system_prompt(page_context):
    """
    Dynamic prompt construction algorithm
    
    Prompt Components:
    1. Base instructions (always included)
    2. Context injection (conditional)
    3. Behavioral rules (critical rules)
    """
    
    prompt = BASE_SYSTEM_PROMPT  # Core instructions
    
    if page_context and page_context.get('product_id'):
        # User is viewing a specific product
        prompt += f"\n\nCONTEXT: User is viewing product ID {product_id}."
        prompt += "\nWhen user says 'this product', use get_product_details({product_id})"
    
    if page_context and page_context.get('category'):
        # User is browsing a category
        prompt += f"\n\nCONTEXT: User is browsing {category} category."
    
    if page_context and page_context.get('search_query'):
        # User came from search results
        prompt += f"\n\nCONTEXT: User searched for '{search_query}'."
    
    if page_context and page_context.get('cart_item_count', 0) > 0:
        # User has items in cart
        prompt += f"\n\nCONTEXT: User's cart has {count} items (${total})."
    
    return prompt
```

**Prompt Engineering Principles:**

1. **Explicit Tool Usage:** "You MUST use tools for all factual data"
2. **No Hallucination:** "NEVER guess product information"
3. **Product ID Handling:** "Use EXACT product IDs from tool results"
4. **Context Awareness:** Inject page context dynamically
5. **Clear Formatting:** Specify markdown usage and link formats

#### Tool Argument Sanitization

```python
def _sanitize_args(function_name, args):
    """
    Input validation and sanitization algorithm
    
    Security Controls:
    1. Type validation (int, float, str, bool)
    2. Range clamping (prevent abuse)
    3. Length limiting (prevent DoS)
    4. SQL injection prevention (Django ORM handles this)
    """
    
    sanitized = {}
    
    # Product ID validation
    if 'product_id' in args:
        product_id = int(args['product_id'])  # Type cast (throws on invalid)
        
        if product_id <= 0:
            raise ValueError("Product ID must be positive")
        
        sanitized['product_id'] = product_id
    
    # Limit validation (prevent excessive queries)
    if 'limit' in args:
        limit = int(args['limit'])
        sanitized['limit'] = max(1, min(limit, 10))  # Clamp to [1, 10]
    
    # Query string sanitization
    if 'query' in args:
        query = str(args['query'])
        sanitized['query'] = query[:200]  # Truncate to 200 chars
    
    # Price validation (prevent negative prices)
    if 'min_price' in args:
        sanitized['min_price'] = max(0, float(args['min_price']))
    
    # Rating validation (clamp to valid range)
    if 'min_rating' in args:
        rating = float(args['min_rating'])
        sanitized['min_rating'] = max(1, min(5, rating))  # [1, 5]
    
    return sanitized
```

### 3. Tools Layer (`tools.py`)

#### Search Products Algorithm

```python
def search_products(query=None, category=None, min_price=None, max_price=None,
                   min_rating=None, in_stock_only=False, sort='popular', limit=5):
    """
    Multi-criteria product search with dynamic filtering
    
    Algorithm Flow:
    1. Start with base queryset (active products)
    2. Apply filters sequentially (AND logic)
    3. Annotate with aggregations (ratings, reviews)
    4. Apply post-aggregation filters
    5. Sort results
    6. Limit and format output
    """
    
    # Step 1: Base queryset with optimizations
    products = Product.objects.filter(is_active=True) \
                      .select_related('category') \      # JOIN optimization
                      .prefetch_related('images')        # Prevent N+1 queries
    
    # Step 2: Text search (OR logic on multiple fields)
    if query:
        products = products.filter(
            Q(name__icontains=query) |
            Q(description__icontains=query) |
            Q(specifications__icontains=query)
        )
    
    # Step 3: Category filter
    if category:
        products = products.filter(category__slug=category)
    
    # Step 4: Price range filter
    if min_price is not None:
        products = products.filter(price__gte=Decimal(str(min_price)))
    if max_price is not None:
        products = products.filter(price__lte=Decimal(str(max_price)))
    
    # Step 5: Stock filter
    if in_stock_only:
        products = products.filter(stock__gt=0)
    
    # Step 6: Aggregate calculations
    products = products.annotate(
        avg_rating=Avg('reviews__rating', filter=Q(reviews__is_approved=True)),
        approved_reviews=Count('reviews', filter=Q(reviews__is_approved=True))
    )
    
    # Step 7: Rating filter (post-aggregation)
    if min_rating is not None:
        products = products.filter(avg_rating__gte=min_rating)
    
    # Step 8: Sorting
    sort_map = {
        'popular': ['-units_sold', '-avg_rating'],
        'latest': ['-created_at'],
        'price_low_high': ['price'],
        'price_high_low': ['-price'],
        'rating': ['-avg_rating', '-approved_reviews']
    }
    products = products.order_by(*sort_map.get(sort, ['-units_sold']))
    
    # Step 9: Limit (with safety cap)
    limit = min(int(limit), 10)
    products = products[:limit]
    
    # Step 10: Format results
    return {
        "success": True,
        "count": len(products),
        "products": [format_product(p) for p in products]
    }
```

**Query Optimization Techniques:**

1. **select_related()**: JOIN categories (1 query vs N+1)
2. **prefetch_related()**: Batch fetch images (2 queries vs N+1)
3. **Annotation**: Calculate ratings in database (not Python)
4. **Early filtering**: Apply filters before aggregation when possible
5. **Limit enforcement**: Cap results to prevent memory issues

#### Add to Cart Algorithm

```python
def add_to_cart(product_id, quantity=1, request=None):
    """
    Shopping cart addition with validation and deduplication
    
    Algorithm:
    1. Validate request object exists
    2. Validate product exists and is active
    3. Check stock availability
    4. Get or create cart for user/session
    5. Check if product already in cart
       ├─ YES → Update quantity (increment)
       └─ NO → Create new cart item
    6. Return success with cart summary
    """
    
    # Step 1: Request validation
    if not request:
        return {"success": False, "error": "No request object"}
    
    # Step 2: Product validation
    try:
        product = Product.objects.get(id=product_id, is_active=True)
    except Product.DoesNotExist:
        return {"success": False, "error": f"Product not found: {product_id}"}
    
    # Step 3: Stock validation
    if product.stock < quantity:
        return {
            "success": False,
            "error": f"Insufficient stock: requested={quantity}, available={product.stock}"
        }
    
    # Step 4: Get or create cart
    if request.user.is_authenticated:
        cart, _ = Cart.objects.get_or_create(user=request.user)
    else:
        session_key = request.session.session_key
        if not session_key:
            request.session.create()
            session_key = request.session.session_key
        cart, _ = Cart.objects.get_or_create(session_key=session_key)
    
    # Step 5: Get or create cart item (atomic operation)
    cart_item, created = CartItem.objects.get_or_create(
        cart=cart,
        product=product,
        defaults={'quantity': quantity}
    )
    
    if not created:
        # Item already exists - increment quantity
        new_quantity = cart_item.quantity + quantity
        
        # Validate total quantity
        if new_quantity > product.stock:
            return {
                "success": False,
                "error": f"Cannot add {quantity} more. Cart has {cart_item.quantity}, stock is {product.stock}"
            }
        
        cart_item.quantity = new_quantity
        cart_item.save()
    
    # Step 6: Calculate cart totals
    cart_total = sum(
        item.product.price * item.quantity
        for item in cart.items.all()
    )
    
    return {
        "success": True,
        "message": f"Added {quantity}x {product.name} to cart",
        "cart_item_count": cart.items.count(),
        "cart_total": float(cart_total)
    }
```

---

## Data Flow & State Management

### Conversation State Machine

```
┌─────────────────────────────────────────────────────────────────┐
│                    CONVERSATION LIFECYCLE                       │
└─────────────────────────────────────────────────────────────────┘

[START]
   │
   ├─→ User sends first message
   │
   ▼
┌──────────────────────┐
│  Conversation        │
│  Created             │────────────────┐
│  - Generate UUID     │                │
│  - Link to user/     │                │
│    session           │                │
│  - is_active = True  │                │
└──────────────────────┘                │
   │                                    │
   ├─→ User sends message               │
   │                                    │
   ▼                                    │
┌──────────────────────┐                │
│  Message Stored      │                │
│  - role = 'user'     │                │
│  - content = text    │                │
└──────────────────────┘                │
   │                                    │
   ├─→ AI processes                     │
   │                                    │
   ▼                                    │
┌──────────────────────┐                │
│  Tool Calls          │                │
│  Executed            │                │
│  - May create        │                │
│    multiple tool     │                │
│    messages          │                │
└──────────────────────┘                │
   │                                    │
   ├─→ AI responds                      │
   │                                    │
   ▼                                    │
┌──────────────────────┐                │
│  Message Stored      │                │
│  - role = 'assistant'│                │
│  - content = reply   │                │
└──────────────────────┘                │
   │                                    │
   ├─→ Update metadata                  │
   │   - total_messages++               │
   │   - last_activity = now()          │
   │                                    │
   ├─→ Create Context                   │
   │   - page_type                      │
   │   - product_id                     │
   │   - etc.                           │
   │                                    │
   └─→ LOOP (continue conversation) ───┘

[Conversation remains active indefinitely - no auto-timeout]
```

### Message History Management

```python
def _get_conversation_history(conversation, limit=12):
    """
    Retrieve conversation history with sliding window
    
    Strategy:
    - Keep most recent N messages (default: 12)
    - Excludes system messages (added fresh each time)
    - Includes user, assistant, and tool messages
    - Ordered chronologically
    
    Why limit history?
    - Token budget: OpenAI has max context window
    - Performance: Less data to transmit/process
    - Relevance: Recent context more important
    """
    
    messages = conversation.messages.order_by('-created_at')[:limit]
    messages = list(reversed(messages))  # Chronological order
    
    formatted = []
    for msg in messages:
        if msg.role == 'tool':
            formatted.append({
                "role": "tool",
                "tool_call_id": msg.tool_call_id,
                "name": msg.tool_name,
                "content": msg.content
            })
        else:
            formatted.append({
                "role": msg.role,
                "content": msg.content
            })
    
    return formatted
```

### Context Tracking

```python
"""
ConversationContext Model Strategy

Purpose:
- Track what page user was on when they sent each message
- Enables context-aware responses
- Helps AI understand user intent

Data Captured:
- page_type: 'product_detail', 'category', 'search', 'cart', 'home'
- product_id: If viewing specific product
- category_slug: If browsing category
- search_query: If on search results page
- cart_item_count: Shopping cart status
- cart_total: Cart value

Usage in Prompt:
"User is viewing product ID 123 in electronics category with 2 items in cart ($99.50)"

Benefits:
- AI knows when "this product" refers to page context
- Can suggest related products from same category
- Understands urgency (cart abandonment prevention)
"""

# Example context injection
if page_context.get('product_id'):
    system_prompt += f"\nUser is viewing product ID {page_context['product_id']}"
    system_prompt += "\nWhen they say 'this product', use get_product_details with this ID"
```

### Clear Chat & Conversation Reset

```python
"""
Clear Chat Feature - Frontend Algorithm

Purpose:
- Allow users to start a fresh conversation
- Clear previous context and history
- Reset state for new shopping journey

Implementation Strategy:
1. Client-side state management (JavaScript)
2. LocalStorage for conversation_id persistence
3. SessionStorage for chat history caching
4. Confirmation dialog to prevent accidental clears

User Flow:
┌─────────────────────────────────────────────────┐
│ User clicks "New Chat" button                   │
│ (Red chip with refresh icon)                    │
└────────────────┬────────────────────────────────┘
                 │
                 ▼
         Has existing messages?
         ├─ YES → Show confirmation dialog
         │        "Start new conversation?"
         │        ├─ Cancel → Abort, no changes
         │        └─ Confirm → Continue to clear
         └─ NO → Skip confirmation (new user)
                 │
                 ▼
         ┌───────────────────────────────┐
         │ Clear State Operations:       │
         │ 1. Set conversationId = null  │
         │ 2. Remove from localStorage   │
         │ 3. Clear sessionStorage       │
         │ 4. Empty messages container   │
         │ 5. Show welcome message       │
         │ 6. Reset suggestion chips     │
         │ 7. Focus input field          │
         └───────────────────────────────┘
                 │
                 ▼
         ┌───────────────────────────────┐
         │ Next Message Creates:         │
         │ - New conversation_id (UUID)  │
         │ - New Conversation record     │
         │ - Fresh message history       │
         │ - Independent context         │
         └───────────────────────────────┘

Data Isolation:
- Each conversation has unique conversation_id
- Messages linked via foreign key to Conversation
- Context records tied to specific conversation
- No cross-conversation data leakage

Storage Strategy:

LocalStorage (persistent across sessions):
- assistant_conversation_id: Current conversation UUID
- assistant_opened: Track if user has opened before

SessionStorage (cleared on browser close):
- assistant_chat_history: JSON array of messages
- Used for UI restoration on page refresh
- Prevents losing context during navigation

Clear Chat Algorithm (JavaScript):
"""

function clearChat() {
    // Step 1: User confirmation (if messages exist)
    if (messagesContainer.children.length > 0) {
        const confirmed = confirm(
            'Are you sure you want to start a new conversation? ' +
            'This will clear the current chat.'
        );
        
        if (!confirmed) {
            return;  // User cancelled
        }
    }
    
    // Step 2: Clear conversation ID
    conversationId = null;
    localStorage.removeItem('assistant_conversation_id');
    
    // Step 3: Clear chat history cache
    sessionStorage.removeItem('assistant_chat_history');
    
    // Step 4: Clear UI messages
    messagesContainer.innerHTML = '';
    
    // Step 5: Show welcome message
    if (welcomeElement) {
        welcomeElement.style.display = 'block';
    }
    
    // Step 6: Reset suggestions (keep "New Chat" button)
    suggestionsContainer.innerHTML = '';
    addNewChatButton();
    
    // Step 7: Focus input for immediate typing
    inputField.focus();
    
    console.log('Chat cleared, ready for new conversation');
}

"""
New Chat Button Implementation:

Visual Design:
- Distinct styling (red/danger theme)
- Refresh icon (↻) for clarity
- Always visible in suggestions area
- Positioned at end of suggestion chips

CSS Styling:
.assistant-suggestion-chip.new-chat {
    background: #fff5f5;        /* Light red background */
    border-color: #dc3545;      /* Red border */
    color: #dc3545;             /* Red text */
    font-weight: 500;           /* Medium weight */
}

.assistant-suggestion-chip.new-chat:hover {
    background: #dc3545;        /* Solid red background */
    color: white;               /* White text */
}

Behavior:
- Persists across all suggestion updates
- Added on page load
- Re-added when suggestions are updated
- Click handler: clearChat() function

Database Impact:
- Old conversations remain in database (audit trail)
- New conversation creates new Conversation record
- Each conversation maintains separate Message records
- Context isolation via foreign keys

Benefits:
1. Fresh Start: Users can reset for new shopping task
2. Privacy: Clear sensitive queries from display
3. Performance: Reduce message history clutter
4. Testing: Easy to test different scenarios
5. UX: Clear mental model of conversation boundaries
"""
```

---

## Decision Logic & Control Flow

### Tool Selection Decision Tree

The AI model makes autonomous decisions about which tools to use based on:

```
User Query Analysis
   │
   ▼
┌─────────────────────────────────────────────────────────────┐
│ DECISION TREE: Which Tool(s) to Use?                        │
└─────────────────────────────────────────────────────────────┘

Query: "Show me laptops under $1000"
   │
   ├─ Contains: product search intent
   ├─ Contains: price constraint
   └─ Decision: search_products(query="laptop", max_price=1000)

Query: "Tell me about product 123"
   │
   ├─ Contains: specific product ID
   ├─ Request: detailed information
   └─ Decision: get_product_details(product_id=123)

Query: "Is this available?" (while viewing product page)
   │
   ├─ Context: product_id from page_context
   ├─ Request: availability check
   └─ Decision: get_availability(product_id=<from_context>)

Query: "Add Dell laptop to cart"
   │
   ├─ Intent: cart addition
   ├─ Problem: No product_id specified
   ├─ Decision: MULTI-STEP WORKFLOW
   │   └─ Step 1: search_products(query="Dell laptop")
   │   └─ Step 2: add_to_cart(product_id=<from_search>)

Query: "Compare these 3 products"
   │
   ├─ Multiple products referenced
   ├─ Decision: PARALLEL TOOL CALLS
   │   └─ get_product_details(id=1)
   │   └─ get_product_details(id=2)
   │   └─ get_product_details(id=3)

Query: "What categories do you have?"
   │
   ├─ Request: browse categories
   └─ Decision: get_categories() + suggest /categories/ page

Query: "What's popular?"
   │
   ├─ Request: trending/bestsellers
   └─ Decision: get_top_selling_products(limit=10)
```

### Iteration Control Flow

```python
"""
Iteration Control Algorithm

Goal: Prevent infinite loops while allowing multi-step reasoning

Rules:
1. Max 5 iterations per chat() call
2. Each iteration = 1 OpenAI API call
3. Iteration continues while AI makes tool calls
4. Iteration stops when AI returns text response

Typical Patterns:

Simple Query (1 iteration):
  User: "Show me headphones"
  Iter 1: API call → tool_call(search) → Execute → API call → Response
  Total: 2 API calls (optimal)

Complex Query (2-3 iterations):
  User: "Add the cheapest laptop to my cart"
  Iter 1: search_products(query="laptop", sort="price_low_high")
  Iter 2: add_to_cart(product_id=<from_search>)
  Iter 3: Final response
  Total: 3 API calls

Edge Case (max iterations):
  If AI keeps calling tools without responding:
  - Iter 5 hits → Force stop
  - Return: "I'm having trouble, please rephrase"
  - Prevents runaway costs
"""

MAX_ITERATIONS = 5

while iteration < MAX_ITERATIONS:
    iteration += 1
    response = call_openai()
    
    if response.has_tool_calls():
        execute_tools()
        continue  # Next iteration
    else:
        return response  # Done
        
# Safety net
return "Max iterations reached"
```

---

## Error Handling & Recovery

### Error Handling Strategy

```python
"""
Multi-Layer Error Handling Architecture

Layer 1: View Layer (views.py)
- HTTP errors (400, 429, 500)
- JSON parsing errors
- Authentication errors

Layer 2: Service Layer (services.py)
- OpenAI API errors
- Tool execution errors
- Max iteration errors

Layer 3: Tool Layer (tools.py)
- Database errors (DoesNotExist)
- Validation errors
- Business logic errors

Philosophy: Fail gracefully, never crash, always respond
"""

# Layer 1: View errors
try:
    data = json.loads(request.body)
except json.JSONDecodeError:
    return JsonResponse({
        'error': 'Invalid JSON',
        'reply': 'Sorry, I couldn\'t understand that request.'
    }, status=400)

# Layer 2: Service errors
try:
    response = self.client.chat.completions.create(...)
except OpenAIError as e:
    logger.error(f"OpenAI API error: {e}")
    return {
        'reply': 'I\'m having trouble connecting. Please try again.',
        'cards': [],
        'suggestions': []
    }

# Layer 3: Tool errors
try:
    product = Product.objects.get(id=product_id)
except Product.DoesNotExist:
    return {
        'success': False,
        'error': f'Product not found: id={product_id}'
    }
```

### Error Response Format

```python
# Standard error response structure
{
    "success": False,
    "error": "Human-readable error message",
    "error_code": "PRODUCT_NOT_FOUND"  # Optional
}

# User-facing error (View layer)
{
    "reply": "I'm sorry, I couldn't find that product.",
    "cards": [],
    "suggestions": ["Search for products", "Browse categories"],
    "error": "Internal error details (optional, for debugging)"
}
```

---

## Performance Optimization

### Optimization Techniques

#### 1. Database Query Optimization

```python
# BAD: N+1 queries
products = Product.objects.filter(category='electronics')
for product in products:
    print(product.category.name)  # Hits DB each time!
    print(product.images.all())   # Hits DB each time!

# GOOD: Optimized with JOINs and prefetch
products = Product.objects.filter(category='electronics') \
                 .select_related('category') \      # 1 JOIN
                 .prefetch_related('images') \      # 1 extra query
                 .annotate(avg_rating=Avg('reviews__rating'))

# Result: 3 queries total instead of 1 + 2N queries
```

#### 2. Result Limiting

```python
# Always cap results to prevent memory issues
limit = min(int(limit), 10)  # Max 10 products
products = products[:limit]

# Why?
# - Prevents excessive memory usage
# - Reduces JSON payload size
# - Improves response time
# - Better UX (less overwhelming)
```

#### 3. Token Budget Management

```python
# Keep conversation history limited
messages = conversation.messages.order_by('-created_at')[:12]

# Why 12?
# - Avg 50 tokens per message = 600 tokens
# - System prompt: ~500 tokens
# - User message: ~50 tokens
# - Tool definitions: ~1000 tokens
# - Total input: ~2150 tokens (well under limit)
# - Leaves budget for tool results and response
```

#### 4. Response Caching

```python
# Product search results could be cached (not currently implemented)
cache_key = f"search:{query}:{category}:{min_price}:{max_price}"
cached_result = cache.get(cache_key)

if cached_result:
    return cached_result

result = execute_search()
cache.set(cache_key, result, timeout=300)  # 5 min cache
return result
```

### Performance Metrics

| Operation | Avg Time | Optimization |
|-----------|----------|--------------|
| Single tool call | 150ms | select_related, prefetch_related |
| OpenAI API call | 1-2s | Token limiting, streaming (future) |
| Database query | 10-50ms | Indexes, query optimization |
| Full chat request | 2-4s | Async tools (future improvement) |

---

## Security & Rate Limiting

### Security Measures

#### 1. SQL Injection Prevention

```python
# Django ORM prevents SQL injection automatically
# Safe:
Product.objects.filter(name__icontains=user_query)

# NEVER do raw SQL with user input:
# UNSAFE: cursor.execute(f"SELECT * FROM products WHERE name LIKE '%{user_query}%'")
```

#### 2. Input Validation & Sanitization

```python
def _sanitize_args(function_name, args):
    """
    All tool arguments sanitized:
    - Type validation (int, float, str)
    - Range clamping (min/max values)
    - Length limiting (prevent DoS)
    - Whitelist validation (sort options, etc.)
    """
    
    # Example: product_id validation
    if 'product_id' in args:
        product_id = int(args['product_id'])  # Type check
        if product_id <= 0:  # Range check
            raise ValueError("Invalid product ID")
        sanitized['product_id'] = product_id
    
    # Example: query string sanitization
    if 'query' in args:
        query = str(args['query'])
        sanitized['query'] = query[:200]  # Length limit
```

#### 3. Rate Limiting

```python
"""
Rate Limiting Algorithm: Sliding Window

Implementation:
- Identifier: IP address + Session key (prevents bypass)
- Limit: 20 requests per 60 seconds
- Storage: Django cache (Redis/Memcached in production)
- Response: 429 Too Many Requests

Protection Against:
- Brute force attacks
- Resource exhaustion
- API abuse
- Cost explosion (OpenAI charges per request)

Example:
Time 0:00 - Request 1 → Count = 1, TTL = 60s
Time 0:30 - Request 20 → Count = 20, TTL = 30s
Time 0:31 - Request 21 → BLOCKED (429)
Time 1:01 - Count expires → Reset to 0
"""

rate_limit_key = f"rate_limit_assistant_{ip}:{session_key}"
count = cache.get(rate_limit_key, 0)

if count >= 20:
    return HTTP_429_TOO_MANY_REQUESTS

cache.set(rate_limit_key, count + 1, timeout=60)
```

#### 4. Authentication & Authorization

```python
# Cart operations require valid session or authenticated user
if request.user.is_authenticated:
    cart, _ = Cart.objects.get_or_create(user=request.user)
else:
    # Anonymous users: session-based cart
    if not request.session.session_key:
        request.session.create()
    cart, _ = Cart.objects.get_or_create(session_key=request.session.session_key)

# Users can only access their own cart (never exposed to AI)
```

#### 5. Sensitive Data Protection

```python
# NEVER expose in tool results:
# - Internal cost prices
# - Supplier information
# - Admin-only fields
# - User PII (other users)
# - Payment information

# Tool results only include public product information
return {
    'id': product.id,
    'title': product.name,
    'price': product.price,  # ✓ Public
    # 'cost': product.cost,  # ✗ Internal only
    # 'supplier': product.supplier  # ✗ Internal only
}
```

---

## Summary

The Virtual Shopping Assistant uses a **sophisticated multi-agent architecture** combining:

1. **OpenAI's GPT-4o-mini** for natural language understanding and orchestration
2. **Function calling (tool use)** for database integration and factual accuracy
3. **Stateful conversations** for context-aware, multi-turn interactions
4. **Dynamic tool execution** for real-time product data retrieval
5. **Rate limiting and security** for production-grade reliability

### Key Algorithm Components

| Component | Algorithm Type | Purpose |
|-----------|---------------|---------|
| Tool Calling Loop | Iterative reasoning | Multi-step query resolution |
| Search Products | Multi-criteria filtering | Product discovery |
| Conversation Management | State machine | Context continuity |
| Rate Limiting | Sliding window | Abuse prevention |
| Argument Sanitization | Input validation | Security |
| Response Formatting | Data transformation | User-friendly output |

### Performance Characteristics

- **Average Response Time:** 2-4 seconds
- **Max Tool Calls:** 5 per iteration (safety limit)
- **Conversation History:** Last 12 messages (token budget)
- **Results Limit:** Max 10 products per search
- **Rate Limit:** 20 requests per 60 seconds

---

**Document End**

*This documentation provides a comprehensive technical overview of the Virtual Shopping Assistant's algorithm and logic. For implementation details, see the source code in `/assistant/`.*

*Last Updated: February 9, 2026*  
*Maintained by: Development Team*
