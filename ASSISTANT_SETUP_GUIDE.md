# Virtual Shopping Assistant - Setup & Testing Guide

## Overview
The Virtual Shopping Assistant is a tool-based AI assistant powered by OpenAI that helps customers find products, answer questions about specifications and availability, provide recommendations, and assist with their shopping journey.

## Features
✅ **Product Search** - Natural language product search with filters
✅ **Product Recommendations** - Context-aware product suggestions
✅ **Product Details** - Specifications, pricing, and availability
✅ **Review Summaries** - Customer review insights and sentiment
✅ **Similar Products** - Find alternatives and related items
✅ **Category Browsing** - Explore product categories
✅ **Context-Aware** - Knows what page the user is viewing
✅ **Tool-Based** - Never hallucinates data, always grounds responses in DB
✅ **Mobile Responsive** - Works seamlessly on all devices

## Installation Steps

### 1. Install Dependencies

Add the OpenAI package to your requirements:

```bash
pip install openai
```

Or update `requirements.txt`:
```
openai>=1.12.0
```

Then install:
```bash
pip install -r requirements.txt
```

### 2. Configure Environment Variables

Add your OpenAI API key to your `.env` file:

```env
OPENAI_API_KEY=sk-your-api-key-here
OPENAI_MODEL=gpt-4o-mini
```

**Important:** Never commit your API key to version control!

### 3. Run Database Migrations

Create and apply migrations for the assistant app:

```bash
python manage.py makemigrations assistant
python manage.py migrate
```

This creates the following tables:
- `assistant_conversation` - Stores conversation threads
- `assistant_message` - Stores individual messages
- `assistant_conversationcontext` - Stores page context for conversations

### 4. Collect Static Files

Collect the assistant CSS and JavaScript files:

```bash
python manage.py collectstatic --noinput
```

This copies:
- `static/assistant/assistant.css`
- `static/assistant/assistant.js`

### 5. Verify Installation

Start the development server:

```bash
python manage.py runserver
```

Visit any page on your site. You should see:
- A purple floating button in the bottom-right corner
- Clicking it opens the chat drawer
- The assistant greets you with an initial message

## Project Structure

```
assistant/
├── __init__.py
├── apps.py                  # App configuration
├── models.py               # Conversation, Message, ConversationContext models
├── admin.py                # Django admin configuration
├── urls.py                 # URL patterns
├── views.py                # Chat endpoint and context retrieval
├── services.py             # OpenAI orchestration and tool calling loop
├── tools.py                # Tool implementations (DB queries)
└── prompts.py              # System prompt and tool definitions

templates/assistant/
└── widget.html             # Chat widget UI

static/assistant/
├── assistant.css           # Widget styles
└── assistant.js            # Frontend logic and API communication
```

## How It Works

### Backend Architecture

1. **User sends message** → Django view receives POST request
2. **Context extraction** → Page context (product_id, category, cart) included
3. **Conversation retrieval** → Load last 12 messages from database
4. **OpenAI orchestration** → Services layer manages tool-calling loop:
   - Send messages + tool schemas to OpenAI
   - If tool calls returned → Execute tools and send results back
   - Loop until final response generated
5. **Response formatting** → Extract product cards from tool results
6. **Store in database** → Save messages for conversation continuity

### Tool-Calling Loop

```
User Message → OpenAI API (with tools)
                    ↓
              Tool Calls?
                    ↓ Yes
              Execute Tools
              (search_products, get_product_details, etc.)
                    ↓
              Send Tool Results → OpenAI API
                    ↓
              Final Response → Return to User
```

### Available Tools

1. **search_products** - Search with filters (price, category, rating, stock)
2. **get_product_details** - Full product information
3. **get_product_specs** - Technical specifications
4. **get_availability** - Stock status and quantity
5. **get_reviews_summary** - Customer reviews and sentiment
6. **get_similar_products** - Related/alternative products
7. **get_categories** - Browse all categories

### Frontend UI

- **Floating Action Button (FAB)** - Always visible, bottom-right
- **Chat Drawer** - Slides in from bottom-right (full-screen on mobile)
- **Message Bubbles** - User and assistant messages
- **Product Cards** - Rich product previews with images, prices, ratings
- **Suggestion Chips** - Quick action buttons
- **Loading Indicator** - Animated typing dots

## Testing Guide

### 1. Basic Conversation Test

**Open the assistant and try:**

```
User: "Hi"
Expected: Friendly greeting and offer to help

User: "What can you help me with?"
Expected: List of capabilities (search, recommendations, etc.)
```

### 2. Product Search Tests

```
User: "Show me laptops under $1000"
Expected: 
- Calls search_products tool
- Returns product cards with laptops
- Prices all under $1000
- Shows stock status

User: "I need a laptop for gaming"
Expected:
- Searches for gaming laptops
- Provides 3-5 recommendations
- Explains why they're good for gaming
```

### 3. Product Details Tests

Navigate to a product page, then:

```
User: "Tell me more about this product"
Expected:
- Recognizes current product (from page context)
- Calls get_product_details
- Provides comprehensive description
- Mentions key features

User: "What are the specifications?"
Expected:
- Calls get_product_specs
- Lists technical specifications
- Formatted clearly
```

### 4. Availability Tests

```
User: "Is this in stock?"
Expected:
- Calls get_availability
- Reports current stock level
- States "In Stock", "Low Stock", or "Out of Stock"

User: "When will it be available?"
Expected:
- Checks stock status
- Provides honest answer (or says unknown if not available)
```

### 5. Reviews Tests

```
User: "What do customers say about this?"
Expected:
- Calls get_reviews_summary
- Reports average rating
- Shares pros and cons
- Mentions sentiment (positive/neutral/negative)
```

### 6. Recommendations Tests

```
User: "Recommend me a phone with good camera"
Expected:
- Searches for phones
- Filters by relevant criteria
- Provides 3-5 options
- Explains camera features
- Asks follow-up preference question

User: "Show me similar products"
Expected:
- Calls get_similar_products
- Returns alternatives in same category
- Similar price range
```

### 7. Category Browsing

```
User: "What categories do you have?"
Expected:
- Calls get_categories
- Lists all active categories
- Shows product counts

User: "Show me electronics"
Expected:
- Searches electronics category
- Returns relevant products
```

### 8. Context Awareness Tests

**On Product Page:**
```
User: "Is this available?"
Expected: Knows which product you're viewing
```

**On Category Page:**
```
User: "Show me more like these"
Expected: Knows current category context
```

**With Items in Cart:**
```
User: "What's in my cart?"
Expected: Aware of cart item count (from context)
```

### 9. Error Handling Tests

```
User: "Show me product ID 999999"
Expected:
- Tool returns error
- Assistant says "Product not found"
- Offers alternative searches

User: "Random gibberish xyzabc"
Expected:
- Handles gracefully
- Asks for clarification
```

### 10. Rate Limiting Test

Send 20+ messages quickly:
- Expected: 429 error after limit
- Message: "Too many requests. Please wait."

## Advanced Configuration

### Adjust Tool Response Limit

In `assistant/tools.py`, modify limits:

```python
def search_products(..., limit=5):
    limit = min(int(limit), 10)  # Change max from 10
```

### Customize System Prompt

Edit `assistant/prompts.py`:

```python
SYSTEM_PROMPT = """
Your custom instructions here...
"""
```

### Change OpenAI Model

In `.env`:
```env
OPENAI_MODEL=gpt-4-turbo-preview  # or gpt-4, gpt-4o, etc.
```

### Adjust Conversation History

In `assistant/views.py`:

```python
messages = _get_conversation_history(conversation, limit=12)  # Change from 12
```

### Modify Rate Limiting

In `assistant/views.py`:

```python
@rate_limit(max_requests=20, window_seconds=60)  # Adjust limits
```

### Custom Styling

Edit `static/assistant/assistant.css` to match your brand:

```css
.assistant-fab {
    background: linear-gradient(135deg, #YOUR_COLOR_1, #YOUR_COLOR_2);
}
```

## Monitoring & Debugging

### View Conversations in Admin

1. Go to `/admin/`
2. Navigate to "Assistant" section
3. View:
   - **Conversations** - All chat threads
   - **Messages** - Individual messages
   - **Conversation Contexts** - Page context data

### Check Logs

```python
import logging
logger = logging.getLogger('assistant')
```

Logs include:
- Tool execution
- API errors
- Rate limiting events

### Database Queries

Monitor tool performance:

```python
from django.db import connection
print(connection.queries)  # In DEBUG mode
```

## Security Considerations

### ✅ Implemented

1. **Rate Limiting** - 20 requests per minute per IP/session
2. **Input Validation** - All tool arguments validated and sanitized
3. **CSRF Protection** - Django CSRF tokens required
4. **PII Redaction** - No sensitive data in responses
5. **Tool Grounding** - Never hallucinates data
6. **Admin-Only Fields** - Cost, supplier info not exposed

### 🔒 Production Recommendations

1. **Enable HTTPS** - Always use SSL in production
2. **Set ALLOWED_HOSTS** - Restrict to your domain
3. **Rate Limit Globally** - Use Django middleware or nginx
4. **Monitor API Costs** - Set OpenAI usage alerts
5. **Cache Aggressively** - Reduce API calls for common queries
6. **Log Monitoring** - Track errors and abuse patterns

## Troubleshooting

### Issue: Widget Not Showing

**Check:**
1. Is `assistant` in `INSTALLED_APPS`?
2. Did you run `collectstatic`?
3. Is `{% include 'assistant/widget.html' %}` in `base.html`?
4. Check browser console for JavaScript errors

### Issue: "OpenAI API Error"

**Check:**
1. Is `OPENAI_API_KEY` set in `.env`?
2. Is the key valid and has credits?
3. Check Django logs for specific error
4. Verify network connectivity

### Issue: Tools Not Working

**Check:**
1. Are products in the database?
2. Are products marked as `is_active=True`?
3. Check tool logs in console
4. Verify database queries return data

### Issue: Styling Broken

**Check:**
1. Run `collectstatic` again
2. Hard refresh browser (Ctrl+F5)
3. Check if CSS file is accessible: `/static/assistant/assistant.css`
4. Check for CSS conflicts with existing styles

### Issue: Rate Limited Too Fast

**Adjust in `views.py`:**
```python
@rate_limit(max_requests=50, window_seconds=60)  # Increase limit
```

## Performance Optimization

### 1. Enable Caching

Product details and specs are cached for 5-10 minutes by default.

Increase cache time in `tools.py`:
```python
cache.set(cache_key, result, 600)  # 10 minutes → increase
```

### 2. Database Indexes

Already optimized with:
- Index on `conversation_id`
- Index on `product.slug`
- Index on `category`

### 3. Reduce Token Usage

- Limit conversation history to 8-10 messages
- Use shorter system prompts
- Request concise responses

### 4. Optimize Images

- Use optimized product images
- Implement lazy loading
- Consider CDN for media files

## API Costs Estimation

**OpenAI GPT-4o-mini pricing (as of 2024):**
- Input: $0.15 per 1M tokens
- Output: $0.60 per 1M tokens

**Typical conversation:**
- System prompt: ~300 tokens
- User message: ~20 tokens
- Tool calls: ~100 tokens
- Assistant response: ~150 tokens
- **Total per exchange: ~570 tokens**

**Monthly estimate (1000 conversations):**
- ~570,000 tokens
- Cost: ~$0.30-$0.50

**Note:** Costs vary based on conversation length and tool usage.

## Next Steps

### Potential Enhancements

1. **Add to Cart Tool** - Allow assistant to add products to cart
2. **Order Tracking** - Check order status via assistant
3. **Voice Input** - Speech-to-text integration
4. **Multi-Language** - Support multiple languages
5. **Analytics Dashboard** - Track popular queries and conversions
6. **A/B Testing** - Test different prompts and UIs
7. **Personalization** - Use browsing history for better recommendations
8. **Proactive Suggestions** - Offer help based on user behavior

### Integration Opportunities

1. **Email Notifications** - Send product recommendations
2. **SMS Support** - Extend to WhatsApp/SMS
3. **Social Media** - Integrate with Facebook Messenger
4. **Live Chat Handoff** - Transfer to human agent
5. **Analytics Integration** - Google Analytics events

## Support

For issues or questions:
1. Check Django logs: `python manage.py runserver` output
2. Review browser console for frontend errors
3. Check OpenAI dashboard for API issues
4. Review this documentation

## Testing Checklist

Before going live, verify:

- [ ] OpenAI API key configured and working
- [ ] Database migrations applied
- [ ] Static files collected
- [ ] Widget appears on all pages
- [ ] Search functionality working
- [ ] Product cards rendering correctly
- [ ] Mobile responsive layout tested
- [ ] Rate limiting functioning
- [ ] Error handling graceful
- [ ] Conversation persistence working
- [ ] Page context detection accurate
- [ ] Admin panel accessible
- [ ] Logs showing tool executions
- [ ] No console errors in browser
- [ ] HTTPS enabled (production)

## Success Metrics

Track these KPIs:
1. **Engagement** - % of visitors who open assistant
2. **Conversation Rate** - Average messages per session
3. **Conversion** - % who view recommended products
4. **Satisfaction** - Positive sentiment in conversations
5. **Tool Usage** - Most frequently called tools
6. **Response Time** - Average API latency
7. **Error Rate** - % of failed requests

---

**Implementation Complete! The Virtual Shopping Assistant is ready for testing.** 🎉
